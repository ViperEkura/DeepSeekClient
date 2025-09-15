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
          timestamp: new Date(msg.created_at)
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
      
      // 添加用户消息到界面
      const userMessage = {
        id: Date.now(),
        content: inputText,
        sender: 'user',
        timestamp: new Date()
      }
      this.messages.push(userMessage)
      
      this.isLoading = true
      
      try {
        // 创建AI消息占位符
        const aiMessageId = Date.now() + 1
        const aiMessage = {
          id: aiMessageId,
          content: '',
          sender: 'system',
          timestamp: new Date(),
          isStreaming: true
        }
        this.messages.push(aiMessage)
        
        // 发送消息到服务器并处理流式响应
        await this.sendMessageToServer(inputText, aiMessageId)
        
      } catch (error) {
        console.error('发送消息失败:', error)
        // 找到AI消息并标记为错误
        const aiMessageIndex = this.messages.findIndex(m => m.isStreaming)
        if (aiMessageIndex !== -1) {
          this.messages[aiMessageIndex].isStreaming = false
          this.messages[aiMessageIndex].content = '抱歉，发生了错误。'
          this.messages[aiMessageIndex].isError = true
          // 使用Vue.set确保响应式更新
          this.$set(this.messages, aiMessageIndex, {...this.messages[aiMessageIndex]})
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
        
        await this.useSSEStream(inputText, aiMessageId, controller.signal)
      } catch (error) {
        console.error('发送消息失败:', error)
        throw error
      } finally {
        this.currentStreamController = null
      }
    },
    async useSSEStream(inputText, aiMessageId) {
      return new Promise((resolve, reject) => {
        const es = new EventSource(
          `${this.apiBaseUrl}/conversations/${this.currentConversationId}/stream?content=${encodeURIComponent(inputText)}`
        );

        es.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'chunk') {
              const index = this.messages.findIndex(m => m.id === aiMessageId);
              if (index !== -1) {
                this.messages[index].content += data.content;
                this.$set(this.messages, index, { ...this.messages[index] });
              }
            } else if (data.type === 'complete') {
              const index = this.messages.findIndex(m => m.id === aiMessageId);
              if (index !== -1) {
                this.messages[index].isStreaming = false;
                this.$set(this.messages, index, { ...this.messages[index] });
              }
              es.close();
              resolve();
            }
          } catch (err) {
            console.error('SSE 数据解析失败:', err);
          }
        };

        es.onerror = (err) => {
          console.error('SSE 连接错误:', err);
          es.close();
          reject(new Error('流式响应失败'));
        };

        this.currentStreamController = {
          abort: () => {
            es.close();
            resolve();
          }
        };
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