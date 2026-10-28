import os
from dotenv import load_dotenv

load_dotenv()  # wczytuje .env z katalogu projektu

class Config:
    DB_PASS = os.getenv["DB_PASS"]
    DB_HOST = os.getenv["DB_HOST"]
    DB_NAME = os.getenv["DB_NAME"]
    DB_TYPE = os.getenv["DB_TYPE"]
    FRONTEND_URL = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    DEBUG = os.getenv("FLASK_ENV") == "development"