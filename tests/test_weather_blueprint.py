import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from api.routes.weather_blueprint import weather_blueprint 

class TestWeatherBlueprint(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__) # NOSONAR
        self.app.register_blueprint(weather_blueprint)
        self.client = self.app.test_client()

    @patch('api.routes.weather_blueprint.requests.get')
    def test_weather_post_happy_flow(self, mock_get):
        # Test successful weather data parsing for multiple dates.
        # Simulate successful raw response from Open-Meteo API
        mock_response_data = {
            "hourly": {
                "time": [f"2026-04-09T{str(i).zfill(2)}:00" for i in range(24)] + \
                        [f"2026-04-15T{str(i).zfill(2)}:00" for i in range(24)],
                "temperature_2m": [4.2]*24 + [7.9]*24,
                "precipitation_probability": [5]*24 + [0]*24,
                "weather_code": [3]*24 + [2]*24,
                "wind_speed_10m": [17.5]*24 + [4.6]*24
            }
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response

        payload = {
            "coordinates": [47.15, 27.60],
            "dates": ["2026-04-09", "2026-04-15"]
        }
        
        response = self.client.post('/findWeatherByLocation/', json=payload)
        self.assertEqual(response.status_code, 200)
        
        output_data = response.get_json()
        self.assertIn("2026-04-09", output_data)
        self.assertIn("2026-04-15", output_data)
        
        self.assertEqual(output_data["2026-04-09"]["details"], "cloudy")
        self.assertEqual(output_data["2026-04-15"]["details"], "partly cloudy")
        
        self.assertEqual(len(output_data["2026-04-09"]["temp"]), 24)
        self.assertEqual(len(output_data["2026-04-15"]["precipitation_probability"]), 24)

    @patch('api.routes.weather_blueprint.requests.get')
    def test_weather_post_date_out_of_range(self, mock_get):
        #Test API error handling when the requested date is out of range.
        mock_response_data = {
            "error": True,
            "reason": "Parameter 'start_date' is out of allowed range from 2026-02-14 to 2026-06-02"
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response

        payload = {
            "coordinates": [47.15, 27.60],
            "dates": ["2027-01-01"]
        }
        
        response = self.client.post('/findWeatherByLocation/', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json())

    @patch('api.routes.weather_blueprint.requests.get')
    def test_weather_post_network_exception(self, mock_get):
        #Test system resilience when the external weather API is offline.
        mock_get.side_effect = Exception("Connection timeout")

        payload = {
            "coordinates": [47.15, 27.60],
            "dates": ["2026-04-09"]
        }
        
        response = self.client.post('/findWeatherByLocation/', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json())

if __name__ == '__main__':
    unittest.main()