from flask import Blueprint, request, jsonify
import requests
weather_blueprint=Blueprint("findWeatherByLocation", __name__, url_prefix="/findWeatherByLocation")
def interpret_weather_code(code):
    mapping = {
        0: "senin",
        1: "mai mult senin",
        2: "parțial noros",
        3: "noros",
        45: "ceață",
        48: "ceață cu depuneri",
        51: "burniță ușoară",
        53: "burniță moderată",
        55: "burniță intensă",
        61: "ploaie ușoară",
        63: "ploaie moderată",
        65: "ploaie puternică",
        71: "ninsoare ușoară",
        73: "ninsoare moderată",
        75: "ninsoare puternică",
        80: "averse ușoare",
        81: "averse moderate",
        82: "averse puternice",
        95: "furtună"
    }
    return mapping.get(code, "cod necunoscut")

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
                    "ziua": data_curenta,
                    "temperatura": [],
                    "probabilitate_precipitatii": [],
                    "viteza_vantului": [],
                    "descriere": interpret_weather_code(codes[i])}
                rezultat[data_curenta]["temperatura"].append(temps[i])
                rezultat[data_curenta]["probabilitate_precipitatii"].append(rain[i])
                rezultat[data_curenta]["viteza_vantului"].append(wind[i])
        return rezultat
    except Exception as e:
        print(f"Eroare tehnică la apelare: {e}")

@weather_blueprint.route("/", methods=["POST"])
def weather_post():
    data=request.get_json()
    location=data.get("coordinates")
    dates=data.get("dates")
    weather_info=findWeatherByLocation(location, dates)
    return jsonify(weather_info)