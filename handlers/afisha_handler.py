import requests
import telebot
import sys
from telebot import types
from handlers.errors_handler import handle_network_errors
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_afisha_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'afisha')
    @handle_network_errors
    def afisha(callback):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton ('Конц', callback_data = 'ai_tools')
        btn2 = types.InlineKeyboardButton ('Концерты', callback_data = 'parser')
        btn3 = types.InlineKeyboardButton ('Афиша МО', url = f'https://visitmo.ru/events/')
        markup.row (btn1, btn2, btn3)
        
        bot.send_message(
            callback.message.chat.id,
            "Что бы вы хотели найти?",
            reply_markup=markup
        )
        