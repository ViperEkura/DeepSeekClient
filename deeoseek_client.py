from openai import OpenAI
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

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
            stream=False, 
        )
        
        assistant_message = {"role": "assistant", "content": response.choices[0].message.content}
        histories.append(assistant_message)
        
        return assistant_message["content"], histories
    
    def batch_generate(
        self, 
        user_messages: List[str], 
        batch_histories: List[List[Tuple]] = None
    ) -> Tuple[List[str], List[List[dict]]]:
        
        if batch_histories is None:
            batch_histories = []
            for _ in user_messages:
                new_history = [{"role": "system", "content": self.init_prompt}]
                batch_histories.append(new_history)

        responses = []

        with ThreadPoolExecutor() as executor:
            future_to_index = {
                executor.submit(self.generate, user_msg, history): idx
                for idx, (user_msg, history) in enumerate(zip(user_messages, batch_histories))
            }

            results = [None] * len(user_messages)
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    result = future.result()
                    results[idx] = result
                except Exception as exc:
                    print(f"Task {idx} generated an exception: {exc}")
                    results[idx] = ("", [])

        for res in results:
            responses.append(res[0])

        return responses, batch_histories
            