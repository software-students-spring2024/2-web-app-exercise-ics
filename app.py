from flask import Flask, redirect, request
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

client = MongoClient(os.environ.get("MONGO_URI"))
db = client["testdb"]

app = Flask(__name__)

@app.route("/")
def hello():
    return "<p>Hello World!</p><br><a href='/testform'>Test Form</a>"

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == 'GET':
        return """
        <form action="/signup" method="post">
            <label for="username">Username:</label><br>
            <input type="text" id="username" name="username" required><br>
            <label for="password">Password:</label><br>
            <input type="password" id="password" name="password" required><br>
            <label for="password">Confirm Password:</label><br>
            <input type="password" id="confirmpassword" name="confirmpassword" required><br>
            <input type="submit" value="Submit" onclick="return check()">
        </form>
        <script type="text/javascript">
            function check() {
                var password = document.getElementById("password").value;
                var confirmPassword = document.getElementById("confirmpassword").value;
                if (password != confirmPassword) {
                    alert("Passwords do not match.");
                    return false;
                }
                return true;
            }
        </script>
        """
    else:
        username = request.form['username']
        password = hash_password(request.form['password'])
        doc = {
            "username": username,
            "password": password
        }
        db.users.insert_one(doc)
        return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'GET':
        return """
        <form action="/login" method="post">
            <label for="username">Username:</label><br>
            <input type="text" id="username" name="username" required><br>
            <label for="password">Password:</label><br>
            <input type="password" id="password" name="password" required><br>
            <input type="submit" value="Submit">
        </form>
        """
    else:
        username = request.form['username']
        password = request.form['password']
        user = db.users.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return "<p>Login successful</p>"
        else:
            return "<p>Login failed</p>"
        

@app.route("/recipetest")
def mongo_test():
    docs = db.testrecipes.find()
    s = ""
    for doc in docs:
        for key in doc:
            s += f"{key}: {doc[key]}<br>"
        s += "<br>"
    return f"<p>{s}</p>"

@app.route("/testform", methods=["GET", "POST"])
def test_form():
    if request.method == 'GET':
        return """
        <form action="/testform" method="post">
            <label for="name">Name:</label><br>
            <input type="text" id="recipeName" name="recipeName" autocomplete="off"><br>
            <label for="ingredient">Ingredient:</label><br>
            <input type="text" id="ingredient" name="ingredient" autocomplete="off"><br>
            <input type="submit" value="Submit">
        </form>
        """
    else: # POST
        recipeName = request.form['recipeName']
        ingredient = request.form['ingredient']
        doc = {
            "recipeName": recipeName,
            "ingredient": ingredient
        }
        mongoid = db.testrecipes.insert_one(doc)
        return f"<p>Inserted: {mongoid}</p><br><a href='/recipetest'>View Recipes</a>"