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

<script>
export default {
  name: 'InputArea',
  
  props: {
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  
  data() {
    return {
      inputText: ''
    }
  },
  
  methods: {
    // 发送消息
    sendMessage() {
      if (this.inputText.trim() && !this.isLoading) {
        this.$emit('send-message', this.inputText.trim())
        this.inputText = ''
        this.$nextTick(() => {
          this.adjustTextareaHeight()
        })
      }
    },
    
    // 处理回车键
    handleEnter(event) {
      if (event.shiftKey) {
        // Shift+Enter 换行
        this.inputText += '\n'
        this.$nextTick(() => {
          this.adjustTextareaHeight()
        })
      } else {
        // Enter 发送消息
        this.sendMessage()
      }
    },
    
    // 自动调整文本区域高度
    adjustTextareaHeight() {
      if (this.$refs.textareaRef) {
        this.$refs.textareaRef.style.height = 'auto'
        this.$refs.textareaRef.style.height = Math.min(this.$refs.textareaRef.scrollHeight, 120) + 'px'
      }
    }
  },
  
  watch: {
    // 监听输入文本变化
    inputText() {
      this.$nextTick(() => {
        this.adjustTextareaHeight()
      })
    }
  },
  
  mounted() {
    // 初始调整高度
    this.adjustTextareaHeight()
  }
}
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