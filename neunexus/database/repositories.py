from abc import ABC, abstractmethod
import sqlite3
from typing import List, Optional, Dict, Any
from neunexus.database.manager import DatabaseManager
from neunexus.database.models import Conversation, Message


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
        with self.db.get_cursor() as cursor:
            cursor.execute("INSERT INTO conversations (title) VALUES (?)", (title,))
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (cursor.lastrowid,))
            row = cursor.fetchone()
        return self._row_to_conversation(row)
    
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
        with self.db.get_cursor() as cursor:
            cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)", 
                           (conversation_id, role, content))
            cursor.execute("SELECT * FROM messages WHERE id = ?", (cursor.lastrowid,))
            row = cursor.fetchone()
        
        return self._row_to_message(row)
    
    def get_by_conversation(self, conversation_id: int) -> List[Message]:
        """获取对话的所有消息"""
        query = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC"
        rows = self.db.execute_query(query, (conversation_id,))
        return [self._row_to_message(row) for row in rows]
    
    def get_recent_by_conversation(self, conversation_id: int, limit: int = 500) -> List[Message]:
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