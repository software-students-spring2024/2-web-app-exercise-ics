from flask import Flask, request
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ.get("MONGO_URI"))
db = client["testdb"]

app = Flask(__name__)

@app.route("/")
def hello():
    return "<p>Hello World!</p><br><a href='/testform'>Test Form</a>"

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