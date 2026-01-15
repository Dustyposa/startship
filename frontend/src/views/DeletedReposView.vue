<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">已删除的仓库</h1>
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

    <div v-else-if="repos.length === 0" class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-12 text-center">
      <div class="text-4xl mb-4">🗑️</div>
      <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">暂无已删除仓库</h2>
      <p class="text-gray-600 dark:text-gray-400">取消星标的仓库会显示在这里，你的笔记和标签会被保留</p>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="repo in repos"
        :key="repo.name_with_owner"
        class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-2">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ repo.name_with_owner }}
              </h3>
              <span class="px-2 py-1 text-xs font-medium rounded bg-orange-100 text-orange-800">
                已删除
              </span>
            </div>
            <p v-if="repo.description" class="text-gray-600 dark:text-gray-400 text-sm mb-2">
              {{ repo.description }}
            </p>
            <div class="flex flex-wrap gap-2 text-sm">
              <span v-if="repo.primary_language" class="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                {{ repo.primary_language }}
              </span>
              <span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">
                ⭐ {{ repo.stargazer_count }}
              </span>
              <span class="px-2 py-1 bg-gray-100 text-gray-800 rounded">
                Starred {{ formatRelativeTime(repo.starred_at) }}
              </span>
              <span v-if="repo.last_synced_at" class="px-2 py-1 bg-purple-100 text-purple-800 rounded">
                同步于 {{ formatDateTime(repo.last_synced_at) }}
              </span>
            </div>
          </div>
          <div class="ml-4 flex flex-col gap-2">
            <button
              @click="handleRestore(repo.name_with_owner)"
              :disabled="isRestoring === repo.name_with_owner"
              class="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition flex items-center gap-1"
            >
              <svg v-if="isRestoring === repo.name_with_owner" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>{{ isRestoring === repo.name_with_owner ? '恢复中...' : '恢复' }}</span>
            </button>
            <a
              :href="`https://github.com/${repo.name_with_owner}`"
              target="_blank"
              class="px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition text-center"
            >
              查看 GitHub
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div
      v-if="toast.show"
      :class="[
        'fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg z-50',
        toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
      ]"
    >
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { syncApi, type DeletedRepo } from '@/api/sync'

const repos = ref<DeletedRepo[]>([])
const isLoading = ref(true)
const isRestoring = ref<string | null>(null)

const toast = ref({
  show: false,
  message: '',
  type: 'success' as 'success' | 'error'
})

function showToast(message: string, type: 'success' | 'error' = 'success') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

async function loadDeletedRepos() {
  try {
    const data = await syncApi.getDeletedRepos(100)
    repos.value = data.results
  } catch (error) {
    console.error('Failed to load deleted repos:', error)
    showToast('加载已删除仓库失败', 'error')
  } finally {
    isLoading.value = false
  }
}

async function handleRestore(nameWithOwner: string) {
  isRestoring.value = nameWithOwner
  try {
    const result = await syncApi.restoreRepo(nameWithOwner)
    showToast(result.message || `已恢复 ${nameWithOwner}`)
    // Reload the list
    await loadDeletedRepos()
  } catch (error) {
    console.error('Failed to restore repo:', error)
    showToast(`恢复 ${nameWithOwner} 失败`, 'error')
  } finally {
    isRestoring.value = null
  }
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  const diffMonths = Math.floor(diffDays / 30)
  const diffYears = Math.floor(diffDays / 365)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 30) return `${diffDays}天前`
  if (diffMonths < 12) return `${diffMonths}个月前`
  return `${diffYears}年前`
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

onMounted(() => {
  loadDeletedRepos()
})
</script>
