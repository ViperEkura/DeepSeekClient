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
        <div class="message-text markdown-body">
          <span v-html="renderMarkdown(message.content)"></span>
          <span v-if="message.isStreaming" class="streaming-cursor">|</span>
        </div>
        <div class="message-time">
          {{ formatTime(message.timestamp) }}
        </div>
      </div>
    </div>
    
    <div v-if="isLoading" class="thinking">
      加载中<span class="thinking-dots"></span>
    </div>
  </div>
</template>

<script>
import MarkdownIt from 'markdown-it'

export default {
  name: 'MessageList',
  
  props: {
    messages: {
      type: Array,
      required: true
    },
    conversationId: {
      type: String,
      required: false
    },
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  
  methods: {
    renderMarkdown(content) {
      const md = new MarkdownIt({
        html: false,
        linkify: true,
        typographer: false
      })
      return md.render(content)
    },
    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.messagesContainer) {
          this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
        }
      })
    }
  },
  
  watch: {
    messages: {
      handler() {
        this.scrollToBottom()
      },
      deep: true
    },
    isLoading: {
      handler() {
        this.scrollToBottom()
      }
    }
  },
  
  mounted() {
    this.scrollToBottom()
  }
}
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8fafd;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
  align-self: flex-start;
}

.message-user {
  flex-direction: row-reverse;
  align-self: flex-end;
  max-width: 85%;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #e6f0ff;
  font-size: 20px;
  flex-shrink: 0;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-text {
  padding: 0px 18px;
  border-radius: 15px;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  position: relative;
  line-height: 1.5;
  font-size: 15px;
  color: #333;
}

.message-user .message-text {
  background-color: #4a7bce;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #777;
  align-self: flex-end;
}

.streaming-cursor {
  animation: blink 1s infinite;
  color: #4a7bce;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.thinking {
  color: #555;
  font-style: italic;
  padding: 10px 15px;
  background: #e6f0ff;
  border-radius: 15px;
  display: inline-block;
  align-self: center;
}

.thinking-dots::after {
  content: '';
  animation: dots 1.5s infinite;
}

@keyframes dots {
  0%, 20% { content: '.'; }
  40% { content: '..'; }
  60%, 100% { content: '...'; }
}
</style>