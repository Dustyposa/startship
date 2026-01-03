<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <div class="flex justify-between items-center">
          <h1 class="text-xl font-bold text-gray-900">⭐ GitHub Star Helper</h1>

          <!-- Desktop Navigation -->
          <nav class="hidden md:flex gap-6">
            <router-link to="/" class="text-gray-600 hover:text-blue-600 font-medium transition">首页</router-link>
            <router-link to="/init" class="text-gray-600 hover:text-blue-600 font-medium transition">初始化</router-link>
            <router-link to="/search" class="text-gray-600 hover:text-blue-600 font-medium transition">搜索</router-link>
            <router-link to="/chat" class="text-gray-600 hover:text-blue-600 font-medium transition">对话</router-link>
            <router-link to="/trends" class="text-gray-600 hover:text-blue-600 font-medium transition">趋势</router-link>
            <router-link to="/network" class="text-gray-600 hover:text-blue-600 font-medium transition">网络</router-link>
          </nav>

          <!-- Mobile Menu Button -->
          <button
            @click="mobileMenuOpen = !mobileMenuOpen"
            class="md:hidden p-2 rounded-lg hover:bg-gray-100 transition"
            aria-label="Toggle menu"
          >
            <svg v-if="!mobileMenuOpen" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Mobile Navigation Menu -->
        <nav
          v-show="mobileMenuOpen"
          class="md:hidden mt-4 pb-4 space-y-2 border-t pt-4 animate-fade-in"
        >
          <router-link
            to="/"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition"
          >
            🏠 首页
          </router-link>
          <router-link
            to="/init"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition"
          >
            ⚙️ 初始化
          </router-link>
          <router-link
            to="/search"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition"
          >
            🔍 搜索
          </router-link>
          <router-link
            to="/chat"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition"
          >
            💬 对话
          </router-link>
          <router-link
            to="/trends"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition"
          >
            📈 趋势分析
          </router-link>
          <router-link
            to="/network"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition"
          >
            🕸️ 关系网络
          </router-link>
        </nav>
      </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 py-8">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const mobileMenuOpen = ref(false)
</script>

<style>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.2s ease-out;
}
</style>
