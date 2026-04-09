"""
Location Autocomplete API Blueprint

This module provides a Flask Blueprint that wraps the Geoapify Autocomplete API 
to return formatted, distance-sorted location suggestions based on user input.

Endpoint: 
    GET /api/autocompleteLocationName/

Query Parameters:
    - partialName (str, required): The search string or prefix (e.g., "Retr").
    - userLatCoord (float, optional): The user's latitude.
    - userLonCoord (float, optional): The user's longitude.

Features:
    - Geo-Fencing & Biasing: If coordinates are provided, the search is strictly 
      filtered to a 100km radius and mathematically biased toward the user.
    - Fault Tolerance: Implements a 5-attempt retry loop with exponential backoff 
      to handle temporary upstream API failures.
    - Data Normalization: Extracts and formats relevant fields (name, place_id, 
      coordinates, and structured address) from the raw Geoapify GeoJSON response.
    - Distance Sorting: Ensures the final JSON response is strictly ordered by 
      proximity to the user.
"""

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
    userLatCoord = request.args.get('userLatCoord')
    userLonCoord = request.args.get('userLonCoord')

    if not partialName:
        return jsonify({"error": "Please provide a partialName parameter"}), 400

    if not api_key:
        return jsonify({"error": "Missing API Key"}), 500
    
    api_url = 'https://api.geoapify.com/v1/geocode/autocomplete'

    params = {
        'text': partialName,
        'apiKey': api_key,
        'limit': 30, # Only if we want an exact number of suggestions
        # 'bias': f'proximity:{userLonCoord},{userLatCoord}'
    }
    if userLatCoord and userLonCoord:
        params['bias'] = f"proximity:{userLonCoord},{userLatCoord}"
        params['filter'] = f"circle:{userLonCoord},{userLatCoord},{100000}" #only recommend within 100 km of the user

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



    