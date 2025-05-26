# import sqlite3
import psycopg2
from psycopg2 import sql
from config import DB_PATH
import logging


logger = logging.getLogger(__name__)


def db_update_user_preference(tg_user_id, event_id, preference):
    """Обновление предпочтений пользователя"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_PATH)
        cursor = conn.cursor()

        # Получаем внутренний ID пользователя
        cursor.execute('SELECT "Id" FROM "Users" WHERE "TgUserId" = %s', (tg_user_id,))
        user_record = cursor.fetchone()
        
        if not user_record:
            logger.error(f"Пользователь с TgUserId {tg_user_id} не найден")
            return False

        user_id = user_record[0]

        # Обновление предпочтений
        cursor.execute('''
            INSERT INTO "UserPreferences" ("UserId", "EventId", "Preference")
            VALUES (%s, %s, %s)
            ON CONFLICT ("UserId", "EventId") 
            DO UPDATE SET "Preference" = EXCLUDED."Preference"
        ''', (user_id, event_id, preference))

        conn.commit()
        logger.info(f"Обновлено предпочтение: TgUserId={tg_user_id}, EventId={event_id}, Preference={preference}")
        return True
    
    except psycopg2.Error as e:
        logger.error(f"Ошибка при обновлении предпочтения: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def db_get_user_preferences(user_id):
    """Возвращает словарь {event_id: preference} для указанного пользователя."""
    try:
        conn = psycopg2.connect(DB_PATH)  # Изменено на psycopg2
        cursor = conn.cursor()

        cursor.execute('''
            SELECT EventId, Preference FROM UserPreferences
            WHERE UserId = %s  # Изменен параметр с ? на %s
        ''', (user_id,))
        
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    except psycopg2.Error as e:  # Изменено на psycopg2.Error
        logger.error(f"Ошибка при получении предпочтений (UserID: {user_id}): {e}")
        return {}
    finally:
        if conn:
            conn.close()           
            
            
# Скрывает событие для пользователя (Dislike)
def db_hide_event_for_user(tg_user_id, event_id):
    """Скрывает событие для пользователя (Dislike)"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_PATH)
        cursor = conn.cursor()

        # Получаем внутренний ID пользователя
        cursor.execute('SELECT "Id" FROM "Users" WHERE "TgUserId" = %s', (tg_user_id,))
        user_record = cursor.fetchone()
        
        if not user_record:
            logger.error(f"Пользователь с TgUserId {tg_user_id} не найден")
            return False

        user_id = user_record[0]

        # Обновляем предпочтение
        cursor.execute('''
            INSERT INTO "UserPreferences" ("UserId", "EventId", "Preference")
            VALUES (%s, %s, 0)
            ON CONFLICT("UserId", "EventId") DO UPDATE SET "Preference" = 0
        ''', (user_id, event_id))
        
        conn.commit()
        logger.info(f"Событие {event_id} скрыто для пользователя {tg_user_id} (Dislike)")
        return True
    
    except psycopg2.Error as e:
        logger.error(f"Ошибка при скрытии события: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()