<template>
  <div class="max-w-2xl mx-auto">
    <div class="bg-white rounded-lg shadow-sm p-8">
      <h1 class="text-2xl font-bold text-gray-900 mb-6">初始化系统</h1>

      <div v-if="initStatus.has_data" class="mb-6 p-4 bg-green-50 text-green-800 rounded-lg">
        系统已初始化，共有 {{ initStatus.repo_count }} 个仓库。
        <router-link to="/search" class="underline hover:text-green-900">开始搜索</router-link>
      </div>

      <form @submit.prevent="startInitialization" class="space-y-6">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 mb-2">
            GitHub 用户名
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            placeholder="your-github-username"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p class="mt-1 text-sm text-gray-500">
            从你的星标仓库中获取数据
          </p>
        </div>

        <div>
          <label for="maxRepos" class="block text-sm font-medium text-gray-700 mb-2">
            最大仓库数 (可选)
          </label>
          <input
            id="maxRepos"
            v-model.number="maxRepos"
            type="number"
            min="1"
            placeholder="全部"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div class="space-y-3">
          <label class="flex items-center gap-3 cursor-pointer">
            <input
              v-model="skipLlm"
              type="checkbox"
              class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <div>
              <span class="text-sm font-medium text-gray-900">跳过 LLM 分析</span>
              <p class="text-xs text-gray-500">加快初始化速度，但会缺少智能分析</p>
            </div>
          </label>

          <label class="flex items-center gap-3 cursor-pointer">
            <input
              v-model="enableSemantic"
              type="checkbox"
              class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <div>
              <span class="text-sm font-medium text-gray-900">启用语义搜索</span>
              <p class="text-xs text-gray-500">更智能的搜索，需要 Ollama 运行 nomic-embed-text 模型</p>
            </div>
          </label>
        </div>

        <div
          v-if="error"
          class="p-4 bg-red-50 text-red-800 rounded-lg text-sm"
        >
          {{ error }}
        </div>

        <div
          v-if="isLoading"
          class="p-4 bg-blue-50 text-blue-800 rounded-lg"
        >
          <div class="flex items-center gap-2">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>正在初始化，请稍候...</span>
          </div>
          <p class="text-sm mt-2 text-blue-700">
            {{ loadingMessage }}
          </p>
        </div>

        <div
          v-if="successMessage"
          class="p-4 bg-green-50 text-green-800 rounded-lg"
        >
          {{ successMessage }}
          <router-link to="/search" class="underline hover:text-green-900 ml-2">
            前往搜索
          </router-link>
        </div>

        <button
          type="submit"
          :disabled="isLoading || !username"
          class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
        >
          {{ isLoading ? '初始化中...' : '开始初始化' }}
        </button>
      </form>
    </div>

    <div class="mt-8 bg-gray-50 rounded-lg p-6 text-sm text-gray-600">
      <h3 class="font-medium text-gray-900 mb-2">功能说明</h3>
      <ul class="space-y-2 list-disc list-inside">
        <li><strong>LLM 分析</strong>: 使用 AI 分析仓库特性，生成分类和摘要</li>
        <li><strong>语义搜索</strong>: 基于向量相似度的智能搜索，理解语义而非关键词</li>
        <li><strong>Ollama 要求</strong>: 启用语义搜索需要先运行 <code class="bg-gray-200 px-1 rounded">ollama pull nomic-embed-text</code></li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const username = ref('')
const maxRepos = ref<number | null>(null)
const skipLlm = ref(false)
const enableSemantic = ref(false)

const isLoading = ref(false)
const loadingMessage = ref('')
const error = ref<string | null>(null)
const successMessage = ref<string | null>(null)

const initStatus = ref({
  has_data: false,
  repo_count: 0
})

onMounted(async () => {
  // Load saved username from localStorage
  const savedUsername = localStorage.getItem('github_username')
  if (savedUsername) {
    username.value = savedUsername
  }

  // Check init status
  try {
    const response = await fetch('/api/init/status')
    if (response.ok) {
      const data = await response.json()
      initStatus.value = data
    }
  } catch (e) {
    console.error('Failed to check init status:', e)
  }
})

async function startInitialization() {
  if (!username.value) return

  isLoading.value = true
  error.value = null
  successMessage.value = null
  loadingMessage.value = '正在获取 GitHub 星标仓库...'

  try {
    const response = await fetch('/api/init/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username.value,
        max_repos: maxRepos.value || undefined,
        skip_llm: skipLlm.value,
        enable_semantic: enableSemantic.value
      })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Initialization failed')
    }

    successMessage.value = data.message || '初始化成功！'
    initStatus.value.has_data = true
    initStatus.value.repo_count = data.stats?.added || 0

    // Save username
    localStorage.setItem('github_username', username.value)

  } catch (err) {
    error.value = err instanceof Error ? err.message : '初始化失败'
  } finally {
    isLoading.value = false
    loadingMessage.value = ''
  }
}
</script>
