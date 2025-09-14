import sqlite3
from dataclasses import dataclass
from typing import List, Optional
    

class DatabaseManager:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row 
        
    def init_db(self):
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
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """
        }
        
        cursor = self.conn.cursor()
        for _, create_sql in tables.items():
            cursor.execute(create_sql)
        self.conn.commit()

    def close(self):
        self.conn.close()


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


class ConversationService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def create_conversation(self, title: str) -> Conversation:
        """创建新的对话"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            (title,)
        )
        self.db_manager.conn.commit()
        return self.get_conversation(cursor.lastrowid)

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """根据ID获取对话"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        row = cursor.fetchone()
        if row:
            return Conversation(
                id=row['id'],
                title=row['title'],
                created_at=row['created_at']
            )
        return None

    def get_all_conversations(self) -> List[Conversation]:
        """获取所有对话"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("SELECT * FROM conversations ORDER BY created_at DESC")
        conversations = []
        for row in cursor.fetchall():
            conversations.append(Conversation(
                id=row['id'],
                title=row['title'],
                created_at=row['created_at']
            ))
        return conversations

    def update_conversation_title(self, conversation_id: int, new_title: str) -> bool:
        """更新对话标题"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "UPDATE conversations SET title = ? WHERE id = ?",
            (new_title, conversation_id)
        )
        self.db_manager.conn.commit()
        return cursor.rowcount > 0

    def delete_conversation(self, conversation_id: int) -> bool:
        """删除对话及其所有消息"""
        cursor = self.db_manager.conn.cursor()
        # 先删除相关消息
        cursor.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )
        # 再删除对话
        cursor.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        self.db_manager.conn.commit()
        return cursor.rowcount > 0


class MessageService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def add_message(self, conversation_id: int, role: str, content: str) -> Message:
        """添加消息"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content)
        )
        self.db_manager.conn.commit()
        return self.get_message(cursor.lastrowid)

    def get_message(self, message_id: int) -> Optional[Message]:
        """根据ID获取消息"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE id = ?",
            (message_id,)
        )
        row = cursor.fetchone()
        if row:
            return Message(
                id=row['id'],
                conversation_id=row['conversation_id'],
                role=row['role'],
                content=row['content'],
                timestamp=row['timestamp']
            )
        return None

    def get_messages_by_conversation(self, conversation_id: int) -> List[Message]:
        """获取对话的所有消息"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,)
        )
        messages = []
        for row in cursor.fetchall():
            messages.append(Message(
                id=row['id'],
                conversation_id=row['conversation_id'],
                role=row['role'],
                content=row['content'],
                timestamp=row['timestamp']
            ))
        return messages

    def get_recent_messages(self, conversation_id: int, limit: int = 10) -> List[Message]:
        """获取最近的几条消息"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT ?",
            (conversation_id, limit)
        )
        messages = []
        for row in cursor.fetchall():
            messages.append(Message(
                id=row['id'],
                conversation_id=row['conversation_id'],
                role=row['role'],
                content=row['content'],
                timestamp=row['timestamp']
            ))
        return list(reversed(messages))  # 按时间顺序返回

    def delete_message(self, message_id: int) -> bool:
        """删除消息"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "DELETE FROM messages WHERE id = ?",
            (message_id,)
        )
        self.db_manager.conn.commit()
        return cursor.rowcount > 0

    def delete_messages_by_conversation(self, conversation_id: int) -> bool:
        """删除对话的所有消息"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )
        self.db_manager.conn.commit()
        return cursor.rowcount > 0