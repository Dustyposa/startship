<template>
  <div class="space-y-8">
    <!-- Hero Section -->
    <section class="text-center py-8 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">
        GitHub Star Helper
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
    <section>
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
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
})
</script>
