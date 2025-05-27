import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
import telebot
from telebot import types
from pathlib import Path
import re
import uuid
import time
from telebot import util
import threading
from config import HF_TOKEN

#HG libs
import huggingface_hub
from huggingface_hub import login
import transformers
from huggingface_hub import InferenceClient
import torch
import diffusers
from diffusers import FluxPipeline
from PIL import Image
from handlers.errors_handler import handle_network_errors

  
prompt = ""
#Глобальные переменные для управления загрузкой
loading_complete = False
sent_message = None
loading_thread = None
 
          
# Функция инициации сохранения промта для генерации фото
def setup_image_gen_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'image_gen')
    @handle_network_errors
    def img_pompt_setup(callback):
        bot.send_message(callback.message.chat.id, f'Опишите подробно, какое изображение хотите сгенерировать. Укажите стиль, уровень реалистичности, цветовую гамму и тд', parse_mode='html')
        # Регистрируем обработчик сообщений для сохранения описания роли
        bot.register_next_step_handler(callback.message, img_pompt_save)

# Функция сохранения промта
    #@bot.message_handler(content_types=['text'])
    def img_pompt_save(message):
        global prompt
        prompt = message.text  # Сохраняем описание роли в переменной system
        print(f"Промт сохранен: {prompt}")
        bot.send_message(message.chat.id, f'Генерация стартовала. Нужно немного подождать', parse_mode='html')
        # Регистрируем обработчик сообщений для сохранения описания роли
        #bot.register_next_step_handler(message, img_generation)
        img_generation(message)
        
        
   
        # Функция для отображения загрузки
    def show_loading(bot, chat_id, message_id):
        global loading_complete
        loading_messages = [
        "Созвонились с дизайнером...",
        "Правим макет...",
        "Пожалуйста, подождите...",
        "Еще немного...",
        "Нужно внести небольшие правки..."] 
        while not loading_complete:  # Пока генерация не завершена
            for msg in loading_messages:
                if loading_complete:  # Проверяем, завершена ли генерация
                    break
                bot.edit_message_text(msg, chat_id, message_id)
                time.sleep(3)  # Пауза между сообщениями

          
            
    def img_generation(message):
        global loading_complete, sent_message, loading_thread

        # Активация статуса "печатает..."
        bot.send_chat_action(message.chat.id, 'typing')

        # Отправка начального сообщения
        sent_message = bot.send_message(message.chat.id, "Созвонились с дизайнером..")

        # Флаг для завершения загрузки
        loading_complete = False

        # Запуск потока для отображения загрузки
        loading_thread = threading.Thread(target=show_loading, args=(bot, message.chat.id, sent_message.message_id))
        loading_thread.start()
        
        try:        
            client = InferenceClient(
                provider="fal-ai",
                api_key=HF_TOKEN
            )
           
            # output is a PIL.Image object
            image = client.text_to_image(
                prompt,  # Позиционный аргумент (текстовое описание)
                model="stabilityai/stable-diffusion-3-medium",  # Именованный аргумент (модель)
                num_inference_steps=30,  # Именованный аргумент (количество шагов генерации)
                guidance_scale=5,  # Именованный аргумент (параметр контроля качества)
                width=512,  # Именованный аргумент (ширина изображения)
                height=512  # Именованный аргумент (высота изображения)
            )

            # Указание директории для сохранения
            output_dir = Path("C:\Disk D\Dev\projects\Boryusik_bot\img_generated")  # Папка для сохранения изображений

            # Проверка существования директории и создание, если она не существует
            output_dir.mkdir(parents=True, exist_ok=True)

            # Очистка промта от недопустимых символов
            def clean_prompt_for_filename(prompt):
                # Удаляем недопустимые символы
                cleaned_prompt = re.sub(r'[\\/*?:"<>|]', '', prompt)
                # Убираем лишние пробелы и обрезаем длину (например, до 50 символов)
                cleaned_prompt = cleaned_prompt.strip()[:50]
                return cleaned_prompt

            # Создание уникального имени файла с промтом
            cleaned_prompt = clean_prompt_for_filename(prompt)
            unique_id = uuid.uuid4().hex[:6]  # Уникальный идентификатор для избежания конфликтов
            filename = f"{cleaned_prompt}_{unique_id}.png"
            output_path = output_dir / filename

            # Удаление текстового сообщения
            bot.delete_message(message.chat.id, sent_message.message_id)
            # Сохранение изображения
            if image:
                image.save(output_path)  # Сохраняем изображение по указанному пути
                print(f"Изображение успешно сохранено как '{output_path}'")
                
                                # Создаем клавиатуру с кнопками
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton('Новая генерация', callback_data='image_gen')
                btn2 = types.InlineKeyboardButton('Назад в меню', callback_data='ai_tools')
                markup.add(btn1, btn2)
                
                with open(output_path, 'rb') as file:
                    bot.send_photo(message.chat.id, file, reply_markup=markup)
            

            # file=open(r'C:\Disk D\Dev\projects\Boryusik_bot\img_generated', 'rb')
            # bot.send_photo(message.chat.id, file)
            else:
                bot.send_message(message.chat.id, "Ошибка: изображение не было сгенерировано.")

        except Exception as e:
            # Логирование ошибки
            print(f"Ошибка при генерации изображения: {e}")
            bot.send_message(message.chat.id, "Произошла ошибка при генерации изображения. Пожалуйста, попробуйте еще раз.")
            
        finally:
            # Устанавливаем флаг завершения загрузки
            loading_complete = True
            if 'loading_thread' in globals():
                loading_thread.join()  # Ожидаем завершения потока

            # Удаление текстового сообщения          
            if sent_message:
                try:
                    bot.delete_message(message.chat.id, sent_message.message_id)
                except Exception as e:
                    print(f"Ошибка при удалении сообщения: {e}")
                    #ot.delete_message(message.chat.id, sent_message.message_id)







