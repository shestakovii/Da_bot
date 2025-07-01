# Функция получения погоды
import requests
import telebot
import sys
from telebot import types
from handlers.errors_handler import handle_network_errors
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import datetime
from config import API_Weather

logger = logging.getLogger(__name__)

def setup_weather_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'weather')
    @handle_network_errors
    def weather(callback):
        if callback.data == 'weather':
            try:
                res = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?q=Moscow&appid={API_Weather}&units=metric')
                res.raise_for_status()  # Проверяем, не возникла ли ошибка при выполнении запроса
                data = res.json()
                # print(data)
                temperature = data["list"][0]["main"]["temp"]
                wind = data["list"][0]["wind"]["speed"]
                temperature_fellslike = data["list"][0]["main"]["feels_like"]
                humidity = data["list"][0]["main"]["humidity"]
                pressure = data["list"][0]["main"]["grnd_level"]
                sunrise_ts = data['city']['sunrise']
                sunset_ts = data['city']['sunset']
                # Конвертируем в формат HH:MM
                sunrise_time = datetime.datetime.fromtimestamp(sunrise_ts).strftime('%H:%M')
                sunset_time = datetime.datetime.fromtimestamp(sunset_ts).strftime('%H:%M')
                #sky = data["list"][0]["weather"]["main"]
                bot.send_message(callback.message.chat.id, f'<b>Погода в Москве:</b> \n 🌡️ Температура: {temperature} °C\n 🫠 Ощущается как: {temperature_fellslike} °C\n 💨 Ветер: {wind} м/с\n 💦 Влажность: {humidity} %\n 🏋 Атмосферное давление: {pressure} кПа\n ☀️ Восход: {sunrise_time}\n 🌙 Закат: {sunset_time}', parse_mode='html')
            except requests.exceptions.RequestException as e:
            # Обработка ошибок запроса
                print(f"Ошибка при выполнении запроса: {e}")
                bot.send_message(callback.message.chat.id, "Произошла ошибка при выполнении запроса к API погоды.")
            except KeyError:
            # Обработка ошибок обработки данных
                # logger.info(f'Ошибка обработки: {e}')
                print("Ошибка при обработке данных")
                bot.send_message(callback.message.chat.id, "Произошла ошибка при обработке данных погоды.")