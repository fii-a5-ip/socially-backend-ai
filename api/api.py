from flask import Flask
from flask import Blueprint

from api.routes.autocompleteLocationName import autocomplete_bp
from api.routes.weather_blueprint import weather_blueprint
from api.routes.findDistanceBetween2Coord import distance_bp

# Blueprints help us split our methods into different files
api_bp = Blueprint('api', __name__, url_prefix='/api') #the root path for all endpoints will be /api

# A simple root endpoint just to check if the server is up
@api_bp.route('/')
def home():
    return "Welcome to the Socially API! Server is up!"

# 2. Create the factory function
def create_app():
    app = Flask(__name__)
    
    # You can load configurations here (e.g., from environment variables)
    # app.config.from_pyfile('config.py')

    # Register blueprints
    api_bp.register_blueprint(autocomplete_bp)
    api_bp.register_blueprint(distance_bp)
    api_bp.register_blueprint(weather_blueprint)
    #...

    app.register_blueprint(api_bp)

    return app



if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)