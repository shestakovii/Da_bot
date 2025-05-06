# Функция получения погоды
import requests
import telebot
import sys
from telebot import types
from handlers.errors_handler import handle_network_errors
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import API_Weather

def setup_weather_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'weather')
    @handle_network_errors
    def weather(callback):
        if callback.data == 'weather':
            try:
                res = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?q=Moscow&appid={API_Weather}&units=metric')
                res.raise_for_status()  # Проверяем, не возникла ли ошибка при выполнении запроса
                data = res.json()
                #print(data)
                temperature = data["list"][0]["main"]["temp"]
                wind = data["list"][0]["wind"]["speed"]
                temperature_fellslike = data["list"][0]["main"]["feels_like"]
                humidity = data["list"][0]["main"]["humidity"]
                pressure = data["list"][0]["main"]["grnd_level"]
                #sky = data["list"][0]["weather"]["main"]
                bot.send_message(callback.message.chat.id, f'<b>Погода сейчас:</b> \n Температура: {temperature} °C\n Ощущается как: {temperature_fellslike} °C\n Ветер: {wind} м/с\n Влажность: {humidity} %\n Атмосферное давление: {pressure} кПа', parse_mode='html')
            except requests.exceptions.RequestException as e:
            # Обработка ошибок запроса
                print(f"Ошибка при выполнении запроса: {e}")
                bot.send_message(callback.message.chat.id, "Произошла ошибка при выполнении запроса к API погоды.")
            except KeyError:
            # Обработка ошибок обработки данных
                print("Ошибка при обработке данных")
                bot.send_message(callback.message.chat.id, "Произошла ошибка при обработке данных погоды.")