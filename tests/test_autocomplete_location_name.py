import os
from unittest.mock import MagicMock, patch
import pytest
import requests
from flask import Flask, Blueprint

# Import the blueprint under test
from api.routes.autocomplete_location_name import autocomplete_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Mimic the real app's blueprint nesting under /api
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    api_bp.register_blueprint(autocomplete_bp)
    app.register_blueprint(api_bp)
    with app.test_client() as client:
        yield client

@patch('api.routes.autocomplete_location_name.requests.get')
@patch.dict(os.environ, {"GEOAPIFY_AUTOCOMPLETE_API_KEY": "mock_api_key"})
def test_autocomplete_happy_flow(mock_get, client):
    """
    Scenario 1: Happy flow (Behavioral).
    Verifies that search returns matching sorted locations.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "features": [
            {
                "properties": {
                    "name": "Restaurant A",
                    "place_id": "id_a",
                    "lat": 47.1,
                    "lon": 27.2,
                    "formatted": "Str. A, Iasi",
                    "country": "Romania",
                    "city": "Iasi",
                    "street": "Str. A",
                    "housenumber": "1",
                    "distance": 500
                }
            },
            {
                "properties": {
                    "name": "Restaurant B",
                    "place_id": "id_b",
                    "lat": 47.2,
                    "lon": 27.3,
                    "formatted": "Str. B, Iasi",
                    "country": "Romania",
                    "city": "Iasi",
                    "street": "Str. B",
                    "housenumber": "2",
                    "distance": 100
                }
            }
        ]
    }
    mock_get.return_value = mock_response

    response = client.get('/api/autocompleteLocationName/?partialName=Rest')
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert len(data) == 2
    # Check that they are sorted by distance_meters (Restaurant B first)
    assert data[0]["name"] == "Restaurant B"
    assert data[0]["distance_meters"] == 100
    assert data[1]["name"] == "Restaurant A"
    assert data[1]["distance_meters"] == 500

@patch.dict(os.environ, {"GEOAPIFY_AUTOCOMPLETE_API_KEY": "mock_api_key"})
def test_autocomplete_missing_partial_name(client):
    """
    Scenario 2: Missing or empty required 'partialName' parameter (Behavioral).
    Expects 400 Bad Request JSON response.
    """
    # Case A: Missing entirely
    response = client.get('/api/autocompleteLocationName/')
    assert response.status_code == 400
    assert "error" in response.get_json()

    # Case B: Empty string value
    response = client.get('/api/autocompleteLocationName/?partialName=')
    assert response.status_code == 400
    assert "error" in response.get_json()

@patch.dict(os.environ, {}, clear=True)
def test_autocomplete_missing_api_key(client):
    """
    Scenario 3: Missing GEOAPIFY_AUTOCOMPLETE_API_KEY in environment (Behavioral).
    Expects 500 Internal Server Error JSON response.
    """
    response = client.get('/api/autocompleteLocationName/?partialName=Rest')
    assert response.status_code == 500
    assert "error" in response.get_json()
    assert "Missing API Key" in response.get_json()["error"]

@patch('api.routes.autocomplete_location_name.time.sleep')
@patch('api.routes.autocomplete_location_name.requests.get')
@patch.dict(os.environ, {"GEOAPIFY_AUTOCOMPLETE_API_KEY": "mock_api_key"})
def test_autocomplete_upstream_error(mock_get, mock_sleep, client):
    """
    Scenario 4: Upstream Geoapify failure (Behavioral).
    Verifies that upstream failures return 502 Bad Gateway JSON response.
    """
    mock_get.side_effect = requests.exceptions.RequestException("API connection timeout")

    response = client.get('/api/autocompleteLocationName/?partialName=Rest')
    
    assert response.status_code == 502
    assert "error" in response.get_json()
    assert "upstream location service is unavailable" in response.get_json()["error"].lower()

@patch('api.routes.autocomplete_location_name.requests.get')
@patch.dict(os.environ, {"GEOAPIFY_AUTOCOMPLETE_API_KEY": "mock_api_key"})
def test_autocomplete_with_bias_proximity(mock_get, client):
    """
    Scenario 5: Search with bias and proximity circle (Behavioral).
    Expects correct parameters to be forwarded to Geoapify API.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": []}
    mock_get.return_value = mock_response

    response = client.get('/api/autocompleteLocationName/?partialName=Rest&userLatCoord=44.4268&userLonCoord=26.1025')
    
    assert response.status_code == 200
    
    mock_get.assert_called_once()
    called_args, called_kwargs = mock_get.call_args
    params = called_kwargs["params"]
    
    assert params.get("text") == "Rest"
    assert params.get("apiKey") == "mock_api_key"
    assert params.get("bias") == "proximity:26.1025,44.4268"

@patch('api.routes.autocomplete_location_name.requests.get')
@patch.dict(os.environ, {"GEOAPIFY_AUTOCOMPLETE_API_KEY": "mock_api_key"})
def test_autocomplete_missing_optional_properties(mock_get, client):
    """
    Scenario 6: Incomplete Geoapify response (Behavioral).
    Expects safe extraction without crashing.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "features": [
            {
                "properties": {
                    "place_id": "incomplete_id"
                }
            }
        ]
    }
    mock_get.return_value = mock_response

    response = client.get('/api/autocompleteLocationName/?partialName=Rest')
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert len(data) == 1
    item = data[0]
    
    assert item.get("place_id") == "incomplete_id"
    assert item.get("name") is None
    assert item.get("distance_meters") == float('inf')

@patch('api.routes.autocomplete_location_name.requests.get')
@patch.dict(os.environ, {"GEOAPIFY_AUTOCOMPLETE_API_KEY": "mock_api_key"})
def test_autocomplete_geoapify_malformed(mock_get, client):
    """
    Scenario 7: Malformed Geoapify response (Exception standard).
    Verifies that unhandled errors propagate correctly.
    """
    # features is None (causes TypeError during iteration)
    mock_response_none = MagicMock()
    mock_response_none.json.return_value = {"features": None}
    mock_get.return_value = mock_response_none

    with pytest.raises(TypeError):
        client.get('/api/autocompleteLocationName/?partialName=Rest')

    # features is [{}] (causes KeyError on 'properties' access)
    mock_response_empty = MagicMock()
    mock_response_empty.json.return_value = {"features": [{}]}
    mock_get.return_value = mock_response_empty

    with pytest.raises(KeyError):
        client.get('/api/autocompleteLocationName/?partialName=Rest')
