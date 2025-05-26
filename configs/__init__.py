import os
from dotenv import load_dotenv
from .dev import DevConfig
from .prod import ProdConfig


def get_config():
    # Определяем окружение
    env = os.getenv("ENV", "dev")  # default to 'dev'

    # Загружаем соответствующий .env файл
    if env == "prod":
        load_dotenv(".env.prod")
        return ProdConfig()
    else:
        load_dotenv(".env.dev")
        return DevConfig()


config = get_config()