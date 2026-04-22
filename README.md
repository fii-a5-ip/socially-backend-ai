# Distance Matrix API Blueprint — Detailed README

## 1. What this module is

This module is a **Flask Blueprint** that exposes one HTTP endpoint.

That endpoint receives:

- a list of **source coordinates** (`sources`)
- a list of **destination coordinates** (`destinations`)

and returns, for **every source → destination combination**:

- the **driving distance** in meters
- the **estimated driving time** in seconds

So, in one sentence:

> You send several starting points and several ending points, and this endpoint returns a routing matrix that tells you how far and how long it takes to drive between each pair.

---

## 2. What endpoint this blueprint exposes

So the route exposed by this blueprint is:

```http
POST /api/findDistanceBetween2Coord/
```

---

## 3. What this endpoint expects as input

This endpoint expects a **JSON body** sent with an HTTP `POST` request.

The JSON must contain exactly these top-level keys:

- `sources`
- `destinations`

Both must be **lists**.

Each item inside those lists must be an object with:

- `lon` = longitude
- `lat` = latitude

### Exact input format

```json
{
  "sources": [
    { "lon": <float>, "lat": <float> }
  ],
  "destinations": [
    { "lon": <float>, "lat": <float> }
  ]
}
```

---

## 4. Full example input

Here is the exact example input from the endpoint contract:

```json
{
  "sources": [
    { "lon": 27.5879, "lat": 47.1585 }
  ],
  "destinations": [
    { "lon": 26.1025, "lat": 44.4268 },
    { "lon": 23.5914, "lat": 46.7712 }
  ]
}
```

### What this means

You are asking:

- from source `0` = `(27.5879, 47.1585)`
- to destination `0` = `(26.1025, 44.4268)`
- to destination `1` = `(23.5914, 46.7712)`

So there are **2 route calculations** total:

1. source `0` → destination `0`
2. source `0` → destination `1`

---

## 6. What the endpoint returns

The endpoint returns a **nested dictionary** (JSON object inside JSON object).
- the **first key** is the source index
- the **second key** is the destination index

And for each pair, you get:

- `distance`
- `time`

### Exact output shape

```json
{
  "<source_index>": {
    "<destination_index>": {
      "distance": <number>,
      "time": <number>
    }
  }
}
```

---

## 9. interpretation of the example response

Given:

### Input

```json
{
  "sources": [
    { "lon": 27.5879, "lat": 47.1585 }
  ],
  "destinations": [
    { "lon": 26.1025, "lat": 44.4268 },
    { "lon": 23.5914, "lat": 46.7712 }
  ]
}
```

### Output

```json
{
  "0": {
    "0": { "distance": 385000, "time": 21500 },
    "1": { "distance": 450000, "time": 26000 }
  }
}
```

This means:

- from source `0` to destination `0`
  - distance = `385000` meters
  - time = `21500` seconds

- from source `0` to destination `1`
  - distance = `450000` meters
  - time = `26000` seconds

---


## 22. Example with multiple sources and multiple destinations

Suppose the request is:

```json
{
  "sources": [
    { "lon": 27.5879, "lat": 47.1585 },
    { "lon": 26.1025, "lat": 44.4268 }
  ],
  "destinations": [
    { "lon": 23.5914, "lat": 46.7712 },
    { "lon": 21.2257, "lat": 45.7489 }
  ]
}
```

Then there are 4 combinations:

- source `0` → destination `0`
- source `0` → destination `1`
- source `1` → destination `0`
- source `1` → destination `1`

A possible output shape would be:

```json
{
  "0": {
    "0": { "distance": 100000, "time": 7000 },
    "1": { "distance": 200000, "time": 14000 }
  },
  "1": {
    "0": { "distance": 300000, "time": 21000 },
    "1": { "distance": 400000, "time": 28000 }
  }
}
```



---

## 23. How to call this endpoint from another service

## 30. Suggested short explanation



> Endpoint-ul primește un POST JSON cu două liste: `sources` și `destinations`.  
> Fiecare element are `{ "lon": ..., "lat": ... }`.  
> Returnează o matrice sub formă de dicționar imbricat unde cheia de nivel 1 este indexul sursei, iar cheia de nivel 2 este indexul destinației.  
> Pentru fiecare pereche primești:
> - `distance` în metri
> - `time` în secunde  
> Exemplu: `result["0"]["1"]` înseamnă ruta de la sursa 0 la destinația 1.

---

##  Java usage example (PRODUCTION READY)

```java
/*
==============================================================================
DISTANCE MATRIX API USAGE (PRODUCTION COMMENT)
==============================================================================

WHAT THIS CODE DOES:

This example shows how to call our backend endpoint:
    POST /api/findDistanceBetween2Coord/

The endpoint receives:
- a list of source coordinates
- a list of destination coordinates

And returns a routing matrix with:
- distance (in meters)
- time (in seconds)

==============================================================================

*/

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Map;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

public class DistanceDemo {

    public static void main(String[] args) throws Exception {

        String apiUrl = ""; //API URL, we'll have it when the api is done and deployed
        String url = "http://" + apiUrl + "/api/findDistanceBetween2Coord/";

        String json = """
        {
          "sources": [
            { "lon": 27.5879, "lat": 47.1585 }
          ],
          "destinations": [
            { "lon": 26.1025, "lat": 44.4268 },
            { "lon": 23.5914, "lat": 46.7712 }
          ]
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

        Map<String, Map<String, Map<String, Integer>>> result =
                mapper.readValue(
                        response.body(),
                        new TypeReference<>() {}
                );

        for (String sourceIndex : result.keySet()) {

            for (String destinationIndex : result.get(sourceIndex).keySet()) {

                int distance = result.get(sourceIndex).get(destinationIndex).get("distance");
                int time = result.get(sourceIndex).get(destinationIndex).get("time");

                System.out.println(
                        sourceIndex + " -> " + destinationIndex +
                        " | distance=" + distance +
                        " | time=" + time
                );
            }
        }

        int distance01 = result.get("0").get("1").get("distance");
        int time01 = result.get("0").get("1").get("time");

        System.out.println("\nExample (0 -> 1): distance=" + distance01 + ", time=" + time01);
    }
}
```
