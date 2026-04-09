import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")