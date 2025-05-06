import requests
import telebot
import sys
from telebot import types
from handlers.errors_handler import handle_network_errors
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_ai_tools_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'ai_tools')
    @handle_network_errors
    def ai_tools(callback):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton ('Изображения', callback_data = 'image_gen')
        btn2 = types.InlineKeyboardButton ('Текст', url = f'https://kudago.com/msk/')
        btn3 = types.InlineKeyboardButton ('Аудио ', url = f'https://visitmo.ru/events/')
        markup.row (btn1, btn2, btn3)
        
        bot.send_message(
            callback.message.chat.id,
            "С чем бы вы хотели поработать?",
            reply_markup=markup
        )