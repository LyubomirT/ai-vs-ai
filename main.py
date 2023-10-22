# Simply a flask app that will allow us to upload two A.I. model instructions, and then they will begin fighting each other.

# Imports
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import random
import requests
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json

load_dotenv()

# Constants
COHERE_API_KEY = os.getenv("KEY")
STORAGE_TARGET_DIR = os.getenv("STORAGE_TARGET")

# Flask app
app = Flask(__name__)
app.secret_key = "secret_key"

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)

# User class
class User(UserMixin):
    def __init__(self, uid, username, display_name, password, email, champions=[]):
        self.id = uid
        self.username = username
        self.display_name = display_name
        self.password = password
        self.email = email
        self.champions = champions

# User database (temporary storage)
users = {}

@login_manager.user_loader
def load_user(uid):
    global users
    if uid in users:
        return users[uid]
    else:
        return None

def load_user_data():
    global users
    if os.path.exists(STORAGE_TARGET_DIR):
        with open(STORAGE_TARGET_DIR, "r") as f:
            users = json.loads(f.read())
            # Convert all UIDs to integers
            for uid in users:
                users[uid]["id"] = int(uid)
            
            # Convert all champion UIDs to integers
            for uid in users:
                for champion in users[uid]["champions"]:
                    champion["id"] = int(champion["id"])
            
            # Create the appropriate User objects
            for uid in users:
                user = users[uid]
                users[uid] = User(
                    user["id"],
                    user["username"],
                    user["display_name"],
                    user["password"],
                    user["email"],
                    user["champions"]
                )
            

load_user_data()

def save_user_data():
    global users
    # Prepare the users dictionary for serialization
    users_serializable = {}
    for user in users.values():
        users_serializable[user.id] = {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "password": user.password,
            "email": user.email,
            "champions": user.champions
        }
    with open(STORAGE_TARGET_DIR, "w") as f:
        f.write(json.dumps(users_serializable))
    # Update the global users dictionary
    users = users_serializable





@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['GET'])
@login_required
def chat():
    return render_template('chat.html')

@app.route('/chat_back', methods=['POST'])
@login_required
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

"""
<!DOCTYPE html>
<html>
    <head>
        <title>AI vs AI - Ultimate Chatbot Battles | Create</title>
        <link rel="stylesheet" href="{{url_for('static', filename='css/create.css')}}">
    </head>
    <body>
        <header>
            <h1>AI vs AI - Ultimate Chatbot Battles</h1>
        </header>
        <main>
            <section class="create">
                <h2>Create your champion</h2>
                <form action="{{url_for('create')}}" method="POST">
                    <label for="name">Name</label>
                    <input type="text" name="name" id="name" placeholder="Enter your champion's name" required>
                    <label for="description">Description</label>
                    <textarea name="description" id="description" cols="30" rows="10" placeholder="Enter your champion's description" required maxlength="500"></textarea>
                    <label for="instructions">Instructions</label>
                    <textarea name="instructions" id="instructions" cols="30" rows="10" placeholder="Enter your champion's instructions" required maxlength="6000"></textarea>
                    <label for="greeting">Greeting</label>
                    <textarea name="greeting" id="greeting" cols="30" rows="10" placeholder="Enter your champion's greeting" required maxlength="500"></textarea>
                    <input type="submit" value="Create">
                </form>
            </section>
        </main>
        <footer>
            <p>AI vs AI is a project maintained by <a href="https://github.com/LyubomirT">LyubomirT</a>.</p>
        </footer>
    </body>
</html>
"""

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        # Get the form data
        name = request.form['name']
        description = request.form['description']
        instructions = request.form['instructions']
        greeting = request.form['greeting']

        # Create the champion
        champion = {
            "id": random.randint(1, 1000000),
            "name": name,
            "description": description,
            "instructions": instructions,
            "greeting": greeting
        }

        # Add the champion to the user's list of champions
        current_user.champions.append(champion)

        # Save the user data
        save_user_data()

        # Redirect to the user's profile page
        return redirect(url_for('profile', username=current_user.username))

    else:
        return render_template('create.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        display_name = request.form['display_name']
        password = request.form['password']
        email = request.form['email']

        if username in users:
            return "Username already exists! Please choose a different username."

        uid = str(random.randint(1000, 9999))
        user = User(uid, username, display_name, password, email, champions=[])
        users[uid] = user
        save_user_data()

        return redirect(url_for('index'))

    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        for user in users.values():
            if user.username == username and user.password == password:
                login_user(user)
                return redirect(url_for('index'))

        return "Invalid username or password"

    return render_template('signin.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile/<username>', methods=['GET'])
def profile(username):
    print("Username:", username)
    checkPassed = False
    # If such a user doesn't exist, return a 404
    for user in users.values():
        if user.username == username:
            checkPassed = True
            break
    if not checkPassed:
        return render_template('404.html'), 404
    else:
        # Get the user by username
        for user in users.values():
            if user.username == username:
                user = user
                break
        champions = user.champions
        return render_template('profile.html', user=user, champions=champions)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)
