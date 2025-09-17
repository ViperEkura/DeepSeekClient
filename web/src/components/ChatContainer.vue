<!-- ChatContainer.vue -->
<template>
  <div class="chat-container">
    <ConversationList @conversation-selected="handleConversationSelected" />
    <div class="main-chat">
      <MessageList
        :messages="currentMessages"
        :is-loading="isLoading"
        :conversation-id="currentConversationId?.toString()"
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
import streamReceiver from '@/services/StreamReceiverService'
import { chatStore } from '@/store/chatStore'

export default {
  name: 'ChatContainer',
  components: { MessageList, ConversationList, InputArea },

  data() {
    return {
      messagesByConversation: new Map(), // 为每个对话单独存储消息
      isLoading: false, 
      apiBaseUrl: 'http://localhost:5000',
      pollTimers: new Map() // 为每个对话单独存储轮询计时器
    }
  },

  computed: {
    currentConversationId() {
      return chatStore.currentConversationId
    },
    
    currentMessages() {
      // 返回当前对话的消息，如果不存在则返回空数组
      return this.messagesByConversation.get(this.currentConversationId) || []
    }
  },

  mounted() {
    // 恢复当前对话的消息
    if (this.currentConversationId) {
      this.loadConversationMessages(this.currentConversationId)
    }
    
    // 全局监听页面可见性变化
    document.addEventListener('visibilitychange', this.handleVisibilityChange)
    
    // 启动所有活跃流的轮询
    this.startAllActiveStreamsPolling()
  },

  beforeUnmount() {
    this.clearAllPolls()
    document.removeEventListener('visibilitychange', this.handleVisibilityChange)
  },

  methods: {
    /* --------------------------------------------------
     * 处理页面可见性变化
     * -------------------------------------------------- */
    handleVisibilityChange() {
      if (document.visibilityState === 'visible') {
        // 页面重新可见时，检查所有活跃的流
        this.startAllActiveStreamsPolling()
      }
    },

    /* --------------------------------------------------
     * 启动所有活跃流的轮询
     * -------------------------------------------------- */
    startAllActiveStreamsPolling() {
      const activeStreams = streamReceiver.getAllActiveStreams()
      activeStreams.forEach((streamData, conversationId) => {
        if (!streamData.isDone && !this.pollTimers.has(conversationId)) {
          this.pollStream(conversationId)
        }
      })
    },

    /* --------------------------------------------------
     * 切换对话
     * -------------------------------------------------- */
    async handleConversationSelected(conversation) {
      if (!conversation) {
        chatStore.setCurrentConversation(null)
        return
      }

      chatStore.setCurrentConversation(conversation)
      
      // 加载该对话的消息（如果还没有加载过）
      if (!this.messagesByConversation.has(conversation.conversation_id)) {
        await this.loadConversationMessages(conversation.conversation_id)
      }

      // 确保该对话的流正在轮询
      const sd = streamReceiver.getStreamData(conversation.conversation_id)
      if (sd && !sd.isDone && !this.pollTimers.has(conversation.conversation_id)) {
        this.pollStream(conversation.conversation_id)
      }
    },

    /* --------------------------------------------------
     * 加载已落库的历史消息
     * -------------------------------------------------- */
    async loadConversationMessages(conversationId) {
      this.isLoading = true
      try {
        const { data } = await axios.get(
          `${this.apiBaseUrl}/conversations/${conversationId}/messages/recent?limit=500`
        )
        
        const messages = data.map(msg => ({
          id: msg.message_id,
          content: msg.content,
          sender: msg.role === 'user' ? 'user' : 'system',
          timestamp: msg.timestamp
        }))
        
        this.messagesByConversation.set(conversationId, messages)
      } catch (e) {
        console.error('加载消息失败:', e)
        alert('加载消息失败，请检查网络')
      } finally {
        this.isLoading = false
      }
    },

    /* --------------------------------------------------
     * 发送消息入口
     * -------------------------------------------------- */
    async handleSendMessage(inputText) {
      if (!this.currentConversationId) {
        await this.createNewConversation(inputText)
        return
      }

      // 获取当前对话的消息数组，如果不存在则创建
      let currentMsgs = this.messagesByConversation.get(this.currentConversationId)
      if (!currentMsgs) {
        currentMsgs = []
        this.messagesByConversation.set(this.currentConversationId, currentMsgs)
      }

      // 1. 落库用户消息
      try {
        await axios.post(
          `${this.apiBaseUrl}/conversations/${this.currentConversationId}/messages`,
          { role: 'user', content: inputText }
        )
      } catch (e) {
        alert('保存用户消息失败')
        return
      }

      // 2. 本地立即展示用户消息
      const userMsg = {
        id: Date.now(),
        content: inputText,
        sender: 'user',
        timestamp: new Date()
      }
      currentMsgs.push(userMsg)
      
      // 触发响应式更新
      this.messagesByConversation.set(this.currentConversationId, [...currentMsgs])

      // 3. 插入占位 AI 消息（流式）
      const aiMsgId = Date.now() + 1
      const aiMsg = {
        id: aiMsgId,
        content: '',
        sender: 'system',
        timestamp: new Date(),
        isStreaming: true
      }
      currentMsgs.push(aiMsg)
      
      // 触发响应式更新
      this.messagesByConversation.set(this.currentConversationId, [...currentMsgs])

      // 4. 启动后台流式接收
      streamReceiver.startStream(this.currentConversationId, inputText, this.apiBaseUrl)
      
      // 启动该对话的轮询（如果还没有启动）
      if (!this.pollTimers.has(this.currentConversationId)) {
        this.pollStream(this.currentConversationId)
      }
    },

    /* --------------------------------------------------
     * 轮询把后台 chunk 合并到对应对话的 messages
     * -------------------------------------------------- */
    pollStream(conversationId) {
      // 清除该对话之前的轮询（如果有）
      this.clearPoll(conversationId)
      
      const timer = setInterval(() => {
        const sd = streamReceiver.getStreamData(conversationId)
        if (!sd) return this.clearPoll(conversationId)

        // 获取该对话的消息数组
        let msgs = this.messagesByConversation.get(conversationId)
        if (!msgs) {
          msgs = []
          this.messagesByConversation.set(conversationId, msgs)
        }

        // 找到正在流式的 AI 消息
        const aiMsg = msgs.find(m => m.isStreaming)
        if (!aiMsg) return

        // 合并内容
        aiMsg.content = sd.messages
          .filter(m => m.type === 'chunk')
          .map(m => m.content)
          .join('')
          
        // 触发响应式更新
        this.messagesByConversation.set(conversationId, [...msgs])

        // 流结束
        if (sd.isDone) {
          aiMsg.isStreaming = false
          // 触发响应式更新
          this.messagesByConversation.set(conversationId, [...msgs])
          this.clearPoll(conversationId)
        }
      }, 80)
      
      // 存储该对话的轮询计时器
      this.pollTimers.set(conversationId, timer)
    },

    // 清除特定对话的轮询
    clearPoll(conversationId) {
      const timer = this.pollTimers.get(conversationId)
      if (timer) {
        clearInterval(timer)
        this.pollTimers.delete(conversationId)
      }
    },
    
    // 清除所有对话的轮询
    clearAllPolls() {
      this.pollTimers.forEach((timer) => {
        clearInterval(timer)
      })
      this.pollTimers.clear()
    },

    /* --------------------------------------------------
     * 创建新对话
     * -------------------------------------------------- */
    async createNewConversation(inputText) {
      try {
        const title = inputText.length > 20 ? inputText.substring(0, 20) + '…' : inputText
        const { data } = await axios.post(`${this.apiBaseUrl}/conversations`, { title })
        chatStore.setCurrentConversation(data)
        await this.handleSendMessage(inputText)
      } catch (e) {
        alert('创建对话失败')
      }
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background:linear-gradient(135deg,#0f1b31 0%,#1d2b50 100%);
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
}

.main-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background:rgba(255,255,255,.04);
  backdrop-filter:blur(20px);
  box-shadow:0 8px 32px rgba(0,0,0,.36);
  border-left:1px solid rgba(255,255,255,.08);
}
</style>