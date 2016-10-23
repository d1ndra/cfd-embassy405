#!/usr/bin/python

import json
from datetime import datetime
from flask import Flask, render_template, redirect, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mongokit import MongoKit, Document

import requests

app = Flask(__name__)
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
        'doctor_email': unicode
    }
    required_fields = ['email', 'dob', 'doctor']
    default_values = {'doctor': False}
    use_dot_notation = True

class Tablet(Document):
    __collection__ = 'cfd'
    structure = {
        'name': unicode,
        "dosage": int,
        "breakfast": bool,
        "lunch": bool,
        "dinner": bool,
        "before": bool,
        "after": bool,
        "interval": bool,
        "special_instructions": unicode,
        "color": unicode
    }
    required_fields = ['name', 'dosage', 'breakfast', 'lunch', 'dinner', \
    'before', 'interval']
    use_dot_notation = True

class Patient(Document):
    __collection__ = 'cfd'
    structure = {
        'email': unicode,
        'doctor': unicode,
        'prescriptions': list
    }
    required_fields = ['email', 'doctor']
    use_dot_notation = True

class Patient_tablet(Document):
    __collection__ = 'cfd'
    structure = {
        'email': unicode,
        'medicine': unicode,
        'start_date': datetime,
        'end_date': datetime
    }
    required_fields = ['email', 'medicine', 'end_date', 'start_date']
    use_dot_notation = True

class Doctor(Document):
    __collection__ = 'cfd'
    structure = {
        'email': unicode,
        'patients': list,
    }
    required_fields = ['email', 'patients']
    use_dot_notation = True


conn = MongoKit(app)
conn.register(User)
conn.register(Tablet)
conn.register(Patient)

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
            data['password'] = generate_password_hash(data['password'])
            collection.insert(data)
            print data
            if data['doctor']:
                doctor = {}
                doctor['email'] = data['email']
                doctor['patients'] = []
                doc_collection = conn['cfd'].doctors
                doc_collection.insert(doctor)
            return jsonify({"success":True})

@app.route("/login", methods = ['POST'])
def login():
    if request.headers.get(_cfd_header) != app_key:
        return "Unauthorised"
    collection = conn['cfd'].users  
    data = request.get_json()
    query = {}
    options = []
    options.append({'email':data['email']})
    query["$or"] = options
    db_data = list(collection.find(query, {"_id":0}))
    res = {}
    res['success'] = False
    if len(db_data) == 0:
        res['message'] = "User not found"
        return jsonify(res)
    else:
        if check_password_hash(str(db_data[0]['password']), str(data['password'])):
            res['success'] = True
            res['doctor'] = db_data[0]['doctor']
            res['email'] = data['email']
            if res['doctor']:
                res['patients'] = get_patients(data['email'])
            else:
                pass
            return jsonify(res)
        else:
            res['message'] = "Bad password"
            return jsonify(res)

@app.route("/patient", methods = ['GET', 'POST'])
def patient():
    if request.headers.get(_cfd_header) != app_key:
        return "Unauthorised"
    # fields = ['email', 'patient']
    collection = conn['cfd'].doctors
    if request.method == 'POST':
        data = request.get_json()
        query = {}
        options = []
        options.append({'email':data['email']})
        query['$or'] = options
        res = list(collection.find(query, {'_id':0}))
        if len(res) == 0:
            return jsonify({'success':False, 'message':'Doctor not found'})
        if data['patient'] not in res[0]['patients']:
            res[0]['patients'].append(data['patient'])
            collection.update(
                {'email':data['email']},
                {
                '$set': {
                    'patients': res[0]['patients']
                }
                },upsert = False, multi = False)
            patient_coll = collection['cfd'].patients
            patient = {}
            patient['email'] = data['patient']
            patient['doctor'] = data['email']
            patient_coll.insert(patient)
            return jsonify({'success':True})
        else:
            return jsonify({'success':False, 'message':'Patient already exists'})
    else:
        doctor_email = request.args.get('doc')
        if doctor_email is not None:
            query = {}
            options = []
            options.append({'email':doctor_email})
            query['$or'] = options
            res = list(collection.find(query, {'_id':0}))
            user_coll = conn['cfd'].users
            response = {}
            response['email'] = doctor_email
            response['patients'] = []
            if len(res) != 0:
                for i in res[0]['patients']:
                    query = {}
                    options = [{'email':i}]
                    query['$or'] = options
                    blah = user_coll.find(query, {'_id':0})
                    for j in blah:
                        entry = {}
                        entry['email'] = j['email']
                        entry['name'] = j['name']
                        response['patients'].append(entry)
            return jsonify(response) 
        else:
            patient_coll = collection['cfd'].patients
            return jsonify(list(patient_coll.find({}, {'_id':0})))

def get_patients(doctor_email):
    collection = conn['cfd'].doctors
    query = {}
    options = []
    options.append({'email':doctor_email})
    query['$or'] = options
    res = list(collection.find(query, {'_id':0}))
    user_coll = conn['cfd'].users
    response = {}
    response['email'] = doctor_email
    response['patients'] = []
    if len(res) != 0:
        for i in res[0]['patients']:
            query = {}
            options = [{'email':i}]
            query['$or'] = options
            blah = user_coll.find(query, {'_id':0})
            for j in blah:
                entry = {}
                entry['email'] = j['email']
                entry['name'] = j['name']
                response['patients'].append(entry)
    return response['patients']



@app.route('/patient/<patient_email>', methods = ['POST'])
def patient_med(patient_email):
    """
    To add new medicines for a particular patient
    JSON fields = list of medicines
    """
    if request.headers.get(_cfd_header) != app_key:
        return "Unauthorised"
    collection = conn['cfd'].patients
    query = {}
    options = []
    options.append({'email':patient_email})
    query['$or'] = options
    res = list(collection.find(query, {'_id':0}))
    if len(res) == 0:
        return jsonify({'success':False, 'message':'Patient not found'})
    meds = request.get_json()['medicines']
    for i in meds:
        if i not in res[0]['prescriptions']:
            res[0]['prescriptions'].append(i)

# @app.route('/')

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

@app.route('/medicine', methods = ['POST', 'GET'])
def medicine():
    if request.headers.get(_cfd_header) != app_key:
        return "Unauthorised"
    collection = conn['cfd'].medicines
    if request.method == 'GET':
        res = []
        meds = list(collection.find({}, {'_id':0}))
        for med in meds:
            res.append(med['name'])
        return jsonify(res)
    else:
        data = json.loads(request.get_json())
        print data['name']
        query = {}
        options = []
        options.append({"name":data['name']})
        query['$or'] = options
        if len(list(collection.find(query))) == 0:
            collection.insert(data)
            return jsonify({'success':True})
        else:
            return jsonify({'success':False, 'message':'Tablet already exists.'})

@app.route('/medicine/<med_name>')
def med_detail(med_name):
    if request.headers.get(_cfd_header) != app_key:
        return "Unauthorised"
    collection = conn['cfd'].medicines
    query = {}
    options = []
    options.append({'name':med_name})
    query['$or'] = options
    res_set = list(collection.find(query, {'_id':0}))
    if len(res_set) == 0:
        return jsonify({})
    else:
        return jsonify(res_set[0])

if __name__ == "__main__":
    app.run()
