<template>
  <div class="space-y-8">
    <section class="text-center py-12">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">
        GitHub Star Helper
      </h1>
      <p class="text-lg text-gray-600 mb-8">
        智能分析你的 GitHub 星标仓库，发现技术宝藏
      </p>
      <div class="flex gap-4 justify-center">
        <router-link
          to="/search"
          class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          开始搜索
        </router-link>
        <router-link
          to="/chat"
          class="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          开始对话
        </router-link>
      </div>
    </section>

    <section>
      <h2 class="text-2xl font-bold text-gray-900 mb-4">快速统计</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white p-6 rounded-lg shadow-sm">
          <div class="text-3xl font-bold text-blue-600">{{ stats.totalRepos }}</div>
          <div class="text-gray-600">总仓库数</div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-sm">
          <div class="text-3xl font-bold text-green-600">{{ stats.totalCategories }}</div>
          <div class="text-gray-600">分类数量</div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-sm">
          <div class="text-3xl font-bold text-purple-600">{{ stats.topLanguage }}</div>
          <div class="text-gray-600">主要语言</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const stats = ref({
  totalRepos: 0,
  totalCategories: 0,
  topLanguage: '-'
})

onMounted(async () => {
  try {
    const response = await fetch('/api/stats')
    const data = await response.json()
    stats.value = {
      totalRepos: data.data?.total_repos || 0,
      totalCategories: Object.keys(data.data?.categories || {}).length,
      topLanguage: data.data?.top_language || '-'
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
})
</script>
