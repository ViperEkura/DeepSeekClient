<!-- ChatContainer.vue -->
<template>
  <div class="chat-container">
    <ConversationList @conversation-selected="handleConversationSelected" />
    <div class="main-chat">
      <MessageList
        :messages="messages"
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


export default {
  name: 'ChatContainer',
  components: { MessageList, ConversationList, InputArea },

  data() {
    return {
      messages: [], 
      isLoading: false, 
      currentConversationId: null,
      apiBaseUrl: 'http://localhost:5000',
      pollTimer: null 
    }
  },

  beforeUnmount() {
    this.clearPoll()
    // 注意：这里不 abort 流，让后台继续接收
  },

  methods: {
    /* --------------------------------------------------
     * 切换对话
     * -------------------------------------------------- */
    async handleConversationSelected(conversation) {
      this.clearPoll()

      if (!conversation) {
        this.messages = []
        this.currentConversationId = null
        return
      }

      this.currentConversationId = conversation.conversation_id
      await this.loadConversationMessages(conversation.conversation_id)

      // 若后台正在接收该对话，继续轮询
      const sd = streamReceiver.getStreamData(conversation.conversation_id)
      if (sd && !sd.isDone) this.pollStream(conversation.conversation_id)
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
        this.messages = data.map(msg => ({
          id: msg.message_id,
          content: msg.content,
          sender: msg.role === 'user' ? 'user' : 'system',
          timestamp: msg.timestamp
        }))
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
      this.messages.push(userMsg)

      // 3. 插入占位 AI 消息（流式）
      const aiMsgId = Date.now() + 1
      const aiMsg = {
        id: aiMsgId,
        content: '',
        sender: 'system',
        timestamp: new Date(),
        isStreaming: true
      }
      this.messages.push(aiMsg)

      // 4. 启动后台流式接收
      streamReceiver.startStream(this.currentConversationId, inputText, this.apiBaseUrl)
      this.pollStream(this.currentConversationId)
    },

    /* --------------------------------------------------
     * 轮询把后台 chunk 合并到当前 messages
     * -------------------------------------------------- */
    pollStream(conversationId) {
      this.clearPoll()
      this.pollTimer = setInterval(() => {
        const sd = streamReceiver.getStreamData(conversationId)
        if (!sd) return this.clearPoll()

        // 找到正在流式的 AI 消息
        const aiMsg = this.messages.find(m => m.isStreaming)
        if (!aiMsg) return

        // 合并内容
        aiMsg.content = sd.messages
          .filter(m => m.type === 'chunk')
          .map(m => m.content)
          .join('')
        this.$set(this.messages, this.messages.indexOf(aiMsg), { ...aiMsg })

        // 流结束
        if (sd.isDone) {
          aiMsg.isStreaming = false
          this.$set(this.messages, this.messages.indexOf(aiMsg), { ...aiMsg })
          this.clearPoll()
        }
      }, 80)
    },

    clearPoll() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
    },

    /* --------------------------------------------------
     * 创建新对话
     * -------------------------------------------------- */
    async createNewConversation(inputText) {
      try {
        const title = inputText.length > 20 ? inputText.substring(0, 20) + '…' : inputText
        const { data } = await axios.post(`${this.apiBaseUrl}/conversations`, { title })
        this.currentConversationId = data.conversation_id
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