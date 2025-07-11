import telebot
import os
import time
import logging
from logging.handlers import RotatingFileHandler
import threading
import traceback
from telebot import types
from config import BOT_TOKEN
from config import ADMIN_CHAT_ID
from telebot import apihelper
from telebot.apihelper import ApiTelegramException
from urllib3.exceptions import ProtocolError, ReadTimeoutError
from handlers.start_handler import setup_start_handler
from handlers.weather_handler import setup_weather_handler
from handlers.afisha_handler import setup_afisha_handler
from handlers.ai_tools_handler import setup_ai_tools_handler
# from handlers.image_gen_handler import setup_image_gen_handler
from handlers.parser_handler import setup_parser_handler
from handlers.preference_handler import setup_preference_handler
from handlers.set_city_handler import setup_set_city_handler
from handlers.set_city_handler import setup_apply_city_selection_handler
from handlers.filters_handler import setup_filter_handler, setup_filter_category_selection_handler, setup_filter_tag_selection_handler, setup_filter_next_to_price_handler, setup_filter_price_selection_handler, setup_filter_apply_filters_handler, setup_filter_all_tags_selection_handler
from handlers.show_events_handler import show_next_events_handler
from handlers.errors_handler import handle_network_errors

# # Настройка логирования
# logging.basicConfig(
#     level=getattr(logging, config.LOG_LEVEL),
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     handlers=[
#         logging.FileHandler("bot_debug.log"),  # Логи в файл
#         logging.StreamHandler()               # Логи в консоль
#     ]
# )

# === Настройка логирования ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Отключаем "всплытие" логов, чтобы избежать дублирования
logger.propagate = False

# === Логирование в файл с ротацией ===
log_file = os.path.join(os.path.dirname(__file__), 'bot.log')

# Проверяем, нет ли уже добавленных обработчиков
if not logger.handlers:
    handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=2)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # === Консольное логирование (опционально) ===
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# Настройки соединения
apihelper.ENABLE_MIDDLEWARE = True  # Включаем middleware
apihelper.SESSION_TIME_TO_LIVE = 5 * 60  # 5 минут
apihelper.READ_TIMEOUT = 30
apihelper.CONNECT_TIMEOUT = 15

# Колбэк для автоматического переподключения
def retry_after_failure(exception):
    logger.warning(f"Connection error: {exception}")
    time.sleep(5)
    return True

bot = telebot.TeleBot(BOT_TOKEN, exception_handler=retry_after_failure)


# Сохраняем оригинальный метод
original_make_request = apihelper._make_request

def safe_make_request(*args, **kwargs):
    """Безопасный wrapper для запросов с обработкой ошибок"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return original_make_request(*args, **kwargs)
        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_after = e.result.get('parameters', {}).get('retry_after', 5)
                logger.warning(f"Rate limited. Waiting {retry_after}s (attempt {attempt+1}/{max_retries})")
                time.sleep(retry_after)
                continue
            logger.error(f"Telegram API error: {e}")
            break
        except Exception as e:
            logger.error(f"Request failed: {e}")
            time.sleep(2 ** attempt)  # Экспоненциальная задержка
            continue
    return None

# Патчим метод
apihelper._make_request = safe_make_request

# # Включаем режим отладки
# apihelper.DEBUG = True


# === Глобальная обработка необработанных исключений ===
def handle_uncaught_exception(bot, update, exception):
    logger.error(f"Необработанное исключение: {exception}", exc_info=True)
    logger.error(traceback.format_exc())

    if update and hasattr(update, "message") and update.message:
        try:
            bot.reply_to(update.message, "Произошла внутренняя ошибка. Попробуйте ещё раз.")
        except Exception as reply_error:
            logger.error(f"Ошибка при ответе пользователю: {reply_error}")

def wrap_with_error_handler(func, handler):
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handler(*args, exception=e)
    return wrapped

# === Лимит на количество перезапусков ===
MAX_RESTARTS = 15
RESTART_WINDOW = 60 * 5  # 5 минут
restarts = []

def should_restart():
    now = time.time()
    global restarts
    restarts = [t for t in restarts if t > now - RESTART_WINDOW]
    restarts.append(now)
    return len(restarts) < MAX_RESTARTS

# Локальное хранилище для chat_id текущего пользователя
thread_local = threading.local()

# Middleware для сохранения chat_id
@bot.middleware_handler(update_types=["message"])
@handle_network_errors
def save_chat_id(bot_instance, message):
    try:
        thread_local.chat_id = message.chat.id
        logger.info(f"Chat ID сохранен: {message.chat.id}")
    except Exception as e:
        logger.error(f"Ошибка в middleware: {e}")
        
# Регистрация обработчиков
def setup_handlers():    
    setup_start_handler(bot)
    setup_weather_handler(bot)
    setup_ai_tools_handler(bot)
    # setup_image_gen_handler(bot)
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


def send_admin_alert(message):
    """Шлёт алерт админу в Telegram"""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID не задан — не могу отправить алерт")
        return
    
    try:
        bot.send_message(ADMIN_CHAT_ID, message)
        logger.info(f"Алерт администратору отправлен: {message}")
    except Exception as e:
        logger.error(f"Не удалось отправить алерт админу: {e}")


def run_bot():
    while True:
        try:
            logger.info("Starting bot...")
            setup_handlers()
            bot.infinity_polling(none_stop=True, interval=2, timeout=5)
        except Exception as e:
            logger.error(f"Critical error: {e}")
            logger.critical(f"CRASH: {str(e)}", exc_info=True)
            logger.info("Restarting in 5 seconds...")

            chat_id = getattr(thread_local, "chat_id", None)
            if chat_id:
                try:
                    bot.send_message(chat_id, "Дружище, подожди, не торопись, дай мне 5 секунд подумать")
                except Exception as send_error:
                    logger.error(f"Ошибка при отправке сообщения пользователю: {send_error}")

            time.sleep(5)

        if not should_restart():
            error_message = "❌ Бот остановлен: превышено количество перезапусков за последние 5 минут"
            logger.critical(error_message)
            send_admin_alert(error_message)
            break

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

