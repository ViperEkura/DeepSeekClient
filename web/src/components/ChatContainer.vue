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
    
    async useSSEStream(inputText, aiMessageId, signal) {
      return new Promise((resolve, reject) => {
        // 使用 fetch 发起 POST 请求
        fetch(`${this.apiBaseUrl}/conversations/${this.currentConversationId}/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content: inputText
          }),
          signal // 传递AbortSignal以便可以取消请求
        }).then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }

          const reader = response.body.getReader()
          const decoder = new TextDecoder()
          let buffer = ''

          // 处理流式数据
          const processStream = ({ done, value }) => {
            if (done) {
              // 完成流式传输，更新消息状态
              const messageIndex = this.messages.findIndex(m => m.id === aiMessageId)
              if (messageIndex !== -1) {
                this.messages[messageIndex].isStreaming = false
                // 使用Vue.set确保响应式更新
                this.$set(this.messages, messageIndex, {...this.messages[messageIndex]})
              }
              resolve()
              return
            }

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() // 保留未完成的行

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6))
                  
                  if (data.type === 'chunk') {
                    // 更新流式消息内容
                    const messageIndex = this.messages.findIndex(m => m.id === aiMessageId)
                    if (messageIndex !== -1) {
                      this.messages[messageIndex].content += data.content
                      // 使用Vue.set确保响应式更新
                      this.$set(this.messages, messageIndex, {...this.messages[messageIndex]})
                    }
                  } else if (data.type === 'complete') {
                    // 完成流式传输
                    const messageIndex = this.messages.findIndex(m => m.id === aiMessageId)
                    if (messageIndex !== -1) {
                      this.messages[messageIndex].isStreaming = false
                      this.$set(this.messages, messageIndex, {...this.messages[messageIndex]})
                    }
                  }
                } catch (parseError) {
                  console.error('解析SSE数据失败:', parseError)
                }
              }
            }

            return reader.read().then(processStream)
          }

          return reader.read().then(processStream)
        }).catch(error => {
          if (error.name === 'AbortError') {
            console.log('请求已被取消')
            resolve() // 如果是主动取消，不视为错误
          } else {
            console.error('请求失败:', error)
            reject(error)
          }
        })
      })
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