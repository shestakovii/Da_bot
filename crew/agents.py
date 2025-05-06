from crewai import Agent
from langchain.llms import OpenAI
from langchain.llms import HuggingFaceHub
from litellm import completion
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_operations import db_update_music_events
from handlers.parse_rockgig_handler import parse_rockgig
from crew.tools import ParseRockgigTool  # Импортируем инструмент
from config import HF_TOKEN

# Создаем инструмент
parse_rockgig_tool = ParseRockgigTool()



# # Инициализация llm (OpenAI)
# llm = HuggingFaceHub(
#     repo_id="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",  # Укажите модель
#     task="text-generation",  # Явно указываем задачу
#     huggingfacehub_api_token=HF_TOKEN
# )
# # Пример запроса
# response = llm("Привет, как дела?")
# print(response)


response = completion(
    model='huggingface/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B',  # Указываем провайдера и модель
    messages=[{"role": "user", "content": "Привет, как дела?"}],
    api_key=HF_TOKEN
)

print(response)

# Парсер
parser_agent = Agent(
    role="Парсер мероприятий",
    goal="Парсинг сайтов с мероприятиями и извлечение данных",
    backstory="Я специализируюсь на извлечении данных с веб-сайтов.",
    tools=[parse_rockgig_tool],  # Здесь можно добавить инструменты для парсинга (например, BeautifulSoup, Scrapy)
    verbose=True,
    allow_delegation=True,
    llm=llm
)



# def setup_concert_parse(bot):
#     @bot.callback_query_handler(func=lambda callback: callback.data == 'concert')
#     def concert(callback):
        
#         def parse_rockgig(date):
#             """Парсинг сайта rockgig.net на указанную дату."""
#             url = f"https://rockgig.net/schedule/{date}"
#             response = requests.get(url)
#             soup = BeautifulSoup(response.text, 'html.parser')

#             events = []
#             for item in soup.find_all('div', class_='el'):
#                     price_element = item.find('div', class_='iTime')
#                 if price_element:
#                     # Проверяем, есть ли информация о стоимости
#                     if price_element.find('span', class_='Free'):
#                         price = "Free"
#                     elif price_element.find('span', class_='Any'):
#                         price = "Any"
#                     elif price_element.find('a'):
#                         price = price_element.find('a').text.strip()
#                     else:
#                         price = "N/A"  # Если цена не указана 
#                 else: 
#                     price = "N/A" # Если элемент с ценой отсутствует  
                
#                 event = {
#                     "event_date": date,
#                     "event_time": item.find('div', class_='iTime').text.strip(),
#                     "event_location_name": item.find('div', class_='elClub').text.strip(),
#                     "event_location_url": "https://rockgig.net" + item.find('div', class_='elClub').find('a')['href'],
#                     "event_name": item.find('div', class_='elName').text.strip(),
#                     "event_name_url": "https://rockgig.net" + item.find('div', class_='elName').find('a')['href'],
#                     "style": item.find('div', class_='elGenr').text.strip() if item.find('div', class_='elGenr') else None,
#                     "price": price
#                 }
#                 events.append(event)

#             return events
#     # Парсинг данных на текущую дату
#     current_date = datetime.now().strftime('%Y-%m-%d')
#     events = parse_rockgig(current_date)
#         # Сохранение данных в базу данных
#     db_update_music_events(events)

# def parse_kudago():
#     """Парсинг сайта kudago.com"""
#     url = "https://kudago.com/msk/"
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, 'html.parser')
    
#     events = []
#     for item in soup.find_all('div', class_='event-item'):
#         title = item.find('h2').text.strip()
#         date = item.find('span', class_='date').text.strip()
#         location = item.find('span', class_='location').text.strip()
#         price = item.find('span', class_='price').text.strip()
        
#         events.append({
#             "title": title,
#             "date": date,
#             "location": location,
#             "price": price
#         })
    
#     return events



# Классификатор
classifier_agent = Agent(
    role="Классификатор мероприятий",
    goal="Сортировка мероприятий по категориям",
    backstory="Я анализирую данные и присваиваю категории.",
    tools=[],  # Здесь можно добавить инструменты для классификации (например, ML-модели)
)

# Фильтр по стоимости
price_filter_agent = Agent(
    role="Фильтр по стоимости",
    goal="Фильтрация мероприятий по цене",
    backstory="Я помогаю находить мероприятия по бюджету пользователя.",
    tools=[],
)

# Рекомендательная система
recommender_agent = Agent(
    role="Рекомендательная система",
    goal="Составление персонализированных подборок",
    backstory="Я анализирую предпочтения пользователя и предлагаю лучшие варианты.",
    tools=[],
)

# Интегратор
integrator_agent = Agent(
    role="Интегратор",
    goal="Координация работы агентов",
    backstory="Я управляю взаимодействием между агентами и формирую финальный ответ.",
    tools=[],
)