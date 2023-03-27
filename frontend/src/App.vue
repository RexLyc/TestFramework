<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import FlowCanvas from './components/FlowCanvas.vue'
import HomeView from './views/HomeView.vue'
</script>

<template>
    <HomeView msg="You did it!" />
</template>

<style>
html,body,#app{
  height: 100%;
  margin: 0;
}

</style>
