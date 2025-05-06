from telebot import types
import logging
from db.operations.db_preferences import db_update_user_preference, db_hide_event_for_user
from db.operations.db_events import db_get_free_events
from handlers.show_events_handler import show_events
# from handlers.filters_handler import apply_filters_handler  # Импортируем обработчик фильтров
from db.operations.db_events import db_get_events  # Импортируем функцию для получения событий
from handlers.filters_handler import apply_filters_handler_func  # Импортируем обработчик
from datetime import datetime
from shared.shared_data import user_data
from handlers.errors_handler import handle_network_errors

logger = logging.getLogger(__name__)

# Глобальный словарь для хранения message_ids для каждого пользователя
user_message_ids = {}

def setup_preference_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data.startswith(('like_', 'dislike_')))
    @handle_network_errors
    def preference_handler(callback):
        """Обрабатывает Like/Dislike."""
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        data = callback.data

        if data.startswith("like_"):
            event_id = int(data.split("_")[1])
            db_update_user_preference(user_id, event_id, 1)  # Like

            # Убираем кнопки Like/Dislike
            bot.edit_message_reply_markup(chat_id, callback.message.message_id, reply_markup=None)
            bot.answer_callback_query(callback.id, "Ваши предпочтения учтены ❤️")
        
        elif data.startswith("dislike_"):
            event_id = int(data.split("_")[1])
            db_hide_event_for_user(user_id, event_id)  # Скрываем событие для пользователя

            # Удаляем сообщение с событием
            try:
                bot.delete_message(chat_id, callback.message.message_id)
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения: {e}")

            bot.answer_callback_query(callback.id, "Событие скрыто 👎")
 

