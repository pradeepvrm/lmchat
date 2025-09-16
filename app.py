from flask import Flask, request, jsonify, render_template, Response
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    base_url=os.getenv('base_url'),
    api_key=os.getenv('api_key')
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat/<string:model>', methods=['POST'])
def chat(model):
    # Get the message from the POST request JSON data
    data = request.json
    user_message = data.get("message")
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "No message provided."}), 400

    if not history:
        history = [{"role": "system", "content": "You are a helpful assistant."}]
    history.append({"role": "user", "content": user_message})

    def generate(history):
        try:
            full_response = ""
            response = client.chat.completions.create(
                model= model,
                messages=history, 
                stream=True,
            )

            for chunk in response:
                if (hasattr(chunk, 'choices') and 
                    len(chunk.choices) > 0 and 
                    hasattr(chunk.choices[0], 'delta') and 
                    hasattr(chunk.choices[0].delta, 'content') and
                    chunk.choices[0].delta.content is not None):
                    
                    content = chunk.choices[0].delta.content
                    print(content, end='') # debugging remove later
                    full_response += content
                    # Send each chunk as JSON
                    yield f"data: {json.dumps({'content': content, 'type': 'chunk'})}\n\n"


            history.append({"role": "assistant", "content": full_response})

            if len(history) >= 9:
                history = [history[0]] + history[-10:]

            yield f"data: {json.dumps({'content': '', 'type': 'end', 'history': history})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'content': f'Error: {str(e)}', 'type': 'error'})}\n\n"

    return Response(generate(history), mimetype='text/plain', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type'
    })

if __name__ == '__main__':
    app.run(debug=True)
