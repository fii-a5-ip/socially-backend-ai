from flask import Blueprint, jsonify, request
from services.geoapify_service import find_location
import request

locations_bp = Blueprint("findLocation", __name__, url_prefix="/findLocation")


@locations_bp.route("/", methods=["GET"])
def findLocation():
    location_name = request.args.get("name", "").strip()

    if not location_name:
        return jsonify({
            "error": "Parametrul 'name' este obligatoriu."
        }), 400

    try:
        results = find_location(location_name)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({
            "error": "A aparut o eroare la cautarea locatiei.",
            "details": str(e)
        }), 500