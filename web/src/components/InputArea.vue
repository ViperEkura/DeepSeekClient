<template>
  <div class="input-area">
    <div class="input-container">
      <textarea
        v-model="inputText"
        placeholder="输入消息..."
        :disabled="isLoading"
        @keydown.enter.prevent="handleEnter"
        ref="textareaRef"
        rows="1"
        class="text-input"
      ></textarea>
      <button 
        @click="sendMessage" 
        :disabled="isLoading || !inputText.trim()"
        class="send-button"
      >
        <span v-if="!isLoading">发送</span>
        <span v-else class="loading">⏳</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, defineEmits, defineProps } from 'vue'

const emit = defineEmits(['send-message'])
const props = defineProps({
  isLoading: {
    type: Boolean,
    default: false
  }
})

const inputText = ref('')
const textareaRef = ref(null)

// 发送消息
const sendMessage = () => {
  if (inputText.value.trim() && !props.isLoading) {
    emit('send-message', inputText.value.trim())
    inputText.value = ''
    adjustTextareaHeight()
  }
}

// 处理回车键
const handleEnter = (event) => {
  if (event.shiftKey) {
    // Shift+Enter 换行
    inputText.value += '\n'
    adjustTextareaHeight()
  } else {
    // Enter 发送消息
    sendMessage()
  }
}

// 自动调整文本区域高度
const adjustTextareaHeight = async () => {
  await nextTick()
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 120) + 'px'
  }
}

// 监听输入文本变化
watch(inputText, adjustTextareaHeight)
</script>

<style scoped>
.input-area {
  padding: 16px;
  border-top: 1px solid #e0e0e0;
  background-color: #fff;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.text-input {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 20px;
  padding: 12px 16px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  max-height: 120px;
  overflow-y: auto;
}

.text-input:focus {
  outline: none;
  border-color: #007bff;
}

.send-button {
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  cursor: pointer;
  font-weight: bold;
}

.send-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.send-button:not(:disabled):hover {
  background-color: #0056b3;
}

.loading {
  display: inline-block;
}
</style>