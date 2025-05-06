import telebot
from telebot import types
from datetime import datetime
from config import DEFAULT_ROLE
from db.operations.db_users import db_update_users
from handlers.errors_handler import handle_network_errors

def setup_start_handler(bot):
    @bot.message_handler(commands=['start']) 
    @handle_network_errors
    def start(message):
        global system
        system = DEFAULT_ROLE
        
         # Получаем данные пользователя
        user_data = {
            "tg_user_id": message.from_user.id,
            "user_nickname": message.from_user.username or 'null',
            "user_first_name": message.from_user.first_name or 'null',
            "user_last_name": message.from_user.last_name or 'null',
            "invite_link": message.chat.invite_link or 'null'
        }
        
        # Сохраняем/обновляем данные в БД
        db_update_users(**user_data)
        
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton ('Афиша', callback_data = 'parser')
        btn2 = types.InlineKeyboardButton ('Погода', callback_data = 'weather')
        btn3 = types.InlineKeyboardButton ('ИИ-инструменты', callback_data = 'ai_tools')
        markup.row(btn1, btn2, btn3)
        # btn4 = types.InlineKeyboardButton('Поговорить с GPT', callback_data='start_gpt')
        # markup.row(btn3, btn4)
        
        file=open(r'C:\Disk D\Dev\projects\Boryusik_bot\cj.jpg', 'rb')
        bot.send_photo(message.chat.id, file)
        bot.send_message(message.chat.id, f'Привет {message.from_user.first_name} {message.from_user.last_name}! Меня зовут <b>Борюсик</b> - я твой лучший бро! Чем могу быть полезен?', reply_markup=markup, parse_mode='html')

#def setup_getUserData_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'getUserData')
    @handle_network_errors
    def getUserData (callback):
        bot.send_message(callback.message.chat.id, callback.message)
        print (callback.message)