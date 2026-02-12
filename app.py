from flask import Flask, request, jsonify, render_template, Response, session, url_for, redirect
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import auth
from database import init_db
import db_helpers

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('secret_key') 

# Initialize database
init_db()

client = OpenAI(
    base_url=os.getenv('base_url'),
    api_key=os.getenv('api_key')
)

@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user = auth.create(name, email, password)

        if user:
            session['user_id'] = user['userId']
            return render_template('index.html')
        else:
            return f"Sign Up failed", 400
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = auth.create_session(email, password)
        
        if user:
            session['user_id'] = user['userId']
            # print(user['userId'])
            return redirect(url_for('home'))
        else:
            return f"Login failed", 400
        
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# get all conversations
@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']
    conversations = db_helpers.get_user_conversations(user_id)
    return jsonify(conversations)

# get a specific conversation
@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    history = db_helpers.get_conversation_history(conversation_id)
    return jsonify({"history": history})

# delete a conversation
@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']
    success = db_helpers.delete_conversation(conversation_id, user_id)
    
    if success:
        return jsonify({"message": "Conversation deleted"})
    return jsonify({"error": "Conversation not found"}), 404

@app.route('/api/chat/<string:model>', methods=['POST'])
def chat(model):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']
    data = request.json
    user_message = data.get("message")
    conversation_id = data.get("conversation_id")
    
    if not user_message:
        return jsonify({"error": "No message provided."}), 400

    # Create new conversation if none exists
    if not conversation_id:
        conversation_id = db_helpers.create_conversation(user_id, model)
    
    # Get conversation history from database
    history = db_helpers.get_conversation_history(conversation_id)
    
    # Add system message if this is a new conversation
    if not history:
        history = [{"role": "system", "content": "You are a helpful assistant."}]
        db_helpers.add_message(conversation_id, "system", "You are a helpful assistant.")
    
    # Save user message to database
    db_helpers.add_message(conversation_id, "user", user_message)
    history.append({"role": "user", "content": user_message})

    def generate(history, conversation_id):
        try:
            full_response = ""
            response = client.chat.completions.create(
                model=model,
                messages=history, 
                stream=True,
            )

            for chunk in response:
                if chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'content': content, 'type': 'chunk'})}\n\n"
                
                if chunk.choices[0].finish_reason == "stop":
                    break

            # Save assistant response to database
            db_helpers.add_message(conversation_id, "assistant", full_response)
            
            yield f"data: {json.dumps({'content': '', 'type': 'end', 'conversation_id': conversation_id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'content': f'Error: {str(e)}', 'type': 'error'})}\n\n"

    return Response(generate(history, conversation_id), mimetype='text/plain', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type'
    })

if __name__ == '__main__':
    app.run(debug=True)
