<template>
  <div class="conversation-list">
    <div class="header">
      <h2>对话记录</h2>
      <button class="new-chat-btn">
        <span>+</span> 新对话
      </button>
    </div>
    
    <div class="search-box">
      <input type="text" placeholder="搜索对话..." v-model="searchQuery">
    </div>
    
    <div class="conversations-container">
      <div 
        v-for="(conv, index) in filteredConversations" 
        :key="index" 
        class="conversation-item"
        :class="{ active: conv.isActive }"
        @click="selectConversation(conv)"
      >
        <div class="avatar">{{ conv.avatar }}</div>
        <div class="conversation-info">
          <div class="title">{{ conv.title }}</div>
          <div class="preview">{{ conv.lastMessage }}</div>
        </div>
        <div class="time">{{ conv.time }}</div>
        <div v-if="conv.unread" class="unread-badge">{{ conv.unread }}</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConversationList',
  
  data() {
    return {
      searchQuery: '',
      conversations: [
        {
          id: 1,
          title: 'AI助手',
          lastMessage: '你好！有什么可以帮助你的吗？',
          time: '10:24',
          avatar: '🤖',
          isActive: true,
          unread: 0
        },
        {
          id: 2,
          title: '项目讨论',
          lastMessage: '明天的会议需要准备什么材料？',
          time: '昨天',
          avatar: '👥',
          isActive: false,
          unread: 3
        },
        {
          id: 3,
          title: '技术咨询',
          lastMessage: '这个问题可以通过API解决',
          time: '09:15',
          avatar: '💻',
          isActive: false,
          unread: 0
        },
        {
          id: 4,
          title: '客户支持',
          lastMessage: '您的订单已发货',
          time: '周一',
          avatar: '🛒',
          isActive: false,
          unread: 2
        }
      ]
    }
  },
  
  computed: {
    filteredConversations() {
      if (!this.searchQuery) return this.conversations
      
      const query = this.searchQuery.toLowerCase()
      return this.conversations.filter(conv => 
        conv.title.toLowerCase().includes(query) || 
        conv.lastMessage.toLowerCase().includes(query)
      )
    }
  },
  
  methods: {
    selectConversation(conv) {
      this.conversations.forEach(c => c.isActive = false)
      conv.isActive = true
    }
  }
}
</script>

<style scoped>
.conversation-list {
  width: 280px;
  background-color: #1a3a6c;
  color: white;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.header {
  padding: 20px 15px 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h2 {
  font-weight: 600;
  font-size: 1.2rem;
  color: #e6f0ff;
}

.new-chat-btn {
  background: #4a7bce;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 6px 12px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: background 0.2s;
}

.new-chat-btn:hover {
  background: #5a8bd9;
}

.search-box {
  padding: 0 15px 15px;
}

.search-box input {
  width: 100%;
  padding: 10px 15px;
  border-radius: 20px;
  border: none;
  background: #2a4a7c;
  color: white;
  font-size: 14px;
}

.search-box input::placeholder {
  color: #a0b8e0;
}

.conversations-container {
  flex: 1;
  overflow-y: auto;
  padding: 0 5px;
}

.conversation-item {
  padding: 12px 15px;
  display: flex;
  align-items: center;
  border-radius: 10px;
  margin: 5px 10px;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}

.conversation-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.conversation-item.active {
  background: rgba(255, 255, 255, 0.15);
}

.avatar {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: #4a7bce;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  margin-right: 12px;
  flex-shrink: 0;
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.title {
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.preview {
  font-size: 13px;
  color: #c0d0f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.time {
  font-size: 12px;
  color: #a0b8e0;
  flex-shrink: 0;
  margin-left: 8px;
}

.unread-badge {
  position: absolute;
  right: 15px;
  top: 12px;
  background: #4a90e2;
  color: white;
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}
</style>