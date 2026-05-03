from flask import Blueprint, request, jsonify
import asyncio
from pathlib import Path

# Importăm funcția de AI pe care tocmai am creat-o
from api.services.groq_service import prompt_ai

# Creăm Blueprint-ul
search_bp = Blueprint('searchToFilters', __name__, url_prefix='/searchToFilters')

@search_bp.route('/', methods=['POST'])
def search_to_filters():
    # 1. Prelucrăm datele primite de la frontend (așteptăm un JSON cu cheia "prompt")
    body = request.get_json()

    if not body or 'prompt' not in body:
        return jsonify({"error": "Te rog trimite un camp 'prompt' valid în format JSON."}), 400

    user_prompt = body['prompt']

    # 2. Apelăm serviciul nostru de AI
    try:

        # CITIREA PROMPTULUI EXTERN
        script_dir = Path(__file__).parent.parent
        file_path = script_dir / 'resources' / 'textToFilters_prompt.txt'
        with open(file_path, 'r', encoding='utf-8') as file:
            mesaj_sistem = file.read()

        # Deoarece funcția get_ai_filters este asincronă (async), 
        # folosim asyncio.run() pentru a o apela din acest mediu sincron de Flask
        rezultat_ai = asyncio.run(prompt_ai(mesaj_sistem, user_prompt))
        
        # 3. Verificăm dacă serviciul a returnat o eroare controlată
        if "error" in rezultat_ai:
            return jsonify(rezultat_ai), 502

        # 4. Dacă totul e ok, returnăm filtrele extrase!
        return jsonify(rezultat_ai), 200

    except Exception as e:
        # Prindem orice eroare neașteptată ca să nu pice serverul
        return jsonify({"error": f"A apărut o eroare internă: {str(e)}"}), 500