
from neunexus.database.manager import DatabaseManager
from neunexus.database.repositories import ConversationRepository


class ConversationService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.conversation_repo = ConversationRepository(db_manager)
        
    def create_conversation(self, title: str) -> dict:
        """创建新的对话"""
        if not title or not isinstance(title, str):
            raise ValueError('Title is required and must be a string')
        
        conversation = self.conversation_repo.create(title)
        
        return {
            'conversation_id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at
        }
            
    def delete_conversation(self, conversation_id: int) -> bool:
        """删除对话"""
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError('Conversation not found')
            
        return self.conversation_repo.delete(conversation_id)

    def get_all_conversations(self) -> list:
        """获取所有对话"""
        conversations = self.conversation_repo.get_all()
        
        return [
            {
                'conversation_id': conv.id,
                'title': conv.title,
                'created_at': conv.created_at
            } for conv in conversations
        ]

    def get_conversation_by_id(self, conversation_id: int) -> dict:
        """根据ID获取单个对话"""
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError('Conversation not found')
        
        return {
            'conversation_id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at
        }
        
    def update_conversation_by_id(self, conversation_id: int, title: str) -> dict:
        """更新对话标题"""
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError('Conversation not found')

        if not title or not isinstance(title, str):
            raise ValueError('Title is required and must be a string')
        
        success = self.conversation_repo.update(conversation_id, title)
        if not success:
            raise Exception('Failed to update conversation')
            
        updated_conversation = self.conversation_repo.get_by_id(conversation_id)
        return {
            'conversation_id': updated_conversation.id,
            'title': updated_conversation.title,
            'created_at': updated_conversation.created_at
        }