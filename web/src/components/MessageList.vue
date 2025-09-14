<template>
  <div class="message-list" ref="messagesContainer">
    <div 
      v-for="message in messages" 
      :key="message.id" 
      :class="['message', `message-${message.sender}`]"
    >
      <div class="message-avatar">
        <span v-if="message.sender === 'user'">👤</span>
        <span v-else>🤖</span>
      </div>
      <div class="message-content">
        <div class="message-text">
          {{ message.content }}
          <span 
            v-if="message.isStreaming" 
            class="streaming-cursor"
          >|</span>
        </div>
        <div class="message-time">
          {{ formatTime(message.timestamp) }}
        </div>
      </div>
    </div>
    
    <div v-if="isLoading" class="message message-ai">
      <div class="message-avatar">🤖</div>
      <div class="message-content">
        <div class="thinking">思考中<span class="thinking-dots">...</span></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, ref, watch, nextTick } from 'vue'

const props = defineProps({
  messages: {
    type: Array,
    required: true
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const messagesContainer = ref(null)

// 自动滚动到底部
watch(() => props.messages, async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}, { deep: true })

// 格式化时间
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: #f5f5f5;
}

.message {
  display: flex;
  margin-bottom: 16px;
}

.message-user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #fff;
  margin: 0 8px;
  font-size: 20px;
}

.message-content {
  max-width: 70%;
}

.message-user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-text {
  padding: 12px;
  border-radius: 18px;
  background-color: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  position: relative;
}

.message-user .message-text {
  background-color: #007bff;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.streaming-cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.thinking {
  color: #666;
  font-style: italic;
}

.thinking-dots {
  animation: dots 1.5s infinite;
}

@keyframes dots {
  0%, 20% { content: '.'; }
  40% { content: '..'; }
  60%, 100% { content: '...'; }
}
</style>