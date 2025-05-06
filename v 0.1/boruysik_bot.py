import telebot
import webbrowser
from telebot import types
import requests
import json
import requests.exceptions
from pydub import AudioSegment
import speech_recognition as sr
import sqlite3

# import soundfile as sf
# import speech_recognition as sr


#AI libs
from langchain.llms import OpenAI
from langchain.docstore.document import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain.prompts import PromptTemplate
from oauth2client.service_account import ServiceAccountCredentials
#from openai import OpenAIEmbeddings
from datetime import datetime
import openai
import tiktoken
import os
import getpass
import re
import pathlib
import subprocess
import tempfile
import gspread





#from telegram.ext import Application, CommandHandler
#from dotenv import load_dotenv
#import os
#from google.colab import drive

bot=telebot.TeleBot('6033467476:AAF2LOxQgz0esiiaRzN4qad58TjcRxHJJFY')
#API_Weather_path = r'keys\weather_apikey.txt'
API_Weather = '8817f01e23170f4e452b70e42b943e82'
openai.api_key_path='keys\gpt_apikey.txt'
OPENAI_API_KEY = openai.api_key_path


# путь к исполняемому файлу ffmpeg
ffmpeg_path = r'C:\Users\ishes\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe'
AudioSegment.ffmpeg = ffmpeg_path

system = ''
default_role='Тебя зовут Борюсик,ты-негр и ты самый лучший друг и личный ассистент. ты любишь черный юмор, расистсткие шутки, и шутишь в каждом ответе. Отвечай на вопросы прямо, кратко, не упускай важных фактов'
dialog_history = []
recognized_text = ""
uploaded_text = '' 

conn = sqlite3.connect('db/boryusik_bot.db', check_same_thread=False)
cursor = conn.cursor()

# Функция записи данных в БД
def db_update_users(date_created, tg_user_id, user_nickname, user_first_name, user_last_name):
    try:
        cursor.execute('SELECT tg_user_id FROM Users WHERE tg_user_id = ?', (tg_user_id,))
        existing_user = cursor.fetchone()

        if existing_user is None:
            cursor.execute('INSERT INTO Users (date_created, tg_user_id, user_nickname, user_first_name, user_last_name) VALUES (?,?,?,?,?)', (date_created, tg_user_id, user_nickname, user_first_name, user_last_name))
        else:
            # Можно обновить существующую запись, если нужно
            cursor.execute('UPDATE Users SET date_created=?, user_nickname=?, user_first_name=?, user_last_name=? WHERE tg_user_id=?', (date_created, user_nickname, user_first_name, user_last_name, tg_user_id))
            pass

        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении/обновлении записи: {e}")

    
def db_update_users_requests (date_created, user_nickname, bot_role, user_request, bot_response, token_count, request_cost):
    try:
        cursor.execute('INSERT INTO Users_Requests (date_created, user_nickname, bot_role, user_request, bot_response, token_count, request_cost) VALUES ("%s","%s","%s","%s","%s","%s","%s")' % (date_created, user_nickname, bot_role, user_request, bot_response, token_count, request_cost))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении/обновлении записи: {e}")
    


# Функция запуска бота 
@bot.message_handler(commands=['start']) 
def start(message):
    global system
    system=default_role
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton ('Афиша', url=f'https://omsk.qtickets.events/')
    btn2 = types.InlineKeyboardButton ('Погода', callback_data='weather')
    btn3 = types.InlineKeyboardButton ('Учить AI', callback_data = 'getUserData')
    markup.row(btn1, btn2, btn3)
    # btn4 = types.InlineKeyboardButton('Поговорить с GPT', callback_data='start_gpt')
    # markup.row(btn3, btn4)
     
    file=open('./cj.jpg', 'rb')
    bot.send_photo(message.chat.id, file)
    bot.send_message(message.chat.id, f'Привет {message.from_user.first_name} {message.from_user.last_name}! Меня зовут <b>Борюсик</b> - я твой лучший бро! Чем могу быть полезен?', reply_markup=markup, parse_mode='html')

    conn = sqlite3.connect('db/boryusik_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    
# Функция вызова Нейро-ассистента 
@bot.message_handler(commands=['neuroassistant'])        
def neuroassistant(message):
    markup = types.InlineKeyboardMarkup()
    #btn1 = types.InlineKeyboardButton('Описать роль', callback_data='set_role_byText')# url=f'https://ya.ru')
    btn2 = types.InlineKeyboardButton('Загрузить документ', callback_data='upload_instruction')#  url =f'https://mail.ru')
    markup.row(btn2)
    file=open('./cj_smart.jpg', 'rb')
    bot.send_photo(message.chat.id, file)
    bot.send_message(message.chat.id, f'Хорошо, давай начнем. Для начала отправь ссылку на документ, с которым нужно работать', reply_markup=markup, parse_mode='html')

# Функция получения погоды
@bot.callback_query_handler(func=lambda callback: callback.data == 'weather')
def weather(callback):
    if callback.data == 'weather':
        try:
            res = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?q=Antalya&appid={API_Weather}&units=metric')
            res.raise_for_status()  # Проверяем, не возникла ли ошибка при выполнении запроса
            data = res.json()
            #print(data)
            temperature = data["list"][0]["main"]["temp"]
            wind = data["list"][0]["wind"]["speed"]
            #sky = data["list"][0]["weather"]["main"]
            bot.send_message(callback.message.chat.id, f'<b>Погода сейчас:</b> \n Температура: {temperature} °C\n Ветер: {wind} м/с\n Облачность:', parse_mode='html')
        except requests.exceptions.RequestException as e:
        # Обработка ошибок запроса
            print(f"Ошибка при выполнении запроса: {e}")
            bot.send_message(callback.message.chat.id, "Произошла ошибка при выполнении запроса к API погоды.")
        except KeyError:
        # Обработка ошибок обработки данных
            print("Ошибка при обработке данных")
            bot.send_message(callback.message.chat.id, "Произошла ошибка при обработке данных погоды.")


@bot.callback_query_handler(func=lambda callback: callback.data == 'getUserData')
def getUserData (callback):
    bot.send_message(callback.message.chat.id, callback.message)
    print (callback.message)


@bot.message_handler(content_types=['text'])    
def gpt_text_response(message): 
    global dialog_history, system  # Добавьте объявление глобальной переменной
    system=default_role
    # Добавьте новое сообщение пользователя в историю диалога
    user_message = {'role': 'user', 'content': message.text.lower()}
    dialog_history.append(user_message)
    reply=''
    response = openai.ChatCompletion.create(
    model='gpt-3.5-turbo',
    messages=[
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': message.text.lower()},
        *dialog_history  # Добавьте историю диалога передавая все предыдущие сообщения
    ],
    max_tokens=300,
    temperature=0.3,
    n=1
    )
    
    if response and response.choices:
        reply = response.choices[0].message.content.strip()
    else:
        reply = 'Что-то мне плохо думается. Давай попробуем еще раз'
    # Добавьте ответ бота в историю диалога
    bot_message = {'role': 'assistant', 'content': reply}
    dialog_history.append(bot_message)
    
    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tg_user_id = message.from_user.id
    user_nickname = message.from_user.username
    user_first_name = message.from_user.first_name 
    user_last_name = message.from_user.last_name
    bot_role = system
    user_request = message.text.lower()
    bot_response = reply
    token_count = None
    request_cost = None
    
    db_update_users (date_created, tg_user_id, user_nickname, user_first_name, user_last_name)
    db_update_users_requests(date_created, user_nickname, bot_role, user_request, bot_response, token_count, request_cost)
    
    print(system)
    bot.send_message(message.chat.id, reply)
    
    
@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):
    global recognized_text, system
    
    # Получите информацию о файле голосового сообщения
    file_info = bot.get_file(message.voice.file_id)
    file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}'

    # Скачайте голосовое сообщение
    voice_message = requests.get(file_url)
    with open('voice_message.ogg', 'wb') as file:
        file.write(voice_message.content)

    # Преобразуйте голосовое сообщение в аудиофайл с помощью PyDub
    audio = AudioSegment.from_file('voice_message.ogg', format='ogg')
    
    # Сохраните аудиофайл в формате PCM WAV
    audio.export('voice_message.wav', format='wav')
    
    # Распознайте речь с помощью SpeechRecognition
    
    recognizer = sr.Recognizer()
    with sr.AudioFile('voice_message.wav') as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language='ru-RU')
            recognized_text = text
            # Добавьте новое сообщение пользователя в историю диалога
            user_message = {'role': 'user', 'content': recognized_text.lower()}
            dialog_history.append(user_message)
            reply=''
            response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': recognized_text.lower()},
                *dialog_history  # Добавьте историю диалога передавая все предыдущие сообщения
            ],
            max_tokens=300,
            temperature=0.3,
            n=1
            )
        except sr.UnknownValueError:
            bot.send_message(message.chat.id, 'Не удалось распознать речь.')
        except sr.RequestError as e:
            bot.send_message(message.chat.id, f'Ошибка при запросе к сервису распознавания речи: {e}')
            
        if response and response.choices:
            reply = response.choices[0].message.content.strip()
        else:
            reply = 'Что-то мне плохо думается. Давай попробуем еще раз'
    # Добавьте ответ бота в историю диалога
    bot_message = {'role': 'assistant', 'content': reply}
    dialog_history.append(bot_message)
    
    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_nickname = message.from_user.username
    bot_role = system
    user_request = recognized_text.lower()
    bot_response = reply
    token_count = None
    request_cost = None
    
    db_update_users_requests(date_created, user_nickname, bot_role, user_request, bot_response, token_count, request_cost)
    
    # Удалите временные файлы
    os.remove('voice_message.ogg')
    os.remove('voice_message.wav')
    print(system)
    bot.send_message(message.chat.id, reply)
             


@bot.callback_query_handler(func=lambda callback: callback.data == 'upload_instruction')
def upload_instruction(callback):
    bot.send_message(callback.message.chat.id, f'Отправь ссылку на Google Doc. \n <b>Важно!</b> документ должен быть доступен для чтения для всех', parse_mode='html' )
    bot.register_next_step_handler(callback.message, upload_instruction_byLink)
    
    
@bot.message_handler(content_types=['text'])
def upload_instruction_byLink(message):
    global uploaded_text 
    # Извлекаем текст сообщения из объекта message
    message_text = message.text
     # Extract the document ID from the URL
    match_ = re.search('/document/d/([a-zA-Z0-9-_]+)', message_text)
    if match_ is None:
        raise ValueError('Invalid Google Docs URL')
    doc_id = match_.group(1)
    
    # Download the document as plain text
    response = requests.get(f'https://docs.google.com/document/d/{doc_id}/export?format=txt')
    response.raise_for_status()
    text = response.text
    uploaded_text = text
    print("Загружено символов:", len(uploaded_text))
    uploaded_text_size=len(uploaded_text)
    bot.send_message(message.chat.id, f'Загружено символов: {uploaded_text_size}', parse_mode='html')
    # Вызываем set_role_byText и передаем объект message
    set_role_byText(message)
    
    # Настраиваем и отправляем в LangChain
    database = uploaded_text
    source_chunks = []
    splitter = CharacterTextSplitter(separator="\n", chunk_size=1024, chunk_overlap=0)

    for chunk in splitter.split_text(database):
        source_chunks.append(Document(page_content=chunk, metadata={}))

    # Откройте файл config.txt и прочитайте ключ API
    with open('keys/config.txt', 'r') as config_file:
        config_lines = config_file.readlines()

    # Извлеките значение ключа API
    for line in config_lines:
        if line.startswith('OPENAI_API_KEY='):
            openai_api_key = line[len('OPENAI_API_KEY='):].strip()

    # Используйте полученный ключ API
    # # Инициализирум модель эмбеддингов
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    # Создадим индексную базу из разделенных фрагментов текста
    db = FAISS.from_documents(source_chunks, embeddings)
    
    bot.register_next_step_handler(message, set_role_byText)
    
    # Запуск нейро-ассистента и установка новой роли (system)
# @bot.callback_query_handler(func=lambda callback: callback.data == 'set_role_byText')

# НАЗНАЧЕНИЕ РОЛИ НЕЙРО-АССИСТЕНТА
role_set = False  # Флаг для отслеживания установки роли

#@bot.callback_query_handler(func=lambda callback: callback.data == 'set_role_byText')
def set_role_byText(message):
    global system, role_set
    if not role_set:
        # Очищаем предыдущее значение system
        system = '' 
        bot.send_message(message.chat.id, f'Опиши подробно мою роль и мои ключевые характеристики, которые помогут решить твою задачу.  \n \n<b>Например:</b> "Ты профессиональный визовый консультант, который специализируется на получении ВНЖ в странах Европы и Азии"', parse_mode='html')
        print(system)
        bot.register_next_step_handler(message, save_role_description)
        role_set = True
   
    
# Функция сохранения описания роли, которое пользователь отправит в чат
@bot.message_handler(content_types=['text'])
def save_role_description(message):
    global system
    system = message.text  # Сохраняем описание роли в переменной system
    print(system)
    bot.send_message(message.chat.id, f'Спасибо за описание роли! \nТеперь можешь задать свой вопрос', parse_mode='html')
    # Регистрируем обработчик сообщений для сохранения описания роли
    bot.register_next_step_handler(message, role_setup)
    
# Функция обработки сообщений с новой ролью        
@bot.message_handler(content_types=['text'])
def role_setup(message):
    global dialog_history, system  # Добавьте объявление глобальной переменной
    # Добавьте новое сообщение пользователя в историю диалога
    print(system)
   
    user_message = {'role': 'user', 'content': message.text.lower()}
    dialog_history.append(user_message)
    reply=''
    response = openai.ChatCompletion.create(
    model='gpt-3.5-turbo',
    # Добавить содержание загруженного документа в историю диалога (uploaded_text)
    messages=[
        {'role': 'system', 'content': uploaded_text},
        {'role': 'user', 'content': message.text.lower()},
        *dialog_history  # Добавьте историю диалога передавая все предыдущие сообщения
    ],
    max_tokens=300,
    temperature=0.3,
    n=1
    )
    
    if response and response.choices:
        reply = response.choices[0].message.content.strip()
    else:
        reply = 'Что-то мне плохо думается. Давай попробуем еще раз'
    # Добавьте ответ бота в историю диалога
    bot_message = {'role': 'assistant', 'content': reply}
    dialog_history.append(bot_message)
    print(system)
    bot.send_message(message.chat.id, reply)

# # Функция, которая позволяет выводить ответ модели в удобочитаемом виде
# def insert_newlines(text: str, max_len: int = 170) -> str:
#     words = text.split()
#     lines = []
#     current_line = ""
#     for word in words:
#         if len(current_line + " " + word) > max_len:
#             lines.append(current_line)
#             current_line = ""
#         current_line += " " + word
#     lines.append(current_line)
#     return " ".join(lines)

def answer_index(system, topic, search_index, temp=1, verbose=0):

    # Поиск релевантных отрезков из базы знаний
    docs = search_index.similarity_search(topic, k=4)
    if verbose: print('\n ===========================================: ')
    message_content = re.sub(r'\n{2}', ' ', '\n '.join([f'\nОтрывок документа №{i+1}\n=====================' + doc.page_content + '\n' for i, doc in enumerate(docs)]))
    if verbose: print('message_content :\n ======================================== \n', message_content)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Документ с информацией для ответа клиенту: {message_content}\n\nВопрос клиента: \n{topic}"}
    ]

    if verbose: print('\n ===========================================: ')

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=temp
    )
    answer = insert_newlines(completion.choices[0].message.content)
    return answer  # возвращает ответ

    
   

bot.polling(non_stop=True)