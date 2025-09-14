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
        
    def register_routes(self) -> Flask:
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
        self.app.add_url_rule(
            '/conversations/<int:conversation_id>', 
            'get_conversation_by_id', 
            self.get_conversation_by_id, 
            methods=['GET']
        )
        self.app.add_url_rule(
            '/conversations/<int:conversation_id>', 
            'delete_conversation', 
            self.delete_conversation, 
            methods=['DELETE']
        )
        self.app.add_url_rule(
            '/conversations/<int:conversation_id>', 
            'update_conversation', 
            self.update_conversation_by_id, 
            methods=['PUT']
        )
    
        return self.app

    @handle_errors
    def create_conversation(self) -> Response:
        """创建新的对话"""
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No JSON data provided'}), 400
        
        title = data.get('title')
        if not title or not isinstance(title, str):
            return jsonify({'message': 'Title is required and must be a string'}), 400
        
        conversation = self.conversation_repo.create(title)
        
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

    @handle_errors
    def get_conversation_by_id(self, conversation_id: int) -> Response:
        """根据ID获取单个对话"""
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'message': 'Conversation not found'}), 404
        
        return jsonify({
            'conversation_id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at
        }), 200
        
    @handle_errors
    def update_conversation_by_id(self, conversation_id: int, title:str) -> Response:
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'message': 'Conversation not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No JSON data provided'}), 400

        title = data.get('title')
        if not title or not isinstance(title, str):
            return jsonify({'message': 'Title is required and must be a string'}), 400
        
        success = self.conversation_repo.update(conversation_id, title)
        if success:
            updated_conversation = self.conversation_repo.get_by_id(conversation_id)
            return jsonify({
                'message': 'Conversation updated successfully',
                'conversation_id': updated_conversation.id,
                'title': updated_conversation.title,
                'created_at': updated_conversation.created_at
            }), 200
        else:
            return jsonify({'message': 'Failed to update conversation'}), 500


class MessageService:
    """消息服务层，处理消息相关的HTTP请求"""
    
    def __init__(self, db_manager: DatabaseManager, app: Flask):
        self.app = app
        self.db_manager = db_manager
        self.message_repo = MessageRepository(db_manager)
        
    def register_routes(self) -> Flask:
        """注册消息相关的路由"""
        
        # 获取对话的最近消息
        self.app.add_url_rule(
            '/conversations/<int:conversation_id>/messages/recent', 
            'get_recent_messages', 
            self.get_recent_messages, 
            methods=['GET']
        )
        
        # 创建新消息
        self.app.add_url_rule(
            '/conversations/<int:conversation_id>/messages', 
            'create_message', 
            self.create_message, 
            methods=['POST']
        )
        
        # 获取特定消息
        self.app.add_url_rule(
            '/messages/<int:message_id>', 
            'get_message', 
            self.get_message, 
            methods=['GET']
        )
        
        # 删除特定消息
        self.app.add_url_rule(
            '/messages/<int:message_id>', 
            'delete_message', 
            self.delete_message, 
            methods=['DELETE']
        )

        # 获取对话的所有消息
        self.app.add_url_rule(
            '/conversations/<int:conversation_id>/messages', 
            'get_conversation_messages', 
            self.get_conversation_messages, 
            methods=['GET']
        )
        
        # 删除对话的所有消息
        self.app.add_url_rule(
            '/conversations/<int:conversation_id>/messages', 
            'delete_conversation_messages', 
            self.delete_conversation_messages, 
            methods=['DELETE']
        )
        
        return self.app
    
    @handle_errors
    def get_recent_messages(self, conversation_id: int) -> Response:
        """获取对话的最近消息"""
        # 获取可选的limit参数
        limit = request.args.get('limit', default=10, type=int)
        
        messages = self.message_repo.get_recent_by_conversation(conversation_id, limit)
        
        return jsonify([
            {
                'message_id': msg.id,
                'conversation_id': msg.conversation_id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp
            } for msg in messages
        ]), 200
    
    @handle_errors
    def create_message(self, conversation_id: int) -> Response:
        """创建新消息"""
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No JSON data provided'}), 400
        
        role = data.get('role')
        content = data.get('content')
        
        # 验证必需字段
        if not role or not isinstance(role, str):
            return jsonify({'message': 'Role is required and must be a string'}), 400
        
        if not content or not isinstance(content, str):
            return jsonify({'message': 'Content is required and must be a string'}), 400
        
        # 创建消息
        message = self.message_repo.create(conversation_id, role, content)
        
        if not message:
            return jsonify({'message': 'Failed to create message'}), 500
        
        # 返回响应
        return jsonify({
            'message': 'Message created successfully',
            'message_id': message.id,
            'conversation_id': message.conversation_id,
            'role': message.role,
            'content': message.content,
            'timestamp': message.timestamp
        }), 201
    
    @handle_errors
    def get_message(self, message_id: int) -> Response:
        """根据ID获取特定消息"""
        message = self.message_repo.get_by_id(message_id)
        if not message:
            return jsonify({'message': 'Message not found'}), 404
        
        return jsonify({
            'message_id': message.id,
            'conversation_id': message.conversation_id,
            'role': message.role,
            'content': message.content,
            'timestamp': message.timestamp
        }), 200
    
    @handle_errors
    def delete_message(self, message_id: int) -> Response:
        """删除特定消息"""
        message = self.message_repo.get_by_id(message_id)
        if not message:
            return jsonify({'message': 'Message not found'}), 404
        
        success = self.message_repo.delete(message_id)
        
        if success:
            return jsonify({'message': 'Message deleted successfully'}), 200
        else:
            return jsonify({'message': 'Failed to delete message'}), 500
    
    @handle_errors
    def delete_conversation_messages(self, conversation_id: int) -> Response:
        """删除对话的所有消息"""
        
        success = self.message_repo.delete_by_conversation(conversation_id)
        
        if success:
            return jsonify({'message': 'All messages in conversation deleted successfully'}), 200
        else:
            return jsonify({'message': 'Failed to delete messages'}), 500

    @handle_errors
    def get_conversation_messages(self, conversation_id: int) -> Response:
        """获取对话的所有消息"""
        messages = self.message_repo.get_by_conversation(conversation_id)
        
        return jsonify([
            {
                'message_id': msg.id,
                'conversation_id': msg.conversation_id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp
            } for msg in messages
        ]), 200
        

        

class NeuNexusApp:
    def __init__(self, db_manager: DatabaseManager):
        self.app = Flask(__name__)
        self.conversation_service = ConversationService(db_manager, self.app)
        self.message_service = MessageService(db_manager, self.app)
        
        self.conversation_service.register_routes()
        self.message_service.register_routes()
        
    def run(self, host, port, debug=True):
        self.app.run(host=host, port=port, debug=debug)