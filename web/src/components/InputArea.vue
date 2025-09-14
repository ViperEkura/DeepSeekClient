<template>
  <div class="input-area">
    <div class="input-container">
      <textarea
        v-model="inputText"
        placeholder="输入消息... (Shift + Enter 换行)"
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
        :class="{ 'sending': isLoading }"
      >
        <span v-if="!isLoading">发送</span>
        <span v-else class="loading">发送中...</span>
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
    sendMessage() {
      if (this.inputText.trim() && !this.isLoading) {
        this.$emit('send-message', this.inputText.trim())
        this.inputText = ''
        this.$nextTick(() => {
          this.adjustTextareaHeight()
        })
      }
    },
    
    handleEnter(event) {
      if (event.shiftKey) {
        this.inputText += '\n'
        this.$nextTick(() => {
          this.adjustTextareaHeight()
        })
      } else {
        this.sendMessage()
      }
    },
    
    adjustTextareaHeight() {
      const textarea = this.$refs.textareaRef
      if (textarea) {
        textarea.style.height = 'auto'
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
      }
    }
  },
  
  watch: {
    inputText() {
      this.$nextTick(() => {
        this.adjustTextareaHeight()
      })
    }
  },
  
  mounted() {
    this.adjustTextareaHeight()
  }
}
</script>

<style scoped>
.input-area {
  padding: 15px 20px;
  background-color: #fff;
  border-top: 1px solid #e0e7ff;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: #f8fafd;
  border-radius: 20px;
  padding: 10px 15px;
  box-shadow: 0 -2px 10px rgba(74, 123, 206, 0.08);
}

.text-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 8px 0;
  resize: none;
  font-family: inherit;
  font-size: 15px;
  max-height: 120px;
  overflow-y: auto;
  line-height: 1.5;
  color: #333;
}

.text-input:focus {
  outline: none;
}

.text-input::placeholder {
  color: #a0b0d0;
}

.send-button {
  background: linear-gradient(to right, #4a7bce, #5a8bd9);
  color: white;
  border: none;
  border-radius: 18px;
  padding: 10px 22px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 5px;
  box-shadow: 0 2px 5px rgba(74, 123, 206, 0.2);
}

.send-button:disabled {
  background: #c0d0f0;
  cursor: not-allowed;
  box-shadow: none;
}

.send-button:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(74, 123, 206, 0.3);
}

.send-button.sending {
  background: #7a9bd9;
  transform: none;
  box-shadow: none;
}

.loading {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
</style>