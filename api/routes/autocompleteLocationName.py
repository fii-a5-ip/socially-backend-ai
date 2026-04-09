import os
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
import requests
import time

load_dotenv()

autocomplete_bp = Blueprint('autocompleteLocationName', __name__, url_prefix='/autocompleteLocationName')

@autocomplete_bp.route('/', methods=['GET'])
def autocompleteLocationName():
    api_key = os.environ.get("GEOAPIFY_AUTOCOMPLETE_API_KEY")

    partialName = request.args.get('partialName')
    if not partialName:
        return jsonify({"error": "Please provide a partialName parameter"}), 400

    if not api_key:
        return jsonify({"error": "Missing API Key"}), 500
    
    api_url = 'https://api.geoapify.com/v1/geocode/autocomplete'

    params = {
        'text': partialName,
        'apiKey': api_key,
        'limit': 30 # Only if we want an exact number of suggestions
    }

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.get(api_url, params=params, timeout=5)
            response.raise_for_status() # Raises an error for 4xx or 5xx statuses

            break # Get successful
        except requests.exceptions.RequestException as e:
            if attempt == max_retries-1:
                return jsonify({"error": f"API request failed: {str(e)}"}), 502
            time.sleep(attempt)

    result = []
    body = response.json()

    for location in body['features']:
        dict = {}

        dict['name'] = location['properties'].get('name')
        dict['place_id'] = location['properties'].get('place_id')

        dict['coordinates'] = {
                                    'lat': location['properties'].get('lat'), 
                                    'lon': location['properties'].get('lon')
                                }
        dict['full_address'] = location['properties'].get('formatted')
        
        dict['address'] = {}
        dict['address']['country'] = location['properties'].get('country')
        dict['address']['city'] = location['properties'].get('city')
        dict['address']['street'] = location['properties'].get('street')
        dict['address']['street_number'] = location['properties'].get('housenumber')

        result.append(dict)

    return jsonify(result)



    