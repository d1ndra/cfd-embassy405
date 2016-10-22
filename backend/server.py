import json
from datetime import datetime
from flask import Flask, render_template, redirect, request, jsonify
from flask_mongokit import MongoKit, Document
from flask_bcrypt import Bcrypt
import requests

app = Flask(__name__)
bcrypt = Bcrypt(app)
app_key = '$2b$12$BYDebu0UIJwb05N8BfwPEOZDJDxJGHrAx7JzqIC6NLP0GUrn1hBmO'
_cfd_header = 'cfd-embassy'

class User(Document):
    __collection__ = 'cfd'
    structure = {
        'name': unicode,
        'email': unicode,
        'dob': datetime,
        'phone': unicode,
        'doctor': bool,
    }
    required_fields = ['email', 'dob', 'doctor']
    default_values = {'doctor': False}
    use_dot_notation = True


conn = MongoKit(app)
conn.register(User)

@app.route("/")
def index():
    if request.headers.get(_cfd_header) != app_key:
        return "Unauthorised"
    else:
        return "Nothing to do here"

@app.route("/user", methods = ['GET', 'POST'])
def user():
    if request.headers.get(_cfd_header) != app_key:
        return "Unauthorised"
    collection = conn['cfd'].users
    if request.method == 'GET':
        return jsonify(list(collection.find({}, {"_id":0, "password":0})))
    elif request.method == 'POST':
        data = request.get_json()
        data['dob'] = datetime.strptime(data['dob'], "%Y%m%d")
        query = {}
        options = []
        options.append({'email':data['email']})
        query["$or"] = options
        if len(list(collection.find(query))) != 0:
            res = {}
            res['success'] = False
            res['message'] = 'User already registered'
            return jsonify(res)
        else:
            data['password'] = bcrypt.generate_password_hash(data['password'])
            collection.insert(data)
            return jsonify({"success":True})

@app.route('/user/<email>')
def user_detail(email):
    if request.headers.get(_cfd_header) != app_key:
        return "Unauthorised"
    collection = conn['cfd'].users
    query = {}
    options = []
    options.append({'email': email})
    result = list(collection.find(query, {"_id":0, "password":0}))
    if len(result) == 0:
        return jsonify({"User not found."})
    else:
        return jsonify(result[0])


if __name__ == "__main__":
    app.run()
