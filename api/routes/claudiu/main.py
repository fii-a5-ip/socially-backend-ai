import os

import requests
import json
import time
import itertools
import sys,os
from dotenv import load_dotenv
load_dotenv()

# 1. CITIREA PROMPTULUI EXTERN

try:
    with open('prompt.txt', 'r', encoding='utf-8') as file:
        mesaj_sistem = file.read()
except FileNotFoundError:
    print("Eroare: Fișierul 'prompt_sistem.txt' nu a fost găsit în acest folder.")
    sys.exit(1)


# 2. ROTIREA A 5 CHEI cu round robin

CHEI_GROQ = [
    os.environ.get("GROQ_API_KEY_1"),
    #"gsk_cheia_2",
    #"gsk_cheia_3",
    #"gsk_cheia_4",
    #"gsk_cheia_5"
]

pool_chei = itertools.cycle(CHEI_GROQ)
URL="https://api.groq.com/openai/v1/chat/completions"

print("------------------ ChatBot -------------------")

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

    MAX_RETRIES=5
    succes=False
    delay_baza=1

    for incercare in range(MAX_RETRIES):
        api_key_curenta = next(pool_chei)

        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key_curenta}"
        }

        try:
            response = requests.post(URL, headers=headers, json=payload, timeout=15)

            if response.status_code == 200:
                data = response.json()
                ai_reply_string = data['choices'][0]['message']['content']
                json_ai = json.loads(ai_reply_string)

                print(f"\nFrontend UI: {json_ai.get('raspuns_pentru_user')}")

                print("\n[Output Database Core]:")
                print(json.dumps(json_ai, indent=4, ensure_ascii=False))
                print("-" * 50 + "\n")

                succes = True
                break

            elif response.status_code==429:
                timp_asteptare=delay_baza * (2 ** incercare)
                print(f"  [Limită atinsă] Aștept {timp_asteptare}s și rotesc cheia...")
                time.sleep(timp_asteptare)
            else:
                print(f"\nEroare API: {response.status_code} - {response.text}")
                break

        except requests.exceptions.RequestException as e:
            print(f"\nConexiune eșuată: {e}. Reîncerc automat...")
            time.sleep(2)

    if not succes:
        print("\nCapacitatea maximă a fost depășită pe toate cele 5 chei. Încearcă din nou peste 1 minut.")



# in natura unde pot sta pe o patura ma pot juca niste boardgames cu prietenii mei ,sa am si toaleta prin apropriere
# vreau undeva sa pot bea o bere sa arunc o bila de bowling si sa ma uit la un meci in acelasi timp
# Vreau un loc unde pot ieși cu prietenii, să bem cocktailuri bune, să avem și muzică live sau DJ, dar să nu fie exagerat de aglomerat și să putem sta la masă.

