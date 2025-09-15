<template>
  <div class="chat-container">
    <ConversationList @conversation-selected="handleConversationSelected" />
    <div class="main-chat">
      <MessageList 
        :messages="messages" 
        :is-loading="isLoading"
        :conversation-id="currentConversationId ? currentConversationId.toString() : null"
      />
      <InputArea 
        @send-message="handleSendMessage"
        :is-loading="isLoading"
      />
    </div>
  </div>
</template>

<script>
import MessageList from './MessageList.vue'
import ConversationList from './ConversationList.vue'
import InputArea from './InputArea.vue'
import axios from 'axios'

export default {
  name: 'ChatContainer',
  
  components: {
    MessageList,
    InputArea,
    ConversationList
  },
  
  data() {
    return {
      messages: [],
      isLoading: false,
      currentConversationId: null,
      apiBaseUrl: 'http://localhost:5000',
      eventSource: null,
      currentStreamController: null // 用于中止当前流式请求
    }
  },
  
  beforeUnmount() {
    // 组件销毁前关闭SSE连接和取消请求
    if (this.eventSource) {
      this.eventSource.close()
    }
    if (this.currentStreamController) {
      this.currentStreamController.abort()
    }
  },
  
  methods: {
    async handleConversationSelected(conversation) {
      if (!conversation) {
        this.messages = []
        this.currentConversationId = null
        return
      }
      
      this.currentConversationId = conversation.conversation_id
      await this.loadConversationMessages(conversation.conversation_id)
    },
    
    async loadConversationMessages(conversationId) {
      this.isLoading = true
      try {
        const response = await axios.get(
          `${this.apiBaseUrl}/conversations/${conversationId}/messages/recent?limit=500`
        )
        this.messages = response.data.map(msg => ({
          id: msg.message_id,
          content: msg.content,
          sender: msg.role === 'user' ? 'user' : 'system',
          timestamp: msg.timestamp
        }))
      } catch (error) {
        console.error('加载消息失败:', error)
        alert('加载消息失败，请检查网络连接')
      } finally {
        this.isLoading = false
      }
    },
    
    async handleSendMessage(inputText) {
      // 如果没有选中对话，先创建新对话
      if (!this.currentConversationId) {
        await this.createNewConversation(inputText)
        return
      }

      try {
        await axios.post(
          `${this.apiBaseUrl}/conversations/${this.currentConversationId}/messages`,
          { role: 'user', content: inputText }
        )
      } catch (e) {
        console.error('保存用户消息失败:', e)
        alert('保存用户消息失败，请检查网络')
        return
      }

      const userMessage = {
        id: Date.now(),
        content: inputText,
        sender: 'user',
        timestamp: new Date()
      }
      this.messages.push(userMessage)

      this.isLoading = true
      const aiMessageId = Date.now() + 1
      const aiMessage = {
        id: aiMessageId,
        content: '',
        sender: 'system',
        timestamp: new Date(),
        isStreaming: true
      }
      this.messages.push(aiMessage)

      try {
        await this.sendMessageToServer(inputText, aiMessageId)
      } catch (error) {
        console.error('发送消息失败:', error)
        const idx = this.messages.findIndex(m => m.id === aiMessageId)
        if (idx !== -1) {
          this.messages[idx].isStreaming = false
          this.messages[idx].isError = true
          this.messages[idx].content = '抱歉，发生了错误。'
          this.$set(this.messages, idx, { ...this.messages[idx] })
        }
      } finally {
        this.isLoading = false
      }
    },
    
    async createNewConversation(inputText) {
      try {
        // 使用输入内容的前20个字符作为对话标题
        const title = inputText.length > 20 ? inputText.substring(0, 20) + '...' : inputText
        
        const response = await axios.post(`${this.apiBaseUrl}/conversations`, {
          title: title || '新对话'
        })
        
        if (response.status === 201) {
          this.currentConversationId = response.data.conversation_id
          // 创建成功后发送消息
          await this.handleSendMessage(inputText)
        }
      } catch (error) {
        console.error('创建对话失败:', error)
        alert('创建对话失败，请检查网络连接')
      }
    },
    
    async sendMessageToServer(inputText, aiMessageId) {
      try {
        // 使用AbortController以便可以取消请求
        const controller = new AbortController()
        this.currentStreamController = controller
        
        await this.useStreamPost(inputText, aiMessageId, controller.signal)
      } catch (error) {
        console.error('发送消息失败:', error)
        throw error
      } finally {
        this.currentStreamController = null
      }
    },
    async useStreamPost(inputText, aiMessageId) {
      return new Promise((resolve, reject) => {
        const controller = new AbortController();
        this.currentStreamController = controller;

        fetch(
          `${this.apiBaseUrl}/conversations/${this.currentConversationId}/stream`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: inputText }),
            signal: controller.signal
          }
        )
          .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.body;
          })
          .then(body => {
            const reader = body.getReader();
            const decoder = new TextDecoder();
            let buf = '';

            const pump = ({ done, value }) => {
              if (done) {                       // 流结束
                const msgIdx = this.messages.findIndex(m => m.id === aiMessageId);
                if (msgIdx !== -1) {
                  this.messages[msgIdx].isStreaming = false;
                  this.$set(this.messages, msgIdx, { ...this.messages[msgIdx] });
                }
                return resolve();
              }

              buf += decoder.decode(value, { stream: true });
              const lines = buf.split('\n');
              buf = lines.pop();                // 保留不完整行

              for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const payload = line.slice(6);
                
                try {
                  const msg = JSON.parse(payload);
                  const idx = this.messages.findIndex(m => m.id === aiMessageId);
                  if (idx === -1) continue;

                  if (msg.type === 'chunk') {
                    this.messages[idx].content += msg.content;
                    this.$set(this.messages, idx, { ...this.messages[idx] });
                  } else if (msg.type === 'complete') {
                    this.messages[idx].isStreaming = false;
                    this.$set(this.messages, idx, { ...this.messages[idx] });
                  } else if (msg.type === 'error') {
                    this.messages[idx].isStreaming = false;
                    this.messages[idx].isError = true;
                    this.messages[idx].content = msg.message || 'Stream failed';
                    this.$set(this.messages, idx, { ...this.messages[idx] });
                  }
                } catch (e) {
                  console.warn('parse error', e);
                }
              }
              return reader.read().then(pump);
            };
            return reader.read().then(pump);
          })
          .catch(err => {
            if (err.name === 'AbortError') return resolve();   // 用户中断
            console.error('fetch stream error', err);
            reject(err);
          })
          .finally(() => {
            this.currentStreamController = null;
          });
      });
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background-color: #f0f5ff;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
}

.main-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.05);
}
</style>