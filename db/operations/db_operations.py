import sqlite3
from datetime import datetime
from config import DB_PATH
import logging
      
# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)        
logger = logging.getLogger(__name__)


# Сохранение посещения пользователя (вызов /start)
def db_update_users(tg_user_id: int, user_nickname: str, user_first_name: str, 
                   user_last_name: str, invite_link: str = None) -> None:
    
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT CreatedDate FROM Users WHERE TgUserId = ?', (tg_user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Обновляем LastVisitDate для существующего пользователя
            cursor.execute('''
                UPDATE Users 
                SET LastVisitDate = ?, Nickname = ?, FirstName = ?, LastName = ?, InviteLink = ?
                WHERE TgUserId = ?
            ''', (now, user_nickname, user_first_name, user_last_name, invite_link, tg_user_id))
        else:
            # Создаем новую запись
            cursor.execute('''
                INSERT INTO Users 
                (CreatedDate, LastVisitDate, TgUserId, Nickname, FirstName, LastName, InviteLink)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (now, now, tg_user_id, user_nickname, user_first_name, user_last_name, invite_link))
      
        conn.commit()
        logger.info(f"User {user_nickname} updated in database")
        
    except sqlite3.Error as e:
        logger.error(f"Ошибка БД: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()
        
        
# Сохранение истории запросов Пользователя к чат-боту
def db_update_users_requests(CreatedDate, LastVisitDate, Nickname, BotRole, UserRequest, BotResponse, TokenCount, RequestCost):
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Users_Requests (CreatedDate, LastVisitDate, Nickname, BotRole, UserRequest, BotResponse, TokenCount, RequestCost) VALUES (?,?,?,?,?,?,?,?)', 
                       (CreatedDate, LastVisitDate, Nickname, BotRole, UserRequest, BotResponse, TokenCount, RequestCost))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении/обновлении записи: {e}")
    finally:
        conn.close()
        

# Сохранение результатов парсинга мероприятий
def db_update_music_events(events):
    """Сохранение данных в базу данных."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Создание таблицы, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Events (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                CreatedDate TEXT NOT NULL,
                EventDate TEXT NOT NULL,
                EventTime TEXT,
                EventLocationName TEXT,
                EventLocationAdress TEXT,
                EventLocationUrl TEXT,
                EventName TEXT,
                EventNameUrl TEXT,
                Tags TEXT,
                Price TEXT
            )
        ''')

        for event in events:
            # Декодируем данные перед сохранением
            event_time = event['event_time'] if event['event_time'] else None
            event_location_name = event['event_location_name'] if event['event_location_name'] else None
            event_location_url = event['event_location_url'] if event['event_location_url'] else None
            event_name = event['event_name'] if event['event_name'] else None
            event_name_url = event['event_name_url'] if event['event_name_url'] else None
            tags = event['tags'] if event['tags'] else None
            price = event['price'] if event['price'] else None

            # Проверка на дубликаты
            cursor.execute('''
                SELECT Id FROM Events
                WHERE EventDate = ? AND EventName = ? AND EventLocationName = ?
            ''', (event['event_date'], event_name, event_location_name))

            existing_event = cursor.fetchone()

            if existing_event:
                # Обновление существующей записи
                cursor.execute('''
                    UPDATE Events
                    SET EventTime = ?, EventLocationUrl = ?, EventNameUrl = ?, Tags = ?, Price = ?
                    WHERE Id = ?
                ''', (event_time, event_location_url, event_name_url, tags, price, existing_event[0]))
                logger.info(f"Обновлено событие: {event_name}")
            else:
                # Добавление новой записи
                cursor.execute('''
                    INSERT INTO Events (CreatedDate, EventDate, EventTime, EventLocationName, EventLocationUrl, EventName, EventNameUrl, Tags, Price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), event['event_date'], event_time, event_location_name, event_location_url, event_name, event_name_url, tags, price))
                logger.info(f"Добавлено новое событие: {event_name}")

        conn.commit()
        logger.info("Данные успешно сохранены в БД.")
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при работе с БД: {e}")
    finally:
        conn.close()
        
# Обновляет предпочтение пользователя (like/dislike) для мероприятия.        
def update_user_preference(event_id, user_like):
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE MusicEvents
            SET UserLike = ?
            WHERE Id = ?
        ''', (user_like, event_id))

        conn.commit()
        logger.info(f"Предпочтение пользователя обновлено: EventId={event_id}, UserLike={user_like}")
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении предпочтения: {e}")
    finally:
        if conn:
            conn.close()
            
            
# Возвращает список бесплатных мероприятий из БД.            
def get_free_events():

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT Id, EventDate, EventTime, EventLocationName, EventName, Style
            FROM MusicEvents
            WHERE Price = 'Free'
        ''')
        
        events = []
        for row in cursor.fetchall():
            event = {
                "Id": row[0],
                "event_date": row[1],
                "event_time": row[2],
                "event_location_name": row[3],
                "event_name": row[4],
                "style": row[5]
            }
            events.append(event)
        
        return events
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении мероприятий: {e}")
        return []
    finally:
        if conn:
            conn.close()