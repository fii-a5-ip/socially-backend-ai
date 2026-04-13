import os
import sys
import json
import httpx
import orjson
import asyncio
import itertools
from dotenv import load_dotenv

load_dotenv()

async def main():
    # 1. CITIREA PROMPTULUI EXTERN
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as file:
            mesaj_sistem = file.read()
    except FileNotFoundError:
        print("Error: file prompt.txt not found")
        sys.exit(1)

    # 2. ROTIREA CHEILOR
    # Preluăm doar cheile care sunt efectiv setate (evităm 'None' în listă)
    chei_brute = [
        os.environ.get("GROQ_API_KEY_1"),
        # os.environ.get("GROQ_API_KEY_2"),
    ]
    CHEI_GROQ = [cheie for cheie in chei_brute if cheie]

    if not CHEI_GROQ:
        print("Eroare: Nu a fost găsită nicio cheie API validă!")
        sys.exit(1)

    pool_chei = itertools.cycle(CHEI_GROQ)
    URL = "https://api.groq.com/openai/v1/chat/completions"

    print("------------------ ChatBot -------------------")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 4. BUCLA DE INTERACȚIUNE
        while True:
            user_input = input("Tu: ")
            if user_input.lower() in ['exit', 'quit']:
                break

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
            succes = False
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

                        print(f"\nFrontend UI: {json_ai.get('raspuns_pentru_user')}")

                        print("\n[Output Database Core]:")
                        print(json.dumps(json_ai, indent=4, ensure_ascii=False))
                        print("-" * 50 + "\n")

                        succes = True
                        break

                    elif response.status_code == 429:
                        timp_asteptare = delay_baza * (2 ** incercare)
                        print(f"  [Limită atinsă] Aștept {timp_asteptare}s și rotesc cheia...")
                        await asyncio.sleep(timp_asteptare)
                    else:
                        print(f"\nEroare API: {response.status_code} - {response.text}")
                        break

                except httpx.RequestError as e:
                    print(f"\nConexiune eșuată: {e}. Reîncerc automat...")
                    await asyncio.sleep(2)

            if not succes:
                print("\nCapacitatea maximă a fost depășită pe toate cheile. Încearcă din nou peste puțin timp.")


if __name__ == "__main__":
    asyncio.run(main())

# in natura unde pot sta pe o patura ma pot juca niste boardgames cu prietenii mei ,sa am si toaleta prin apropriere
# vreau undeva sa pot bea o bere sa arunc o bila de bowling si sa ma uit la un meci in acelasi timp
# Vreau un loc unde pot ieși cu prietenii, să bem cocktailuri bune, să avem și muzică live sau DJ, dar să nu fie exagerat de aglomerat și să putem sta la masă.

