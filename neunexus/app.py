from flask import Flask
from flask_cors import CORS
from neunexus.database import DatabaseManager
from neunexus.service import ConversationService, MessageService
from neunexus.client import DeepSeekClient


class NeuNexusApp:
    def __init__(
        self, 
        db_manager: DatabaseManager,
        client: DeepSeekClient
    ):
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.conversation_service = ConversationService(db_manager, self.app)
        self.message_service = MessageService(db_manager, self.app, client)
        
        self.conversation_service.register_routes()
        self.message_service.register_routes()
        
    def run(self, host=None, port=None, debug=True):
        self.app.run(host=host, port=port, debug=debug)