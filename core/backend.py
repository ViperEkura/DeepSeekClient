from flask import Flask, request, Response
from core.deeoseek_client import DeepSeekClient

class DeepSeekChatApp:
    def __init__(self, api_key, base_url):
        self.app = Flask(__name__)
        self.deepseek_client = DeepSeekClient(api_key=api_key, base_url=base_url)
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        self.app.add_url_rule('/chat-stream', methods=['POST'], view_func=self.chat_stream)
    
    def chat_stream(self):
        """
        流式聊天接口
        请求体格式:
        {
            "user_message": "用户输入",
            "histories": [{"role": "user/assistant", "content": "..."}, ...]
        }
        """
        data = request.get_json()
        user_message = data.get('user_message')
        histories = data.get('histories', [])
        
        def generate():
            try:
                for chunk, _ in self.deepseek_client.stream_chat(user_message, histories):
                    # 使用Server-Sent Events格式传输数据
                    yield f"data: {chunk}\n\n"
            except Exception as e:
                yield f"data: [ERROR] {str(e)}\n\n"
        
        return Response(
            generate(), 
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'  # 禁用Nginx缓冲
            }
        )
    
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """启动应用"""
        self.app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    chat_app = DeepSeekChatApp()
    chat_app.run()