<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-gray-900">GitHub Star Helper</h1>
        <nav class="flex gap-4">
          <router-link to="/" class="text-gray-600 hover:text-gray-900">首页</router-link>
          <router-link to="/search" class="text-gray-600 hover:text-gray-900">搜索</router-link>
          <router-link to="/chat" class="text-gray-600 hover:text-gray-900">对话</router-link>
        </nav>
      </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 py-8">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  console.log('GitHub Star Helper loaded')
})
</script>
