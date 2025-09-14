from functools import wraps
from typing import Any, Callable
from neunexus.database import DatabaseManager, ConversationRepository, MessageRepository
from flask import Flask, Response, jsonify, request


def handle_errors(func: Callable) -> Callable:
    """处理控制器方法错误的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if args and hasattr(args[0], 'app') and isinstance(args[0].app, Flask):
                args[0].app.logger.error(f"Error in {func.__name__}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    return wrapper


class ConversationService:
    def __init__(self, db_manager: DatabaseManager, app: Flask):
        self.app = app
        self.db_manager = db_manager
        self.conversation_repo = ConversationRepository(db_manager)
        
    def register_routes(self):
        self.app.add_url_rule(
            '/conversations', 
            'create_conversation', 
            self.create_conversation, 
            methods=['POST']
        )
        self.app.add_url_rule(
            '/conversations', 
            'get_all_conversations', 
            self.get_all_conversations, 
            methods=['GET']
        )
        # 添加删除对话的路由
        self.app.add_url_rule(
            '/conversations/<int:conversation_id>', 
            'delete_conversation', 
            self.delete_conversation, 
            methods=['DELETE']
        )

    @handle_errors
    def create_conversation(self) -> Response:
        """创建新的对话"""
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No JSON data provided'}), 400
        
        title = data.get('title')
        if not title or not isinstance(title, str):
            return jsonify({'message': 'Title is required and must be a string'}), 400
        
        # 创建对话
        conversation = self.conversation_repo.create(title)
        
        # 返回响应
        return jsonify({
            'message': 'Conversation created successfully',
            'conversation_id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at
        }), 201
            
        
    @handle_errors
    def delete_conversation(self, conversation_id: int) -> Response:
        """删除对话"""
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'message': 'Conversation not found'}), 404
            
        success = self.conversation_repo.delete(conversation_id)
        
        if success:
            return jsonify({'message': 'Conversation deleted successfully'}), 200
        else:
            return jsonify({'message': 'Failed to delete conversation'}), 500

    @handle_errors
    def get_all_conversations(self) -> Response:
        """获取所有对话"""
        conversations = self.conversation_repo.get_all()
        
        return jsonify([
            {
                'conversation_id': conv.id,
                'title': conv.title,
                'created_at': conv.created_at
            } for conv in conversations
        ]), 200




class MessageService:
    def __init__(self, db_manager: DatabaseManager, app: Flask):
        self.app = app
        self.db_manager = db_manager
        self.message_repo = MessageRepository(db_manager)
        
    def register_routes(self):
        
        pass