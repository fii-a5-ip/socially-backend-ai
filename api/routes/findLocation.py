import requests
from pathlib import Path
import asyncio
import json
import os
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify

# --- COD ADAUGAT PENTRU HARTA INTERACTIVA: Importul librariei Folium ---
import folium

from api.services.groq_service import get_ai_filters
from api.services.db_service import extrage_filtre_din_db

load_dotenv()

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

findLocation_bp = Blueprint('findLocation', __name__, url_prefix='/findLocation')

def safe_get(url: str, params: dict) -> dict:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def get_place_details_by_id(place_id: str) -> dict:
    if not place_id:
        return {}

    url = "https://api.geoapify.com/v2/place-details"
    params = {
        "id": place_id,
        "features": "details,building",
        "apiKey": GEOAPIFY_API_KEY
    }

    try:
        data = safe_get(url, params)
        features = data.get("features", [])
        if not features:
            return {}
        return features[0].get("properties", {})
    except Exception:
        return {}

def get_static_data(details: dict) -> dict:
    # Static data is data that can be directly extracted from api without any significant AI processing / parsing
    # Opening Hours will be parsed dynamically
    result = {}

    # Name
    result['name'] = details.get('name')

    # Address
    result['formatted_address'] = details.get('formatted')

    result['address'] = {}
    result['address']['country'] = details.get('country')
    result['address']['state'] = details.get('state')
    result['address']['postcode'] = details.get('postcode')
    result['address']['city'] = details.get('city')
    result['address']['street'] = details.get('street')
    result['address']['street_number'] = details.get('housenumber')

    # Extra Identity
    result['brand'] = details.get('brand')
    result['operator'] = details.get('operator')

    # Coordinates
    result['coord'] = {}
    result['coord']['lat'] = details.get('lat')
    result['coord']['lon'] = details.get('lon')

    # Contact
    contact_data = details.get('contact', {})
    result['contact'] = {}
    result['contact']['website'] = details.get('website')
    result['contact']['email'] = contact_data.get('email') # Va returna None daca nu exista
    result['contact']['phone'] = contact_data.get('phone')
    result['contact']['facebook'] = contact_data.get('facebook')
    result['contact']['instagram'] = contact_data.get('instagram')

    return result

def normalize_tags(api_tags: dict) -> list:
    # Map Geoapify API tags to our normalized tags
    try:
        # CITIREA PROMPTULUI EXTERN
        script_dir = Path(__file__).parent.parent
        file_path = script_dir / 'resources' / 'geoapifyToFilters_prompt.txt'
        with open(file_path, 'r', encoding='utf-8') as file:
            mesaj_sistem = file.read()

        # Deoarece funcția get_ai_filters este asincronă (async), 
        # folosim asyncio.run() pentru a o apela din acest mediu sincron de Flask

        filtre_db_text = extrage_filtre_din_db()
        mesaj_sistem_complet = mesaj_sistem.replace("{FILTERS_PLACEHOLDER}", filtre_db_text)

        rezultat_ai = asyncio.run(get_ai_filters(mesaj_sistem_complet, json.dumps(api_tags)))
        
        # 3. Verificăm dacă serviciul a returnat o eroare controlată
        if "error" in rezultat_ai:
            return []

        print(rezultat_ai)
        # 4. Dacă totul e ok, returnăm filtrele extrase!
        return rezultat_ai['tags']

    except Exception:
        return []
    
def normalize_opening_hours(string: str) -> dict:
    # Transform string into parsable format
    try:
        # CITIREA PROMPTULUI EXTERN
        script_dir = Path(__file__).parent.parent
        file_path = script_dir / 'resources' / 'openingHoursToDict_prompt.txt'
        with open(file_path, 'r', encoding='utf-8') as file:
            mesaj_sistem = file.read()

        # Deoarece funcția get_ai_filters este asincronă (async), 
        # folosim asyncio.run() pentru a o apela din acest mediu sincron de Flask
        rezultat_ai = asyncio.run(get_ai_filters(mesaj_sistem, string))
        
        # 3. Verificăm dacă serviciul a returnat o eroare controlată
        if "error" in rezultat_ai:
            return {}

        # 4. Dacă totul e ok, returnăm filtrele extrase!
        return rezultat_ai
    except Exception:
        return {}

def get_dynamic_data(details: dict) -> dict:
    # Dynamic data is data that needs significant parsing / AI processing
    result = {}

    opening_hours_string = details.get('opening_hours') # MUST be parsed by AI

    # Gathering data for filters
    api_tags = {} # dict of data that will be translated to filters by AI

    api_tags['location_name'] = details.get('name')
    if details.get('brand'):
        api_tags['brand'] = details.get('brand')
    if details.get('description'):
        api_tags['description'] = details.get('description')
    if details.get('formatted_address'):
        api_tags['formatted_address'] = details.get('formatted_address')
    
    properties_types = ['fuel_options', 'accommodation', 'catering',
                        'parking', 'airport', 'building',
                        'place_of_worship', 'commercial', 'historic',
                        'artwork', 'heritage', 'facilities',
                        'restriction', 'wiki_and_media', 'categories']
    
    for type in properties_types:
        if details.get(type):
            api_tags[type] = details.get(type)

    # Give api_tags to AI service with appropiate user_prompt
    tags = normalize_tags(api_tags)
    result['tags'] = tags

    # Give opening_hours_string to AI service with appropiate user_prompt
    if opening_hours_string:
        opening_hours = normalize_opening_hours(opening_hours_string)
        result['opening_hours'] = opening_hours
    else:
        result['opening_hours'] = {}

    return result

def clean_dict(data):
    """
    Recursively removes None, empty strings, empty lists, and empty dicts.
    Preserves 0 and False.
    """
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            # Recursively clean the value
            cleaned_v = clean_dict(v)
            # Keep it if it's not strictly empty
            if cleaned_v not in (None, "", [], {}):
                cleaned[k] = cleaned_v
        return cleaned
    
    elif isinstance(data, list):
        # Recursively clean lists and drop empty items
        cleaned_list = [clean_dict(v) for v in data]
        return [v for v in cleaned_list if v not in (None, "", [], {})]
    
    # Base case: return the value (strings, ints, bools)
    return data
def build_map_data(location_data: dict) -> dict:
    lat = location_data.get("coord", {}).get("lat")
    lon = location_data.get("coord", {}).get("lon")

    if lat is None or lon is None:
        return {}

    # --- COD ADAUGAT PENTRU HARTA INTERACTIVA: Generarea codului HTML pentru Leaflet ---
    html_map = ""
    try:
        m = folium.Map(location=[lat, lon], zoom_start=16, tiles=None)
        tile_url = f"https://maps.geoapify.com/v1/tile/osm-bright/{{z}}/{{x}}/{{y}}.png?apiKey={GEOAPIFY_API_KEY}"
        
        folium.TileLayer(
            tiles=tile_url,
            attr='Powered by Geoapify | © OpenStreetMap',
            name='Geoapify Map',
            max_zoom=20
        ).add_to(m)

        folium.Marker(
            [lat, lon],
            popup='Locația selectată',
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)

        html_map = m.get_root().render()
        # Fix pentru zona gri: forțăm browser-ul să declanșeze 'resize' după 500ms pentru ca Leaflet să descarce tot
        fix_script = "<script>setTimeout(function() { window.dispatchEvent(new Event('resize')); }, 500);</script>"
        html_map = html_map.replace('</body>', fix_script + '\n</body>')
    except Exception as e:
        print(f"Eroare la generarea hartii Folium: {e}")
    # --- SFARSIT COD ADAUGAT ---

    return {
        "provider": "geoapify",
        "interactive": True,
        "center": {
            "lat": lat,
            "lon": lon
        },
        "zoom": 16,
        "marker": {
            "lat": lat,
            "lon": lon,
            "label": location_data.get("name", "Locația selectată")
        },
        "tile_url": f"https://maps.geoapify.com/v1/tile/osm-bright/{{z}}/{{x}}/{{y}}.png?apiKey={GEOAPIFY_API_KEY}",
        # --- COD ADAUGAT PENTRU HARTA INTERACTIVA: Injectarea html-ului in JSON ---
        "html": html_map
    }

def find_location_from_place_id(place_id: str) -> list:
    if not GEOAPIFY_API_KEY:
        raise ValueError("Lipseste variabila GEOAPIFY_API_KEY")

    results = {}

    details = get_place_details_by_id(place_id)
    static_properties = get_static_data(details)
    dynamic_properties = get_dynamic_data(details)

    results.update(static_properties)
    results.update(dynamic_properties)

    results["map"] = build_map_data(results)

    return clean_dict(results)

# --- COD ADAUGAT PENTRU HARTA INTERACTIVA: Ruta de debug pentru vizualizarea directa in browser ---
@findLocation_bp.route('/view', methods=['GET'])
def view_map():
    """Ruta pur vizuala pentru a testa harta direct in browser (ex: /view?lat=47.155&lon=27.605)"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if lat is None or lon is None:
        return "Te rog adauga coordonatele in link. Exemplu: ?lat=47.1551&lon=27.6051", 400
        
    try:
        m = folium.Map(location=[lat, lon], zoom_start=16, tiles=None)
        tile_url = f"https://maps.geoapify.com/v1/tile/osm-bright/{{z}}/{{x}}/{{y}}.png?apiKey={GEOAPIFY_API_KEY}"
        folium.TileLayer(tiles=tile_url, attr='Powered by Geoapify', max_zoom=20).add_to(m)
        folium.Marker([lat, lon], popup='Locația selectată', icon=folium.Icon(color='green', icon='info-sign')).add_to(m)
        
        html_map = m.get_root().render()
        fix_script = "<script>setTimeout(function() { window.dispatchEvent(new Event('resize')); }, 500);</script>"
        return html_map.replace('</body>', fix_script + '\n</body>')
    except Exception as e:
        return f"Eroare la generarea hartii: {e}", 500
# --- SFARSIT COD ADAUGAT ---

@findLocation_bp.route('/', methods=['POST'])
def find_location():

    body = request.get_json()

    if not body or 'place_id' not in body:
        return jsonify({"error": "Te rog trimite un camp 'place_id' valid în format JSON."}), 400
    
    place_id = body['place_id']

    return jsonify(find_location_from_place_id(place_id)), 200



# if __name__ == '__main__': #NOSONAR
#     place_id = '5110afeb17ec9a3b4059b33f506edb934740f00103f901ad2f621d03000000c0020192030a566970657220436c7562e203246f70656e7374726565746d61703a76656e75653a6e6f64652f3133333737383735383835'
#     print(find_location(place_id))