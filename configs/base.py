import os
from dataclasses import dataclass

@dataclass
class BaseConfig:
    """Базовые настройки для всех окружений"""
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    DEBUG: bool = False
    DB_POOL_SIZE: int = 5
    REQUEST_TIMEOUT: int = 30

    # Эти поля будут переопределены в dev/prod
    DB_HOST: str = ""
    DB_PORT: str = ""
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASS: str = ""
    BOT_TOKEN: str = ""
    OPENAI_TOKEN: str = ""
    HF_TOKEN: str = ""

    @property
    def DB_PATH(self):
        return {
            "host": self.DB_HOST,
            "port": int(self.DB_PORT),
            "database": self.DB_NAME,
            "user": self.DB_USER,
            "password": self.DB_PASS,
        }