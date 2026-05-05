import os
import httpx
import orjson
import asyncio
import itertools
from dotenv import load_dotenv

from api.services.db_service import extrage_filtre_din_db

load_dotenv()


async def get_ai_filters(mesaj_sistem: str, user_input: str) -> dict:

    # 1. CITIM FILTRELE DIN BAZA DE DATE ȘI LE ADĂUGĂM LA PROMPT
    filtre_sql = extrage_filtre_din_db()
    mesaj_sistem_complet = f"{mesaj_sistem}\n\nFILTRE DISPONIBILE DIN BAZA DE DATE (ID: Nume):\n{filtre_sql}"

    # 2. ROTIREA CHEILOR
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
        mesaje_request_curent = [
            {"role": "system", "content": mesaj_sistem_complet},
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

                    # Returnăm dicționarul curat către API
                    return json_ai

                elif response.status_code == 429:
                    timp_asteptare = delay_baza * (2 ** incercare)
                    await asyncio.sleep(timp_asteptare)
                else:
                    return {"error": f"Eroare API: {response.status_code} - {response.text}"}

            except httpx.RequestError as e:
                # Conexiune eșuată, așteptăm înainte de retry
                await asyncio.sleep(2)

        return {"error": "Capacitatea maximă a fost depășită pe toate cheile. Încearcă din nou peste puțin timp."}