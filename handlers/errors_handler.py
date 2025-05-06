import logging
import time
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


# Обработчик сетевых ошибок (добавить в каждый хендлер)

def handle_network_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RequestException as e:
            logger.error(f"Network error in {func.__name__}: {e}")
            # Можно добавить повторную попытку
            time.sleep(1)
            return wrapper(*args, **kwargs)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise
    return wrapper