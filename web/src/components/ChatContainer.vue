<template>
  <div class="chat-container">
    <MessageList 
      :messages="messages" 
      :is-loading="isLoading"
    />
    <InputArea 
      @send-message="handleSendMessage"
      :is-loading="isLoading"
    />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import MessageList from './MessageList.vue'
import InputArea from './InputArea.vue'


const messages = reactive([])
const isLoading = ref(false)

const handleSendMessage = async (inputText) => {
  // 添加用户消息
  messages.push({
    id: Date.now(),
    content: inputText,
    sender: 'user',
    timestamp: new Date()
  })
  
  // 设置加载状态
  isLoading.value = true
  
  try {
    // 添加初始AI消息（空内容）
    const aiMessageId = Date.now() + 1
    messages.push({
      id: aiMessageId,
      content: '',
      sender: 'ai',
      timestamp: new Date(),
      isStreaming: true
    })
    
    // 模拟流式响应 - 实际中这里应该是API调用
    const response = simulateStreamingResponse(inputText)
    
    // 处理流式数据
    for await (const chunk of response) {
      const messageIndex = messages.findIndex(m => m.id === aiMessageId)
      if (messageIndex !== -1) {
        messages[messageIndex].content += chunk
      }
    }
    
    // 完成流式传输
    const messageIndex = messages.findIndex(m => m.id === aiMessageId)
    if (messageIndex !== -1) {
      messages[messageIndex].isStreaming = false
    }
  } catch (error) {
    console.error('Error:', error)
    messages.push({
      id: Date.now() + 2,
      content: '抱歉，发生了错误。',
      sender: 'ai',
      timestamp: new Date(),
      isError: true
    })
  } finally {
    isLoading.value = false
  }
}

// 模拟流式响应的函数
async function* simulateStreamingResponse(input) {
  const responses = {
    '你好': ['你', '好！', '有', '什', '么', '可', '以', '帮', '助', '你', '的', '吗', '？'],
    '天气': ['今', '天', '天', '气', '晴', '朗', '，', '适', '合', '出', '门', '。'],
    '默认': ['我', '是', '一', '个', 'AI', '助', '手', '，', '可', '以', '回', '答', '你', '的', '问', '题', '。']
  }
  
  const response = responses[input] || responses['默认']
  
  for (const word of response) {
    yield word
    await new Promise(resolve => setTimeout(resolve, 100)) // 模拟延迟
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}
</style>