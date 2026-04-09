from flask import Flask
from config import Config
from routes.locations import locations_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(locations_bp)

    @app.route("/")
    def home():
        return {"message": "API is running"}

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)