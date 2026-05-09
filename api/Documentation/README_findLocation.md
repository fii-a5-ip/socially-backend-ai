# findLocation API Blueprint — 

## What this module is

This module is a Flask Blueprint that exposes one HTTP endpoint for retrieving location details based on a Geoapify `place_id`.

In one sentence:

You send a `place_id`, and the endpoint returns available information about that location, such as name, address, coordinates, contact data, tags, opening hours and map data.

---

## What endpoint this blueprint exposes

Route exposed by this blueprint:

POST /findLocation/

In the full backend API, it may be available as:

POST /api/findLocation/

depending on how the Blueprint is registered in the main Flask app.

---

## What this endpoint expects as input

This endpoint expects a JSON body sent with an HTTP POST request.

The JSON must contain:

- `place_id`

Exact input format:

{
  "place_id": "<geoapify_place_id>"
}

---

## Full example input

{
  "place_id": "5110afeb17ec9a3b4059b33f506edb934740f00103f901ad2f621d03000000c0020192030a566970657220436c7562e203246f70656e7374726565746d61703a76656e75653a6e6f64652f3133333737383735383835"
}

---

## What this means

You are asking the backend to return information about the location identified by that Geoapify `place_id`.

The `place_id` must come from Geoapify, usually from a previous search/autocomplete request.

---

## What the endpoint returns

The endpoint returns a JSON object with location information.

Possible response fields:

{
  "name": "Viper Club",
  "formatted_address": "Example Street, Iași, Romania",
  "address": {
    "country": "Romania",
    "state": "Iași",
    "postcode": "700000",
    "city": "Iași",
    "street": "Example Street",
    "street_number": "10"
  },
  "brand": "Example Brand",
  "operator": "Example Operator",
  "coord": {
    "lat": 47.1585,
    "lon": 27.6014
  },
  "contact": {
    "website": "https://example.com",
    "email": "contact@example.com",
    "phone": "+40123456789",
    "facebook": "exampleFacebook",
    "instagram": "exampleInstagram"
  },
  "tags": [
    "club",
    "entertainment"
  ],
  "opening_hours": {
    "monday": {
      "open": "10:00",
      "close": "22:00"
    }
  },
  "map": {
    "provider": "geoapify",
    "interactive": true,
    "center": {
      "lat": 47.1585,
      "lon": 27.6014
    },
    "zoom": 16,
    "marker": {
      "lat": 47.1585,
      "lon": 27.6014,
      "label": "Viper Club"
    },
    "tile_url": "https://maps.geoapify.com/v1/tile/osm-bright/{z}/{x}/{y}.png?apiKey=...",
    "html": "<html>...</html>"
  }
}

---

## Critical note for Backend Core

Some fields in the response are optional.

The backend depends on Geoapify data, so not every location will have all fields.

For example, these fields may be missing:

- `formatted_address`
- `address.country`
- `address.state`
- `address.postcode`
- `address.city`
- `address.street`
- `address.street_number`
- `brand`
- `operator`
- `contact.website`
- `contact.email`
- `contact.phone`
- `contact.facebook`
- `contact.instagram`
- `tags`
- `opening_hours`
- `map`
- `map.html`

Important:

The response is cleaned before being returned, so fields with `null`, empty strings, empty arrays or empty objects may be completely removed from the JSON.

Must not assume that every field exists!

Use safe parsing and null checks to avoid errors such as:

- `NullPointerException`
- missing key errors
- invalid cast errors

Example:

Do not assume this is always safe:

location.get("contact").get("phone")

Because `contact` or `phone` may be missing.

Use safe checks before accessing nested fields.

---

## Error response

If the request body is missing or does not contain `place_id`, the endpoint returns:

Status code:

400 Bad Request

Response:

{
  "error": "Te rog trimite un camp 'place_id' valid în format JSON."
}

---

## Suggested short explanation

Endpoint-ul primește un POST JSON cu un câmp `place_id`.

Pe baza acestui `place_id`, returnează informații disponibile despre locație:

- nume
- adresă
- coordonate
- date de contact
- tag-uri
- program
- date pentru hartă interactivă

Important: multe câmpuri sunt opționale deoarece depind de răspunsul Geoapify. Backend Core trebuie să parseze răspunsul defensiv, cu verificări de null/missing fields.

---

## Java usage example

```java
/*
==============================================================================
findLocation API USAGE - PRODUCTION COMMENT
==============================================================================

WHAT THIS CODE DOES:

This example shows how to call our backend endpoint:

    POST /api/findLocation/

The endpoint receives:
- a Geoapify place_id

And returns available location data:
- name
- address
- coordinates
- contact data
- tags
- opening hours
- map data

CRITICAL:

Some fields are optional because they depend on the Geoapify response.
Do not parse the response assuming that all fields exist.
Always check if a field is present before using it.

==============================================================================
*/

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class FindLocationDemo {

    public static void main(String[] args) throws Exception {

        String apiUrl = ""; // API URL, example: localhost:5000
        String url = "http://" + apiUrl + "/api/findLocation/";

        String json = """
        {
          "place_id": "5110afeb17ec9a3b4059b33f506edb934740f00103f901ad2f621d03000000c0020192030a566970657220436c7562e203246f70656e7374726565746d61703a76656e75653a6e6f64652f3133333737383735383835"
        }
        """;

        HttpClient client = HttpClient.newHttpClient();

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        HttpResponse<String> response =
                client.send(request, HttpResponse.BodyHandlers.ofString());

        ObjectMapper mapper = new ObjectMapper();
        JsonNode location = mapper.readTree(response.body());

        if (response.statusCode() != 200) {
            System.out.println("Request failed: " + location.toPrettyString());
            return;
        }

        String name = location.path("name").asText(null);
        String formattedAddress = location.path("formatted_address").asText(null);

        JsonNode coord = location.path("coord");
        Double lat = coord.has("lat") ? coord.get("lat").asDouble() : null;
        Double lon = coord.has("lon") ? coord.get("lon").asDouble() : null;

        JsonNode contact = location.path("contact");
        String phone = contact.path("phone").asText(null);
        String website = contact.path("website").asText(null);

        System.out.println("Name: " + name);
        System.out.println("Address: " + formattedAddress);
        System.out.println("Latitude: " + lat);
        System.out.println("Longitude: " + lon);
        System.out.println("Phone: " + phone);
        System.out.println("Website: " + website);

        if (location.has("tags")) {
            System.out.println("Tags: " + location.get("tags"));
        }

        if (location.has("opening_hours")) {
            System.out.println("Opening hours: " + location.get("opening_hours"));
        }

        if (location.has("map")) {
            JsonNode map = location.get("map");

            String provider = map.path("provider").asText(null);
            String html = map.path("html").asText(null);

            System.out.println("Map provider: " + provider);

            if (html != null) {
                System.out.println("Interactive map HTML is available.");
            }
        }
    }
}