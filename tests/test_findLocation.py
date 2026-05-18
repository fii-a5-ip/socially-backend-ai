import sys
import json
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from flask import Flask, Blueprint

# Mock flask_caching BEFORE importing anything from api
sys.modules['flask_caching'] = MagicMock()

from api.extensions import cache

def mock_memoize(*args, **kwargs):
    def decorator(f):
        return f
    return decorator

cache.memoize = mock_memoize

# Import the blueprint under test
from api.routes.findLocation import findLocation_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Mimic the real app's blueprint nesting under /api
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    api_bp.register_blueprint(findLocation_bp)
    app.register_blueprint(api_bp)
    with app.test_client() as client:
        yield client

# Define a robust mock side effect for AI filters that handles empty inputs gracefully
async def robust_get_ai_filters_mock(mesaj_sistem, user_input):
    if "opening" in mesaj_sistem.lower() or "openingHours" in mesaj_sistem:
        if not user_input or user_input == "None":
            return {}
        return {"monday": {"open": "10:00", "close": "22:00"}}
    else:
        try:
            parsed = json.loads(user_input)
            if not parsed or not any(parsed.values()):
                return {"tags": []}
        except Exception:
            if not user_input:
                return {"tags": []}
        return {"tags": ["club", "entertainment"]}

@patch('api.routes.findLocation.extrage_filtre_din_db')
@patch('api.routes.findLocation.get_ai_filters', new_callable=AsyncMock)
@patch('api.routes.findLocation.requests.get')
@patch('api.routes.findLocation.GEOAPIFY_API_KEY', 'mock_geoapify_key')
def test_find_location_happy_flow(mock_get, mock_get_ai_filters, mock_extrage_filtre_din_db, client):
    """
    Scenario 1: Happy flow (Behavioral).
    Verifies that a valid place_id returns the complete normalized location info and dynamic map.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "features": [
            {
                "properties": {
                    "name": "Viper Club",
                    "formatted": "Iași, Romania",
                    "country": "Romania",
                    "city": "Iași",
                    "lat": 47.1585,
                    "lon": 27.6014,
                    "website": "https://example.com",
                    "contact": {"phone": "+40123456789"},
                    "opening_hours": "Mo-Fr 10:00-22:00"
                }
            }
        ]
    }
    mock_get.return_value = mock_response
    mock_extrage_filtre_din_db.return_value = "1: club"
    mock_get_ai_filters.side_effect = robust_get_ai_filters_mock

    payload = {"place_id": "5110afeb17ec9a3b4059b33f506e"}
    response = client.post('/api/findLocation/', json=payload)
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Behavioral assertions using safe dict access
    assert data.get("name") == "Viper Club"
    assert data.get("formatted_address") == "Iași, Romania"
    assert data.get("address", {}).get("city") == "Iași"
    assert data.get("coord", {}).get("lat") == 47.1585
    assert data.get("tags") == ["club", "entertainment"]
    assert data.get("opening_hours", {}).get("monday", {}).get("open") == "10:00"
    
    # Interactive Map structure (contains <html)
    assert data.get("map") is not None
    assert "<html" in data["map"].get("html", "").lower()

def test_find_location_invalid_input(client):
    """
    Scenario 2: Input Validation (Behavioral).
    Verifies missing schema fields return a 400 Bad Request JSON error response.
    """
    # Empty payload
    response = client.post('/api/findLocation/', json={})
    assert response.status_code == 400
    assert "error" in response.get_json()

    # Missing place_id key
    response = client.post('/api/findLocation/', json={"wrong_key": "val"})
    assert response.status_code == 400
    assert "error" in response.get_json()

@patch('api.routes.findLocation.requests.get')
@patch('api.routes.findLocation.GEOAPIFY_API_KEY', 'mock_geoapify_key')
def test_find_location_geoapify_error(mock_get, client):
    """
    Scenario 3: Graceful Upstream Failure handling (Behavioral).
    Verifies that upstream API failure does not crash the system and returns safe/clean response.
    """
    mock_get.side_effect = Exception("Service unavailable")

    payload = {"place_id": "error_id"}
    response = client.post('/api/findLocation/', json=payload)
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert data.get("name") is None

@patch('api.routes.findLocation.GEOAPIFY_API_KEY', None)
def test_find_location_missing_api_key(client):
    """
    Scenario 4: Missing configuration API key (Exception standard).
    ValueError is raised by the backend logic, propagating up to the test client.
    """
    payload = {"place_id": "test_id"}
    with pytest.raises(ValueError, match="Lipseste variabila GEOAPIFY_API_KEY"):
        client.post('/api/findLocation/', json=payload)

@patch('api.routes.findLocation.requests.get')
@patch('api.routes.findLocation.GEOAPIFY_API_KEY', 'mock_geoapify_key')
def test_find_location_empty_features(mock_get, client):
    """
    Scenario 5: Empty upstream data (Behavioral).
    Verifies empty feature results are handled gracefully.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": []}
    mock_get.return_value = mock_response

    payload = {"place_id": "empty_id"}
    response = client.post('/api/findLocation/', json=payload)
    
    assert response.status_code == 200
    assert response.get_json() == {}

@patch('api.routes.findLocation.requests.get')
@patch('api.routes.findLocation.GEOAPIFY_API_KEY', 'mock_geoapify_key')
def test_find_location_missing_optional_fields(mock_get, client):
    """
    Scenario 6: Missing optional fields (Behavioral).
    Verifies that omission of coordinates or optional keys is handled cleanly.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "features": [
            {
                "properties": {
                    "name": "Minimal Location"
                }
            }
        ]
    }
    mock_get.return_value = mock_response

    payload = {"place_id": "minimal_id"}
    response = client.post('/api/findLocation/', json=payload)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("name") == "Minimal Location"
    assert data.get("coord") is None
    assert data.get("map") is None

@patch('api.routes.findLocation.requests.get')
@patch('api.routes.findLocation.GEOAPIFY_API_KEY', 'mock_geoapify_key')
def test_find_location_input_variations(mock_get, client):
    """
    Scenario 7: Input variations (Behavioral).
    Verifies place_id values such as None, empty string or wrong types.
    """
    # None place_id
    response = client.post('/api/findLocation/', json={"place_id": None})
    assert response.status_code == 200
    assert response.get_json() == {}

    # Empty string place_id
    response = client.post('/api/findLocation/', json={"place_id": ""})
    assert response.status_code == 200
    assert response.get_json() == {}

    # Integer place_id
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": []}
    mock_get.return_value = mock_response
    response = client.post('/api/findLocation/', json={"place_id": 123})
    assert response.status_code == 200
    assert response.get_json() == {}

@patch('api.routes.findLocation.requests.get')
@patch('api.routes.findLocation.GEOAPIFY_API_KEY', 'mock_geoapify_key')
def test_find_location_geoapify_malformed(mock_get, client):
    """
    Scenario 8: Malformed Geoapify response (Behavioral).
    Verifies that malformed payloads from upstream like features=None are handled gracefully.
    """
    mock_response_none = MagicMock()
    mock_response_none.json.return_value = {"features": None}
    mock_get.return_value = mock_response_none

    response = client.post('/api/findLocation/', json={"place_id": "malformed_none"})
    assert response.status_code == 200
    assert response.get_json() == {}
