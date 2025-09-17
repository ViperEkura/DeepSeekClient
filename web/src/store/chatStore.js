import { reactive } from 'vue'

// 全局状态管理
export const chatStore = reactive({
  currentConversationId: null,
  conversations: [],
  messages: [],
  isLoading: false,
  
  // 从localStorage恢复状态
  init() {
    const saved = localStorage.getItem('chatState')
    if (saved) {
      try {
        const state = JSON.parse(saved)
        this.currentConversationId = state.currentConversationId
        this.conversations = state.conversations || []
      } catch (e) {
        console.error('Failed to restore chat state:', e)
      }
    }
  },
  
  // 保存状态到localStorage
  persist() {
    const state = {
      currentConversationId: this.currentConversationId,
      conversations: this.conversations
    }
    localStorage.setItem('chatState', JSON.stringify(state))
  },
  
  // 设置当前对话
  setCurrentConversation(conversation) {
    this.currentConversationId = conversation ? conversation.conversation_id : null
    this.persist()
  },
  
  // 添加对话
  addConversation(conversation) {
    this.conversations.unshift(conversation)
    this.persist()
  },
  
  // 删除对话
  removeConversation(conversationId) {
    this.conversations = this.conversations.filter(c => c.conversation_id !== conversationId)
    if (this.currentConversationId === conversationId) {
      this.currentConversationId = null
    }
    this.persist()
  },
  
  // 更新对话列表
  updateConversations(conversations) {
    this.conversations = conversations
    this.persist()
  }
})

// 初始化
chatStore.init()