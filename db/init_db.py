import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH

def init_db_users():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            UserId INTEGER PRIMARY KEY AUTOINCREMENT,
            CreatedDate DATETIME NOT NULL,
            LastVisitDate DATETIME NOT NULL,
            TgUserId INTEGER UNIQUE NOT NULL,
            Nickname TEXT,
            FirstName TEXT,
            LastName TEXT,
            InviteLink TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db_users()
    
    
def init_db_music_events():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создание таблицы, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS MusicEvents (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            CreatedDate TEXT NOT NULL,
            EventDate TEXT NOT NULL,
            EventTime TEXT NOT NULL,
            EventLocationName TEXT NOT NULL,
            EventLocationAdress TEXT,
            EventLocationUrl TEXT NOT NULL,
            EventName TEXT NOT NULL,
            EventNameUrl TEXT NOT NULL,
            Tags TEXT,
            Price TEXT NOT NULL,
        )
    ''')
    conn.commit()
    conn.close()
        
if __name__ == "__main__":
    init_db_music_events()
    
def init_db_user_preferences():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserPreferences (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            UserId INTEGER NOT NULL,
            EventId INTEGER NOT NULL,
            Preference INTEGER,  -- 1 (Like), 0 (Dislike), NULL (Skip)
            FOREIGN KEY (EventId) REFERENCES Events(Id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db_user_preferences()