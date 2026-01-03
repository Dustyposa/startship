<template>
  <div class="space-y-8">
    <!-- Onboarding Banner for First-Time Users -->
    <div v-if="showOnboarding" class="relative overflow-hidden bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-8 text-white shadow-lg">
      <div class="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-white opacity-10 rounded-full"></div>
      <div class="absolute bottom-0 left-0 -mb-4 -ml-4 w-32 h-32 bg-white opacity-10 rounded-full"></div>

      <div class="relative z-10">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-4">
              <span class="text-4xl">👋</span>
              <div>
                <h2 class="text-2xl font-bold">欢迎使用 GitHub Star Helper!</h2>
                <p class="text-blue-100">智能管理你的星标仓库，发现技术宝藏</p>
              </div>
            </div>

            <div class="grid md:grid-cols-3 gap-4 mb-6">
              <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div class="text-2xl mb-2">🔍</div>
                <h3 class="font-semibold mb-1">智能搜索</h3>
                <p class="text-sm text-blue-100">按分类、语言快速筛选</p>
              </div>
              <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div class="text-2xl mb-2">💬</div>
                <h3 class="font-semibold mb-1">AI 对话</h3>
                <p class="text-sm text-blue-100">自然语言查询仓库</p>
              </div>
              <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div class="text-2xl mb-2">🕸️</div>
                <h3 class="font-semibold mb-1">关系网络</h3>
                <p class="text-sm text-blue-100">可视化项目关联</p>
              </div>
            </div>

            <div class="flex flex-wrap gap-3">
              <router-link
                to="/init"
                @click="dismissOnboarding"
                class="px-6 py-3 bg-white text-blue-600 font-semibold rounded-lg hover:bg-blue-50 transition shadow-lg"
              >
                🚀 立即开始初始化
              </router-link>
              <button
                @click="dismissOnboarding"
                class="px-6 py-3 bg-white/10 backdrop-blur-sm text-white font-semibold rounded-lg hover:bg-white/20 transition"
              >
                稍后再说
              </button>
            </div>
          </div>

          <button
            @click="dismissOnboarding"
            class="ml-4 p-2 hover:bg-white/10 rounded-lg transition"
            aria-label="关闭"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State for Non-Initialized Users -->
    <div v-else-if="stats.total_repositories === 0" class="bg-white rounded-xl shadow-sm p-12 text-center">
      <div class="text-6xl mb-4">📭</div>
      <h2 class="text-2xl font-bold text-gray-900 mb-2">还没有数据</h2>
      <p class="text-gray-600 mb-6">请先初始化系统，从你的 GitHub 星标仓库中获取数据</p>
      <router-link
        to="/init"
        class="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition shadow-lg"
      >
        <span>前往初始化</span>
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </router-link>
    </div>

    <!-- Hero Section -->
    <section v-else class="text-center py-8 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">
        ⭐ GitHub Star Helper
      </h1>
      <p class="text-lg text-gray-600 mb-6">
        智能分析你的 GitHub 星标仓库，发现技术宝藏
      </p>
      <div class="flex gap-3 justify-center flex-wrap">
        <router-link
          to="/search"
          class="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          🔍 搜索仓库
        </router-link>
        <router-link
          to="/chat"
          class="px-5 py-2.5 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition"
        >
          💬 智能对话
        </router-link>
        <router-link
          to="/network"
          class="px-5 py-2.5 border border-purple-600 text-purple-600 rounded-lg hover:bg-purple-50 transition"
        >
          🕸️ 关系网络
        </router-link>
      </div>
    </section>

    <!-- Quick Stats -->
    <section v-if="stats.total_repositories > 0">
      <h2 class="text-xl font-bold text-gray-900 mb-4">📊 数据概览</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-blue-500">
          <div class="text-2xl font-bold text-blue-600">{{ displayStats.totalRepos }}</div>
          <div class="text-sm text-gray-600">总仓库数</div>
        </div>
        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-green-500">
          <div class="text-2xl font-bold text-green-600">{{ displayStats.totalCategories }}</div>
          <div class="text-sm text-gray-600">分类数量</div>
        </div>
        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-purple-500">
          <div class="text-2xl font-bold text-purple-600">{{ displayStats.topLanguage }}</div>
          <div class="text-sm text-gray-600">主要语言</div>
        </div>
        <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-orange-500">
          <div class="text-2xl font-bold text-orange-600">{{ displayStats.totalConversations }}</div>
          <div class="text-sm text-gray-600">对话数</div>
        </div>
      </div>
    </section>

    <!-- Feature Cards -->
    <section>
      <h2 class="text-xl font-bold text-gray-900 mb-4">🚀 快速功能</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Search Card -->
        <router-link to="/search" class="block group">
          <div class="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition">
            <div class="text-4xl mb-3">🔍</div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">仓库搜索</h3>
            <p class="text-gray-600 text-sm">按分类、语言、星标数搜索你的仓库</p>
            <div class="mt-4 text-blue-600 text-sm group-hover:underline">立即搜索 →</div>
          </div>
        </router-link>

        <!-- Chat Card -->
        <router-link to="/chat" class="block group">
          <div class="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition">
            <div class="text-4xl mb-3">💬</div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">智能对话</h3>
            <p class="text-gray-600 text-sm">自然语言查询，智能意图识别</p>
            <div class="mt-4 text-blue-600 text-sm group-hover:underline">开始对话 →</div>
          </div>
        </router-link>

        <!-- Network Card -->
        <router-link to="/network" class="block group">
          <div class="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition">
            <div class="text-4xl mb-3">🕸️</div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">关系网络</h3>
            <p class="text-gray-600 text-sm">可视化仓库之间的关联关系</p>
            <div class="mt-4 text-blue-600 text-sm group-hover:underline">查看网络 →</div>
          </div>
        </router-link>

        <!-- Trends Card -->
        <router-link to="/trends" class="block group">
          <div class="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition">
            <div class="text-4xl mb-3">📈</div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">趋势分析</h3>
            <p class="text-gray-600 text-sm">Star 时间线、语言趋势、主题演变</p>
            <div class="mt-4 text-blue-600 text-sm group-hover:underline">查看趋势 →</div>
          </div>
        </router-link>

        <!-- Init Card -->
        <router-link to="/init" class="block group">
          <div class="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition">
            <div class="text-4xl mb-3">⚙️</div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">数据初始化</h3>
            <p class="text-gray-600 text-sm">从 GitHub 同步你的星标仓库</p>
            <div class="mt-4 text-blue-600 text-sm group-hover:underline">管理数据 →</div>
          </div>
        </router-link>

        <!-- About Card -->
        <div class="bg-gradient-to-br from-blue-500 to-purple-600 p-6 rounded-lg shadow-sm text-white">
          <div class="text-4xl mb-3">ℹ️</div>
          <h3 class="text-lg font-semibold mb-2">关于</h3>
          <p class="text-sm opacity-90 mb-4">基于 AI 的 GitHub 星标仓库管理和分析工具，帮助你发现和组织技术资源。</p>
          <div class="text-sm opacity-75">Stage 4: 网络可视化</div>
        </div>
      </div>
    </section>

    <!-- Top Categories -->
    <section v-if="topCategories.length > 0">
      <h2 class="text-xl font-bold text-gray-900 mb-4">🏷️ 热门分类</h2>
      <div class="flex flex-wrap gap-2">
        <router-link
          v-for="count in topCategories"
          :key="count[0]"
          :to="`/search?category=${encodeURIComponent(count[0])}`"
          class="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:border-blue-500 hover:text-blue-600 transition"
        >
          {{ count[0] }} <span class="text-gray-500">({{ count[1] }})</span>
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

interface Stats {
  total_repositories: number
  total_conversations: number
  categories: Record<string, number>
  top_language: string | null
}

const stats = ref<Stats>({
  total_repositories: 0,
  total_conversations: 0,
  categories: {},
  top_language: null
})

const showOnboarding = ref(false)

// Check if user has seen onboarding
const hasSeenOnboarding = () => {
  return localStorage.getItem('hasSeenOnboarding') === 'true'
}

// Dismiss onboarding
const dismissOnboarding = () => {
  localStorage.setItem('hasSeenOnboarding', 'true')
  showOnboarding.value = false
}

const displayStats = computed(() => ({
  totalRepos: stats.value.total_repositories,
  totalCategories: Object.keys(stats.value.categories || {}).length,
  totalConversations: stats.value.total_conversations,
  topLanguage: stats.value.top_language || '-'
}))

const topCategories = computed(() => {
  const entries = Object.entries(stats.value.categories || {})
  return entries
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
})

onMounted(async () => {
  try {
    const response = await fetch('/api/stats')
    const data = await response.json()
    stats.value = data.data || stats.value

    // Show onboarding if first time visit
    if (!hasSeenOnboarding()) {
      showOnboarding.value = true
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
})
</script>
