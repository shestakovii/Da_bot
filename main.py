import telebot
import os
import time
import logging
import threading
from telebot import types
from config import BOT_TOKEN
from telebot import apihelper
from telebot.apihelper import ApiTelegramException
from urllib3.exceptions import ProtocolError, ReadTimeoutError, MaxRetryError
from requests.exceptions import RequestException

from handlers.start_handler import setup_start_handler
from handlers.weather_handler import setup_weather_handler
from handlers.afisha_handler import setup_afisha_handler
from handlers.ai_tools_handler import setup_ai_tools_handler
from handlers.image_gen_handler import setup_image_gen_handler
from handlers.parser_handler import setup_parser_handler
from handlers.preference_handler import setup_preference_handler
from handlers.set_city_handler import setup_set_city_handler
from handlers.set_city_handler import setup_apply_city_selection_handler
from handlers.filters_handler import setup_filter_handler, setup_filter_category_selection_handler, setup_filter_tag_selection_handler, setup_filter_next_to_price_handler, setup_filter_price_selection_handler, setup_filter_apply_filters_handler, setup_filter_all_tags_selection_handler
from handlers.show_events_handler import show_next_events_handler
from handlers.errors_handler import handle_network_errors

# Константы для управления повторами
MAX_RETRIES = 3
BASE_DELAY = 5
MAX_DELAY = 30  # 1 минута максимального ожидания

# Настройки соединения (оптимизированные)
apihelper.ENABLE_MIDDLEWARE = True
apihelper.SESSION_TIME_TO_LIVE = 5 * 60
apihelper.READ_TIMEOUT = 30
apihelper.CONNECT_TIMEOUT = 15
apihelper.MAX_RETRIES = 2


# Улучшенное логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
telebot.logger.setLevel(logging.WARNING)  # Уменьшаем логи telebot


# Локальное хранилище
thread_local = threading.local()
bot = telebot.TeleBot(BOT_TOKEN)

# Сохраняем оригинальный метод
original_make_request = apihelper._make_request

def patched_make_request(*args, **kwargs):
    """Модифицированный метод с обработкой ошибок"""
    for attempt in range(MAX_RETRIES):
        try:
            return original_make_request(*args, **kwargs)
        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_after = e.result.get('parameters', {}).get('retry_after', BASE_DELAY)
                logger.warning(f"Rate limited. Waiting {retry_after}s")
                time.sleep(retry_after)
                continue
            raise
        except (ConnectionError, ProtocolError, ReadTimeoutError) as e:
            logger.warning(f"Network error: {e}. Retry {attempt + 1}/{MAX_RETRIES}")
            time.sleep(BASE_DELAY * (attempt + 1))
            continue
    raise Exception(f"Failed after {MAX_RETRIES} attempts")

# Применяем патч
apihelper._make_request = patched_make_request

# Улучшенный middleware
@bot.middleware_handler(update_types=["message"])
def save_chat_id(bot_instance, message):
    try:
        thread_local.chat_id = message.chat.id
    except Exception as e:
        logger.error(f"Middleware error: {e}")

# Уведомление пользователя об ошибках
def notify_user(message):
    if hasattr(thread_local, 'chat_id'):
        try:
            bot.send_message(thread_local.chat_id, message)
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")


# Регистрация обработчиков (без изменений)
def setup_handlers():
    setup_start_handler(bot)
    setup_weather_handler(bot)
    setup_ai_tools_handler(bot)
    setup_image_gen_handler(bot)
    setup_parser_handler(bot)
    setup_set_city_handler(bot)
    setup_afisha_handler(bot)
    setup_filter_handler(bot)
    setup_apply_city_selection_handler(bot)
    setup_filter_category_selection_handler(bot)
    setup_filter_tag_selection_handler(bot)
    setup_filter_all_tags_selection_handler(bot)
    setup_filter_next_to_price_handler(bot)
    setup_filter_price_selection_handler(bot)
    setup_filter_apply_filters_handler(bot)
    show_next_events_handler(bot)
    setup_preference_handler(bot)

# Основной цикл бота
def run_bot():
    while True:
        try:
            logger.info("Starting bot...")
            bot.polling(
                non_stop=True,
                interval=2,
                timeout=10,
            )
        except Exception as e:
            logger.critical(f"Bot crashed: {e}", exc_info=True)
            notify_user("🔧 Произошла ошибка. Перезапускаюсь...")
            time.sleep(BASE_DELAY)

if __name__ == "__main__":
    # Настройка соединения
    apihelper.SESSION_TIME_TO_LIVE = 300
    apihelper.READ_TIMEOUT = 30
    apihelper.CONNECT_TIMEOUT = 15
    
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal startup error: {e}")