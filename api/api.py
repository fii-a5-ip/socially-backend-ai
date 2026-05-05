from flask import Flask
from flask import Blueprint

# Importăm Blueprint-urile
from api.routes.autocomplete_location_name import autocomplete_bp
from api.routes.searchToFilters import search_bp
from api.routes.weather_blueprint import weather_blueprint
from api.routes.find_distance_between_2coord import distance_bp
from api.routes.findLocation import findLocation_bp

# Blueprints help us split our methods into different files
api_bp = Blueprint('api', __name__, url_prefix='/api')  # the root path for all endpoints will be /api


# A simple root endpoint just to check if the server is up
@api_bp.route('/', methods=['GET'])
def home():
    return "Welcome to the Socially API! Server is up!"


# Create the factory function
def create_app():
    app = Flask(__name__) # NOSONAR

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
    app.run(host="0.0.0.0", port=5000, debug=False) #Am modificat linia aceasta ca să văd dacă funcționează Docker-ul. Înainte era ”app.run(debug=False)”