<template>
  <div v-if="repo" class="max-w-4xl mx-auto">
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm p-6">
      <div class="flex justify-between items-start mb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ repo.name_with_owner }}</h1>
          <p v-if="repo.description" class="text-gray-600 dark:text-gray-400 mt-2">{{ repo.description }}</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="handleReanalyze"
            :disabled="isReanalyzing"
            class="p-2 bg-purple-600 dark:bg-purple-700 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-600 disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition"
            :title="isReanalyzing ? '正在分析中...' : '使用 AI 重新分析此仓库'"
          >
            <svg v-if="isReanalyzing" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </button>
          <a
            :href="`https://github.com/${repo.name_with_owner}`"
            target="_blank"
            class="p-2 bg-gray-900 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-800 dark:hover:bg-gray-600 transition"
            title="查看 GitHub"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>
            </svg>
          </a>
        </div>
      </div>

      <div class="flex gap-4 mb-6 flex-wrap">
        <span v-if="repo.primary_language" class="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-full text-sm">
          {{ repo.primary_language }}
        </span>
        <span class="px-3 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 rounded-full text-sm">
          ⭐ {{ formatStarCount(repo.stargazer_count) }} stars
        </span>
        <span v-if="repo.starred_at" class="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 rounded-full text-sm">
          Starred {{ formatRelativeTime(repo.starred_at) }}
        </span>
        <span v-if="repo.fork_count !== undefined" class="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-full text-sm">
          🍴 {{ formatStarCount(repo.fork_count) }} forks
        </span>
        <span v-if="lastAnalyzedTime" class="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 rounded-full text-sm">
          🤖 分析于 {{ lastAnalyzedTime }}
        </span>
      </div>

      <!-- Language Distribution -->
      <div v-if="repo.languages && repo.languages.length > 0" class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-3">语言分布</h2>
        <div class="space-y-2">
          <div
            v-for="lang in repo.languages"
            :key="lang.name"
            class="flex items-center gap-3"
          >
            <span class="w-16 text-sm text-gray-700 dark:text-gray-300 truncate">{{ lang.name }}</span>
            <div class="flex-1 h-6 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-blue-500 to-blue-600 dark:from-blue-400 dark:to-blue-500 rounded-full transition-all duration-500"
                :style="{ width: `${lang.percent}%` }"
              ></div>
            </div>
            <span class="w-12 text-right text-sm text-gray-600 dark:text-gray-400">{{ lang.percent }}%</span>
          </div>
        </div>
      </div>

      <!-- Re-analyze Message -->
      <div v-if="reanalyzeMessage" :class="[
        'mb-4 p-3 rounded-lg',
        reanalyzeMessage.type === 'success'
          ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
          : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
      ]">
        <div class="flex items-center gap-2 text-sm"
          :class="reanalyzeMessage.type === 'success' ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'"
        >
          <svg v-if="reanalyzeMessage.type === 'success'" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <span>{{ reanalyzeMessage.text }}</span>
        </div>
      </div>

      <div v-if="repo.summary" class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-2">简介</h2>
        <p class="text-gray-700 dark:text-gray-300">{{ repo.summary }}</p>
      </div>

      <div v-if="repo.categories?.length" class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-2">分类</h2>
        <div class="flex gap-2 flex-wrap">
          <span
            v-for="cat in repo.categories"
            :key="cat"
            class="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm"
          >
            {{ cat }}
          </span>
        </div>
      </div>

      <div v-if="repo.tech_stack?.length" class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-2">技术栈</h2>
        <div class="flex gap-2 flex-wrap">
          <span
            v-for="tech in repo.tech_stack"
            :key="tech"
            class="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-200 rounded-full text-sm"
          >
            {{ tech }}
          </span>
        </div>
      </div>

      <div class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-2">收藏</h2>
        <CollectionManager :repo-id="nameWithOwner" />
      </div>

      <div class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-2">我的笔记</h2>
        <NoteEditor :repo-id="nameWithOwner" @update="handleNoteUpdate" />
      </div>

      <div class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-2">标签</h2>
        <TagManager :repo-id="nameWithOwner" @update="handleTagUpdate" />
      </div>
    </div>
  </div>

  <div v-else-if="isLoading" class="text-center py-12">
    <div class="text-gray-600 dark:text-gray-400">加载中...</div>
  </div>

  <div v-else class="text-center py-12">
    <div class="text-gray-600 dark:text-gray-400">仓库未找到</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useReposStore } from '../stores/repos'
import type { Repository } from '../types'
import CollectionManager from '../components/CollectionManager.vue'
import NoteEditor from '../components/NoteEditor.vue'
import TagManager from '../components/TagManager.vue'
import { syncApi } from '@/api/sync'
import { formatStarCount, formatRelativeTime } from '@/utils/format'

const route = useRoute()
const reposStore = useReposStore()

const repo = ref<Repository | null>(null)
const isLoading = ref(true)
const isReanalyzing = ref(false)
const reanalyzeMessage = ref<{ type: 'success' | 'error'; text: string } | null>(null)

const nameWithOwner = computed(() => repo.value?.name_with_owner || '')

const lastAnalyzedTime = computed(() => {
  if (!repo.value?.last_analyzed_at) return null
  return formatRelativeTime(repo.value.last_analyzed_at)
})

async function handleReanalyze() {
  if (!nameWithOwner.value) return

  reanalyzeMessage.value = null
  isReanalyzing.value = true

  try {
    const result = await syncApi.reanalyzeRepo(nameWithOwner.value)
    reanalyzeMessage.value = {
      type: 'success',
      text: result.message || '重新分析已加入队列，请稍后刷新查看结果'
    }

    // Reload repo data after a delay to get updated analysis
    setTimeout(async () => {
      const data = await reposStore.loadRepo(nameWithOwner.value)
      repo.value = data
      isReanalyzing.value = false
    }, 5000)
  } catch (error) {
    console.error('Failed to reanalyze repo:', error)
    reanalyzeMessage.value = {
      type: 'error',
      text: '重新分析失败，请稍后重试'
    }
    isReanalyzing.value = false
  }
}

function handleNoteUpdate() {
  // Notes updated - could trigger refresh if needed
}

function handleTagUpdate() {
  // Tags updated - could trigger refresh if needed
}

onMounted(async () => {
  const { owner, name } = route.params
  const repoNameWithOwner = `${owner}/${name}`

  const data = await reposStore.loadRepo(repoNameWithOwner)
  repo.value = data
  isLoading.value = false
})
</script>
