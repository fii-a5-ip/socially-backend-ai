"""


What this file is, in very simple words:
This file defines one Flask Blueprint with one GET endpoint.
That endpoint receives a partial location name from the client,
optionally receives the user's coordinates, calls the Geoapify
Autocomplete API, cleans the response, sorts it by distance,
and returns a simpler JSON list that is much easier for the rest
of the backend or frontend to use.

Think about it like this:
- the frontend sends a text such as "Retr"
- this backend endpoint asks Geoapify: "what places match this text?"
- Geoapify returns a large raw response
- this code keeps only the useful fields
- this code returns a clean response to the caller

Main endpoint exposed by this blueprint:
    GET /autocompleteLocationName/

If the main Flask app registers this blueprint under /api,
then the final route used by the frontend will usually be:
    GET /api/autocompleteLocationName/

Required query parameter:
    partialName (str)
        The text typed by the user.
        Example: "Retr", "Buch", "Pia", "McD"

Optional query parameters:
    userLatCoord (float as query string)
        The latitude of the user.
        Example: 44.4268

    userLonCoord (float as query string)
        The longitude of the user.
        Example: 26.1025

What the endpoint returns on success:
A JSON list. Each element in the list is one location suggestion
normalized into this structure:

[
    {
        "name": "Restaurant Demo",
        "place_id": "some_place_id",
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

Very important behavior:
1. If partialName is missing -> returns HTTP 400.
2. If GEOAPIFY_AUTOCOMPLETE_API_KEY is missing -> returns HTTP 500.
3. If userLatCoord and userLonCoord are both provided:
   - the search is biased toward the user's location
   - the search is also restricted to a 100 km circle around the user
4. If Geoapify fails temporarily, the code retries up to 5 times.
5. Final results are sorted by distance_meters ascending,
   which means the closest locations are returned first.

Example request:
    /autocompleteLocationName/?partialName=Retr&userLatCoord=44.4268&userLonCoord=26.1025

Example success response:
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

In one sentence:
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
        partialName   -> required string
        userLatCoord  -> optional string/float-like value
        userLonCoord  -> optional string/float-like value

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
        400 -> if partialName is missing
        500 -> if API key is missing
        502 -> if Geoapify fails after all retries

    Example input:
        /autocompleteLocationName/?partialName=Retr&userLatCoord=44.4268&userLonCoord=26.1025

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



    
