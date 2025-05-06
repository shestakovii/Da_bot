import sys
from telebot import types
import os
import logging
from db.operations.db_users import db_update_user_city
from handlers.filters_handler import show_category_selection
from handlers.errors_handler import handle_network_errors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

def setup_set_city_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'change_city')
    @handle_network_errors
    def show_city_selection(callback):
        # user_id = callback.from_user.id if callback.from_user else None
        # chat_id = callback.message.chat.id if callback.message else None
        logger.info(f"handle_parsing вызван с callback=change_city")
        
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton ('✮ Москва', callback_data = 'apply_city_Москва')
        btn2 = types.InlineKeyboardButton ('❄ Омск', callback_data = 'apply_city_Омск')
        markup.row (btn1, btn2)
        
        bot.send_message(
            callback.message.chat.id, f'Выберите город, в котором будете искать мероприятия', reply_markup=markup
        )
        
        
def setup_apply_city_selection_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('apply_city_'))
    @handle_network_errors
    def apply_city_selection(callback):
        try:
            logger.info(f"Обработчик handle_city_selection_callback вызван с callback.data={callback.data}")
            user_id: int = callback.from_user.id
            handle_city_selection (bot, callback, user_id)
        except Exception as e:
            logger.error(f"Ошибка в handle_city_selection: {e}")



def handle_city_selection(bot, callback, user_id: int):
    """
    Обрабатывает выбор города пользователем.
    """
    try:
        city: str = callback.data.split("_")[-1]  # Пример: "set_city_Москва" -> "Москва"
        logger.info(f"Пользователь: {user_id} выбрал город: {city}")
        
        # Сохраняем город в БД
        success = db_update_user_city(user_id, city)
        if not success:
            raise ValueError("Не удалось обновить город в БД")

        # Сообщаем пользователю об успешном выборе
        bot.answer_callback_query(callback.id, f" Город успешно установлен: {city}")
        
        # Переходим к выбору фильтров
        show_category_selection (bot, callback.message.chat.id, user_id, city)
    except Exception as e:
        logger.error(f"Ошибка в handle_city_selection: {e}")