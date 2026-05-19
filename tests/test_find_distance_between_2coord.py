import os
import json
from unittest.mock import MagicMock, patch
import pytest
import requests
from flask import Flask, Blueprint

# Import the blueprint under test
from api.routes.find_distance_between_2coord import distance_bp

@pytest.fixture
def client():
    app = Flask(__name__) # NOSONAR
    app.config['TESTING'] = True
    
    # Mimic the real app's blueprint nesting under /api
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    api_bp.register_blueprint(distance_bp)
    app.register_blueprint(api_bp)
    with app.test_client() as client:
        yield client

@patch('api.routes.find_distance_between_2coord.requests.request')
@patch.dict(os.environ, {"GEOAPIFY_DISTANCE_API_KEY": "mock_api_key"})
def test_distance_happy_flow(mock_request, client):
    """
    Scenario 1: Happy flow (Behavioral).
    Verifies that a valid matrix of sources and destinations returns correct parsed distances.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "sources_to_targets": [
            [
                {"source_index": 0, "target_index": 0, "distance": 1500, "time": 120},
                {"source_index": 0, "target_index": 1, "distance": 3200, "time": 250}
            ]
        ]
    }
    mock_request.return_value = mock_response

    payload = {
        "sources": [{"lon": 27.5879, "lat": 47.1585}],
        "destinations": [
            {"lon": 26.1025, "lat": 44.4268},
            {"lon": 23.5914, "lat": 46.7712}
        ]
    }

    response = client.post('/api/findDistanceBetween2Coord/', json=payload)
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Behavioral assertions
    assert isinstance(data, dict)
    keys = list(data.keys())
    assert len(keys) == 1
    
    first_key = keys[0]
    assert first_key in ["0", 0]
    
    source_results = data[first_key]
    assert isinstance(source_results, dict)
    assert "0" in source_results or 0 in source_results
    assert "1" in source_results or 1 in source_results

@patch.dict(os.environ, {"GEOAPIFY_DISTANCE_API_KEY": "mock_api_key"})
def test_distance_invalid_input(client):
    """
    Scenario 2: Missing required payload or invalid format (Exception standard).
    Verify exact KeyError / TypeError raised when schema is malformed.
    """
    # Test case A: Empty body / None (raises KeyError)
    with pytest.raises(KeyError, match="sources"):
        client.post('/api/findDistanceBetween2Coord/', json={})

    # Test case B: Missing sources key (raises KeyError)
    with pytest.raises(KeyError, match="sources"):
        client.post('/api/findDistanceBetween2Coord/', json={"destinations": [{"lon": 26.1, "lat": 44.4}]})

    # Test case C: Wrong schema type (raises TypeError)
    with pytest.raises(TypeError):
        client.post('/api/findDistanceBetween2Coord/', json={"sources": "invalid", "destinations": []})

@patch('api.routes.find_distance_between_2coord.time.sleep')
@patch('api.routes.find_distance_between_2coord.requests.request')
@patch.dict(os.environ, {"GEOAPIFY_DISTANCE_API_KEY": "mock_api_key"})
def test_distance_upstream_error_all_retries_fail(mock_request, mock_sleep, client):
    """
    Scenario 3: Upstream Geoapify failure (Behavioral).
    Expects 502 Bad Gateway JSON response.
    """
    mock_request.side_effect = requests.exceptions.RequestException("Geoapify is completely down")

    payload = {
        "sources": [{"lon": 27.5, "lat": 47.1}],
        "destinations": [{"lon": 26.1, "lat": 44.4}]
    }

    response = client.post('/api/findDistanceBetween2Coord/', json=payload)
    
    assert response.status_code == 502
    assert "error" in response.get_json()
    assert "upstream location service is unavailable" in response.get_json()["error"].lower()

@patch('api.routes.find_distance_between_2coord.time.sleep')
@patch('api.routes.find_distance_between_2coord.requests.request')
@patch.dict(os.environ, {"GEOAPIFY_DISTANCE_API_KEY": "mock_api_key"})
def test_distance_upstream_success_on_retry(mock_request, mock_sleep, client):
    """
    Scenario 4: Upstream recovery (Behavioral).
    Verifies that system recovers and succeeds if subsequent retry works.
    """
    mock_success_response = MagicMock()
    mock_success_response.json.return_value = {
        "sources_to_targets": [
            [
                {"source_index": 0, "target_index": 0, "distance": 1000, "time": 90}
            ]
        ]
    }
    mock_request.side_effect = [
        requests.exceptions.RequestException("Temporary glitch"),
        mock_success_response
    ]

    payload = {
        "sources": [{"lon": 27.5, "lat": 47.1}],
        "destinations": [{"lon": 26.1, "lat": 44.4}]
    }

    response = client.post('/api/findDistanceBetween2Coord/', json=payload)
    
    assert response.status_code == 200
    data = response.get_json()
    
    keys = list(data.keys())
    first_key = keys[0]
    assert data[first_key]["0"]["distance"] == 1000

@patch('api.routes.find_distance_between_2coord.requests.request')
@patch.dict(os.environ, {"GEOAPIFY_DISTANCE_API_KEY": "mock_api_key"})
def test_distance_payload_verification(mock_request, client):
    """
    Scenario 5: Payload verification (Behavioral).
    Assert that the payload forwarded to the Geoapify API is correctly structured.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"sources_to_targets": []}
    mock_request.return_value = mock_response

    payload = {
        "sources": [{"lon": 27.111, "lat": 47.222}],
        "destinations": [{"lon": 26.333, "lat": 44.444}]
    }

    response = client.post('/api/findDistanceBetween2Coord/', json=payload)
    
    assert response.status_code == 200
    mock_request.assert_called_once()
    called_args, called_kwargs = mock_request.call_args
    
    assert called_args[0] == "POST"
    sent_payload = json.loads(called_kwargs["data"])
    assert sent_payload.get("mode") == "drive"
    assert sent_payload.get("sources") == [{"location": [27.111, 47.222]}]

@patch('api.routes.find_distance_between_2coord.requests.request')
@patch.dict(os.environ, {}, clear=True)
def test_distance_missing_api_key(mock_request, client):
    """
    Scenario 6: Missing API Key configuration (Exception standard).
    TypeError is raised internally when replacing None in the error logging.
    """
    mock_request.side_effect = requests.exceptions.RequestException("401 Unauthorized")

    payload = {
        "sources": [{"lon": 27.5, "lat": 47.1}],
        "destinations": [{"lon": 26.1, "lat": 44.4}]
    }
    
    with pytest.raises(TypeError):
        client.post('/api/findDistanceBetween2Coord/', json=payload)

@patch('api.routes.find_distance_between_2coord.requests.request')
@patch.dict(os.environ, {"GEOAPIFY_DISTANCE_API_KEY": "mock_api_key"})
def test_distance_empty_sources_destinations(mock_request, client):
    """
    Scenario 7: Empty lists (Behavioral).
    Verifies that empty list inputs return a valid empty dictionary cleanly.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "sources_to_targets": []
    }
    mock_request.return_value = mock_response

    payload = {
        "sources": [],
        "destinations": []
    }

    response = client.post('/api/findDistanceBetween2Coord/', json=payload)
    
    assert response.status_code == 200
    assert response.get_json() == {}

@patch('api.routes.find_distance_between_2coord.requests.request')
@patch.dict(os.environ, {"GEOAPIFY_DISTANCE_API_KEY": "mock_api_key"})
def test_distance_none_coordinate_values(mock_request, client):
    """
    Scenario 8: None coordinate values (Behavioral).
    Verifies that coord lists containing None are safely packaged and forwarded.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"sources_to_targets": []}
    mock_request.return_value = mock_response

    payload = {
        "sources": [{"lon": None, "lat": 47.1}],
        "destinations": [{"lon": 26.1, "lat": None}]
    }

    response = client.post('/api/findDistanceBetween2Coord/', json=payload)
    assert response.status_code == 200

    mock_request.assert_called_once()
    _, called_kwargs = mock_request.call_args
    sent_payload = json.loads(called_kwargs["data"])
    
    assert sent_payload.get("sources") == [{"location": [None, 47.1]}]
    assert sent_payload.get("targets") == [{"location": [26.1, None]}]
