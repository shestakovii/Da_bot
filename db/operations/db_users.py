# import sqlite3
import psycopg2
from datetime import datetime
from config import DB_PATH
import logging
from psycopg2 import sql

logger = logging.getLogger(__name__)


 
def db_update_users(tg_user_id: int, user_nickname: str, user_first_name: str, 
                   user_last_name: str, invite_link: str = None) -> None:
    """
    Обновляет или создает запись пользователя в таблице Users.
    Работает только с TgUserId, не возвращает внутренний ID.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = None

    try:
        # Подключение к PostgreSQL
        conn = psycopg2.connect(**DB_PATH)
        cursor = conn.cursor()
        
        # UPSERT для PostgreSQL
        query = """
            INSERT INTO "Users" 
            ("CreatedDate", "LastVisitDate", "TgUserId", "Nickname", 
             "FirstName", "LastName", "InviteLink")
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ("TgUserId") DO UPDATE SET
                "LastVisitDate" = EXCLUDED."LastVisitDate",
                "Nickname" = EXCLUDED."Nickname",
                "FirstName" = EXCLUDED."FirstName",
                "LastName" = EXCLUDED."LastName",
                "InviteLink" = EXCLUDED."InviteLink"
        """
        
        cursor.execute(query, (now, now, tg_user_id, user_nickname, 
                             user_first_name, user_last_name, invite_link))
      
        conn.commit()
        logger.info(f"User {user_nickname} (TgID: {tg_user_id}) updated")

    except psycopg2.Error as e:
        logger.error(f"Ошибка БД при обновлении пользователя {tg_user_id}: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
 
 
 
def db_get_user_city(user_id):
    conn = None
    try:
        conn = psycopg2.connect(**DB_PATH)
        cursor = conn.cursor()
        
        # Используем кавычки для сохранения регистра имен таблицы и столбцов
        cursor.execute(
            'SELECT "CurrentCity" FROM "Users" WHERE "TgUserId" = %s', 
            (user_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
        
    except psycopg2.Error as e:
        logger.error(f"Ошибка при получении города пользователя {user_id}: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()




def db_update_user_city(user_id: int, city: str) -> bool:
    """
    Обновляет город пользователя в БД.
    Возвращает True, если операция успешна, иначе False.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_PATH)
        cursor = conn.cursor()

        # Пытаемся обновить город для существующего пользователя
        cursor.execute(
            'UPDATE "Users" SET "CurrentCity" = %s WHERE "TgUserId" = %s', 
            (city, user_id)
        )
        
        if cursor.rowcount > 0:
            conn.commit()
            logger.info(f"Updated CurrentCity to '{city}' for User {user_id}")
            return True

        # Если пользователь не найден, создаем новую запись
        cursor.execute(
            'INSERT INTO "Users" ("TgUserId", "CurrentCity") VALUES (%s, %s)',
            (user_id, city)
        )
        conn.commit()
        logger.info(f"Inserted new user {user_id} with city '{city}'")
        return True

    except psycopg2.Error as e:
        logger.error(f"Ошибка при обновлении города для user_id={user_id}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

            
def db_get_user_by_id(user_id):
    """
    Возвращает данные пользователя по его внутреннему UserId.
    :param user_id: Внутренний идентификатор пользователя (UserId).
    :return: Словарь с данными пользователя или None, если пользователь не найден.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_PATH)
        cursor = conn.cursor()

        # Выполняем запрос к таблице Users с сохранением регистра
        cursor.execute('''
            SELECT "Id", "TgUserId", "Nickname", "FirstName", "LastName", 
                   "CreatedDate", "LastVisitDate", "InviteLink"
            FROM "Users"
            WHERE "Id" = %s
        ''', (user_id,))
        
        # Получаем данные пользователя
        user = cursor.fetchone()
        if user:
            return {
                "Id": user[0],
                "TgUserId": user[1],
                "Nickname": user[2],
                "FirstName": user[3],
                "LastName": user[4],
                "CreatedDate": user[5],
                "LastVisitDate": user[6],
                "InviteLink": user[7]
            }
        return None
    
    except psycopg2.Error as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        return None
    finally:
        if conn:
            conn.close()