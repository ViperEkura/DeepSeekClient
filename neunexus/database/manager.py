import sqlite3
import threading
from contextlib import contextmanager
from typing import List


class SQLiteConnection:
    def __init__(self, db_file: str, timeout: int = 5):
        self.db_file = db_file
        self.timeout = timeout
        self._connection = None
        self._lock = threading.RLock()  # 使用可重入锁

    
    def _create_connection(self):
        """创建新连接"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_file, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接（单例模式）"""
        with self._lock:
            if self._connection is None:
                self._create_connection()
            return self._connection
    
    def close_connection(self):
        """关闭连接"""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None


class DatabaseManager:
    """数据库连接管理器（单连接版本）"""
    
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.pool = SQLiteConnection(db_file)
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = None
        try:
            conn = self.pool.get_connection()
            yield conn 
        finally:
            if conn:
                self.pool.close_connection()
    
    @contextmanager
    def get_cursor(self):
        """上下文管理器用于获取游标，自动处理异常"""
        with self.get_connection() as conn:
            cursor = None
            try:
                cursor = conn.cursor()
                yield cursor
                conn.commit()
            except sqlite3.Error:
                conn.rollback()
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def init_db(self):
        """初始化数据库表"""
        tables = {
            'conversations': """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            """,
            'messages': """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
                )
            """
        }
        
        try:
            with self.get_cursor() as cursor:
                for _, create_sql in tables.items():
                    cursor.execute(create_sql)
        except sqlite3.Error:
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> List[sqlite3.Row]:
        """执行查询并返回结果"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    
    def execute_command(self, query: str, params: tuple = None) -> int:
        """执行命令并返回影响的行数"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount