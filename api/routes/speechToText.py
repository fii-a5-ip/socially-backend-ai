# This blueprint manages the speech-to-text API routing and HTTP responses.
# 
# Core features:
#   - Exposes a POST endpoint at `/speechToText/` to receive an audio file.
#   - Handles multipart/form-data requests and returns JSON responses with transcriptions.
# Components:
#   - speechToText(): Manages the interaction with Groq's Whisper API.
#                     It opens the saved temporary file, sends it for transcription, 
#                     and ensures the file is deleted in a `finally` block to prevent disk bloat.
import uuid
import os
from flask import Blueprint, request, jsonify
from groq import Groq
speech_blueprint=Blueprint("speechToText", __name__, url_prefix="/speechToText")

api=Groq(api_key=os.environ.get('GROQ_API_KEY_1'))
# Sends the audio file to Groq Whisper API and ensures file cleanup.
#     :param audio: Path to the temporary audio file.
#     :return: Transcribed text.
def speechToText(audio):
    try:
        with open(audio, "rb") as audio_file:
            response=api.audio.transcriptions.create(file=audio_file, model="whisper-large-v3")
        return response.text
    except Exception as e:
        raise e
    finally:
        if audio and os.path.exists(audio):
            os.remove(audio)

@speech_blueprint.route("/", methods=["POST"])
# Endpoint to handle audio file uploads and trigger transcription.
#     Expects a file attached to the 'file' key in a multipart/form-data request.
def speech_post():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"status": "error", "transcription": ''}), 400
    audio=request.files['file']
    # Check if the user actually selected a file
    if audio.filename == '':
        return jsonify({"status": "error", "transcription": ''}), 400
    try:
        audio_filename=f"upload_{uuid.uuid4().hex}.mp3"
        audio.save(audio_filename)
        speech_recognized=speechToText(audio_filename)
        return jsonify({"status": "success", "transcription": speech_recognized}), 200
    except Exception as e:
        return jsonify({"status": "error", "transcription": ''}), 500

    