from neunexus.service import DeepSeekChatApp
import json
 

def config_loader(config_path="./config.json"):
    with open(config_path, "r") as f:
        config = json.load(f)
        return config["api_key"], config["base_url"], config["init_prompt"]


if __name__ == "__main__":
    api_key, base_url, init_prompt = config_loader()
    client = DeepSeekChatApp(api_key, base_url)
    client.run()