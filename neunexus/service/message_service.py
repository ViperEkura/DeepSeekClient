import json
from typing import Any
from neunexus.client import DeepSeekClient
from neunexus.database.manager import DatabaseManager
from neunexus.database.repositories import MessageRepository


class MessageService:
    """消息服务层，处理消息相关的业务逻辑"""
    
    def __init__(self, db_manager: DatabaseManager, client: DeepSeekClient):
        self.client = client
        self.db_manager = db_manager
        self.message_repo = MessageRepository(db_manager)
    
    def get_recent_messages(self, conversation_id: int, limit: int = 500) -> list:
        """获取对话的最近消息"""
        messages = self.message_repo.get_recent_by_conversation(conversation_id, limit)
        
        return [
            {
                'message_id': msg.id,
                'conversation_id': msg.conversation_id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp
            } for msg in messages
        ]
    
    def create_message(self, conversation_id: int, role: str, content: str) -> dict:
        """创建新消息"""
        if not role or not isinstance(role, str):
            raise ValueError('Role is required and must be a string')
        
        if not content or not isinstance(content, str):
            raise ValueError('Content is required and must be a string')
        
        message = self.message_repo.create(conversation_id, role, content)
        
        if not message:
            raise Exception('Failed to create message')
        
        return {
            'message_id': message.id,
            'conversation_id': message.conversation_id,
            'role': message.role,
            'content': message.content,
            'timestamp': message.timestamp
        }
    
    def get_message(self, message_id: int) -> dict:
        """根据ID获取特定消息"""
        message = self.message_repo.get_by_id(message_id)
        if not message:
            raise ValueError('Message not found')
        
        return {
            'message_id': message.id,
            'conversation_id': message.conversation_id,
            'role': message.role,
            'content': message.content,
            'timestamp': message.timestamp
        }
    
    def stream_message(self, conversation_id: int, content: str) -> Any:
        """流式处理消息"""
        if not content or not isinstance(content, str):
            raise ValueError('Content is required and must be a string')

        histories = self.message_repo.get_recent_by_conversation(conversation_id)
        history_messages = [{"role": msg.role, "content": msg.content} for msg in histories]

        full_response = []
        try:
            for chunk, _ in self.client.stream_chat(content, histories=history_messages):
                full_response.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            self.message_repo.create(conversation_id, 'system', "".join(full_response))

        except Exception as e:
            raise Exception(f"Stream processing failed: {str(e)}")
        
    def delete_message(self, message_id: int) -> bool:
        """删除特定消息"""
        message = self.message_repo.get_by_id(message_id)
        if not message:
            raise ValueError('Message not found')
        
        return self.message_repo.delete(message_id)
    
    def delete_conversation_messages(self, conversation_id: int) -> bool:
        """删除对话的所有消息"""
        return self.message_repo.delete_by_conversation(conversation_id)

    def get_conversation_messages(self, conversation_id: int) -> list:
        """获取对话的所有消息"""
        messages = self.message_repo.get_by_conversation(conversation_id)
        
        return [
            {
                'message_id': msg.id,
                'conversation_id': msg.conversation_id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp
            } for msg in messages
        ]