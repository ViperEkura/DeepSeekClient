from flask import Flask, Response, jsonify, request
from neunexus.service import ConversationService
from neunexus.api.base import handle_errors




class ConversationController:
    def __init__(self, app: Flask, conversation_service: ConversationService):
        self.app = app
        self.conversation_service = conversation_service
        
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
        conversation = self.conversation_service.create_conversation(title)
        
        return jsonify({
            'message': 'Conversation created successfully',
            **conversation
        }), 201
            
    @handle_errors
    def delete_conversation(self, conversation_id: int) -> Response:
        """删除对话"""
        success = self.conversation_service.delete_conversation(conversation_id)
        
        if success:
            return jsonify({'message': 'Conversation deleted successfully'}), 200
        else:
            return jsonify({'message': 'Failed to delete conversation'}), 500

    @handle_errors
    def get_all_conversations(self) -> Response:
        """获取所有对话"""
        conversations = self.conversation_service.get_all_conversations()
        return jsonify(conversations), 200

    @handle_errors
    def get_conversation_by_id(self, conversation_id: int) -> Response:
        """根据ID获取单个对话"""
        conversation = self.conversation_service.get_conversation_by_id(conversation_id)
        return jsonify(conversation), 200
        
    @handle_errors
    def update_conversation_by_id(self, conversation_id: int) -> Response:
        """更新对话标题"""
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No JSON data provided'}), 400

        title = data.get('title')
        updated_conversation = self.conversation_service.update_conversation_by_id(conversation_id, title)
        
        return jsonify({
            'message': 'Conversation updated successfully',
            **updated_conversation
        }), 200
