# Simply a flask app that will allow us to upload two A.I. model instructions, and then they will begin fighting each other.

# Imports
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import subprocess
import shutil
import time
import random
import requests
from dotenv import load_dotenv

load_dotenv()

# Constants
COHERE_API_KEY = os.getenv("KEY")

# Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['GET'])
def chat():
    return render_template('chat.html')

@app.route('/chat_back', methods=['POST'])
def chat_back():
    # Get the message, the instructions, the model name, the description, the author, the greeting, and the chat history
    message = request.form['message']
    instructions = request.form['instructions']
    model_name = request.form['model_name']
    description = request.form['description']
    author = request.form['author']
    greeting = request.form['greeting']

    # Get the chat history
    chat_history = request.form['chat_history']

    # Get the response from the A.I. model
    url = "https://api.cohere.ai/v1/chat"

    payload = {
        "message": message,
        "model": "command",
        "stream": False,
        "preamble_override": instructions,
        "chat_history": chat_history,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {COHERE_API_KEY}",
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    # Get the response text
    response_text = response.json()['text']
    print("Response text:", response_text)

    # Return the response text
    return response_text

@app.route('/create', methods=['GET', 'POST'])
def create():
    return render_template('create.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)

    
