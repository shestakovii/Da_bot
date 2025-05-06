import os
import telebot
import openai

BOT_TOKEN = '6033467476:AAF2LOxQgz0esiiaRzN4qad58TjcRxHJJFY'
#API_Weather_path = r'keys\weather_apikey.txt'
API_Weather = '8817f01e23170f4e452b70e42b943e82'
DEFAULT_ROLE = 'Тебя зовут Борюсик,ты-негр и ты самый лучший друг и личный ассистент. ты любишь черный юмор, расистсткие шутки, и шутишь в каждом ответе. Отвечай на вопросы прямо, кратко, не упускай важных фактов'
DEFAULT_CITY = 'Москва'
DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'Boryusik_bot.db') #'db/Boryusik_bot.db'
HF_TOKEN = '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'
OPENAI_TOKEN = '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'
# путь к исполняемому файлу ffmpeg
#ffmpeg_path = r'C:\Users\ishes\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe'
system = DEFAULT_ROLE


