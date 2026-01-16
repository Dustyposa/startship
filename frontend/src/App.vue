<template>
  <div id="app" :class="{'dark': isDark}" class="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
    <header class="bg-white dark:bg-gray-800 shadow-sm sticky top-0 z-50 transition-colors duration-200">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <div class="flex justify-between items-center">
          <h1 class="text-xl font-bold text-gray-900 dark:text-white">⭐ GitHub Star Helper</h1>

          <!-- Desktop Navigation & Controls -->
          <div class="hidden md:flex items-center gap-6">
            <nav class="flex gap-6">
              <router-link to="/" class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition">首页</router-link>
              <router-link to="/init" class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition">初始化</router-link>
              <router-link to="/search" class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition">搜索</router-link>
              <router-link to="/chat" class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition">对话</router-link>
              <router-link to="/trends" class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition">趋势</router-link>
              <router-link to="/network" class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition">网络</router-link>
              <router-link to="/collections" class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition">收藏</router-link>
              <router-link to="/profile" class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition">画像</router-link>
            </nav>

            <!-- Dark Mode Toggle -->
            <DarkModeToggle :is-dark="isDark" @click="toggle" />
          </div>

          <!-- Mobile Menu Button & Dark Mode Toggle -->
          <div class="md:hidden flex items-center gap-2">
            <!-- Dark Mode Toggle (Mobile) -->
            <DarkModeToggle :is-dark="isDark" @click="toggle" />

            <!-- Menu Button -->
            <button
              @click="mobileMenuOpen = !mobileMenuOpen"
              class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
              aria-label="Toggle menu"
            >
              <svg v-if="!mobileMenuOpen" class="w-6 h-6 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
              <svg v-else class="w-6 h-6 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Mobile Navigation Menu -->
        <nav
          v-show="mobileMenuOpen"
          class="md:hidden mt-4 pb-4 space-y-2 border-t border-gray-200 dark:border-gray-700 pt-4 animate-fade-in"
        >
          <router-link
            to="/"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition"
          >
            首页
          </router-link>
          <router-link
            to="/init"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition"
          >
            初始化
          </router-link>
          <router-link
            to="/search"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition"
          >
            搜索
          </router-link>
          <router-link
            to="/chat"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition"
          >
            对话
          </router-link>
          <router-link
            to="/trends"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition"
          >
            趋势分析
          </router-link>
          <router-link
            to="/network"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition"
          >
            关系网络
          </router-link>
          <router-link
            to="/collections"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition"
          >
            收藏
          </router-link>
          <router-link
            to="/profile"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition"
          >
            画像
          </router-link>
        </nav>
      </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 py-8">
      <router-view />
    </main>

    <!-- Keyboard Shortcuts Modal -->
    <div
      v-if="showKeyboardShortcuts"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="showKeyboardShortcuts = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full animate-fade-in">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">键盘快捷键</h2>
          <button
            @click="showKeyboardShortcuts = false"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
            aria-label="关闭"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="space-y-3">
          <div class="flex justify-between items-center">
            <span class="text-gray-700 dark:text-gray-300">显示快捷键</span>
            <kbd class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm font-mono text-gray-900 dark:text-gray-100">⌘K</kbd>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-700 dark:text-gray-300">创建收藏夹</span>
            <kbd class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm font-mono text-gray-900 dark:text-gray-100">⌘N</kbd>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-700 dark:text-gray-300">关闭弹窗</span>
            <kbd class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm font-mono text-gray-900 dark:text-gray-100">Esc</kbd>
          </div>
        </div>
        <p class="mt-4 text-sm text-gray-500 dark:text-gray-400">在 Windows/Linux 上使用 Ctrl 代替 ⌘</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDark } from './composables/useDark'
import { useKeyboard } from './composables/useKeyboard'
import { useCollections } from './composables/useCollections'
import DarkModeToggle from './components/DarkModeToggle.vue'

const mobileMenuOpen = ref(false)
const showKeyboardShortcuts = ref(false)
const { isDark, toggle } = useDark()
const { createCollection } = useCollections()

function handleKeyboardShortcuts() {
  showKeyboardShortcuts.value = true
}

function handleNewCollection() {
  createCollection('新建收藏夹')
}

function handleEscape() {
  showKeyboardShortcuts.value = false
  mobileMenuOpen.value = false
}

useKeyboard({
  'cmd+k': handleKeyboardShortcuts,
  'cmd+n': handleNewCollection,
  'escape': handleEscape
})
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

@keyframes slide-in-right {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slide-in-left {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes bounce-in {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    transform: scale(1.05);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-fade-in {
  animation: fade-in 0.2s ease-out;
}

.animate-slide-in-right {
  animation: slide-in-right 0.3s ease-out;
}

.animate-slide-in-left {
  animation: slide-in-left 0.3s ease-out;
}

.animate-scale-in {
  animation: scale-in 0.2s ease-out;
}

.animate-bounce-in {
  animation: bounce-in 0.4s ease-out;
}

/* Vue transition classes for global use */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Slide fade transition */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s ease-in;
}

.slide-fade-enter-from {
  transform: translateX(20px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateX(-20px);
  opacity: 0;
}

/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
