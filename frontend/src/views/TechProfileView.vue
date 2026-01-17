<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white">🧠 技术画像</h1>
      <button @click="regenerate" :disabled="isLoading" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50">
        {{ isLoading ? '分析中...' : '重新生成' }}
      </button>
    </div>

    <div v-if="isLoading" class="text-center py-12 text-gray-600 dark:text-gray-400">
      <div class="flex justify-center"><svg class="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg></div>
      <p class="mt-2">正在分析你的技术栈...</p>
    </div>

    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
      {{ error }}
    </div>

    <div v-else-if="profile" class="space-y-6">
      <section class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">学习阶段</h2>
        <div class="text-center">
          <div class="text-4xl font-bold" :class="stageColor">{{ stageText }}</div>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">基于你收藏项目的平均 star 数评估</p>
        </div>
      </section>

      <section class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">关注领域</h2>
        <div class="flex flex-wrap gap-2">
          <span v-for="domain in profile.domains" :key="domain" class="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full text-sm font-medium">
            {{ domain }}
          </span>
        </div>
      </section>

      <section class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">洞察</h2>
        <ul class="space-y-2">
          <li v-for="(insight, i) in profile.insights" :key="i" class="flex items-start gap-2">
            <span class="text-blue-600">•</span>
            <span class="text-gray-700 dark:text-gray-300">{{ insight }}</span>
          </li>
        </ul>
      </section>

      <section v-if="profile.trends.length > 0" class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">兴趣趋势</h2>
        <div class="space-y-3">
          <div v-for="trend in profile.trends" :key="trend.period" class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{ trend.period }}</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ trend.top_language }}</span>
          </div>
        </div>
      </section>
    </div>

    <div v-else class="text-center py-12 text-gray-600 dark:text-gray-400">
      <p>暂无技术画像数据</p>
      <button @click="regenerate" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
        生成画像
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProfile } from '@/composables/useProfile'
import { useReposStore } from '@/stores/repos'

const { profile, isLoading, error, generate } = useProfile()
const reposStore = useReposStore()

const stageText = computed(() => {
  const stageMap = {
    beginner: '初学者',
    intermediate: '进阶者',
    advanced: '高级开发者'
  } as const
  return profile.value ? stageMap[profile.value.learning_stage] : ''
})

const stageColor = computed(() => {
  const colorMap = {
    beginner: 'text-green-600',
    intermediate: 'text-blue-600',
    advanced: 'text-purple-600'
  } as const
  return profile.value ? colorMap[profile.value.learning_stage] : ''
})

async function regenerate() {
  await generate(reposStore.repos)
}

onMounted(() => {
  if (!profile.value) regenerate()
})
</script>
