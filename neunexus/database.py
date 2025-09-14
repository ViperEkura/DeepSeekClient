import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from contextlib import contextmanager
import threading
from queue import Queue, Empty

@dataclass
class Conversation:
    id: int
    title: str
    created_at: str


@dataclass
class Message:
    id: int
    conversation_id: int
    role: str
    content: str
    timestamp: str


class BaseRepository(ABC):
    """基础仓库抽象类"""
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Any]:
        pass
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Any:
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        pass


class SQLiteConnectionPool:
    def __init__(self, db_file: str, max_connections: int = 5, timeout: int = 5):
        self.db_file = db_file
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool = Queue(max_connections)
        self._connections_created = 0
        self._lock = threading.Lock()
        
        # 预先创建一些连接
        for _ in range(min(2, max_connections)):
            self._create_connection()
    
    def _create_connection(self):
        """创建新连接"""
        conn = sqlite3.connect(self.db_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        self._pool.put(conn)
        with self._lock:
            self._connections_created += 1
    
    def get_connection(self) -> sqlite3.Connection:
        """从池中获取连接"""
        try:
            # 尝试获取现有连接
            return self._pool.get(block=True, timeout=self.timeout)
        except Empty:
            # 如果没有可用连接且可以创建新连接
            with self._lock:
                if self._connections_created < self.max_connections:
                    self._create_connection()
                    return self._pool.get(block=True, timeout=self.timeout)
            # 如果已达到最大连接数，等待
            return self._pool.get(block=True, timeout=self.timeout)
    
    def return_connection(self, conn: sqlite3.Connection):
        """将连接返回池中"""
        try:
            self._pool.put(conn, block=False)
        except:
            # 如果池已满，关闭连接
            conn.close()
            with self._lock:
                self._connections_created -= 1
    
    def close_all(self):
        """关闭所有连接"""
        while not self._pool.empty():
            try:
                conn = self._pool.get(block=False)
                conn.close()
            except Empty:
                break
        with self._lock:
            self._connections_created = 0


class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self, db_file: str, pool_size: int = 5):
        self.db_file = db_file
        self.pool = SQLiteConnectionPool(db_file, max_connections=pool_size)
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
                self.pool.return_connection(conn)
    
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'messages': """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    
    def close_all_connections(self):
        """关闭所有连接"""
        self.pool.close_all()


class ConversationRepository:
    """对话数据访问层"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """根据ID获取对话"""
        query = "SELECT * FROM conversations WHERE id = ?"
        rows = self.db.execute_query(query, (conversation_id,))
        return self._row_to_conversation(rows[0]) if rows else None
    
    def create(self, title: str) -> Conversation:
        """创建新的对话"""
        query = "INSERT INTO conversations (title) VALUES (?)"
        rowcount = self.db.execute_command(query, (title,))
        if rowcount > 0:
            # 获取最后插入的ID
            last_id_query = "SELECT last_insert_rowid() as id"
            result = self.db.execute_query(last_id_query)
            return self.get_by_id(result[0]['id'])
        return None
    
    def get_all(self) -> List[Conversation]:
        """获取所有对话"""
        query = "SELECT * FROM conversations ORDER BY created_at DESC"
        rows = self.db.execute_query(query)
        return [self._row_to_conversation(row) for row in rows]
    
    def update(self, conversation_id: int, title: str) -> bool:
        """更新对话标题"""
        query = "UPDATE conversations SET title = ? WHERE id = ?"
        rowcount = self.db.execute_command(query, (title, conversation_id))
        return rowcount > 0
    
    def delete(self, conversation_id: int) -> bool:
        """删除对话（级联删除消息）"""
        query = "DELETE FROM conversations WHERE id = ?"
        rowcount = self.db.execute_command(query, (conversation_id,))
        return rowcount > 0
    
    def _row_to_conversation(self, row: sqlite3.Row) -> Conversation:
        """将数据库行转换为Conversation对象"""
        return Conversation(
            id=row['id'],
            title=row['title'],
            created_at=row['created_at']
        )


class MessageRepository:
    """消息数据访问层"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_by_id(self, message_id: int) -> Optional[Message]:
        """根据ID获取消息"""
        query = "SELECT * FROM messages WHERE id = ?"
        rows = self.db.execute_query(query, (message_id,))
        return self._row_to_message(rows[0]) if rows else None
    
    def create(self, conversation_id: int, role: str, content: str) -> Message:
        """创建新消息"""
        query = "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)"
        rowcount = self.db.execute_command(query, (conversation_id, role, content))
        if rowcount > 0:
            last_id_query = "SELECT last_insert_rowid() as id"
            result = self.db.execute_query(last_id_query)
            return self.get_by_id(result[0]['id'])
        return None
    
    def get_by_conversation(self, conversation_id: int) -> List[Message]:
        """获取对话的所有消息"""
        query = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC"
        rows = self.db.execute_query(query, (conversation_id,))
        return [self._row_to_message(row) for row in rows]
    
    def get_recent_by_conversation(self, conversation_id: int, limit: int = 10) -> List[Message]:
        """获取对话的最近消息"""
        query = """
            SELECT * FROM messages 
            WHERE conversation_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        rows = self.db.execute_query(query, (conversation_id, limit))
        return [self._row_to_message(row) for row in reversed(rows)]
    
    def delete(self, message_id: int) -> bool:
        """删除消息"""
        query = "DELETE FROM messages WHERE id = ?"
        rowcount = self.db.execute_command(query, (message_id,))
        return rowcount > 0
    
    def delete_by_conversation(self, conversation_id: int) -> bool:
        """删除对话的所有消息"""
        query = "DELETE FROM messages WHERE conversation_id = ?"
        rowcount = self.db.execute_command(query, (conversation_id,))
        return rowcount > 0
    
    def _row_to_message(self, row: sqlite3.Row) -> Message:
        """将数据库行转换为Message对象"""
        return Message(
            id=row['id'],
            conversation_id=row['conversation_id'],
            role=row['role'],
            content=row['content'],
            timestamp=row['timestamp']
        )