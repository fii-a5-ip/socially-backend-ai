"""
AutocompleteLocationName API Blueprint


This file is a clean adapter between your app and Geoapify autocomplete.
"""
"""
    Main endpoint handler.

    Very simple explanation:
    - reads input from query params
    - validates required data
    - calls Geoapify autocomplete
    - extracts only the fields needed by the app
    - sorts results by distance
    - returns JSON list

    Input received from request.args:
        partial_name   -> required string
        user_lat_coord  -> optional string/float-like value
        user_lon_coord  -> optional string/float-like value

    Success return value:
        Flask JSON response containing a list of dictionaries.

    Exact dictionary format for each result:
        {
            "name": <str or None>,
            "place_id": <str or None>,
            "coordinates": {
                "lat": <float or None>,
                "lon": <float or None>
            },
            "full_address": <str or None>,
            "address": {
                "country": <str or None>,
                "city": <str or None>,
                "street": <str or None>,
                "street_number": <str or None>
            },
            "distance_meters": <number or inf>
        }

    Error returns:
        400 -> if partial_name is missing
        500 -> if API key is missing
        502 -> if Geoapify fails after all retries

    Example input:
        /api/autocompleteLocationName/?partial_name=Retr&user_lat_coord=44.4268&user_lon_coord=26.1025

    Example output:
        [
            {
                "name": "Restaurant Demo",
                "place_id": "123",
                "coordinates": {
                    "lat": 44.4268,
                    "lon": 26.1025
                },
                "full_address": "Strada Exemplu 10, Bucharest, Romania",
                "address": {
                    "country": "Romania",
                    "city": "Bucharest",
                    "street": "Strada Exemplu",
                    "street_number": "10"
                },
                "distance_meters": 215
            }
        ]
    """

import logging
import os
import urllib.parse
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
import requests
import time

logger = logging.getLogger(__name__)

load_dotenv()

autocomplete_bp = Blueprint('autocompleteLocationName', __name__, url_prefix='/autocompleteLocationName')

@autocomplete_bp.route('/', methods=['GET'])
def autocomplete_location_name():
    api_key = os.environ.get("GEOAPIFY_AUTOCOMPLETE_API_KEY")

    partial_name = request.args.get('partial_name')
    user_lat_coord = request.args.get('user_lat_coord')
    user_lon_coord = request.args.get('user_lon_coord')

    if not partial_name:
        return jsonify({"error": "Please provide a partial_name parameter"}), 400

    if not api_key:
        return jsonify({"error": "Missing API Key"}), 500
    
    api_url = 'https://api.geoapify.com/v1/geocode/autocomplete'

    params = {
        'text': partial_name,
        'apiKey': api_key,
        'limit': 30, # Only if we want an exact number of suggestions
        # 'bias': f'proximity:{user_lon_coord},{user_lat_coord}'
    }
    if user_lat_coord and user_lon_coord:
        params['bias'] = f"proximity:{user_lon_coord},{user_lat_coord}"
        params['filter'] = f"circle:{user_lon_coord},{user_lat_coord},{100000}" #only recommend within 100 km of the user

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.get(api_url, params=params, timeout=5)
            response.raise_for_status() # Raises an error for 4xx or 5xx statuses

            break # Get successful
        except requests.exceptions.RequestException as e:
            if attempt == max_retries-1:
                safe_error = str(e).replace(api_key, '[REDACTED]').replace(urllib.parse.quote(api_key, safe=''), '[REDACTED]')
                logger.error("Geoapify request failed after %d attempts: %s", max_retries, safe_error)
                return jsonify({"error": "Upstream location service is unavailable. Please try again later."}), 502
            time.sleep(attempt)

    result = []
    body = response.json()

    for location in body['features']:
        location_data = {}

        location_data['name'] = location['properties'].get('name')
        location_data['place_id'] = location['properties'].get('place_id')

        location_data['coordinates'] = {
                                    'lat': location['properties'].get('lat'), 
                                    'lon': location['properties'].get('lon')
                                }
        location_data['full_address'] = location['properties'].get('formatted')
        
        location_data['address'] = {}
        location_data['address']['country'] = location['properties'].get('country')
        location_data['address']['city'] = location['properties'].get('city')
        location_data['address']['street'] = location['properties'].get('street')
        location_data['address']['street_number'] = location['properties'].get('housenumber')

        location_data['distance_meters'] = location['properties'].get('distance', float('inf'))
        

        result.append(location_data)
    
    result.sort(key=lambda x: x['distance_meters'])

    return jsonify(result)



    
