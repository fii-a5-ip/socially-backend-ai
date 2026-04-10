"""
Main Functionality:
This endpoint calculates the driving distance and estimated travel time between multiple 
source and destination coordinates. It processes the coordinates, queries the Geoapify 
Route Matrix API, and returns a comprehensive routing matrix. It includes built-in 
resiliency via an exponential backoff retry loop and secure error logging that strips 
API keys from the output.

Expected Input (JSON POST Request):
A JSON object containing two lists: 'sources' and 'destinations'. Each coordinate 
must be an object containing 'lon' (longitude) and 'lat' (latitude) as floats.

Example Input:
{
    "sources": [
        {"lon": 27.5879, "lat": 47.1585}
    ],
    "destinations": [
        {"lon": 26.1025, "lat": 44.4268},
        {"lon": 23.5914, "lat": 46.7712}
    ]
}

Expected Output (JSON Response):
A nested dictionary representing a 2D matrix of the results. The outer keys correspond 
to the index of the source coordinates, and the inner keys correspond to the index of 
the destination coordinates. Each combination provides the 'distance' (in meters) 
and 'time' (in seconds).

Example Output:
{
    "0": {
        "0": {"distance": 385000, "time": 21500},
        "1": {"distance": 450000, "time": 26000}
    }
}
"""

from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
import os
import json
import requests
import urllib.parse
import logging
import time

logger = logging.getLogger(__name__)

load_dotenv()

distance_bp = Blueprint('findDistanceBetween2Coord', __name__, url_prefix='/findDistanceBetween2Coord')

@distance_bp.route('/', methods=['POST'])
def findDistanceBetween2Coord():
    api_key = os.environ.get("GEOAPIFY_DISTANCE_API_KEY")
    api_url = f'https://api.geoapify.com/v1/routematrix?api_key={api_key}'

    data = request.get_json()

    payload = {
            "mode": "drive",
            'sources': [],
            'targets': []
        }
    headers = {
            'Content-Type': 'application/json'
        }
    
    for source in data['sources']:
        payload['sources'].append({'location': [source['lon'], source['lat']]})
    for target in data['destinations']:
        payload['targets'].append({'location': [target['lon'], target['lat']]})

    

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.request("POST", api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # Raises an error for 4xx or 5xx statuses

            break # Get successful
        except requests.exceptions.RequestException as e:
            if attempt == max_retries-1:
                safe_error = str(e).replace(api_key, '[REDACTED]').replace(urllib.parse.quote(api_key, safe=''), '[REDACTED]')
                logger.error("Geoapify request failed after %d attempts: %s", max_retries, safe_error)
                return jsonify({"error": "Upstream location service is unavailable. Please try again later."}), 502
            time.sleep(attempt)

    body = response.json()

    result = {}

    for i in range(len(payload['sources'])):
        result[i] = {}

    for info_list in body['sources_to_targets']:
        for item in info_list:
            result[item['source_index']][item['target_index']] = {'distance': item['distance'], 'time': item['time']}

    return jsonify(result)


