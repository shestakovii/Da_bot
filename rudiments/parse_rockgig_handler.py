import requests
import logging
import chardet
from bs4 import BeautifulSoup
from datetime import datetime
from fake_useragent import UserAgent
from db.operations.db_events import db_update_events
from handlers.show_events_handler import show_events
from db.operations.db_events import db_get_events  # Добавляем функцию для получения событий
from db.operations.db_events import db_get_free_events
from handlers.preference_handler import user_message_ids  # Импортируем глобальный словар

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Парсинг сайта rockgig.net на текущую дату
def setup_parser_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'parser')
    def parse_rockgig(callback):

        date = datetime.now().strftime('%Y-%m-%d')
        url = f"https://rockgig.net/schedule/{date}"           
        user_id = callback.from_user.id # Получаем user_id из callback
        
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
            logger.info(f"Первые 500 символов ответа: {response_text[:500]}")
            if detected_encoding:
                response_text = raw_content.decode(detected_encoding, errors='replace')
            else:
                response_text = raw_content.decode('ISO-8859-1', errors='replace')  # Запасной вариант
            
            # Используем BeautifulSoup             
            soup = BeautifulSoup(response_text, 'html.parser')
            events = []
                   
            for item in soup.find_all('div', class_='el'):
                try:
                    # Извлечение данных с декодированием
                    #event_date = item.find('div', class_='iDate').text.strip() if item.find('div', class_='iDate') else "N/A"
                    event_time = item.find('div', class_='iTime').text.strip() if item.find('div', class_='iTime') else "N/A"
                    event_location = item.find('div', class_='elClub').text.strip() if item.find('div', class_='elClub') else "N/A"
                    event_name = item.find('div', class_='elName').text.strip() if item.find('div', class_='elName') else "N/A"
                    event_genre = item.find('div', class_='elGenr').text.strip() if item.find('div', class_='elGenr') else None
                    event_date = date
                    
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
                           
            db_update_events(events)
            logger.info(f"Данные отправлены в БД. Количество событий: {len(events)}")        
    # # БЛОК   отправки первой подборки вынесен в отдельный метод
    #         # Получаем user_id и chat_id
    #         user_id = callback.from_user.id
    #         chat_id = callback.message.chat.id
    #         # Получаем первую подборку бесплатных событий
    #         events = db_get_free_events(user_id)

    #         if events:
    #             bot.send_message(callback.message.chat.id, f"Подготовил вам подборку БЕСПЛАТНЫХ событий на СЕГОДНЯ. Пожалуйста, оценивайте мероприятия в подборке, чтобы я мог в дальнейшем учитывать Ваши предпочтения и рекомендовать события по Вашим интересам")
    #             message_ids = show_events(bot, chat_id, user_id, events)
    #             user_message_ids[user_id] = message_ids  # Сохраняем ID сообщений первой подборки

    #             # show_events(bot, chat_id, user_id, events) # Отображение мероприятий пользователю
    #         else:
    #             logger.warning("Нет данных для сохранения в БД.")
    #             bot.send_message(callback.message.chat.id, "Событий не найдено.")

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к сайту: {e}")
            bot.send_message(callback.message.chat.id, "Произошла ошибка при запросе к сайту.")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            bot.send_message(callback.message.chat.id, "Произошла критическая ошибка при обработке данных.")