import sqlite3
from datetime import datetime
from config import DB_PATH
import logging

logger = logging.getLogger(__name__)


# # Регистрирует нового пользователя
# def db_update_users(tg_user_id: int, user_nickname: str, user_first_name: str, 
#                    user_last_name: str, invite_link: str = None) -> int:
#     """
#     Обновляет или создает запись пользователя в таблице Users.
#     Возвращает внутренний UserId.
#     """
#     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     conn = None

#     try:
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()
        
#         # Проверяем, существует ли пользователь
#         cursor.execute('SELECT Id FROM Users WHERE TgUserId = ?', (tg_user_id,))
#         existing_user = cursor.fetchone()
        
#         if existing_user:
#             # Обновляем LastVisitDate для существующего пользователя
#             cursor.execute('''
#                 UPDATE Users 
#                 SET LastVisitDate = ?, Nickname = ?, FirstName = ?, LastName = ?, InviteLink = ?
#                 WHERE TgUserId = ?
#             ''', (now, user_nickname, user_first_name, user_last_name, invite_link, tg_user_id))
#             user_id = existing_user[0]  # Возвращаем существующий UserId
#         else:
#             # Создаем новую запись
#             cursor.execute('''
#                 INSERT INTO Users 
#                 (CreatedDate, LastVisitDate, TgUserId, Nickname, FirstName, LastName, InviteLink)
#                 VALUES (?, ?, ?, ?, ?, ?, ?)
#             ''', (now, now, tg_user_id, user_nickname, user_first_name, user_last_name, invite_link))
#             user_id = cursor.lastrowid  # Возвращаем новый UserId
      
#         conn.commit()
#         logger.info(f"User {user_nickname} updated in database. Id={user_id}")
#         return user_id
        
#     except sqlite3.Error as e:
#         logger.error(f"Ошибка БД: {str(e)}")
#         raise
#     finally:
#         if conn:
#             conn.close()
            
 
 
 
def db_update_users(tg_user_id: int, user_nickname: str, user_first_name: str, 
                   user_last_name: str, invite_link: str = None) -> None:
    """
    Обновляет или создает запись пользователя в таблице Users.
    Работает только с TgUserId, не возвращает внутренний ID.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Упрощенный UPSERT за один запрос
        cursor.execute('''
            INSERT INTO Users 
            (CreatedDate, LastVisitDate, TgUserId, Nickname, FirstName, LastName, InviteLink)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(TgUserId) DO UPDATE SET
                LastVisitDate = excluded.LastVisitDate,
                Nickname = excluded.Nickname,
                FirstName = excluded.FirstName,
                LastName = excluded.LastName,
                InviteLink = excluded.InviteLink
        ''', (now, now, tg_user_id, user_nickname, user_first_name, user_last_name, invite_link))
      
        conn.commit()
        logger.info(f"User {user_nickname} (TgID: {tg_user_id}) updated")

    except sqlite3.Error as e:
        logger.error(f"Ошибка БД при обновлении пользователя {tg_user_id}: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()
 
 
 
def db_get_user_city(user_id):
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT CurrentCity FROM Users WHERE TgUserId = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result [0] if result else None




def db_update_user_city(user_id: int, city: str) -> bool:
    """
    Обновляет город пользователя в БД.
    Возвращает True, если операция успешна, иначе False.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Пытаемся обновить город для существующего пользователя
            cursor.execute('UPDATE Users SET CurrentCity = ? WHERE TgUserId = ?', (city, user_id))
            if cursor.rowcount > 0:
                logger.info(f"Updated CurrentCity to '{city}' for User {user_id}")
                return True  # Успешное обновление

            # Если пользователь не найден, создаем новую запись
            cursor.execute('INSERT INTO Users (TgUserId, CurrentCity) VALUES (?, ?)', (user_id, city))
            logger.info(f"Inserted new user {user_id} with city '{city}'")
            return True  # Успешное создание

    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении города для user_id={user_id}: {e}")
        return False  # Ошибка


            
# Возвращает данные по пользователю из таблицы Users            
def db_get_user_by_id(user_id):
    """
    Возвращает данные пользователя по его внутреннему UserId.
    :param user_id: Внутренний идентификатор пользователя (UserId).
    :return: Словарь с данными пользователя или None, если пользователь не найден.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Выполняем запрос к таблице Users
        cursor.execute('''
            SELECT Id, TgUserId, Nickname, FirstName, LastName, CreatedDate, LastVisitDate, InviteLink
            FROM Users
            WHERE Id = ?
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
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        return None
    finally:
        if conn:
            conn.close()