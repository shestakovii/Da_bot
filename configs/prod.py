import os
from configs.base import BaseConfig

class ProdConfig(BaseConfig):
    def __init__(self):
        self.DEBUG = False
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")

        self.DB_HOST = os.getenv("DB_HOST")
        self.DB_PORT = os.getenv("DB_PORT", "5432")
        self.DB_NAME = os.getenv("DB_NAME")
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASS = os.getenv("DB_PASS")
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
        self.API_Weather = os.getenv("API_Weather")
        self.HF_TOKEN = os.getenv("HF_TOKEN")