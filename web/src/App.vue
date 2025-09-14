<template>
  <div id="app">
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
body {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
}
</style>