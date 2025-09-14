<template>
  <div class="chat-container">
    <ConversationList />
    <div class="main-chat">
      <MessageList 
        :messages="messages" 
        :is-loading="isLoading"
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
      isLoading: false
    }
  },
  
  methods: {
    async handleSendMessage(inputText) {
      this.messages.push({
        id: Date.now(),
        content: inputText,
        sender: 'user',
        timestamp: new Date()
      })
      
      this.isLoading = true
      
      try {
        const aiMessageId = Date.now() + 1
        this.messages.push({
          id: aiMessageId,
          content: '',
          sender: 'ai',
          timestamp: new Date(),
          isStreaming: true
        })
        
        const response = this.simulateStreamingResponse(inputText)
        
        for await (const chunk of response) {
          const messageIndex = this.messages.findIndex(m => m.id === aiMessageId)
          if (messageIndex !== -1) {
            this.messages[messageIndex].content += chunk
            this.$set(this.messages, messageIndex, { ...this.messages[messageIndex] })
          }
        }
        
        const messageIndex = this.messages.findIndex(m => m.id === aiMessageId)
        if (messageIndex !== -1) {
          this.messages[messageIndex].isStreaming = false
          this.$set(this.messages, messageIndex, { ...this.messages[messageIndex] })
        }
      } catch (error) {
        console.error('Error:', error)
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
    
    async * simulateStreamingResponse(input) {
      const responses = {
        '你好': ['你', '好！', '有', '什', '么', '可', '以', '帮', '助', '你', '的', '吗', '？'],
        '天气': ['今', '天', '天', '气', '晴', '朗', '，', '适', '合', '出', '门', '。'],
        '默认': ['我', '是', '一', '个', 'AI', '助', '手', '，', '可', '以', '回', '答', '你', '的', '问', '题', '。']
      }
      
      const response = responses[input] || responses['默认']
      
      for (const word of response) {
        yield word
        await new Promise(resolve => setTimeout(resolve, 100))
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