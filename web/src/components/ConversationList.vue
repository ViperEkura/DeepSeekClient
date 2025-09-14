<template>
  <div class="conversation-list">
    <div class="header">
      <h2>对话记录</h2>
      <button class="new-chat-btn" @click="createNewConversation">
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
        :class="{ active: activeConversationId === conv.conversation_id }"
        @click="selectConversation(conv)"
      >
        <div class="avatar">{{ getAvatar(conv.title) }}</div>
        <div class="conversation-info">
          <div class="title">{{ conv.title }}</div>
          <div class="preview">{{ formatDate(conv.created_at) }}</div>
        </div>
        <div class="time">{{ formatTime(conv.created_at) }}</div>
        <button class="delete-btn" @click.stop="deleteConversation(conv.conversation_id)">×</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'ConversationList',
  
  data() {
    return {
      searchQuery: '',
      conversations: [],
      activeConversationId: null,
      apiBaseUrl: 'http://localhost:5000'
    }
  },
  
  computed: {
    filteredConversations() {
      if (!this.searchQuery) return this.conversations
      
      const query = this.searchQuery.toLowerCase()
      return this.conversations.filter(conv => 
        conv.title.toLowerCase().includes(query)
      )
    }
  },
  
  async mounted() {
    await this.fetchConversations();
  },
  
  methods: {
    async fetchConversations() {
      try {
        const response = await axios.get(`${this.apiBaseUrl}/conversations`);
        this.conversations = response.data;
      } catch (error) {
        console.error('获取对话列表失败:', error);
        alert('获取对话列表失败，请检查网络连接');
      }
    },
    
    async createNewConversation() {
      const title = prompt('请输入新对话的标题:');
      if (!title) return;
      
      try {
        const response = await axios.post(`${this.apiBaseUrl}/conversations`, {
          title: title
        });
        
        if (response.status === 201) {
          this.conversations.unshift(response.data);
          this.selectConversation(response.data);
          alert('对话创建成功');
        }
      } catch (error) {
        console.error('创建对话失败:', error);
        alert('创建对话失败，请检查网络连接');
      }
    },
    
    async deleteConversation(conversationId) {
      if (!confirm('确定要删除这个对话吗？')) return;
      
      try {
        const response = await axios.delete(`${this.apiBaseUrl}/conversations/${conversationId}`);
        
        if (response.status === 200) {
          this.conversations = this.conversations.filter(conv => conv.conversation_id !== conversationId);
          
          if (this.activeConversationId === conversationId) {
            this.activeConversationId = null;
            this.$emit('conversation-selected', null);
          }
          
          alert('对话删除成功');
        }
      } catch (error) {
        console.error('删除对话失败:', error);
        alert('删除对话失败，请检查网络连接');
      }
    },
    
    selectConversation(conversation) {
      this.activeConversationId = conversation.conversation_id;
      this.$emit('conversation-selected', conversation);
    },
    
    getAvatar(title) {
      // 根据标题生成头像
      if (!title) return '💬';
      return title.charAt(0).toUpperCase();
    },
    
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('zh-CN');
    },
    
    formatTime(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      const now = new Date();
      const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) {
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
      } else if (diffDays === 1) {
        return '昨天';
      } else if (diffDays < 7) {
        return `${diffDays}天前`;
      } else {
        return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
      }
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
</style>