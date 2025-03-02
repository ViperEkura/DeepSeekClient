from openai import OpenAI
from typing import List, Tuple

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
    
    def batch_generate(
        self, 
        user_messages: List[str], 
        histories: List[List[Tuple]] = None
    ) -> Tuple[List[str], List[List[dict]]]:
        
        if histories is None:
            processed_histories = []
            for _ in user_messages:
                new_history = [{"role": "system", "content": self.init_prompt}]
                processed_histories.append(new_history)

        responses = []
        updated_histories = []

        for user_msg, history in zip(user_messages, histories):
            history.append({"role": "user", "content": user_msg})
            response = self.client.chat.completions.create(
                model=self.model,
                messages=history,
                stream=False
            )
            
            assistant_content = response.choices[0].message.content
            history.append({"role": "assistant", "content": assistant_content})
            
            responses.append(assistant_content)
            updated_histories.append(history)

        return responses, updated_histories
    

class DeepSeekProcessor:
    def __init__(self, client: DeepSeekClient):
        self.client = client
    
    def processor(questions: List[str], histories: List[List[Tuple]]) -> List[str]:
        pass
        