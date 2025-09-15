<template>
  <div class="chat-container">
    <ConversationList @conversation-selected="handleConversationSelected" />
    <div class="main-chat">
      <MessageList 
        :messages="messages" 
        :is-loading="isLoading"
        :conversation-id="currentConversationId"
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
      eventSource: null
    }
  },
  
  beforeUnmount() {
    // 组件销毁前关闭SSE连接
    if (this.eventSource) {
      this.eventSource.close()
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
          sender: msg.role === 'user' ? 'user' : 'ai',
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
          sender: 'ai',
          timestamp: new Date(),
          isStreaming: true
        }
        this.messages.push(aiMessage)
        
        // 发送消息到服务器并处理流式响应
        await this.sendMessageToServer(inputText, aiMessageId)
        
      } catch (error) {
        console.error('发送消息失败:', error)
        this.messages.push({
          id: Date.now() + 2,
          content: '抱歉，发生了错误。',
          sender: 'ai',
          timestamp: new Date(),
          isError: true
        })
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
        // 首先尝试使用SSE流式接口
        try {
          await this.useSSEStream(inputText, aiMessageId)
        } catch (sseError) {
          console.warn('SSE流式接口失败，尝试普通接口:', sseError)
          await this.useRegularApi(inputText, aiMessageId)
        }
        
      } catch (error) {
        console.error('发送消息失败:', error)
        throw error
      }
    },
    
    async useSSEStream(inputText, aiMessageId) {
      return new Promise((resolve, reject) => {
        // 使用POST请求发送内容
        const eventSource = new EventSource(
          `${this.apiBaseUrl}/conversations/${this.currentConversationId}/stream`
        )
        
        this.eventSource = eventSource
        
        // 先发送消息内容
        axios.post(`${this.apiBaseUrl}/conversations/${this.currentConversationId}/stream`, {
          content: inputText
        }).catch(err => {
          console.error('发送消息内容失败:', err)
        })
        
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            
            if (data.type === 'chunk') {
              // 更新流式消息内容
              const messageIndex = this.messages.findIndex(m => m.id === aiMessageId)
              if (messageIndex !== -1) {
                this.messages[messageIndex].content += data.content
                this.$set(this.messages, messageIndex, { ...this.messages[messageIndex] })
              }
            } else if (data.type === 'complete') {
              // 完成流式传输
              const messageIndex = this.messages.findIndex(m => m.id === aiMessageId)
              if (messageIndex !== -1) {
                this.messages[messageIndex].isStreaming = false
                this.$set(this.messages, messageIndex, { ...this.messages[messageIndex] })
              }
              eventSource.close()
              resolve()
            }
          } catch (parseError) {
            console.error('解析SSE数据失败:', parseError)
          }
        }
        
        eventSource.onerror = (error) => {
          console.error('SSE连接错误:', error)
          eventSource.close()
          reject(error)
        }
        
        // 设置超时，防止SSE连接长时间不关闭
        setTimeout(() => {
          if (eventSource.readyState !== EventSource.CLOSED) {
            eventSource.close()
            reject(new Error('SSE连接超时'))
          }
        }, 30000) // 30秒超时
      })
    },
    
    async useRegularApi(inputText, aiMessageId) {
      try {
        // 使用普通API接口发送消息
        const response = await axios.post(
          `${this.apiBaseUrl}/conversations/${this.currentConversationId}/messages`,
          {
            role: 'user',
            content: inputText
          }
        )
        
        if (response.status === 201) {
          // 模拟流式效果
          const aiResponse = "这是AI的回复（流式接口不可用，使用普通接口）"
          const words = aiResponse.split('')
          
          for (const word of words) {
            await new Promise(resolve => setTimeout(resolve, 50))
            const messageIndex = this.messages.findIndex(m => m.id === aiMessageId)
            if (messageIndex !== -1) {
              this.messages[messageIndex].content += word
              this.$set(this.messages, messageIndex, { ...this.messages[messageIndex] })
            }
          }
          
          // 完成流式传输
          const messageIndex = this.messages.findIndex(m => m.id === aiMessageId)
          if (messageIndex !== -1) {
            this.messages[messageIndex].isStreaming = false
            this.$set(this.messages, messageIndex, { ...this.messages[messageIndex] })
          }
        }
      } catch (error) {
        console.error('普通接口发送消息失败:', error)
        throw error
      }
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