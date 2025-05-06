import sqlite3
from config import DB_PATH
import logging


logger = logging.getLogger(__name__)


def db_update_user_preference(tg_user_id, event_id, preference):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Прямое обновление предпочтений по TgUserId (без поиска в таблице Users)
        cursor.execute('''
            INSERT INTO UserPreferences (UserId, EventId, Preference)
            VALUES (?, ?, ?)
            ON CONFLICT(UserId, EventId) DO UPDATE SET Preference = excluded.Preference
        ''', (tg_user_id, event_id, preference))

        conn.commit()
        logger.info(f"Обновлено предпочтение: TgUserId={tg_user_id}, EventId={event_id}, Preference={preference}")
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении предпочтения: {e}")
    finally:
        if conn:
            conn.close()


def db_get_user_preferences(user_id):
    """Возвращает словарь {event_id: preference} для указанного пользователя."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT EventId, Preference FROM UserPreferences
            WHERE UserId = ?
        ''', (user_id,))
        
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении предпочтений (UserID: {user_id}): {e}")
        return {}
    finally:
        if conn:
            conn.close()           
            
            
# Скрывает событие для пользователя (Dislike)
def db_hide_event_for_user(user_id, event_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Используем правильные имена столбцов (UserId, EventId)
        cursor.execute('''
            INSERT INTO UserPreferences (UserId, EventId, Preference)
            VALUES (?, ?, 0)
            ON CONFLICT(UserId, EventId) DO UPDATE SET Preference = 0
        ''', (user_id, event_id))
        
        conn.commit()
        logger.info(f"Событие {event_id} скрыто для пользователя {user_id} (Dislike)")
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при скрытии события: {e}")
    finally:
        if conn:
            conn.close()