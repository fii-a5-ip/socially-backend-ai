# Distance Matrix API Blueprint — Detailed README

## 1. What this module is, in very simple words

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

The blueprint is defined like this:

```python
distance_bp = Blueprint(
    'findDistanceBetween2Coord',
    __name__,
    url_prefix='/findDistanceBetween2Coord'
)
```

and the route is defined like this:

```python
@distance_bp.route('/', methods=['POST'])
```

So the route exposed by this blueprint is:

```http
POST /findDistanceBetween2Coord/
```

If your main Flask app registers the blueprint under `/api`, then the final route becomes:

```http
POST /api/findDistanceBetween2Coord/
```

That part depends on how the main Flask app mounts the blueprint.

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

## 4. Input explained in very simple terms

### `sources`
This is the list of points you start from.

Example:

```json
"sources": [
  { "lon": 27.5879, "lat": 47.1585 }
]
```

This means:

- there is **one starting point**
- that starting point is at longitude `27.5879`, latitude `47.1585`

---

### `destinations`
This is the list of points you want to go to.

Example:

```json
"destinations": [
  { "lon": 26.1025, "lat": 44.4268 },
  { "lon": 23.5914, "lat": 46.7712 }
]
```

This means:

- destination with index `0` is `[26.1025, 44.4268]`
- destination with index `1` is `[23.5914, 46.7712]`

---

## 5. Full example input

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

### Very important
The response is **not** a list.

It is a dictionary where:

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

## 7. Exact output example

For the example input above, the expected output looks like this:

```json
{
  "0": {
    "0": { "distance": 385000, "time": 21500 },
    "1": { "distance": 450000, "time": 26000 }
  }
}
```

---

## 8. Output explained like for a beginner

Let us read this very slowly:

```json
{
  "0": {
    "0": { "distance": 385000, "time": 21500 },
    "1": { "distance": 450000, "time": 26000 }
  }
}
```

### Outer key `"0"`
This is the source index.

So:

```json
"0": { ... }
```

means:

> these are the results for source number 0

---

### Inner key `"0"`
This is the destination index.

So:

```json
"0": {
  "0": { "distance": 385000, "time": 21500 }
}
```

means:

> from source 0 to destination 0, the distance is 385000 meters and the time is 21500 seconds

---

### Inner key `"1"`
This is destination number 1.

So:

```json
"1": { "distance": 450000, "time": 26000 }
```

means:

> from source 0 to destination 1, the distance is 450000 meters and the time is 26000 seconds

---

## 9. Very explicit interpretation of the example response

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




## 10. Step 1 — read the API key

```python
api_key = os.environ.get("GEOAPIFY_DISTANCE_API_KEY")
```

The function reads the API key from an environment variable.

### Required environment variable

```bash
GEOAPIFY_DISTANCE_API_KEY
```

Without this key, the request to Geoapify cannot work.

### Important note
This code does **not** explicitly check whether the API key is missing before building the URL.
So if the key is missing, the request may fail later when trying to call Geoapify.

---

## 11. Step 2 — build Geoapify URL

```python
api_url = f'https://api.geoapify.com/v1/routematrix?api_key={api_key}'
```

This creates the external API URL.

So the request is sent to the Geoapify Route Matrix endpoint.

---

## 12. Step 3 — read the incoming JSON request

```python
data = request.get_json()
```

This reads the JSON body sent by the caller.

For example, if the caller sends:

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

then `data` becomes a Python dictionary with those two keys.

---

## 13. Step 4 — create the payload that Geoapify expects

The code creates this initial payload:

```python
payload = {
    "mode": "drive",
    "sources": [],
    "targets": []
}
```

### What this means

- `mode: "drive"` means car routing
- `sources` will contain all starting points
- `targets` will contain all destination points

Important:
the incoming request uses the name `destinations`, but Geoapify expects the key `targets`.

So internally the code translates:

- incoming `destinations` → external `targets`

---

## 14. Step 5 — convert request coordinates to Geoapify format

The code loops through input sources:

```python
for source in data['sources']:
    payload['sources'].append({'location': [source['lon'], source['lat']]})
```

and loops through input destinations:

```python
for target in data['destinations']:
    payload['targets'].append({'location': [target['lon'], target['lat']]})
```

### Very important
The location array is built like this:

```python
[lon, lat]
```

not like this:

```python
[lat, lon]
```

So the exact structure sent to Geoapify is:

```json
{
  "location": [longitude, latitude]
}
```

This order matters a lot.

If you swap them, results become wrong.

---

## 15. Example of the exact payload sent to Geoapify

For this input:

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

the payload sent to Geoapify becomes:

```json
{
  "mode": "drive",
  "sources": [
    { "location": [27.5879, 47.1585] }
  ],
  "targets": [
    { "location": [26.1025, 44.4268] },
    { "location": [23.5914, 46.7712] }
  ]
}
```

That is the exact transformed format.

---

## 16. Step 6 — send the POST request to Geoapify

The code sends:

```python
response = requests.request(
    "POST",
    api_url,
    headers=headers,
    data=json.dumps(payload)
)
```

with:

```python
headers = {
    'Content-Type': 'application/json'
}
```

So the external call is a JSON `POST` request.

---

## 17. Step 7 — retry if the external service fails

This part exists so temporary Geoapify/network problems do not instantly fail the endpoint.

```python
max_retries = 5
for attempt in range(max_retries):
    try:
        response = requests.request(...)
        response.raise_for_status()
        break
    except requests.exceptions.RequestException as e:
        ...
        time.sleep(attempt)
```

### What this means

The code tries up to **5 times**.

If the request works:
- it breaks out of the loop
- continues normally

If the request fails:
- it waits a bit
- tries again

### Actual waiting times
Because the code uses:

```python
time.sleep(attempt)
```

the sleeps are:

- attempt `0` → sleep `0` seconds
- attempt `1` → sleep `1` second
- attempt `2` → sleep `2` seconds
- attempt `3` → sleep `3` seconds
- last attempt fails → returns error

So this is a **simple incremental backoff**.

Strictly speaking, it is not a true exponential backoff.
It is more like a linear retry delay.

---

## 18. Step 8 — secure error logging

If all retries fail, the code does this:

```python
safe_error = str(e).replace(api_key, '[REDACTED]').replace(
    urllib.parse.quote(api_key, safe=''),
    '[REDACTED]'
)
logger.error("Geoapify request failed after %d attempts: %s", max_retries, safe_error)
```

### Why this matters

Sometimes error messages can accidentally include the API key in plain text or URL-encoded form.

This code removes the API key before logging.

So even if logs are stored somewhere, the secret is less likely to leak.

### Returned error in that case

```json
{
  "error": "Upstream location service is unavailable. Please try again later."
}
```

with HTTP status:

```http
502 Bad Gateway
```

---

## 19. Step 9 — read Geoapify response body

If the request succeeds:

```python
body = response.json()
```

Now `body` contains the response from Geoapify.

The code expects Geoapify to return a field called:

```python
body['sources_to_targets']
```

This field contains the route matrix data.

---

## 20. Step 10 — initialize the result dictionary

The code starts with:

```python
result = {}

for i in range(len(payload['sources'])):
    result[i] = {}
```

### What this does

If you have 1 source:

```python
result = {
    0: {}
}
```

If you have 2 sources:

```python
result = {
    0: {},
    1: {}
}
```

So first, it creates one empty inner dictionary for each source index.

---

## 21. Step 11 — fill the matrix with distance and time

The code then does:

```python
for info_list in body['sources_to_targets']:
    for item in info_list:
        result[item['source_index']][item['target_index']] = {
            'distance': item['distance'],
            'time': item['time']
        }
```

### What this means

For every route item returned by Geoapify, it reads:

- `source_index`
- `target_index`
- `distance`
- `time`

and stores them in the result dictionary.

So if Geoapify gives:

```json
{
  "source_index": 0,
  "target_index": 1,
  "distance": 450000,
  "time": 26000
}
```

the code writes:

```python
result[0][1] = {
    "distance": 450000,
    "time": 26000
}
```

---




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

### Example request in Python

```python
import requests

url = "http://localhost:5000/api/findDistanceBetween2Coord/"

data = {
    "sources": [
        {"lon": 27.5879, "lat": 47.1585}
    ],
    "destinations": [
        {"lon": 26.1025, "lat": 44.4268},
        {"lon": 23.5914, "lat": 46.7712}
    ]
}

response = requests.post(url, json=data)
result = response.json()

print(result)
```

Possible output:

```python
{
    "0": {
        "0": {"distance": 385000, "time": 21500},
        "1": {"distance": 450000, "time": 26000}
    }
}
```

---



## 24. How to iterate through the response in Python

Suppose you receive:

```python
result = {
    "0": {
        "0": {"distance": 385000, "time": 21500},
        "1": {"distance": 450000, "time": 26000}
    }
}
```

You can iterate like this:

```python
for source_index, destinations in result.items():
    print("Source:", source_index)

    for destination_index, route_info in destinations.items():
        print("  Destination:", destination_index)
        print("    Distance:", route_info["distance"], "meters")
        print("    Time:", route_info["time"], "seconds")
```

### Output

```text
Source: 0
  Destination: 0
    Distance: 385000 meters
    Time: 21500 seconds
  Destination: 1
    Distance: 450000 meters
    Time: 26000 seconds
```

---


## 25. Very simple mental model for parsing the response

Think of the response like a table:

| Source Index | Destination Index | Distance | Time |
|---|---:|---:|---:|
| 0 | 0 | 385000 | 21500 |
| 0 | 1 | 450000 | 26000 |

Only the actual JSON is not returned as a flat table.
It is returned as a nested object:

```json
{
  "0": {
    "0": { "distance": 385000, "time": 21500 },
    "1": { "distance": 450000, "time": 26000 }
  }
}
```

So the developer must understand:

- first select source
- then select destination
- then read distance/time

---

## 26. cURL example

```bash
curl -X POST "http://localhost:5000/api/findDistanceBetween2Coord/" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": [
      {"lon": 27.5879, "lat": 47.1585}
    ],
    "destinations": [
      {"lon": 26.1025, "lat": 44.4268},
      {"lon": 23.5914, "lat": 46.7712}
    ]
  }'
```

---

## 27. Exact error response currently implemented

If Geoapify fails after all retries, the endpoint returns:

### HTTP status
```http
502 Bad Gateway
```

### JSON body

```json
{
  "error": "Upstream location service is unavailable. Please try again later."
}
```

---

## 28. Important limitations of the current code


### A. No explicit input validation
The code assumes that:

- `data` exists
- `data['sources']` exists
- `data['destinations']` exists
- every source has `lon` and `lat`
- every destination has `lon` and `lat`

If one of these is missing, the function may crash with a `KeyError` or another exception.

So right now the expected format is strict.

### B. API key missing is not handled explicitly
If `GEOAPIFY_DISTANCE_API_KEY` is missing, the code still builds the URL.
Failure happens later at request time.

### C. Retry delay is linear, not truly exponential
The description says “exponential backoff retry loop”, but the actual code is:

```python
time.sleep(attempt)
```

That is linear/incremental delay:

- 0s
- 1s
- 2s
- 3s
- 4s

not exponential like:

- 1s
- 2s
- 4s
- 8s
- 16s

### D. It depends on Geoapify response shape
The code expects `body['sources_to_targets']` to exist and each item to contain:

- `source_index`
- `target_index`
- `distance`
- `time`

If Geoapify changes shape, this code would need updates.

---

## 29. this is the essential contract:



### Send this

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

### Receive this

```json
{
  "0": {
    "0": { "distance": 385000, "time": 21500 },
    "1": { "distance": 450000, "time": 26000 }
  }
}
```

### And interpret it like this

- `result["0"]["0"]` = source 0 → destination 0
- `result["0"]["1"]` = source 0 → destination 1

Each route gives:

- `distance` in meters
- `time` in seconds

That is the main integration contract.

---

## 30. Suggested short explanation



> Endpoint-ul primește un POST JSON cu două liste: `sources` și `destinations`.  
> Fiecare element are `{ "lon": ..., "lat": ... }`.  
> Returnează o matrice sub formă de dicționar imbricat unde cheia de nivel 1 este indexul sursei, iar cheia de nivel 2 este indexul destinației.  
> Pentru fiecare pereche primești:
> - `distance` în metri
> - `time` în secunde  
> Exemplu: `result["0"]["1"]` înseamnă ruta de la sursa 0 la destinația 1.

---

## 31. Minimal integration example

```python
response = requests.post(
    "http://localhost:5000/api/findDistanceBetween2Coord/",
    json={
        "sources": [
            {"lon": 27.5879, "lat": 47.1585}
        ],
        "destinations": [
            {"lon": 26.1025, "lat": 44.4268},
            {"lon": 23.5914, "lat": 46.7712}
        ]
    }
)

result = response.json()

route_0_to_0 = result["0"]["0"]
route_0_to_1 = result["0"]["1"]

print("0 -> 0 distance:", route_0_to_0["distance"])
print("0 -> 0 time:", route_0_to_0["time"])

print("0 -> 1 distance:", route_0_to_1["distance"])
print("0 -> 1 time:", route_0_to_1["time"])
```

---

## 32. One last beginner-friendly explanation

This endpoint is basically a **distance/time calculator between coordinate lists**.

You give it:

- where you start
- where you want to arrive

and it gives you back a matrix.

So if the consumer sees:

```json
{
  "1": {
    "2": {
      "distance": 123456,
      "time": 7890
    }
  }
}
```

they should read it as:

> from source index 1 to destination index 2, the driving distance is 123456 meters and the estimated travel time is 7890 seconds

That is all the consumer really needs to understand.

---

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

        String url = "http://localhost:5000/api/findDistanceBetween2Coord/";

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
