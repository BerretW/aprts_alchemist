# database.py
import pymysql
from pymysql.cursors import DictCursor
import config

class DatabaseManager:
    def __init__(self):
        self.conn = None

    def connect(self):
        try:
            cfg = config.DB_CONFIG.copy()
            if 'cursorclass' in cfg:
                del cfg['cursorclass']
            
            self.conn = pymysql.connect(**cfg, cursorclass=DictCursor)
            return True
        except Exception as e:
            print(f"Chyba pripojeni k DB: {e}")
            return False

    def fetch_all(self, query, params=None):
        if not self.conn or not self.conn.open:
            if not self.connect(): return []
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            print(f"SQL Fetch Error: {e}")
            self.connect()
            return []

    def execute(self, query, params=None):
        if not self.conn or not self.conn.open:
            if not self.connect(): return False
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"SQL Execute Error: {e}")
            self.conn.rollback()
            return False

# Vytvoření jedné globální instance
db = DatabaseManager()