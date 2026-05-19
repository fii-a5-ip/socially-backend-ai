import unittest
from unittest.mock import patch, MagicMock
import io
from flask import Flask
from api.routes.speech_to_text import speech_blueprint

class TestSpeechToTextBlueprint(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__) #NOSONAR
        self.app.register_blueprint(speech_blueprint)
        self.client = self.app.test_client()

    @patch('api.routes.speech_to_text.Groq')
    @patch('api.routes.speech_to_text.os.remove')
    @patch('api.routes.speech_to_text.os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_speech_post_happy_flow(self, mock_file, mock_exists, mock_remove, mock_groq_class):
        # Test successful audio upload and transcription.
        # Create a mock instance for the Groq client
        mock_api_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Hello, this is a simulated transcription test."
        
        # Chain the mocks to match: api.audio.transcriptions.create
        mock_api_instance.audio.transcriptions.create.return_value = mock_response
        # Make the Groq class constructor return our mock instance
        mock_groq_class.return_value = mock_api_instance

        # Prepare dummy file data
        data = {
            'file': (io.BytesIO(b"dummy audio content"), 'test_voice.mp3')
        }

        response = self.client.post('/speechToText/', data=data, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        output = response.get_json()
        self.assertEqual(output["status"], "success")
        self.assertEqual(output["transcription"], "Hello, this is a simulated transcription test.")
        
        # Verify that the file cleanup logic was triggered
        mock_remove.assert_called_once()

    def test_speech_post_missing_file_key(self):
        # Test error handling when the 'file' key is completely missing.
        response = self.client.post('/speechToText/', data={}, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        output = response.get_json()
        self.assertEqual(output["status"], "error")
        self.assertEqual(output["transcription"], '')

    def test_speech_post_empty_filename(self):
        # Test error handling when a file is submitted but has no name.
        data = {
            'file': (io.BytesIO(b""), '')
        }
        
        response = self.client.post('/speechToText/', data=data, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        output = response.get_json()
        self.assertEqual(output["status"], "error")

    @patch('api.routes.speech_to_text.Groq')
    @patch('api.routes.speech_to_text.os.remove')
    @patch('api.routes.speech_to_text.os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_speech_post_groq_api_exception(self, mock_file, mock_exists, mock_remove, mock_groq_class):
        # Test system resilience when Groq API raises an internal exception.
        mock_api_instance = MagicMock()
        # Simulate Groq API crashing during the call
        mock_api_instance.audio.transcriptions.create.side_effect = Exception("Groq API Error")
        mock_groq_class.return_value = mock_api_instance

        data = {
            'file': (io.BytesIO(b"dummy data"), 'test_voice.mp3')
        }

        response = self.client.post('/speechToText/', data=data, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 500)
        output = response.get_json()
        self.assertEqual(output["status"], "error")
        self.assertEqual(output["transcription"], '')
        
        # Ensure cleanup runs even if the API throws an exception
        mock_remove.assert_called_once()

if __name__ == '__main__':
    unittest.main()