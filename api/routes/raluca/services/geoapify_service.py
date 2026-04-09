import requests
from config import Config

GEOAPIFY_API_KEY = Config.GEOAPIFY_API_KEY


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
        "features": "details",
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


def get_places_extra(lat: float, lon: float) -> dict:
    if lat is None or lon is None:
        return {
            "extra_filters": [],
            "facilitati_extra": {}
        }

    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": ",".join([
            "catering",
            "commercial",
            "accommodation",
            "service",
            "healthcare",
            "education",
            "entertainment",
            "leisure"
        ]),
        "filter": f"circle:{lon},{lat},30",
        "limit": 5,
        "apiKey": GEOAPIFY_API_KEY
    }

    try:
        data = safe_get(url, params)

        extra_filters = []
        facilitati_extra = {}

        for feature in data.get("features", []):
            props = feature.get("properties", {})
            extra_filters.extend(props.get("categories", []))
            extra_filters.extend(props.get("details", []))

            if "facilities" in props and isinstance(props["facilities"], dict):
                facilitati_extra.update(props["facilities"])

            if "internet_access" in props:
                facilitati_extra["internet_access"] = props.get("internet_access")

            if "wheelchair" in props:
                facilitati_extra["wheelchair"] = props.get("wheelchair")

            if "toilets" in props:
                facilitati_extra["toilets"] = props.get("toilets")

            if "levels" in props:
                facilitati_extra["levels"] = props.get("levels")

            if "type" in props:
                facilitati_extra["type"] = props.get("type")

        return {
            "extra_filters": list(dict.fromkeys(extra_filters)),
            "facilitati_extra": facilitati_extra
        }
    except Exception:
        return {
            "extra_filters": [],
            "facilitati_extra": {}
        }


def build_attributes(merged_filters: list, facilitati_extra: dict) -> dict:
    wheelchair_value = facilitati_extra.get("wheelchair")

    attrs = {
        "wifi": False,
        "wheelchair": False,
        "wheelchair_yes": False,
        "wheelchair_limited": False,
        "vegan": "necunoscut",
        "vegan_only": False,
        "vegetarian": "necunoscut",
        "vegetarian_only": False,
        "outdoor_seating": False
    }

    if "internet_access" in merged_filters or "internet_access.free" in merged_filters:
        attrs["wifi"] = True

    if wheelchair_value is True:
        attrs["wheelchair"] = True
        attrs["wheelchair_yes"] = True
    elif wheelchair_value == "yes":
        attrs["wheelchair"] = True
        attrs["wheelchair_yes"] = True
    elif wheelchair_value == "limited":
        attrs["wheelchair"] = True
        attrs["wheelchair_limited"] = True

    if "wheelchair" in merged_filters:
        attrs["wheelchair"] = True
    if "wheelchair.yes" in merged_filters:
        attrs["wheelchair"] = True
        attrs["wheelchair_yes"] = True
    if "wheelchair.limited" in merged_filters:
        attrs["wheelchair"] = True
        attrs["wheelchair_limited"] = True

    if "vegan.only" in merged_filters:
        attrs["vegan"] = "da"
        attrs["vegan_only"] = True
    elif "vegan" in merged_filters:
        attrs["vegan"] = "da"

    if "vegetarian.only" in merged_filters:
        attrs["vegetarian"] = "da"
        attrs["vegetarian_only"] = True
    elif "vegetarian" in merged_filters:
        attrs["vegetarian"] = "da"

    if "outdoor_seating" in merged_filters:
        attrs["outdoor_seating"] = True

    return attrs


def build_tags(facilitati_extra: dict, attrs: dict, categories: list) -> list:
    tags = []

    if attrs.get("wifi"):
        tags.append("WiFi")

    if attrs.get("wheelchair"):
        tags.append("Acces persoane cu dizabilitati")

    if facilitati_extra.get("toilets") is True:
        tags.append("Toalete")

    if attrs.get("outdoor_seating"):
        tags.append("Terasa")

    if attrs.get("vegan") == "da":
        tags.append("Optiuni vegane")

    if attrs.get("vegetarian") == "da":
        tags.append("Optiuni vegetariene")

    if "commercial.shopping_mall" in categories:
        tags.append("Mall")

    if "catering.restaurant" in categories:
        tags.append("Restaurant")

    if "catering.cafe" in categories:
        tags.append("Cafea")

    if facilitati_extra.get("type") == "retail":
        tags.append("Retail")

    return list(dict.fromkeys(tags))


def get_tip_locatie(categories: list, facilitati_extra: dict) -> str:
    if "commercial.shopping_mall" in categories:
        return "mall"
    if "catering.restaurant" in categories:
        return "restaurant"
    if "catering.cafe" in categories:
        return "cafe"
    if "accommodation.hotel" in categories:
        return "hotel"
    if facilitati_extra.get("type") == "retail":
        return "retail"
    return "necunoscut"


def map_location(props: dict, details: dict, extra_filters: list, facilitati_extra: dict) -> dict:
    contact = details.get("contact", {}) if details else {}

    categories = props.get("categories", [])
    details_list = props.get("details", [])
    merged_filters = list(dict.fromkeys(categories + details_list + extra_filters))

    attrs = build_attributes(merged_filters, facilitati_extra)
    tags = build_tags(facilitati_extra, attrs, merged_filters)
    tip_locatie = get_tip_locatie(merged_filters, facilitati_extra)

    return {
        "nume": props.get("name") or props.get("formatted"),
        "adresa": props.get("formatted"),
        "formatted": props.get("formatted"),
        "street": props.get("street"),
        "place_id": props.get("place_id"),
        "osm_type": props.get("osm_type"),
        "result_type": props.get("result_type"),
        "lat": props.get("lat"),
        "lon": props.get("lon"),
        "coordonate": {
            "lat": props.get("lat"),
            "lon": props.get("lon")
        },
        "date_contact": {
            "telefon": contact.get("phone"),
            "website": contact.get("website"),
            "email": contact.get("email")
        },
        "contact": {
            "telefon": contact.get("phone"),
            "website": contact.get("website"),
            "email": contact.get("email")
        },
        "program": details.get("opening_hours"),
        "categories": categories,
        "details": details_list,
        "filtre": merged_filters,
        "facilitati_extra": facilitati_extra,
        "atribute": attrs,
        "tip_locatie": tip_locatie,
        "tags": tags,
        "operator": details.get("operator"),
        "wikidata": details.get("wikidata")
    }


def find_location(location_name: str) -> list:
    if not GEOAPIFY_API_KEY:
        raise Exception("Lipseste variabila GEOAPIFY_API_KEY")

    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": location_name,
        "limit": 10,
        "filter": "countrycode:ro",
        "bias": "proximity:27.5877,47.1585",
        "apiKey": GEOAPIFY_API_KEY
    }

    data = safe_get(url, params)
    results = []

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        place_id = props.get("place_id")
        lat = props.get("lat")
        lon = props.get("lon")

        details = get_place_details_by_id(place_id)

        extra_data = get_places_extra(lat, lon)
        extra_filters = extra_data.get("extra_filters", [])
        facilitati_extra = extra_data.get("facilitati_extra", {})

        results.append(
            map_location(props, details, extra_filters, facilitati_extra)
        )

    return results