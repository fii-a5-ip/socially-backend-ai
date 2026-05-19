from flask import Flask
from flask import Blueprint
import os

# Importăm Blueprint-urile
from api.routes.autocomplete_location_name import autocomplete_bp
from api.routes.searchToFilters import search_bp
from api.routes.weather_blueprint import weather_blueprint
from api.routes.find_distance_between_2coord import distance_bp
from api.routes.onboarding import onboarding_bp
from api.routes.speech_to_text import speech_blueprint
from api.extensions import cache

# Blueprints help us split our methods into different files
api_bp = Blueprint('api', __name__, url_prefix='/api')  # the root path for all endpoints will be /api



# A simple root endpoint just to check if the server is up
@api_bp.route('/', methods=['GET'])
def home():
    return "Welcome to the Socially API! Server is up! Vasy e cel mai tare Bolojan plang pentru tineeee"


# Create the factory function
def create_app():
    app = Flask(__name__) # NOSONAR

    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300

    cache.init_app(app)

    from api.routes.findLocation import findLocation_bp

    # Register blueprints
    api_bp.register_blueprint(autocomplete_bp)
    api_bp.register_blueprint(search_bp)
    api_bp.register_blueprint(distance_bp)
    api_bp.register_blueprint(weather_blueprint)
    api_bp.register_blueprint(findLocation_bp)
    api_bp.register_blueprint(onboarding_bp)

    api_bp.register_blueprint(speech_blueprint)
    
    #...

    app.register_blueprint(api_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False) #Am modificat linia aceasta ca să văd dacă funcționează Docker-ul. Înainte era ”app.run(debug=False)”