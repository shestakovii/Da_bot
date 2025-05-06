import telebot
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from telebot import types
import logging
from datetime import datetime
# from handlers.show_events_handler import show_events
from db.operations.db_users import db_get_user_city, db_update_user_city



logger = logging.getLogger(__name__)

def setup_set_city_Moscow(bot):
    # logger.info("Регистрация обработчика выбора города Москва")
    @bot.callback_query_handler(func=lambda callback: callback.data == 'set_city111')
    def set_city_Moscow(callback):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Москва', callback_data = 'set_city_Москва111')
        btn2 = types.InlineKeyboardButton('Омск', callback_data = 'set_city_Омск111')
        markup.row (btn1, btn2)
        bot.send_message(callback.message.chat.id, f'Выберите город, в котором будете искать мероприятия', reply_markup=markup)
        # print ('Удалоось!')
    
    
    @bot.callback_query_handler(func=lambda callback: callback.data.startwith('set_city_'))    
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
            bot.answer_callback_query(callback.id, f"Выбран город: {city}")
            
            # # Переходим к выбору фильтров
            # show_event_filters(bot, callback.message.chat.id, user_id)
        except Exception as e:
            logger.error(f"Ошибка в handle_city_selection: {e}")
        
        # try:
        #     logger.info(f"Вызвана функция set_city_Moscow. Callback data: {callback.data}")
        #     user_id: int = callback.from_user.id if callback.from_user else None
        #     city: str = "Москва"
        #     logger.info(f"Пользователь: {user_id} выбрал город: {city}")
            
        #     # Сохраняем город в БД
        #     success = db_update_user_city(user_id, city)
        #     if not success:
        #         raise ValueError("Не удалось обновить город в БД")
            
        #     # Сообщаем пользователю об успешном выборе
        #     try:
        #         bot.answer_callback_query(callback.id, f"Выбран город: {city}")
        #     except Exception as e:
        #         logger.error(f"Ошибка в answer_callback_query: {e}")
            
        #     #Переходим к выбору фильтров
        #     show_event_filters(bot, callback.message.chat.id, user_id)
        # except Exception as e:
        #     logger.error(f"Ошибка в handle_city_selection: {e}")