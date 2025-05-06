import logging
from telebot import types
from services.parser_service import parse_all_sources
from db.operations.db_users import db_get_user_city
from handlers.errors_handler import handle_network_errors

logger = logging.getLogger(__name__)

def setup_parser_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'parser')
    @handle_network_errors
    def handle_parsing(callback):
        try:
            
            logger.info(f"handle_parsing вызван с callback={callback}")

            # Проверяем, что у callback есть message и from_user
            if not callback.message:
                raise ValueError("Ошибка: callback.message отсутствует (None)")
            if not callback.from_user:
                raise ValueError("Ошибка: callback.from_user отсутствует (None)")   
            
            user_id = callback.from_user.id if callback.from_user else None
            chat_id = callback.message.chat.id if callback.message else None
            events = parse_all_sources(user_id)
            
            if not isinstance(chat_id, int):
                raise ValueError(f"chat_id должен быть числом, получено: {type(chat_id)}")
            if not events:  # Если список пуст
                logger.warning("Парсинг завершен, но события не найдены.")
                bot.send_message(callback.message.chat.id, "Событий не найдено.")
                return
            user_id = callback.from_user.id
            logger.info(f'Парсинг инициирован пользователем {user_id}, событий добавлено в БД {len(events)}, событий обновлено в БД "UpdatedEvents"')
            
            city = db_get_user_city(chat_id)
            if not city:
                city = "МОСКВА"
                      
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton ('🔄 Изменить город', callback_data = 'change_city')
            btn2 = types.InlineKeyboardButton ('➡️ Выбрать мероприятия', callback_data = 'filters')
            markup.row (btn1)
            markup.row (btn2)

            bot.send_message(callback.message.chat.id, f'В городе 🏛️{city}.\nНайдено {len(events)} событий. \nВы можете изменить город или перейти к выбору мероприятий' , reply_markup=markup)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке элемента: {e}")
    

                
