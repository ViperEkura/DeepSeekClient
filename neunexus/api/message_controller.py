
import json
from flask import Flask, Response, jsonify, request, stream_with_context
from neunexus.service import MessageService
from neunexus.api.base import handle_errors


class MessageController:
    """消息控制器，处理消息相关的HTTP请求"""
    
    def __init__(self, app: Flask, message_service: MessageService):
        self.app = app
        self.message_service = message_service
        
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
        
        # 添加流式消息路由
        self.app.add_url_rule(
            '/conversations/<int:conversation_id>/stream',
            'stream_message',
            self.stream_message,
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
        limit = request.args.get('limit', default=500, type=int)
        messages = self.message_service.get_recent_messages(conversation_id, limit)
        return jsonify(messages), 200
    
    @handle_errors
    def create_message(self, conversation_id: int) -> Response:
        """创建新消息"""
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No JSON data provided'}), 400
        
        role = data.get('role')
        content = data.get('content')
        
        message = self.message_service.create_message(conversation_id, role, content)
        
        return jsonify({
            'message': 'Message created successfully',
            **message
        }), 201
    
    @handle_errors
    def get_message(self, message_id: int) -> Response:
        """根据ID获取特定消息"""
        message = self.message_service.get_message(message_id)
        return jsonify(message), 200
    
    @handle_errors
    def stream_message(self, conversation_id: int) -> Response:
        """POST 流式处理消息(fetch 消费)"""
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No JSON data provided'}), 400

        content = data.get('content')
        
        def generate():
            try:
                for chunk in self.message_service.stream_message(conversation_id, content):
                    yield chunk
            except Exception as e:
                self.app.logger.error(f"Stream error: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': 'Stream processing failed'})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache'}
        )
    
    @handle_errors
    def delete_message(self, message_id: int) -> Response:
        """删除特定消息"""
        success = self.message_service.delete_message(message_id)
        
        if success:
            return jsonify({'message': 'Message deleted successfully'}), 200
        else:
            return jsonify({'message': 'Failed to delete message'}), 500
    
    @handle_errors
    def delete_conversation_messages(self, conversation_id: int) -> Response:
        """删除对话的所有消息"""
        success = self.message_service.delete_conversation_messages(conversation_id)
        
        if success:
            return jsonify({'message': 'All messages in conversation deleted successfully'}), 200
        else:
            return jsonify({'message': 'Failed to delete messages'}), 500

    @handle_errors
    def get_conversation_messages(self, conversation_id: int) -> Response:
        """获取对话的所有消息"""
        messages = self.message_service.get_conversation_messages(conversation_id)
        return jsonify(messages), 200