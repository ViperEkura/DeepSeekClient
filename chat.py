from core.deeoseek_client import DeepSeekClient
import json

def save_histoty(histories, output_path):
    with open(output_path, "w") as f:
        json.dump(histories, f)
        
def config_loader(config_path="./config.json"):
    with open(config_path, "r") as f:
        config = json.load(f)
        return config["api_key"], config["base_url"], config["init_prompt"]


if __name__ == "__main__":
    api_key, base_url, init_prompt = config_loader()
    client = DeepSeekClient(api_key=api_key, base_url=base_url, init_prompt=init_prompt)
    history = []
    
    while True:
        user_input = input(">> ")
        if user_input.lower() == "!exit":
            break
        for chunk, history in client.stream_chat(user_input, histories=history):
            print(chunk, end="", flush=True)