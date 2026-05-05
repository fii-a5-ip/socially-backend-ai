"""

DistanceBetween2Coord API Blueprint

This endpoint receives some coordinates (points on a map) and tells you:
- how far they are from each other (distance)
- how long it takes to drive between them (time)

You must send a POST request with JSON like this:

{
    "sources": [
        {"lon": 27.5879, "lat": 47.1585}
    ],
    "destinations": [
        {"lon": 26.1025, "lat": 44.4268},
        {"lon": 23.5914, "lat": 46.7712}
    ]
}

EXPLANATION:

- "sources" = starting points
- "destinations" = ending points

Each point has:
- lon = longitude
- lat = latitude

WHAT THE CODE DOES INTERNALLY (STEP BY STEP):

1. Reads the input JSON from the request
2. Converts the data into the format required by Geoapify
3. Sends a request to Geoapify (external API)
4. Geoapify calculates the routes
5. The code processes the response
6. Returns a simplified result back to the caller

--------------------------------------------------------------------------

WHAT IT RETURNS (OUTPUT):

The response is a nested dictionary (JSON) like this:

{
    "0": {
        "0": {"distance": 385000, "time": 21500},
        "1": {"distance": 450000, "time": 26000}
    }
}


- first "0" = index of the source
- second "0" or "1" = index of the destination

So:

result["0"]["0"] = from source 0 to destination 0
result["0"]["1"] = from source 0 to destination 1
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
def find_distance_between_2coord():
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


