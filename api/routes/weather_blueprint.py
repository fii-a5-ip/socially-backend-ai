"""
This module defines a Flask Blueprint that exposes one HTTP API endpoint.
That endpoint allows another part of the system to ask for weather forecast information for a specific place and for one or more specific dates.

Input (JSON):
    - coordinates: List of [latitude, longitude]
    - dates: List of strings in "YYYY-MM-DD" format
    
Output (JSON):
    - A dictionary keyed by date, containing:
        * temperatura: 24-hour array of temperature values (°C)
        * probabilitate_precipitatii: 24-hour array of precipitation probability (%)
        * viteza_vantului: 24-hour array of wind speeds (km/h)
        * descriere: General weather description in Romanian (e.g., 'senin', 'noros')
"""

from flask import Blueprint, request, jsonify
import requests
weather_blueprint=Blueprint("findWeatherByLocation", __name__, url_prefix="/findWeatherByLocation")
# a function for interpreting the weather code given by Open-Meteo API 
# Maps WMO weather codes to Romanian descriptions.
def interpret_weather_code(code):
    mapping = {
        0: "clear",
        1: "mostly clear",
        2: "partly cloudy",
        3: "cloudy",
        45: "fog",
        48: "freezing fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "heavy drizzle",
        61: "light rain",
        63: "moderate rain",
        65: "heavy rain",
        71: "light snow",
        73: "moderate snow",
        75: "heavy snow",
        80: "light showers",
        81: "moderate showers",
        82: "heavy showers",
        95: "thunderstorm"
    }
    return mapping.get(code, "unknown")

# Fetches weather data for specific coordinates and a list of dates.
def findWeatherByLocation(location, dates):
    url="https://api.open-meteo.com/v1/forecast"
    lat, lon=location
    params={
        "latitude": lat,
        "longitude": lon,
        "start_date": min(dates),  
        "end_date": max(dates),   
        "hourly": "temperature_2m,precipitation_probability,weather_code,wind_speed_10m",
        "timezone": "auto"
     }
    try:
        response=requests.get(url, params=params)
        info=response.json()
        if "error" in info:
            print(f"Eroare: {info['reason']}")
            return
        rezultat = {}
        timp=info["hourly"]["time"]
        temps=info["hourly"]["temperature_2m"]
        rain=info["hourly"]["precipitation_probability"]
        codes=info["hourly"]["weather_code"]
        wind=info["hourly"]["wind_speed_10m"]

        for i in range(len(timp)):
            data_curenta=timp[i].split("T")[0]
            if data_curenta in dates:
                if data_curenta not in rezultat:
                    rezultat[data_curenta]={
                    "date": data_curenta,
                    "temp": [],
                    "precipitation_probability": [],
                    "wind_speed": [],
                    "details": interpret_weather_code(codes[i])}
                rezultat[data_curenta]["temp"].append(temps[i])
                rezultat[data_curenta]["precipitation_probability"].append(rain[i])
                rezultat[data_curenta]["wind_speed"].append(wind[i])
        return rezultat
    except Exception as e:
        print(f"Error: {e}")

@weather_blueprint.route("/", methods=["POST"])
def weather_post():
    data=request.get_json()
    location=data.get("coordinates")
    dates=data.get("dates")
    # Process and return the final JSON structure
    weather_info=findWeatherByLocation(location, dates)
    return jsonify(weather_info)