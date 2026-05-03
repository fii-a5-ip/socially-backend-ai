from flask import Flask
from flask import Blueprint

# Importăm Blueprint-urile
from api.routes.autocompleteLocationName import autocomplete_bp
from api.routes.searchToFilters import search_bp
from api.routes.weather_blueprint import weather_blueprint
from api.routes.findDistanceBetween2Coord import distance_bp
from api.routes.findLocation import findLocation_bp

# Blueprints help us split our methods into different files
api_bp = Blueprint('api', __name__, url_prefix='/api')  # the root path for all endpoints will be /api


# A simple root endpoint just to check if the server is up
@api_bp.route('/')
def home():
    return "Welcome to the Socially API! Server is up!"


# Create the factory function
def create_app():
    app = Flask(__name__)

    # Register blueprints
    api_bp.register_blueprint(autocomplete_bp)
    api_bp.register_blueprint(search_bp)
    api_bp.register_blueprint(distance_bp)
    api_bp.register_blueprint(weather_blueprint)
    api_bp.register_blueprint(findLocation_bp)
    #...

    app.register_blueprint(api_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)