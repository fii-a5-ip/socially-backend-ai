from flask import Blueprint, request, jsonify
import asyncio
from pathlib import Path

# Importăm serviciile noastre
from api.services.groq_service import get_ai_filters
from api.services.db_service import extrage_filtre_din_db

# Creăm Blueprint-ul
search_bp = Blueprint('searchToFilters', __name__, url_prefix='/searchToFilters')


@search_bp.route('/', methods=['POST'])
def search_to_filters():
    # 1. Prelucrăm datele primite de la frontend
    body = request.get_json()

    if not body or 'prompt' not in body:
        return jsonify({"error": "Te rog trimite un camp 'prompt' valid în format JSON."}), 400

    user_prompt = body['prompt']

    try:
        # 2. CITIREA PROMPTULUI EXTERN
        script_dir = Path(__file__).parent.parent
        file_path = script_dir / 'resources' / 'textToFilters_prompt.txt'
        with open(file_path, 'r', encoding='utf-8') as file:
            mesaj_sistem = file.read()

        # 3. EXTRAGEM FILTRELE DIN BAZA DE DATE
        filtre_db_text = extrage_filtre_din_db()

        # 4. INSERĂM FILTRELE ÎN MESAJUL SISTEM
        # Înlocuim {FILTERS_PLACEHOLDER} cu lista din BD
        mesaj_sistem_complet = mesaj_sistem.replace("{FILTERS_PLACEHOLDER}", filtre_db_text)

        # 5. Apelăm AI-ul cu mesajul complet (care acum conține filtrele)
        rezultat_ai = asyncio.run(get_ai_filters(mesaj_sistem_complet, user_prompt))

        # === DEBUGGING: AFIȘĂM ÎN TERMINAL SĂ VEDEM CE SE ÎNTÂMPLĂ ===
        print("\n" + "=" * 40)
        print("1. Există {FILTERS_PLACEHOLDER} în txt?:", "{FILTERS_PLACEHOLDER}" in mesaj_sistem)
        print("2. Câte caractere au venit din baza de date?:", len(filtre_db_text))
        if len(filtre_db_text) > 0:
            print("3. Primele 3 filtre din DB arată așa:", filtre_db_text[:100], "...")
        else:
            print("EROARE CRITICĂ: Nu s-a extras nimic din baza de date!")
        print("=" * 40 + "\n")
        # ==============================================================

        if "error" in rezultat_ai:
            return jsonify(rezultat_ai), 502

        return jsonify(rezultat_ai), 200

    except Exception as e:
        return jsonify({"error": f"A apărut o eroare internă: {str(e)}"}), 500