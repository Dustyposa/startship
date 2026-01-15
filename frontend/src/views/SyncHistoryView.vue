<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">同步历史</h1>
      <router-link
        to="/"
        class="text-blue-600 hover:text-blue-700 flex items-center gap-1"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        返回首页
      </router-link>
    </div>

    <div v-if="isLoading" class="text-center py-12">
      <div class="text-gray-600 dark:text-gray-400">加载中...</div>
    </div>

    <div v-else-if="history.length === 0" class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-12 text-center">
      <div class="text-4xl mb-4">📋</div>
      <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">暂无同步历史</h2>
      <p class="text-gray-600 dark:text-gray-400 mb-4">开始首次同步以记录同步历史</p>
      <router-link
        to="/"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        前往首页
      </router-link>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="item in history"
        :key="item.id"
        class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span
                :class="[
                  'px-2 py-1 text-xs font-medium rounded',
                  item.sync_type === 'full' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                ]"
              >
                {{ item.sync_type === 'full' ? '全量同步' : '增量同步' }}
              </span>
              <span
                v-if="item.completed_at"
                class="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-800"
              >
                完成
              </span>
              <span
                v-else
                class="px-2 py-1 text-xs font-medium rounded bg-yellow-100 text-yellow-800"
              >
                进行中
              </span>
              <span v-if="item.error_message" class="px-2 py-1 text-xs font-medium rounded bg-red-100 text-red-800">
                失败
              </span>
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              开始于 {{ formatDateTime(item.started_at) }}
            </div>
            <div v-if="item.completed_at" class="text-sm text-gray-600 dark:text-gray-400">
              完成于 {{ formatDateTime(item.completed_at) }}
            </div>
          </div>
          <div v-if="item.error_message" class="ml-4 text-red-600 dark:text-red-400 text-sm max-w-xs">
            {{ item.error_message }}
          </div>
        </div>

        <div v-if="!item.completed_at && !item.error_message" class="flex items-center gap-2 text-yellow-600 dark:text-yellow-400 text-sm">
          <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>同步进行中，请稍后刷新查看结果...</span>
        </div>

        <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
          <div class="text-center p-2 bg-green-50 dark:bg-green-900/20 rounded">
            <div class="text-lg font-bold text-green-600 dark:text-green-400">+{{ item.stats_added }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">新增</div>
          </div>
          <div class="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
            <div class="text-lg font-bold text-blue-600 dark:text-blue-400">~{{ item.stats_updated }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">更新</div>
          </div>
          <div class="text-center p-2 bg-orange-50 dark:bg-orange-900/20 rounded">
            <div class="text-lg font-bold text-orange-600 dark:text-orange-400">-{{ item.stats_deleted }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">删除</div>
          </div>
          <div v-if="item.stats_failed > 0" class="text-center p-2 bg-red-50 dark:bg-red-900/20 rounded">
            <div class="text-lg font-bold text-red-600 dark:text-red-400">{{ item.stats_failed }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">失败</div>
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
