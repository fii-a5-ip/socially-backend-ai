# Location Autocomplete API Blueprint — Detailed README

## What this module is, in very simple words

This module is a **Flask Blueprint** that exposes one HTTP endpoint.
That endpoint receives a piece of text like:

- `"Retr"`
- `"Bucha"`
- `"Pia"`

and returns a list of matching places.

The module does **not** search the database directly.
Instead, it calls the **Geoapify Autocomplete API**, receives Geoapify's answer, cleans it up, keeps only the useful fields, sorts the results by distance, and then sends a much simpler JSON response to the rest of your application.

So, in one sentence:

> The user types some letters, this endpoint asks Geoapify for suggestions, and returns a clean list of places.

---

## Endpoint exposed by this blueprint

When this blueprint is registered in Flask, it exposes:

```http
GET /api/autocompleteLocationName/
```

---

## Query parameters

### Required

#### `partialName`
- Type: `string`
- Meaning: the incomplete text entered by the user.
- Example values:
  - `Retr`
  - `McD`
  - `Pia`
  - `Buch`

### Optional

#### `userLatCoord`
- Type: `float` sent as query string
- Meaning: user's latitude
- Example: `44.4268`

#### `userLonCoord`
- Type: `float` sent as query string
- Meaning: user's longitude
- Example: `26.1025`

If both coordinates are present:
- Geoapify is **biased toward nearby results**.
- Results are **strictly filtered to 100 km around the user**.
- Returned locations are then **sorted by distance**.

If coordinates are missing:
- Search still works.
- But it is no longer proximity-based.

---

## Example requests and outputs

## Example 1 — request without coordinates

### Request

```http
GET /api/autocompleteLocationName/?partialName=Retr
```

### What it means
User typed `Retr`, but we do not know where the user is.
So we do a normal autocomplete search.

### Example response

```json
[
  {
    "name": "Retro Cafe",
    "place_id": "place_1",
    "coordinates": {
      "lat": 44.4501,
      "lon": 26.0912
    },
    "full_address": "Retro Cafe, Bucharest, Romania",
    "address": {
      "country": "Romania",
      "city": "Bucharest",
      "street": null,
      "street_number": null
    },
    "distance_meters": 0
  },
  {
    "name": "Retro Bistro",
    "place_id": "place_2",
    "coordinates": {
      "lat": 44.4310,
      "lon": 26.1200
    },
    "full_address": "Retro Bistro, Bucharest, Romania",
    "address": {
      "country": "Romania",
      "city": "Bucharest",
      "street": "Example Street",
      "street_number": "5"
    },
    "distance_meters": 0
  }
]
```

Note:
When Geoapify does not provide meaningful distance, ordering may be less useful.
The code still returns the normalized structure.

---

## Example 2 — request with coordinates

### Request

```http
GET /autocompleteLocationName/?partialName=Retr&userLatCoord=44.4268&userLonCoord=26.1025
```

### What it means
User typed `Retr`, and their current location is known.
So:
- Geoapify is biased toward nearby matches.
- Only results within 100 km are allowed.
- The final list is sorted by `distance_meters`.

### Example response

```json
[
  {
    "name": "Restaurant Demo",
    "place_id": "123",
    "coordinates": {
      "lat": 44.4268,
      "lon": 26.1025
    },
    "full_address": "Strada Exemplu 10, Bucharest, Romania",
    "address": {
      "country": "Romania",
      "city": "Bucharest",
      "street": "Strada Exemplu",
      "street_number": "10"
    },
    "distance_meters": 215
  },
  {
    "name": "Restaurant Demo 2",
    "place_id": "456",
    "coordinates": {
      "lat": 44.4300,
      "lon": 26.1100
    },
    "full_address": "Another Street 5, Bucharest, Romania",
    "address": {
      "country": "Romania",
      "city": "Bucharest",
      "street": "Another Street",
      "street_number": "5"
    },
    "distance_meters": 890
  }
]
```

Notice the order:
- first result: `215` meters
- second result: `890` meters

So the response is intentionally ordered from nearest to farthest.

---


### Request explination

```http
GET /api/autocompleteLocationName/?partialName=Retr&userLatCoord=44.4268&userLonCoord=26.1025
```

We will receive

```json
[
  {
    "name": "...",
    "place_id": "...",
    "coordinates": {
      "lat": 0,
      "lon": 0
    },
    "full_address": "...",
    "address": {
      "country": "...",
      "city": "...",
      "street": "...",
      "street_number": "..."
    },
    "distance_meters": 0
  }
]
```

So if they want to display suggestions in UI, they typically use:
- `name`
- `full_address`
- `distance_meters`

If they want to save the selected place, they may use:
- `place_id`
- `coordinates.lat`
- `coordinates.lon`

---

##  Java usage example (PRODUCTION READY)

```java
/*
==============================================================================
LOCATION AUTOCOMPLETE API USAGE (PRODUCTION COMMENT)
==============================================================================

WHAT THIS CODE DOES:

This example shows how to call our backend endpoint:
    GET /api/autocompleteLocationName/

The endpoint receives:
- a partial location name (text typed by user)
- optional user coordinates (lat, lon)

And returns:
- a list of location suggestions sorted by distance

------------------------------------------------------------------------------

REQUEST FORMAT (what we send):

GET /api/autocompleteLocationName/?partialName=Retr&userLatCoord=47.1585&userLonCoord=27.6014

Query params:
- partialName (REQUIRED)
- userLatCoord (OPTIONAL)
- userLonCoord (OPTIONAL)

------------------------------------------------------------------------------

RESPONSE FORMAT (what we receive):

[
  {
    "name": "Restaurant X",
    "place_id": "abc123",
    "coordinates": {
      "lat": 47.1585,
      "lon": 27.6014
    },
    "full_address": "Strada Exemplu 10, Iasi, Romania",
    "address": {
      "country": "Romania",
      "city": "Iasi",
      "street": "Strada Exemplu",
      "street_number": "10"
    },
    "distance_meters": 350
  }
]

IMPORTANT:
- Response is a LIST (array)
- Each element = one location suggestion
- Results are already sorted by distance (closest first)

------------------------------------------------------------------------------

HOW IT IS STORED IN JAVA:

We map JSON to:
List<Map<String, Object>>

Meaning:
- each element in list = one location
- inside map:
    - "name"
    - "place_id"
    - "coordinates" (another map)
    - "address" (another map)
    - "distance_meters"

------------------------------------------------------------------------------

HOW TO ITERATE:

for each location in list:
    read fields from map

------------------------------------------------------------------------------

HOW TO ACCESS FIELDS:

location.get("name")

((Map) location.get("coordinates")).get("lat")

((Map) location.get("address")).get("city")

==============================================================================

*/

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

public class AutocompleteDemo {

    public static void main(String[] args) throws Exception {

        // Base URL of OUR backend API (not Geoapify)
        String apiUrl = ""; //API URL, we'll have it when the api is done and deployed
        String baseUrl = "http://" + apiUrl + "/api/findDistanceBetween2Coord/";

        // Input parameters (what user typed + optional coords)
        String partialName = "Retr";
        double lat = 47.1585;
        double lon = 27.6014;

        // --- BUILD GET URL ---
        String url = baseUrl +
                "?partialName=" + partialName +
                "&userLatCoord=" + lat +
                "&userLonCoord=" + lon;

        HttpClient client = HttpClient.newHttpClient();

        // --- CALL API (GET request) ---
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .GET()
                .build();

        HttpResponse<String> response =
                client.send(request, HttpResponse.BodyHandlers.ofString());

        // --- PARSE JSON RESPONSE INTO LIST OF MAPS ---
        ObjectMapper mapper = new ObjectMapper();

        List<Map<String, Object>> result =
                mapper.readValue(
                        response.body(),
                        new TypeReference<>() {}
                );

        // --- ITERATE THROUGH RESULTS ---
        for (Map<String, Object> location : result) {

            String name = (String) location.get("name");
            String fullAddress = (String) location.get("full_address");

            Map<String, Object> coordinates =
                    (Map<String, Object>) location.get("coordinates");

            Map<String, Object> address =
                    (Map<String, Object>) location.get("address");

            Double latValue = (Double) coordinates.get("lat");
            Double lonValue = (Double) coordinates.get("lon");

            String city = (String) address.get("city");

            Object distance = location.get("distance_meters");

            System.out.println(
                    "Name: " + name +
                    " | City: " + city +
                    " | Lat: " + latValue +
                    " | Lon: " + lonValue +
                    " | Distance: " + distance +
                    " | Address: " + fullAddress
            );
        }

        // --- ACCESS FIRST (CLOSEST) RESULT ---
        Map<String, Object> first = result.get(0);

        System.out.println("\nClosest location: " + first.get("name"));
    }
}
```
