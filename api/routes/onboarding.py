import json
import os
from flask import Blueprint, request, jsonify
from api.services.groq_service import get_ai_filters
import asyncio

onboarding_bp = Blueprint('onboardingProcess', __name__, url_prefix='/onboardingProcess')

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, '..', 'resources', 'onboarding_questions.json')
PROMPT_PATH = os.path.join(BASE_DIR, '..', 'resources', 'onboarding_prompt.txt')
FILTERS_PATH = os.path.join(BASE_DIR, '..', 'resources', 'filters.txt')

# Încărcăm dicționarul de întrebări o singură dată la pornire
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    ONBOARDING_DATA = json.load(f)

@onboarding_bp.route('/', methods=['POST'])
def process_step():
    data = request.json
    step = data.get('step')

    # --- LOGICA PENTRU PASUL 0 (INIȚIALIZARE) ---
    if step == 0:
        user_info = data.get('user_info', {})
        varsta = int(user_info.get('varsta', 0))
        ocupatie = user_info.get('ocupatie', '').lower()
        is_remote = user_info.get('is_remote', False)
        oras = user_info.get('oras', 'orașul tău')

        ROUTING_CONDITIONS = [
            {"id": "L1-AA", "check": lambda v, o, r: 18 <= v <= 25 and o == 'student'},
            {"id": "L1-AD", "check": lambda v, o, r: 18 <= v <= 25 and r is True},
            {"id": "L1-AF", "check": lambda v, o, r: 18 <= v <= 25 and o == 'angajat'},
            {"id": "L1-AE", "check": lambda v, o, r: 26 <= v <= 35 and r is True},
            {"id": "L1-AB", "check": lambda v, o, r: 26 <= v <= 35 and o == 'angajat'},
            {"id": "L1-AG", "check": lambda v, o, r: v > 35 and (r is True or o == 'antreprenor')},
            {"id": "L1-AC", "check": lambda v, o, r: v > 35}
        ]

        selected_id = "L1-H"
        for condition in ROUTING_CONDITIONS:
            if condition["check"](varsta, ocupatie, is_remote):
                selected_id = condition["id"]
                break

        question_text = ONBOARDING_DATA['questions'].get(selected_id, ONBOARDING_DATA['questions']['L1-H'])
        final_text = question_text.replace("[Oraș]", oras)

        return jsonify({
            "status": "start",
            "next_step": 1,
            "current_question_id": selected_id,
            "question_text": final_text,
            "user_info": user_info
        }), 200

    # --- LOGICA PENTRU PAȘII 1, 2, 3 (CONVERSAȚIE AI) ---
    conversation_history = data.get('conversation_history', [])

    if not conversation_history or not isinstance(conversation_history, list):
        return jsonify({"error": "Lipsește istoricul conversației."}), 400

    # Validăm lungimea ultimului răspuns (minim 30 caractere)
    last_answer = conversation_history[-1].get('a', '')
    if len(last_answer.strip()) < 30:
        return jsonify({"error": "Te rog oferă un răspuns mai detaliat (minim 30 caractere)."}), 400

    # Construim istoricul textual pentru prompt
    history_text = ""
    for i, entry in enumerate(conversation_history):
        history_text += f"--- PASUL {i + 1} ---\n"
        history_text += f"Întrebare AI: {entry.get('q', '')}\n"
        history_text += f"Răspuns User: {entry.get('a', '')}\n\n"

    # Citim resursele externe (Prompt și Filtre)
    with open(PROMPT_PATH, 'r', encoding='utf-8') as file:
        prompt_template = file.read()
    with open(FILTERS_PATH, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        lista_filtre_profil = "\n".join([f"{i+1} - {name}" for i, name in enumerate(lines)])

    # Determinăm opțiunile de rutare pentru pasul curent
    available_next_questions = ONBOARDING_DATA['routing'].get(str(step), "L3-UNIVERSAL-LOGISTICS")

    # Injectăm datele în prompt
    mesaj_sistem = prompt_template.replace("{conversation_history_text}", history_text) \
                                  .replace("{current_filters_list}", lista_filtre_profil) \
                                  .replace("{available_next_questions}", available_next_questions)

    # Apelăm Groq
    groq_response = asyncio.run(get_ai_filters(mesaj_sistem=mesaj_sistem, user_input="Analizează contextul și returnează JSON-ul."))

    if "error" in groq_response:
        return jsonify({"error": groq_response["error"]}), 500

    # Filtrele recalculate de AI din toată conversația
    recalculated_filters = groq_response.get("extracted_filters", [])

    if step < 3:
        next_id = groq_response.get("next_question_id", "L2-UNIVERSAL-FALLBACK")
        next_text = ONBOARDING_DATA['questions'].get(next_id, "Hai să continuăm. Ce altceva preferi?")

        return jsonify({
            "status": "continue",
            "next_step": step + 1,
            "next_question_id": next_id,
            "next_question_text": next_text,
            "current_filters": recalculated_filters
        }), 200
    else:
        # Final de drum (Pasul 3)
        return jsonify({
            "status": "complete",
            "message": "Profil configurat cu succes!",
            "final_filters": recalculated_filters
        }), 200