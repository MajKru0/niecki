import os
from dotenv import load_dotenv

load_dotenv()  # wczytuje .env z katalogu projektu

class Config:
    DB_PASS = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT= os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_TYPE = os.getenv("DB_TYPE")
    DB_USERNAME = os.getenv("DB_USER")
    FRONTEND_URL = os.getenv("FRONTEND_HOST", "http://127.0.0.1:5500")
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173").split(",")
    DEBUG = os.getenv("FLASK_ENV") == "development"