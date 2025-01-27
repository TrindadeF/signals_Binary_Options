import os

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    IQ_EMAIL = os.getenv("IQ_EMAIL")
    IQ_PASSWORD = os.getenv("IQ_PASSWORD")
    API_ID_TELEGRAM = os.getenv("API_ID_TELEGRAM")
    API_HASH_TELEGRAM = os.getenv("API_HASH_TELEGRAM")