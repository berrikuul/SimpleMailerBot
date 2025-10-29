import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path='bot.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_username TEXT,
                message_text TEXT,
                image_url TEXT,
                scheduled_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent BOOLEAN DEFAULT FALSE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mailing_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_username TEXT,
                message_text TEXT,
                image_url TEXT,
                scheduled_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent BOOLEAN DEFAULT FALSE
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована")

    def add_subscriber(self, user_id, username, first_name, last_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO subscribers 
            (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        conn.commit()
        conn.close()
        return True

    def get_all_subscribers(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM subscribers')
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    # Методы для постов в группу
    def add_group_post(self, author_username, message_text, image_url, scheduled_time):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO group_posts 
            (author_username, message_text, image_url, scheduled_time)
            VALUES (?, ?, ?, ?)
        ''', (author_username, message_text, image_url, scheduled_time))
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return post_id

    def get_pending_group_posts(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, author_username, message_text, image_url, scheduled_time 
            FROM group_posts 
            WHERE sent = FALSE AND scheduled_time <= datetime('now')
        ''')
        posts = cursor.fetchall()
        conn.close()
        return posts

    def get_all_group_posts(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, author_username, message_text, image_url, scheduled_time, sent
            FROM group_posts 
            ORDER BY scheduled_time
        ''')
        posts = cursor.fetchall()
        conn.close()
        return posts

    def mark_group_post_as_sent(self, post_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE group_posts SET sent = TRUE WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return True

    def delete_group_post(self, post_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM group_posts WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return True

    # Методы для рассылок
    def add_mailing_post(self, author_username, message_text, image_url, scheduled_time):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO mailing_posts 
            (author_username, message_text, image_url, scheduled_time)
            VALUES (?, ?, ?, ?)
        ''', (author_username, message_text, image_url, scheduled_time))
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return post_id

    def get_pending_mailing_posts(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, author_username, message_text, image_url, scheduled_time 
            FROM mailing_posts 
            WHERE sent = FALSE AND scheduled_time <= datetime('now')
        ''')
        posts = cursor.fetchall()
        conn.close()
        return posts

    def get_all_mailing_posts(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, author_username, message_text, image_url, scheduled_time, sent
            FROM mailing_posts 
            ORDER BY scheduled_time
        ''')
        posts = cursor.fetchall()
        conn.close()
        return posts

    def mark_mailing_post_as_sent(self, post_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE mailing_posts SET sent = TRUE WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return True

    def delete_mailing_post(self, post_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM mailing_posts WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return True