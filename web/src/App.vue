<template>
  <div id="app">
    <h1>LLM流式对话演示</h1>
    <ChatContainer />
  </div>
</template>

<script setup>
import ChatContainer from './components/ChatContainer.vue'
</script>

<style>
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 20px;
  background-color: #f9f9f9;
}

#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
</style>