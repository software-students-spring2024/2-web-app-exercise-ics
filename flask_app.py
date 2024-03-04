from flask import Flask, render_template, request, jsonify, redirect
import flask_login
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import bcrypt
from datetime import date
import uuid
import json
from bson import json_util

###############################################
# MONGO AND FLASK SETUP
###############################################
load_dotenv()

uri = "mongodb+srv://admin:pass@cluster0.p7jcted.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi("1"), uuidRepresentation="standard")
db = client.flask_db
# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

app = Flask(__name__)

###############################################
# FLASK LOGIN SETUP
###############################################
app.secret_key = "secret key"  # required for flask login
login_manager = flask_login.LoginManager()
login_manager.session_protection = "strong"
login_manager.init_app(app)


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
    username = request.form.get("username")
    if not db.users.find_one({"username": username}):
        return
    user = User()
    user.id = username
    return user


@login_manager.unauthorized_handler
def unauthorized_handler():
    return "<p>You must be logged in.<br><a href='/login'>Login</a></p>", 401


# Hash passwords using bcrypt
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


###############################################
# ROUTES
###############################################


@app.route("/")
def hello_world():
    return render_template("index.html")


# Login Signup Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login/login.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # find user in db
        user = db.users.find_one({"username": username})
        # verify user
        if user and bcrypt.checkpw(
            password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            user = User()
            user.id = username
            flask_login.login_user(user)
            return jsonify(
                {"success": True, "message": "Login successful", "username": username}
            )
        else:
            return jsonify({"success": False, "message": "Login unsuccessful"})


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("login/signup.html")
    if request.method == "POST":
        # get form data
        username = request.form.get("username")
        found_user_doc = db.users.find_one({"username": username})
        if found_user_doc:
            return jsonify({"success": False, "message": "Username taken"})

        password = hash_password(request.form.get("password"))
        doc = {"username": username, "password": password}
        db.users.insert_one(doc)

        # flask login
        user = User()
        user.id = username
        flask_login.login_user(user)

        return jsonify({"success": True, "message": "User signed up"})


@app.route("/addrecipe", methods=["GET", "POST"])
@flask_login.login_required
def add_recipe():
    name = flask_login.current_user.id
    if name == None:
        return redirect("/unathorized")
    if request.method == "GET":
        name = flask_login.current_user.id
        return render_template("home/add-recipe/add-recipe.html", name=name)
    if request.method == "POST":
        doc = {
            "recipeId": str(uuid.uuid4()),
            "date": str(date.today().strftime("%B %d, %Y")),
            "author": flask_login.current_user.id,
            "dishName": request.form.get("dishName"),
            "ingredientsList": request.form.get("ingredientsList"),
            "instructions": request.form.get("instructions"),
        }
        db.recipes.insert_one(doc)
        return jsonify({"success": True, "message": "Added new entry"})


@app.route("/recipe", methods=["GET"])
@flask_login.login_required
def recipe_page():
    name = flask_login.current_user.id
    if name == None:
        return redirect("/unathorized")
    if request.method == "GET":
        id = request.args.get("id")
        return render_template("home/recipe/recipe.html", id=id)


@app.route("/recipe_details", methods=["GET"])
@flask_login.login_required
def recipe_details():
    name = flask_login.current_user.id
    if name == None:
        return redirect("/unathorized")
    if request.method == "GET":
        id = request.args.get("id")
        doc = db.recipes.find_one({"recipeId": id})

        editable = False
        if doc["author"] == name:
            editable = True

        return jsonify(
            {
                "success": True,
                "dishName": doc["dishName"],
                "instructions": doc["instructions"],
                "author": doc["author"],
                "ingredients": doc["ingredientsList"],
                "date": doc["date"],
                "editable": editable,
            }
        )


@app.route("/addrecipe/success", methods=["GET"])
@flask_login.login_required
def add_recipes_success():
    name = flask_login.current_user.id
    if name == None:
        return redirect("/unathorized")
    return render_template("home/add-recipe/success.html")

@app.route("/recipe/update-success", methods=["GET"])
@flask_login.login_required
def update_recipe_success():
    name = flask_login.current_user.id
    if name == None:
        return redirect("/unathorized")
    return render_template("home/recipe/update-success.html")


@app.route("/recipes", methods=["GET"])
@flask_login.login_required
def get_recipes():
    if request.method == "GET":
        all_recipes_list = list(db.recipes.find({}))
        return json.loads(json_util.dumps(all_recipes_list))


@app.route("/myrecipes", methods=["GET", "POST"])
@flask_login.login_required
def my_recipes():
    name = flask_login.current_user.id
    if name == None:
        return redirect("/unathorized")
    if request.method == "GET":
        return render_template("home/recipe/my-recipes.html", name=name)
    if request.method == "POST":
        name = flask_login.current_user.id
        my_recipes_list = list(db.recipes.find({"author": name}))
        return json.loads(json_util.dumps(my_recipes_list))


@app.route("/recipe/delete", methods=["GET", "POST"])
@flask_login.login_required
def delete_recipe():
    name = flask_login.current_user.id
    if name == None:
        return redirect("/unathorized")
    if request.method == "GET":
        return render_template("home/recipe/delete-recipe.html", name=name)
    if request.method == "POST":
        recipeId = request.args.get("id")
        print(recipeId)
        db.recipes.delete_one({"recipeId": recipeId})
        # return jsonify({"success": True, "message": "Deleted recipe with id " + id})
        return jsonify({"success": True})

@app.route("/recipe/edit", methods=["GET", "POST"])
@flask_login.login_required
def edit_recipe():
    # redirect unauthorized if no user or user not original author
    if request.method == "GET":
        recipeId = request.args.get("id")
    else:
        recipeId = request.form.get("id")
    foundRecipe = db.recipes.find_one({"recipeId": recipeId})
    if foundRecipe["author"] != flask_login.current_user.id:
        return redirect("/unathorized")
    name = flask_login.current_user.id
    if name == None:
        return redirect("/unathorized")
    
    if request.method == "GET":
        id = request.args.get("id")
        originalRecipe = db.recipes.find_one({"recipeId": id})
        doc = originalRecipe
        print(doc)
        return render_template("home/recipe/edit-recipe.html", doc=json.loads(json_util.dumps(doc)), name=name)
    if request.method == "POST":
        doc = {
            "recipeId": recipeId,
            "lastUpdated": str(date.today().strftime("%B %d, %Y")),
            "author": flask_login.current_user.id,
            "dishName": request.form.get("dishName"),
            "ingredientsList": request.form.get("ingredientsList"),
            "instructions": request.form.get("instructions"),
        }
        db.recipes.update_one({"recipeId": recipeId}, {"$set": doc})
        return jsonify({"success": True, "message": "Updated entry"})

# Home Routes
@app.route("/home")
@flask_login.login_required
def home():
    name = flask_login.current_user.id
    if name == None:
        return redirect("/unathorized")
    return render_template("home/home.html", name=name)


# unauthorized
@app.route("/unathorized")
@flask_login.login_required
def unauthorized():
    return render_template("login/unauthorized.html")


# actions
@app.route("/delete")
@flask_login.login_required
def delete():
    name = flask_login.current_user.id
    if name == None:
        return redirect("/unathorized")
    db.recipes.delete_many({})
    return jsonify({"success": True})


@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return jsonify({"success": True, "message": "Logged out"})


app.run(debug=True)
