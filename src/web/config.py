from flask import Flask
from flask_cors import CORS

# Create Flask app
app = Flask(__name__, 
           static_folder='static',
           static_url_path='/static')
CORS(app) 