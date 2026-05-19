import os
from dotenv import load_dotenv
load_dotenv()

import pytest
from unittest.mock import patch, mock_open, AsyncMock
from flask import Flask

from api.routes.searchToFilters import search_bp


@pytest.fixture
def client():
    """
    Configurează un test client de Flask pentru a simula request-uri HTTP.
    """
    app = Flask(__name__)
    app.config['TESTING'] = True

    # Înregistrăm blueprint-ul (el are deja url_prefix='/searchToFilters' intern,
    # așa că rutele vor fi accesibile la /searchToFilters/)
    app.register_blueprint(search_bp)

    with app.test_client() as client:
        yield client


# -----------------------------------------------------------------------------
# TESTE
# -----------------------------------------------------------------------------

@patch('api.routes.searchToFilters.extrage_filtre_din_db')
@patch('api.routes.searchToFilters.get_ai_filters', new_callable=AsyncMock)
@patch('builtins.open', new_callable=mock_open, read_data="Context sistem: {FILTERS_PLACEHOLDER}")
def test_search_to_filters_happy_flow(mock_file, mock_get_ai_filters, mock_extrage_filtre, client):
    """
    Scenariul 1: Happy flow.
    Verifică dacă un prompt valid procesează corect datele, înlocuiește placeholder-ul
    și returnează un JSON corect (HTTP 200).
    """
    # 1. Configurăm Mock-urile
    mock_extrage_filtre.return_value = "- filter1\n- filter2"
    mock_get_ai_filters.return_value = {"filtru_detectat": "filter1"}

    # 2. Executăm request-ul
    payload = {"prompt": "Caut o locatie cu filter1"}
    response = client.post('/searchToFilters/', json=payload)

    # 3. Verificăm rezultatul
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"filtru_detectat": "filter1"}

    # 4. Verificăm comportamentul intern (că AI-ul a primit string-ul corect înlocuit)
    mesaj_sistem_asteptat = "Context sistem: - filter1\n- filter2"
    mock_get_ai_filters.assert_called_once_with(mesaj_sistem_asteptat, "Caut o locatie cu filter1")
    mock_extrage_filtre.assert_called_once()
    mock_file.assert_called_once()


def test_search_to_filters_missing_prompt(client):
    """
    Scenariul 2: Input Validation (fără prompt).
    Verifică dacă un payload greșit returnează HTTP 400 Bad Request.
    """
    response = client.post('/searchToFilters/', json={"alta_cheie": "valoare"})

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "prompt" in data["error"]


def test_search_to_filters_empty_body(client):
    """
    Scenariul 3: Input Validation (payload complet gol).
    Verifică gestiunea unui request fără body JSON.
    """
    response = client.post('/searchToFilters/', json={})

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


@patch('api.routes.searchToFilters.extrage_filtre_din_db')
@patch('api.routes.searchToFilters.get_ai_filters', new_callable=AsyncMock)
@patch('builtins.open', new_callable=mock_open, read_data="Context: {FILTERS_PLACEHOLDER}")
def test_search_to_filters_ai_error(mock_file, mock_get_ai_filters, mock_extrage_filtre, client):
    """
    Scenariul 4: AI Service Error.
    Verifică dacă o eroare preluată de la AI (ex. model indisponibil)
    este pasată mai departe ca HTTP 502 Bad Gateway.
    """
    mock_extrage_filtre.return_value = "filtre_mock"
    # Simulăm o eroare returnată de serviciul AI
    mock_get_ai_filters.return_value = {"error": "Rate limit exceeded pe modelul Groq"}

    response = client.post('/searchToFilters/', json={"prompt": "Ceva..."})

    assert response.status_code == 502
    data = response.get_json()
    assert data["error"] == "Rate limit exceeded pe modelul Groq"


@patch('api.routes.searchToFilters.extrage_filtre_din_db')
@patch('builtins.open', new_callable=mock_open, read_data="Context")
def test_search_to_filters_internal_exception(mock_file, mock_extrage_filtre, client):
    """
    Scenariul 5: Internal Server Error.
    Simulează o crăpare neașteptată a codului (ex: pică conexiunea la baza de date)
    pentru a ne asigura că este prinsă în blocul try-except și returnează 500.
    """
    # Forțăm funcția de DB să arunce o eroare fatală
    mock_extrage_filtre.side_effect = Exception("Conexiunea la DB a picat")

    response = client.post('/searchToFilters/', json={"prompt": "Vreau eroare"})

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert "A apărut o eroare internă" in data["error"]
    assert "Conexiunea la DB a picat" in data["error"]