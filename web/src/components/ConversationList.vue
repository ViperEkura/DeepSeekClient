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
        <button class="delete-btn" @click.stop="deleteConversation(conv.conversation_id)">x</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { chatStore } from '@/store/chatStore';

export default {
  name: 'ConversationList',
  
  data() {
    return {
      searchQuery: '',
      apiBaseUrl: 'http://localhost:5000'
    }
  },
  
  computed: {
    conversations() {
      return chatStore.conversations
    },
    activeConversationId() {
      return chatStore.currentConversationId
    },
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
        chatStore.updateConversations(response.data);
      } catch (error) {
        console.error('获取对话列表失败:', error);
        alert('获取对话列表失败，请检查网络连接');
      }
    },
    
    async createNewConversation() {
      const title = prompt('请输入新对话的标题:') || '新对话';
      
      try {
        const response = await axios.post(`${this.apiBaseUrl}/conversations`, {
          title: title
        });
        
        if (response.status === 201) {
          chatStore.addConversation(response.data);
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
          chatStore.removeConversation(conversationId);
          alert('对话删除成功');
        }
      } catch (error) {
        console.error('删除对话失败:', error);
        alert('删除对话失败，请检查网络连接');
      }
    },
    
    selectConversation(conversation) {
      this.$emit('conversation-selected', conversation);
    },
    
    getAvatar(title) {
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
.conversation-list{
  width: 18vw;
  background:rgba(57, 67, 124, 0.85);
  backdrop-filter:blur(20px);
  color:#e1e8f0;
  display:flex;
  flex-direction:column;
  height:100vh;
  border-right:1px solid rgba(255,255,255,.06);
}
.header{
  padding:20px 18px 14px;
  display:flex;
  justify-content:space-between;
  align-items:center;
}
.header h2{
  font-weight:600;
  font-size:1.1rem;
  letter-spacing:.5px;
}
.new-chat-btn{
  background:linear-gradient(135deg,#00c6ff 0%,#0072ff 100%);
  color:#fff;
  border:none;
  border-radius:20px;
  padding:6px 14px;
  font-size:13px;
  cursor:pointer;
  transition:transform .2s,box-shadow .2s;
}
.new-chat-btn:hover{
  transform:translateY(-2px);
  box-shadow:0 4px 12px rgba(0,114,255,.35);
}
.search-box{
  padding:0 18px 12px;
}
.search-box input{
  width:100%;
  height:34px;
  border-radius:17px;
  border:none;
  background:rgba(255,255,255,.07);
  color:#fff;
  padding:4px;
  font-size:14px;
  transition:background .2s;
}
.search-box input:focus{
  background:rgba(255,255,255,.12);
  outline:none;
}
.conversations-container{
  flex:1;
  overflow-y:auto;
  padding:4px 10px 20px;
}
.conversation-item{
  padding:12px;
  margin-bottom:8px;
  border-radius:8px;
  display:flex;
  align-items:center;
  cursor:pointer;
  transition:background .2s;
}
.conversation-item:hover{
  background:rgba(255,255,255,.06);
}
.conversation-item.active{
  background:rgba(0, 115, 255, 0.2);
  color:#fff;
}
.avatar{
  width:42px;
  height:42px;
  border-radius:50%;
  background:linear-gradient(135deg,#00c8ff 0%,#0072ff 100%);
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:1.2rem;
  margin-right:12px;
  flex-shrink:0;
}
.conversation-info{flex:1}
.title{
  font-weight:500;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.preview{
  font-size:12px;
  color:#a0aec0;
  margin-top:2px;
}
.time{
  font-size:11px;
  color:#718096;
  margin-left:6px;
}
.delete-btn{
  width:22px;
  height:22px;
  border-radius:50%;
  background:rgba(255,255,255,.1);
  color:#e1e8f0;
  border:none;
  font-size:14px;
  line-height:22px;
  text-align:center;
  cursor:pointer;
  transition:background .2s,transform .2s;
}
.delete-btn:hover{
  background:#ff4d4f;
  transform:scale(1.15);
}
</style>