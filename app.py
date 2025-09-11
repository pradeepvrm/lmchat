from flask import Flask, request, jsonify, render_template
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    base_url=os.getenv('base_url'),
    api_key=os.getenv('api_key')
)

# model = 'lightning-ai/gpt-oss-20b'

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

    try:
        response = client.chat.completions.create(
            model= model,
            messages=history
        )
        
        # Extract the assistant's message from the response
        assistant_message = response.choices[0].message.content.strip()
        history.append({"role": "assistant", "content": assistant_message})
        return jsonify({"response": assistant_message, "history":history})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
