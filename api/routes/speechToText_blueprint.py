# This blueprint manages the speech-to-text API routing and HTTP responses.
# 
# Core features:
#   - Exposes a POST endpoint at `/speechToText/` to trigger the voice recording.
#   - Handles incoming requests and sends back clear JSON responses in case of success or error.
# Components:
#   - getRecording(): Captures audio from the microphone at 44.1 kHz, generates a unique 
#                     temporary .wav file using UUIDs to prevent conflicts, and saves the data.
#   - speechToText(): Manages the lifecycle of the recording and transcription process. 
#                     It sends the temporary file to Groq's Whisper API and cleans up the 
#                     file in a `finally` block to ensure no disk space is wasted.
import requests
import uuid
import sounddevice as sd
import os
from flask import Blueprint, request, jsonify
from scipy.io.wavfile import write
from groq import Groq
speech_blueprint=Blueprint("speechToText", __name__, url_prefix="/speechToText")

# Records audio from the microphone and saves it into a temporary .wav file.    
#     :param sec: Recording duration in seconds (default is 5).
#     :return: The path to the temporary .wav file.
def getRecording(sec=5):
    fs = 44100
    file_temp=f"voice_{uuid.uuid4().hex}.wav"
    print(f"\n[LISTENING] I am listening for {sec} seconds...")
    audio_data = sd.rec(int(sec * fs), samplerate=fs, channels=1)
    sd.wait()
    write(file_temp, fs, audio_data)
    print("[INFO] Audio saved")
    return file_temp

api=Groq(api_key=os.environ.get('groq_key'))
# Handles the complete process of recording, sending to Groq API, and returning the transcription.  
#     :param sec: Recording duration in seconds.
#     :return: The transcribed text.
#     :raises e: Propagates any error to the endpoint.
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
def speech_post():
    try:
        audio=getRecording(10)
        speech_recognized=speechToText(audio)
        return jsonify({"status": "success", "transcription": speech_recognized}), 200
    except Exception as e:
        return jsonify({"status": "error", "transcription": ''}), 500

    