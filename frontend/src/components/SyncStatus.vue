<template>
  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <span>🔄</span>
        <span>数据同步</span>
      </h3>
      <div class="flex items-center gap-2">
        <span
          v-if="status"
          :class="[
            'w-2 h-2 rounded-full',
            isSyncing ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'
          ]"
        ></span>
        <span v-if="isSyncing" class="text-sm text-gray-600 dark:text-gray-400">同步中...</span>
      </div>
    </div>

    <div v-if="status" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
      <div class="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ status.total_repos }}</div>
        <div class="text-xs text-gray-600 dark:text-gray-400">总仓库</div>
      </div>
      <div class="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ status.deleted_repos }}</div>
        <div class="text-xs text-gray-600 dark:text-gray-400">已删除</div>
      </div>
      <div class="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
        <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ status.pending_updates }}</div>
        <div class="text-xs text-gray-600 dark:text-gray-400">待更新</div>
      </div>
      <div class="text-center p-3 bg-gray-50 dark:bg-gray-900/20 rounded-lg">
        <div class="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
          {{ lastSyncTime }}
        </div>
        <div class="text-xs text-gray-600 dark:text-gray-400">最后同步</div>
      </div>
    </div>

    <div v-else class="mb-4 text-center py-4 text-gray-500 dark:text-gray-400">
      加载同步状态中...
    </div>

    <div class="flex flex-wrap gap-2">
      <button
        @click="handleManualSync"
        :disabled="isSyncing"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition flex items-center gap-2"
      >
        <svg v-if="isSyncing" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>{{ isSyncing ? '同步中...' : '增量同步' }}</span>
      </button>

      <button
        @click="handleFullSync"
        :disabled="isSyncing"
        class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition flex items-center gap-2"
      >
        <svg v-if="isSyncing" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>全量同步</span>
      </button>

      <router-link
        to="/sync/history"
        class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
      >
        同步历史
      </router-link>

      <router-link
        v-if="status && status.deleted_repos > 0"
        to="/sync/deleted"
        class="px-4 py-2 border border-orange-300 text-orange-700 rounded-lg hover:bg-orange-50 transition"
      >
        已删除 ({{ status.deleted_repos }})
      </router-link>
    </div>

    <div v-if="error" class="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
      <div class="flex items-center gap-2 text-red-700 dark:text-red-400">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        <span class="text-sm">{{ error }}</span>
      </div>
    </div>

    <div v-if="successMessage" class="mt-3 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
      <div class="flex items-center gap-2 text-green-700 dark:text-green-400">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <span class="text-sm">{{ successMessage }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { syncApi, type SyncStatus } from '@/api/sync'

const status = ref<SyncStatus | null>(null)
const isSyncing = ref(false)
const error = ref<string | null>(null)
const successMessage = ref<string | null>(null)

const lastSyncTime = computed(() => {
  if (!status.value?.last_sync_at) return '从未同步'

  const date = new Date(status.value.last_sync_at)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`

  return date.toLocaleDateString('zh-CN')
})

async function loadStatus() {
  try {
    status.value = await syncApi.getStatus()
    error.value = null
  } catch (err) {
    console.error('Failed to load sync status:', err)
    error.value = '加载同步状态失败'
  }
}

async function handleManualSync() {
  error.value = null
  successMessage.value = null
  isSyncing.value = true

  try {
    const result = await syncApi.manualSync({ full_sync: false })
    successMessage.value = result.message || '增量同步已启动，请稍后刷新查看结果'

    // Refresh status after a delay
    setTimeout(() => {
      loadStatus()
      isSyncing.value = false
    }, 3000)
  } catch (err) {
    console.error('Failed to start manual sync:', err)
    error.value = '启动同步失败，请稍后重试'
    isSyncing.value = false
  }
}

async function handleFullSync() {
  error.value = null
  successMessage.value = null
  isSyncing.value = true

  try {
    const result = await syncApi.manualSync({ full_sync: true })
    successMessage.value = result.message || '全量同步已启动，请稍后刷新查看结果'

    // Refresh status after a delay
    setTimeout(() => {
      loadStatus()
      isSyncing.value = false
    }, 5000)
  } catch (err) {
    console.error('Failed to start full sync:', err)
    error.value = '启动同步失败，请稍后重试'
    isSyncing.value = false
  }
}

onMounted(() => {
  loadStatus()
})
</script>
