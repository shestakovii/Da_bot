import sqlite3
from datetime import datetime
from config import DB_PATH
import logging
import re
# from decorators.wrap_users import convert_tg_id_to_user_id
# from db.operations.db_users import db_get_user_id_by_tg_id


logger = logging.getLogger(__name__)


        
        
# Сохранение результатов парсинга мероприятий

def db_update_events(events, user_id):
    """Сохранение данных в базу данных."""
    # user_id=db_get_user_id_by_tg_id(tg_user_id)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # # Получаем внутренний UserId по TgUserId
        # cursor.execute('''
        #     SELECT Id FROM Users WHERE TgUserId = ?
        # ''', (tg_user_id,))
        # user = cursor.fetchone()

        # Создание таблицы, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Events (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                CreatedDate TEXT NOT NULL,
                UpdatedDate TEXT,
                EventCity TEXT,
                EventDate TEXT NOT NULL,
                EventTime TEXT,
                EventDateTime TEXT NOT NULL,
                EventLocationName TEXT,
                EventLocationAdress TEXT,
                EventLocationUrl TEXT,
                EventName TEXT,
                EventNameUrl TEXT,
                Category TEXT,
                Tags TEXT,
                Price TEXT
            )
        ''')

        for event in events:
            # Очищаем event_time от лишних данных (оставляем только время)
            event_time = event['event_time'].split(' ')[0] if event['event_time'] else None
            event_datetime = event['event_datetime'] if event['event_datetime'] else None
            event_city = event['event_city']
            # Декодируем данные перед сохранением
            event_location_name = event['event_location_name'] if event['event_location_name'] else None
            event_location_url = event['event_location_url'] if event['event_location_url'] else None
            event_name = event['event_name'] if event['event_name'] else None
            event_name_url = event['event_name_url'] if event['event_name_url'] else None
            tags = event['tags'] if event['tags'] else None
            category = event['category']  # Категория передается из parse_rockgig
            price = event['price'] if event['price'] else None

            # Проверка на дубликаты
            cursor.execute('''
                SELECT Id, CreatedDate FROM Events
                WHERE EventDateTime = ? AND EventName = ? AND EventLocationName = ?
            ''', (event['event_datetime'], event_name, event_location_name))

            existing_event = cursor.fetchone()

            if existing_event:
                # Если запись найдена, распаковываем значения
                event_id, created_date = existing_event
                # Обновление существующей записи
                cursor.execute('''
                    UPDATE Events
                    SET 
                        UpdatedDate = ?,
                        EventCity = ?,
                        EventTime = ?,
                        EventDateTime = ?,
                        EventLocationUrl = ?,
                        EventNameUrl = ?,
                        Category = ?,
                        Tags = ?,
                        Price = ?
                    WHERE Id = ?
                ''', (
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # UpdatedDate
                    event_city,
                    event_time,
                    event_datetime,
                    event_location_url,
                    event_name_url,
                    category,
                    tags,
                    price,
                    event_id
                ))
                logger.info(f"Обновлено событие: {event_name}")
            else:
                # Если запись не найдена, добавляем новую
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO Events (
                        CreatedDate,
                        UpdatedDate,
                        EventCity,
                        EventDate,
                        EventTime,
                        EventDateTime,
                        EventLocationName,
                        EventLocationUrl,
                        EventName,
                        EventNameUrl,
                        Category,
                        Tags,
                        Price
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    current_time,  # CreatedDate
                    current_time,  # UpdatedDate (равно CreatedDate при создании)
                    event_city,
                    event['event_date'],
                    event_time,
                    event_datetime,
                    event_location_name,
                    event_location_url,
                    event_name,
                    event_name_url,
                    category,
                    tags,
                    price
                ))
                logger.info(f"Добавлено новое событие: {event_name}")

        conn.commit()
        logger.info("Данные успешно сохранены в БД.")
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при работе с БД: {e}")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        if conn:
            conn.close()          



# # Увеличивает счетчик показов события для пользователя
# def db_increment_event_show_count(user_id, event_id):

#     try:
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()

#         # Получаем внутренний UserId по TgUserId
#         cursor.execute('''
#             SELECT Id FROM Users WHERE TgUserId = ?
#         ''', (user_id,))
#         user = cursor.fetchone()
#         if user:
#             user_id = user[0]
#             # Увеличиваем счетчик показов
#             cursor.execute('''
#                 INSERT INTO UserPreferences (Id, EventId, EventShowCount)
#                 VALUES (?, ?, 1)
#                 ON CONFLICT(Id, EventId) DO UPDATE SET EventShowCount = EventShowCount + 1
#             ''', (user_id, event_id))
#             conn.commit()
#             logger.info(f"Увеличено количество показов для события: {event_id} у пользователя: {user_id}")
#         else:
#             logger.error(f"Пользователь с TgUserId {user_id} не найден.")
            
#     except sqlite3.Error as e:
#         logger.error(f"Ошибка при обновлении счетчика показов: {e}")
#     finally:
#         if conn:
#             conn.close()


def db_increment_event_show_count(user_id, event_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Увеличиваем счетчик показов
        cursor.execute('''
            INSERT INTO UserPreferences (UserId, EventId, EventShowCount)
            VALUES (?, ?, 1)
            ON CONFLICT(UserId, EventId) DO UPDATE SET EventShowCount = EventShowCount + 1
        ''', (user_id, event_id))
        conn.commit()
        logger.info(f"Увеличено количество показов для события: {event_id} у пользователя: {user_id}")
            
    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении счетчика показов: {e}")
    finally:
        if conn:
            conn.close()


def db_get_events(date, filters=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query = """
            SELECT Id, EventCity, EventDate, EventTime, EventLocationName, EventLocationUrl, 
                   EventName, EventNameUrl, Category, Tags, Price
            FROM Events
            WHERE EventDate = ?
        """
        params = [date]

        if filters:
            conditions = []
            
            # Фильтр по городу
            if filters.get("city"):
                conditions.append("EventCity LIKE ?")
                params.append(f"%{filters['city']}%")
            
            # Фильтр по категории
            if filters.get("category"):
                conditions.append("Category LIKE ?")
                params.append(f"%{filters['category']}%")
            
            # Фильтр по тегам (ищем хотя бы одно совпадение)
            if filters.get("search_tags"):
                tag_conditions = []
                for tag in filters['search_tags']:
                    tag_conditions.append("Tags LIKE ?")
                    params.append(f"%{tag}%")
                conditions.append(f"({' OR '.join(tag_conditions)})")
            
            # Фильтр по цене
            if filters.get("price") == "free":
                conditions.append("(Price LIKE '%Free%' OR Price LIKE '%Бесплатно%')")
            elif filters.get("price") == "paid":
                conditions.append("(Price NOT LIKE '%Free%' AND Price NOT LIKE '%Бесплатно%')")
            
            if conditions:
                query += " AND " + " AND ".join(conditions)

        cursor.execute(query, params)
        events = cursor.fetchall()

        # Преобразуем в список словарей
        events_list = []
        for event in events:
            events_list.append({
                                "Id": event[0],
                "event_city": event[1],
                "event_date": event[2],
                "event_time": event[3],
                "event_location_name": event[4],
                "event_location_url": event[5],  
                "event_name": event[6],
                "event_name_url": event[7],      
                "category": event[8],
                "tags": event[9].split(", ") if event[9] else [],
                "price": event[10]
                # "Id": event[0],
                # "event_city": event[1],
                # "event_date": event[2],
                # "event_time": event[3],
                # "event_location_name": event[4],
                # "event_name": event[5],
                # "category": event[6],
                # "tags": event[7].split(", ") if event[7] else [],
                # "price": event[8]
            })

        return events_list

    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении мероприятий: {e}")
        return []
    finally:
        if conn:
            conn.close()



# Получает бесплатные события для пользователя, отсортированные по количеству показов
def db_get_free_events(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Фильтруем события, где price не содержит цифр, и сортируем по количеству показов
        query = '''
            SELECT e.Id, e.EventDate, e.EventTime, e.EventLocationName, e.EventName, e.Tags, e.Price, COALESCE(up.EventShowCount, 0) AS ShowCount
            FROM Events e
            LEFT JOIN UserPreferences up ON e.Id = up.EventId AND up.UserId = ?
            WHERE e.Price NOT LIKE '%0%'
              AND e.Price NOT LIKE '%1%'
              AND e.Price NOT LIKE '%2%'
              AND e.Price NOT LIKE '%3%'
              AND e.Price NOT LIKE '%4%'
              AND e.Price NOT LIKE '%5%'
              AND e.Price NOT LIKE '%6%'
              AND e.Price NOT LIKE '%7%'
              AND e.Price NOT LIKE '%8%'
              AND e.Price NOT LIKE '%9%'
            ORDER BY ShowCount ASC
            LIMIT 3  -- Ограничиваем количество событий
        '''
        cursor.execute(query, (user_id,))
        events = cursor.fetchall()

        # Преобразуем результат в список словарей
        events_list = []
        for event in events:
            events_list.append({
                "Id": event[0],
                "event_date": event[1],
                "event_time": event[2],
                "event_location_name": event[3],
                "event_name": event[4],
                "tags": event[5],
                "price": event[6],
                "show_count": event[7]  # Количество показов
            })
        
        return events_list
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении мероприятий: {e}")
        return []
    finally:
        if conn:
            conn.close()
            

            
# Возвращает мероприятия по тегу            
def db_get_events_by_tag(tag):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM Events
            WHERE Tags LIKE ?
        ''', (f"%{tag}%",))
        
        events = []
        for row in cursor.fetchall():
            event = {
                "Id": row[0],
                "EventDate": row[1],
                "EventTime": row[2],
                "EventLocationName": row[3],
                "EventName": row[4],
                "Tags": row[5],
                "Price": row[6]
            }
            events.append(event)
        
        return events
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении мероприятий: {e}")
        return []
    finally:
        if conn:
            conn.close()
            

    