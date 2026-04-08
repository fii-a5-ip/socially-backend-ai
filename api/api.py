from flask import Flask
from flask import Blueprint, jsonify


app = Flask(__name__)

# Blueprints help us split our methods into different files
api_bp = Blueprint('api', __name__, url_prefix='/api') #the root path for all endpoints will be /api



# A simple root endpoint just to check if the server is up
@api_bp.route('/')
def home():
    return "Welcome to the Socially API! Server is up!"

app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(debug=True)