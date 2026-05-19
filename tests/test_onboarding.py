import unittest
from unittest.mock import patch, AsyncMock
from api.api import create_app

class TestOnboardingProcess(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.testing = True
        cls.client = cls.app.test_client()

    def setUp(self):
        self.client = self.__class__.client

    # ==========================================
    # SCENARIUL 1: Pasul 0 - Student
    # ==========================================
    def test_step0_logic_for_student(self):
        payload = {
            "step": 0,
            "user_info": {
                "nume": "Alex",
                "varsta": 20,
                "ocupatie": "student",
                "oras": "Iași",
                "is_remote": False
            }
        }

        response = self.client.post('/api/onboardingProcess/', json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'start')
        self.assertEqual(response.json['current_question_id'], 'L1-AA')

    # ==========================================
    # SCENARIUL 2: Pasul 0 - Angajat Remote
    # ==========================================
    def test_step_0_logic_for_remote_adult(self):
        payload = {
            "step": 0,
            "user_info": {
                "nume": "Elena",
                "varsta": 30,
                "ocupatie": "angajat",
                "oras": "Cluj",
                "is_remote": True
            }
        }

        response = self.client.post('/api/onboardingProcess/', json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['current_question_id'], 'L1-AE')

    # ==========================================
    # SCENARIUL 3: Happy Flow - Pasul 1 (MOCK AI)
    # ==========================================
    @patch('api.routes.onboarding.get_ai_filters', new_callable=AsyncMock)
    def test_step_1_ai_processing_success(self, mock_get_ai_filters):
        mock_get_ai_filters.return_value = {
            "analiza_logica": "Userul vrea liniște.",
            "extracted_filters": ["cafe", "free_wifi"],
            "next_question_id": "L2-C"
        }

        payload = {
            "step": 1,
            "conversation_history": [
                {"q": "Unde vrei sa mergi?", "a": "Vreau sa merg neaparat intr-o cafenea linistita unde am wifi."}
            ]
        }

        response = self.client.post('/api/onboardingProcess/', json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'continue')
        self.assertEqual(response.json['next_question_id'], 'L2-C')
        mock_get_ai_filters.assert_called_once()

    # ==========================================
    # SCENARIUL 4: Happy Flow - Pasul 3 (Finalizare)
    # ==========================================
    @patch('api.routes.onboarding.get_ai_filters', new_callable=AsyncMock)
    def test_step_3_completion_success(self, mock_get_ai_filters):
        mock_get_ai_filters.return_value = {
            "analiza_logica": "Gata profilul.",
            "extracted_filters": ["cafe", "free_wifi", "vegan_options", "parking_available"],
            "next_question_id": "NONE"
        }

        payload = {
            "step": 3,
            "conversation_history": [
                {"q": "Intrebare", "a": "Acesta este un raspuns suficient de lung pentru a trece de filtru."}
            ]
        }

        response = self.client.post('/api/onboardingProcess/', json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'complete')

    # ==========================================
    # SCENARIUL 5: Edge Case - Eroare AI
    # ==========================================
    @patch('api.routes.onboarding.get_ai_filters', new_callable=AsyncMock)
    def test_ai_api_failure(self, mock_get_ai_filters):
        mock_get_ai_filters.return_value = {"error": "Rate limit exceeded"}

        payload = {
            "step": 1,
            "conversation_history": [
                {"q": "Intrebare", "a": "Acesta este un raspuns suficient de lung pentru a trece de filtru."}
            ]
        }

        response = self.client.post('/api/onboardingProcess/', json=payload)

        self.assertEqual(response.status_code, 500)