from flask import Flask, redirect, request
import flask_login
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import bcrypt
from bson.objectid import ObjectId

###############################################
# MONGO AND FLASK SETUP
###############################################
load_dotenv()
login_manager = flask_login.LoginManager()

client = MongoClient(os.environ.get("MONGO_URI"))
db = client["testdb"]

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") # required for flask login
login_manager.init_app(app)

###############################################
# FLASK LOGIN SETUP
###############################################
class User(flask_login.UserMixin):
    pass
@login_manager.user_loader
def user_loader(username):
    if not db.users.find_one({"username": username}):
        return
    user = User()
    user.id = username
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if not db.users.find_one({"username": username}):
        return
    user = User()
    user.id = username
    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return "<p>You must be logged in.<br><a href='/login'>Login</a></p>", 401

###############################################
# ROUTES
###############################################
@app.route("/")
def hello():
    return """
    <p>Hello World!</p><br>
    <a href='/recipetest'>View recipes</a><br>
    <a href='/testform'>Test Form</a><br>
    <a href='/login'>Login</a><br>
    <a href='/signup'>Sign Up</a>
    """

# Hash passwords using bcrypt
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
            user = User()
            user.id = username
            flask_login.login_user(user)
            return redirect("/profile")
        else:
            return "<p>Login failed</p>"
        
@app.route("/profile")
@flask_login.login_required
def profile():
    s = ""
    user = db.users.find_one({"username": flask_login.current_user.id})
    if "createdRecipes" in user:
        for recipe in user["createdRecipes"]:
            recipe = db.testrecipes.find_one({"_id": recipe})
            s += f"{recipe['recipeName']}<br>"
    return f"""
    <p>Logged in as: {flask_login.current_user.id}</p><br>
    <p>Created Recipes:<br>{s}</p>
    <a href='/'>Home</a><br><a href='/logout'>Logout</a>
    """

@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect("/")

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
@flask_login.login_required
def test_form():
    if request.method == 'GET':
        return """
        <form action="/testform" method="post">
            <label for="name">Name:</label><br>
            <input type="text" id="recipeName" name="recipeName" autocomplete="off" required><br>
            <label for="ingredient">Ingredients:</label><br>
            <textarea id="ingredients" name="ingredients" autocomplete="off" rows="5" cols="50" placeholder="Add each ingredient on a new line" required></textarea><br>
            <label for="directions">Directions:</label><br>
            <textarea id="directions" name="directions" autocomplete="off" rows="5" cols="50" required></textarea><br>
            <input type="submit" value="Submit">
        </form>
        """
    else: # POST
        recipeName = request.form['recipeName']
        ingredients = request.form['ingredients']
        ingredients = ingredients.split(os.linesep)
        directions = request.form['directions']
        doc = {
            "recipeName": recipeName,
            "ingredients": ingredients,
            "directions": directions,
            "createdBy": flask_login.current_user.id
        }
        mongoid = db.testrecipes.insert_one(doc)
        if mongoid.acknowledged:
            mongoid = ObjectId(mongoid.inserted_id)
            pushResult = db.users.update_one(
                {"username": flask_login.current_user.id}, 
                {"$push": {"createdRecipes": mongoid}})
            if not pushResult.acknowledged or pushResult.modified_count != 1:
                mongoid = "Failed to insert"
        else:
            mongoid = "Failed to insert"
        return f"<p>Inserted: {mongoid}</p><br><a href='/recipetest'>View Recipes</a><br><a href='/profile'>Profile</a>"