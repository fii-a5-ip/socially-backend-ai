FLUX AI

Userul scrie in aplicatie un prompt. Aplicatia impacheteaza acest text intr-un JSON 
{
	"prompt" : "vreau sa beau un suculet de mere"
}

si face un request http de tip POST catre server pe ruta /api/searchToFilters/


Preluarea datelor (searchToFilters.py)
	Ruta preia request-ul.
	Verifică existența câmpului prompt și extrage textul.
	Apelează funcția get_ai_filters(text) (importată din groq_service.py).
	În acest moment, execuția în searchToFilters.py se oprește și așteaptă rezultatul.

Procesarea AI (groq_service.py)
	Funcția get_ai_filters ia textul primit ca parametru.
	Citește instrucțiunile din prompt.txt.
	Preia cheia API din fișierul .env.
	Face un request asincron către API-ul groq. Dacă e nevoie, rotește cheile.
	Groq returnează un JSON cu filtrele extrase.
	Funcția dă return json_ai (trimite datele înapoi de unde a fost apelată).


searchToFilters.py primeste dictionarul cu filtre si il trimite cu http inapoi catre aplicatie


pentru a integra aceasta functie in aplicatie trebuie sa se faca un request respectand:

	-endpoint: POST http://<IP SERVER>:5000/api/searchToFilters/
	-header necesar: Content-Type: application/json
	-body ( ce trebuie sa trimita aplicatia) { "prompt": "text random introdus de user" } 
	-response : {
					"filtre_id": [
						710,
						419,
						412
					]
				}
				
				
sava poate folosi OkHttp 

si asta e un ex de cod pentru el: ?nu stiu daca ajuta


import okhttp3.*;
import org.json.JSONObject;
import org.json.JSONArray;
import java.io.IOException;

public class SociallyApiClient {
    private static final OkHttpClient client = new OkHttpClient();

    public static void fetchFilters(String userInput) {
        // 1. Definim tipul datelor (JSON)
        MediaType JSON = MediaType.get("application/json; charset=utf-8");

        // 2. Construim body-ul request-ului conform contractului
        String jsonBody = "{\"prompt\": \"" + userInput + "\"}";
        RequestBody body = RequestBody.create(jsonBody, JSON);

        // 3. Construim request-ul POST
        // IMPORTANT pentru Sava: Daca ruleaza aplicatia pe emulatorul Android local, 
        // IP-ul trebuie sa fie 10.0.2.2 in loc de 127.0.0.1 sau localhost.
        Request request = new Request.Builder()
                .url("http://10.0.2.2:5000/api/searchToFilters/")
                .header("Content-Type", "application/json")
                .post(body)
                .build();

        // 4. Executam request-ul asincron (pe fundal)
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                System.out.println("Eroare la conectare: " + e.getMessage());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful() && response.body() != null) {
                    // Preluam raspunsul brut de la server
                    String rawData = response.body().string();

                    try {
                        // Parsam JSON-ul primit pentru a extrage filtrele
                        JSONObject jsonResponse = new JSONObject(rawData);
                        JSONArray filtreArray = jsonResponse.getJSONArray("filtre_id");

                        System.out.println("ID-urile filtrelor primite sunt:");
                        for (int i = 0; i < filtreArray.length(); i++) {
                            int filtruId = filtreArray.getInt(i);
                            System.out.println(filtruId);
                        }
                        
                        // Aici se scrie logica de update a interfetei grafice cu rezultatele

                    } catch (Exception e) {
                        System.out.println("Eroare la parsarea datelor: " + e.getMessage());
                    }
                } else {
                    System.out.println("Eroare server (posibil 400 sau 500): " + response.code());
                }
            }
        });
    }
}