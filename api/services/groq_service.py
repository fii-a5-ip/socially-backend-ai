import os
import httpx
import orjson
import asyncio
import itertools
from dotenv import load_dotenv

load_dotenv()

async def get_ai_filters(mesaj_sistem: str, user_input: str) -> dict:
    """
    Preia input-ul utilizatorului, comunică cu Groq API, folosind setările din main.py și returnează un dicționar JSON.
    """

    # ROTIREA CHEILOR
    chei_brute = [
        os.environ.get("GROQ_API_KEY_1"),
        # os.environ.get("GROQ_API_KEY_2"),
    ]
    CHEI_GROQ = [cheie for cheie in chei_brute if cheie]

    if not CHEI_GROQ:
        return {"error": "Eroare: Nu a fost găsită nicio cheie API validă!"}

    pool_chei = itertools.cycle(CHEI_GROQ)
    URL = "https://api.groq.com/openai/v1/chat/completions"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # execut o singura cerere REQUEST
        mesaje_request_curent = [
            {"role": "system", "content": mesaj_sistem},
            {"role": "user", "content": user_input}
        ]

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": mesaje_request_curent,
            "temperature": 0.0,
            "top_p": 0.1,
            "response_format": {"type": "json_object"}
        }

        MAX_RETRIES = 5
        delay_baza = 1

        for incercare in range(MAX_RETRIES):
            api_key_curenta = next(pool_chei)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key_curenta}"
            }

            try:
                response = await client.post(URL, headers=headers, json=payload)

                if response.status_code == 200:
                    data = orjson.loads(response.content)
                    ai_reply_string = data.get('choices')[0].get('message').get('content')
                    json_ai = orjson.loads(ai_reply_string)

                    # În loc să dăm print, returnăm dicționarul curat către API
                    return json_ai

                elif response.status_code == 429:
                    timp_asteptare = delay_baza * (2 ** incercare)
                    await asyncio.sleep(timp_asteptare)
                else:
                    return {"error": f"Eroare API: {response.status_code} - {response.text}"}

            except httpx.RequestError as e:
                # Conexiune eșuată, așteptăm înainte de retry
                await asyncio.sleep(2)

        # Dacă se epuizează toate încercările:
        return {"error": "Capacitatea maximă a fost depășită pe toate cheile. Încearcă din nou peste puțin timp."}