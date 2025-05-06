import requests
import logging
import chardet
from bs4 import BeautifulSoup
from datetime import datetime
from fake_useragent import UserAgent
from db.operations.db_events import db_update_events
from telebot import TeleBot
from config import BOT_TOKEN


# from bot_start import bot
# from handlers.show_events_handler import show_events
# from db.operations.db_events import db_get_events  # Добавляем функцию для получения событий
# from db.operations.db_events import db_get_free_events
# from handlers.preference_handler import user_message_ids  # Импортируем глобальный словар

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = TeleBot(BOT_TOKEN)

# Парсинг сайта rockgig.net на текущую дату

def parse_rockgig():

    date = datetime.now().strftime('%Y-%m-%d')
    url = f"https://rockgig.net/schedule/{date}"           
    # user_id = callback.from_user.id # Получаем user_id из callback
    
    # Заголовки для имитации запроса от браузера
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,de;q=0.8,tr;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": "https://rockgig.net/",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # Инициализация переменной response
    response = None
    events = []
    try:
        logger.info(f"Запрос к сайту: {url}")
        logger.info(f"Используемые заголовки: {headers}")  # Логируем заголовки
        response = requests.get(url, headers=headers)
        
        # Проверка, что response не равен None
        if response is None:
            raise Exception("Запрос к сайту не был выполнен.")
        
        # Логируем заголовки ответа
        logger.info(f"Заголовки ответа: {response.headers}")
        logger.info(f"Кодировка ответа до декодирования: {response.encoding}")
        response.encoding = 'ISO-8859-1'  # Указываем правильную кодировку
        logger.info(f"Кодировка ответа после декодирования: {response.encoding}")
        # Определяем кодировку автоматически
        raw_content = response.content  # Получаем байтовый контент
        detected_encoding = chardet.detect(raw_content)['encoding']
        response_text = response.content.decode('ISO-8859-1', errors='replace')
        
        # Логируем первые 500 символов ответа для отладки
        logger.info(f"Первые 300 символов ответа: {response_text[:300]}")
        if detected_encoding:
            response_text = raw_content.decode(detected_encoding, errors='replace')
        else:
            response_text = raw_content.decode('ISO-8859-1', errors='replace')  # Запасной вариант
        
        # Используем BeautifulSoup             
        soup = BeautifulSoup(response_text, 'html.parser')
        items = soup.find_all('div', class_='el')
        if not items:
            logger.warning("Не найдено событий на странице.")
            return events
        # events = []
                
        for item in items:
            try:
                # Извлечение данных с декодированием
                #event_date = item.find('div', class_='iDate').text.strip() if item.find('div', class_='iDate') else "N/A"
                event_date = date
                event_time = item.find('div', class_='iTime').text.strip() if item.find('div', class_='iTime') else "N/A"
                event_time = event_time.split()[0]  # Берем только время (первое слово)
                if event_time == "N/A":
                    continue  # Пропускаем события без времени
                event_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
                event_location = item.find('div', class_='elClub').text.strip() if item.find('div', class_='elClub') else "N/A"
                event_name = item.find('div', class_='elName').text.strip() if item.find('div', class_='elName') else "N/A"
                event_genre = item.find('div', class_='elGenr').text.strip() if item.find('div', class_='elGenr') else None
                
                
                # Извлечение цены
                price = "N/A"
                price_element = item.find('div', class_='iTime')
                if price_element:
                    if price_element.find('span', class_='Free'):
                        price = "Free"
                    elif price_element.find('span', class_='Any'):
                        price = "Any"
                    elif price_element.find('a'):
                        price =price_element.find('a').text.strip()
                        
                # Формируем словарь события
                event = {
                    "event_date": event_date,
                    "event_time": event_time,
                    "event_datetime": event_datetime.strftime("%Y-%m-%d %H:%M"),
                    "event_location_name": event_location,
                    "event_location_url": "https://rockgig.net" + item.find('div', class_='elClub').find('a')['href'] if item.find('div', class_='elClub') and item.find('div', class_='elClub').find('a') else "N/A",
                    "event_name": event_name,
                    "event_name_url": "https://rockgig.net" + item.find('div', class_='elName').find('a')['href'] if item.find('div', class_='elName') and item.find('div', class_='elName').find('a') else "N/A",
                    "tags": event_genre,
                    "price": price,
                    "category": "concert",
                    "event_city": "Москва"
                }
                events.append(event)
                logger.info(f"Извлечено событие: {event}")

            except Exception as e:
                logger.error(f"Ошибка при обработке элемента: {e}")
                        
        # db_update_events(events)
        # logger.info(f"Данные отправлены в БД. Количество событий: {len(events)}")        

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к сайту: {e}")
        bot.send_message(bot.message.chat.id, "Произошла ошибка при сборе информации о событиях. Попробуйте повторить запрос еще раз")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        bot.send_message(bot.message.chat.id, "Всё сломалось, наш информатор не выходит на связь. Попробуйте повторить запрос еще раз")
        
    return events