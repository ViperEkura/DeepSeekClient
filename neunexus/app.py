from flask import Flask
from flask_cors import CORS
from neunexus.database import DatabaseManager
from neunexus.api import ConversationController, MessageController
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
        
        conversation_service = ConversationService(db_manager)
        message_service = MessageService(db_manager, client)
        
        conversation_controller = ConversationController(self.app, conversation_service)
        message_controller = MessageController(self.app, message_service)
        
        conversation_controller.register_routes()
        message_controller.register_routes()
        
    def run(self, host=None, port=None, debug=True):
        self.app.run(host=host, port=port, debug=debug)