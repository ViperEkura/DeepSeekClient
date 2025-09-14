from typing import Dict, List, Optional
from neunexus.database import DatabaseManager, ConversationRepository, MessageRepository


class ConversationService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.conversation_repo = ConversationRepository(db_manager)
    
    
    def create_conversation(self, title: str) -> Dict[str, str]:
        conversation = self.conversation_repo.create(title)
        return {
            "id": str(conversation.id),
            "title": conversation.title
        }