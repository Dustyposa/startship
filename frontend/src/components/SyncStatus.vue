<template>
  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm p-6">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <span>🔄</span>
          <span>数据同步</span>
        </h3>
        <!-- Sync Status Indicator -->
        <span
          v-if="status"
          :class="[
            'w-2 h-2 rounded-full',
            isSyncing ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'
          ]"
          :title="isSyncing ? '正在同步' : '系统正常'"
        ></span>
        <span v-if="isSyncing" class="text-sm text-gray-600 dark:text-gray-400">同步中...</span>
      </div>

      <!-- Sync History Icon with Hover -->
      <div class="relative" @mouseenter="loadHistory" @mouseleave="showHistory = false">
        <button
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
          title="同步历史"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
        <!-- History Popover -->
        <div
          v-if="showHistory && history.length > 0"
          class="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50"
          @mouseenter="showHistory = true"
          @mouseleave="showHistory = false"
        >
          <div class="p-3">
            <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">同步历史</h4>
            <div class="space-y-2 max-h-60 overflow-y-auto">
              <div
                v-for="item in history"
                :key="item.id"
                class="text-xs p-2 bg-gray-50 dark:bg-gray-700 rounded"
              >
                <div class="flex justify-between items-center mb-1">
                  <span class="font-medium text-gray-700 dark:text-gray-300">{{ formatSyncTime(item.started_at) }}</span>
                  <span
                    :class="[
                      'px-1.5 py-0.5 rounded text-[10px]',
                      item.stats_failed > 0
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                        : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                    ]"
                  >
                    {{ item.stats_failed > 0 ? '失败' : '成功' }}
                  </span>
                </div>
                <div class="text-gray-500 dark:text-gray-400">
                  +{{ item.stats_added }} ~{{ item.stats_updated }} -{{ item.stats_deleted }}
                </div>
              </div>
            </div>
            <router-link
              to="/sync/history"
              class="block text-center text-xs text-blue-600 dark:text-blue-400 hover:underline mt-2 pt-2 border-t border-gray-200 dark:border-gray-700"
              @click="showHistory = false"
            >
              查看全部 →
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <div v-if="status" class="grid grid-cols-2 gap-4 mb-4">
      <div class="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ status.total_repos }}</div>
        <div class="text-xs text-gray-600 dark:text-gray-400">总仓库</div>
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

    <div class="flex gap-2">
      <button
        @click="handleSync"
        :disabled="isSyncing"
        class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
      >
        <svg v-if="isSyncing" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>{{ isSyncing ? '同步中...' : '同步' }}</span>
      </button>
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
import { syncApi, type SyncStatus, type SyncHistory } from '@/api/sync'

const status = ref<SyncStatus | null>(null)
const isSyncing = ref(false)
const error = ref<string | null>(null)
const successMessage = ref<string | null>(null)
const showHistory = ref(false)
const history = ref<SyncHistory[]>([])

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

function formatSyncTime(dateStr: string): string {
  const date = new Date(dateStr)
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
}

async function loadStatus() {
  try {
    status.value = await syncApi.getStatus()
    error.value = null
  } catch (err) {
    console.error('Failed to load sync status:', err)
    error.value = '加载同步状态失败'
  }
}

async function loadHistory() {
  if (history.value.length > 0) {
    showHistory.value = true
    return
  }
  try {
    const result = await syncApi.getHistory(5)
    history.value = result.results
    showHistory.value = true
  } catch (err) {
    console.error('Failed to load history:', err)
  }
}

async function handleSync() {
  error.value = null
  successMessage.value = null
  isSyncing.value = true

  try {
    const result = await syncApi.manualSync()
    successMessage.value = result.message || '同步已启动，请稍后刷新查看结果'

    // Refresh status after a delay
    setTimeout(() => {
      loadStatus()
      isSyncing.value = false
    }, 3000)
  } catch (err) {
    console.error('Failed to start sync:', err)
    error.value = '启动同步失败，请稍后重试'
    isSyncing.value = false
  }
}

onMounted(() => {
  loadStatus()
})
</script>
