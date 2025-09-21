from neunexus import NeuNexusApp
from neunexus.database import DatabaseManager
from neunexus.core.client import DeepSeekClient
import json
 

def config_loader(config_path="./config.json"):
    with open(config_path, "r") as f:
        config = json.load(f)
        return config["api_key"], config["init_prompt"]

if __name__ == "__main__":
    api_key, init_prompt = config_loader()
    
    db_manager = DatabaseManager("./neunexus.db")
    client = DeepSeekClient(api_key=api_key, init_prompt=init_prompt)
    app = NeuNexusApp(db_manager, client)
    
    app.run(port=5000)