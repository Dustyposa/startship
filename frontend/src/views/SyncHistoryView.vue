<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">同步历史</h1>
      <router-link to="/" class="text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        返回首页
      </router-link>
    </div>

    <div v-if="isLoading" class="text-center py-8">
      <div class="text-gray-600 dark:text-gray-400 text-sm">加载中...</div>
    </div>

    <div v-else-if="history.length === 0" class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
      <div class="text-3xl mb-2">📋</div>
      <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-1">暂无同步历史</h2>
      <p class="text-gray-600 dark:text-gray-400 text-sm mb-3">开始首次同步以记录同步历史</p>
      <router-link to="/" class="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition">
        前往首页
      </router-link>
    </div>

    <div v-else class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-200 dark:divide-gray-700">
      <div
        v-for="item in history"
        :key="item.id"
        class="p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition"
      >
        <div class="flex items-start justify-between gap-3">
          <!-- 左侧：类型、时间、状态 -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span :class="['px-1.5 py-0.5 text-xs font-medium rounded', item.sync_type === 'full' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300']">
                {{ item.sync_type === 'full' ? '全量' : '增量' }}
              </span>
              <span v-if="item.completed_at" class="text-xs text-green-600 dark:text-green-400">● 完成</span>
              <span v-else-if="item.error_message" class="text-xs text-red-600 dark:text-red-400">● 失败</span>
              <span v-else class="text-xs text-yellow-600 dark:text-yellow-400">● 进行中</span>
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ formatDateTime(item.started_at) }}
            </div>
            <div v-if="item.error_message" class="text-xs text-red-600 dark:text-red-400 mt-1 truncate">
              {{ item.error_message }}
            </div>
          </div>

          <!-- 右侧：统计数据（紧凑行内显示） -->
          <div v-if="item.completed_at || item.error_message" class="flex items-center gap-3 text-xs flex-shrink-0">
            <span v-if="item.stats_added > 0" class="flex items-center gap-1 text-green-600 dark:text-green-400">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
              {{ item.stats_added }}
            </span>
            <span v-if="item.stats_updated > 0" class="flex items-center gap-1 text-blue-600 dark:text-blue-400">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
              {{ item.stats_updated }}
            </span>
            <span v-if="item.stats_deleted > 0" class="flex items-center gap-1 text-orange-600 dark:text-orange-400">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"/></svg>
              {{ item.stats_deleted }}
            </span>
            <span v-if="item.stats_failed > 0" class="flex items-center gap-1 text-red-600 dark:text-red-400">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              {{ item.stats_failed }}
            </span>
          </div>

          <!-- 进行中动画 -->
          <div v-else class="flex items-center gap-2 text-yellow-600 dark:text-yellow-400 text-xs flex-shrink-0">
            <svg class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            同步中
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { syncApi, type SyncHistory } from '@/api/sync'

const history = ref<SyncHistory[]>([])
const isLoading = ref(true)

onMounted(async () => {
  try {
    const data = await syncApi.getHistory(50)
    history.value = data.results
  } catch (error) {
    console.error('Failed to load sync history:', error)
  } finally {
    isLoading.value = false
  }
})

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>
