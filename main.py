from openai import OpenAI
from typing import List, Tuple
import json


class DeepSeekClient:
    def __init__(self, api_key, base_url, model="deepseek-chat", init_prompt="你是一个人工智能助手"):
        self.model = model
        self.init_prompt = init_prompt
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def stream_chat(self, user_message: str, histories: List[Tuple]=None):
        if histories is None:
            histories = []

        if isinstance(histories, list) and len(histories) == 0:
            histories = [{"role": "system", "content": self.init_prompt}]
            
        histories.append({"role": "user", "content": user_message})
        assistant_message = {"role": "assistant", "content": ""}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=histories,
            stream=True,
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                assistant_message["content"] += content
                yield content, histories
                
        histories.append(assistant_message)
        
        yield "\n", histories
        
def generate(self, user_message: str, histories: List[Tuple]=None):
    if histories is None:
        histories = []

    if isinstance(histories, list) and len(histories) == 0:
        histories = [{"role": "system", "content": self.init_prompt}]
        
    histories.append({"role": "user", "content": user_message})
    
    response = self.client.chat.completions.create(
        model=self.model,
        messages=histories,
        stream=False,  # 非流式响应
    )
    
    assistant_message = {"role": "assistant", "content": response.choices[0].message.content}
    histories.append(assistant_message)
    
    return assistant_message["content"], histories
        
        
        
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
        
        print(history)