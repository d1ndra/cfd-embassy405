import json
from datetime import datetime
from flask import Flask, render_template, redirect, request, jsonify
from flask_mongokit import MongoKit, Document
import requests

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()
