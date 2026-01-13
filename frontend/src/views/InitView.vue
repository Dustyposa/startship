<template>
  <div class="max-w-2xl mx-auto">
    <div class="bg-white rounded-lg shadow-sm p-8">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">🚀 初始化系统</h1>
        <p class="text-gray-600">从你的 GitHub 星标仓库中获取数据</p>
      </div>

      <div v-if="initStatus.has_data" class="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div class="flex items-center gap-3">
          <span class="text-2xl">✅</span>
          <div>
            <div class="font-semibold text-green-800">系统已初始化</div>
            <div class="text-sm text-green-700">
              共有 <strong>{{ initStatus.repo_count }}</strong> 个仓库。
              <router-link to="/search" class="underline hover:text-green-900 font-medium">开始探索 →</router-link>
            </div>
          </div>
        </div>
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
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
          />
          <p class="mt-2 text-sm text-gray-500 flex items-center gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            我们会从你的星标列表中获取公开数据
          </p>
        </div>

        <div>
          <label for="maxRepos" class="block text-sm font-medium text-gray-700 mb-2">
            最大仓库数 <span class="text-gray-400 font-normal">(可选)</span>
          </label>
          <input
            id="maxRepos"
            v-model.number="maxRepos"
            type="number"
            min="1"
            placeholder="获取全部仓库"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
          />
          <p class="mt-1 text-xs text-gray-500">限制数量可以加快初始化速度</p>
        </div>

        <!-- Mode Selection Cards -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-3">初始化模式</label>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <!-- Fast Mode -->
            <div
              @click="skipLlm = true"
              :class="[
                'p-4 rounded-lg border-2 cursor-pointer transition',
                skipLlm ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'
              ]"
            >
              <div class="flex items-start gap-3">
                <div class="text-2xl">⚡</div>
                <div class="flex-1">
                  <div class="font-semibold text-gray-900 mb-1">快速模式</div>
                  <p class="text-xs text-gray-600">使用 GitHub Topics 作为分类，速度快，推荐新手使用</p>
                </div>
                <div v-if="skipLlm" class="text-blue-600">
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>

            <!-- Deep Mode -->
            <div
              @click="skipLlm = false"
              :class="[
                'p-4 rounded-lg border-2 cursor-pointer transition',
                !skipLlm ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-purple-300'
              ]"
            >
              <div class="flex items-start gap-3">
                <div class="text-2xl">🧠</div>
                <div class="flex-1">
                  <div class="font-semibold text-gray-900 mb-1">深度模式</div>
                  <p class="text-xs text-gray-600">使用 AI 分析仓库特性，分类更准确，但需要配置 API Key</p>
                </div>
                <div v-if="!skipLlm" class="text-purple-600">
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Semantic Search Toggle -->
        <div class="bg-gray-50 rounded-lg p-4">
          <label class="flex items-center justify-between cursor-pointer">
            <div class="flex items-center gap-3">
              <div class="text-xl">🔮</div>
              <div>
                <span class="text-sm font-medium text-gray-900 block">启用智能搜索</span>
                <p class="text-xs text-gray-500">理解自然语言查询，而非关键词匹配</p>
              </div>
            </div>
            <div class="relative">
              <input
                v-model="enableSemantic"
                type="checkbox"
                class="sr-only"
              />
              <div
                :class="[
                  'block w-14 h-8 rounded-full transition',
                  enableSemantic ? 'bg-blue-600' : 'bg-gray-300'
                ]"
              >
                <div
                  :class="[
                    'absolute top-1 left-1 bg-white w-6 h-6 rounded-full transition transform',
                    enableSemantic ? 'translate-x-6' : ''
                  ]"
                ></div>
              </div>
            </div>
          </label>
          <p v-if="enableSemantic" class="text-xs text-blue-600 mt-2 ml-9">
            💡 需要安装 Ollama 并运行 <code class="bg-blue-100 px-1 rounded">ollama pull nomic-embed-text</code>
          </p>
        </div>

        <div
          v-if="error"
          class="p-4 bg-red-50 border border-red-200 rounded-lg text-sm flex items-start gap-2"
        >
          <svg class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <span class="text-red-800">{{ error }}</span>
        </div>

        <div
          v-if="isLoading"
          class="p-4 bg-blue-50 border border-blue-200 rounded-lg"
        >
          <div class="flex items-center gap-3">
            <svg class="animate-spin h-5 w-5 text-blue-600" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span class="font-medium text-blue-800">正在初始化，请稍候...</span>
          </div>
          <p class="text-sm mt-2 text-blue-700 pl-8">
            {{ loadingMessage }}
          </p>
        </div>

        <div
          v-if="successMessage"
          class="p-4 bg-green-50 border border-green-200 rounded-lg"
        >
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <span class="font-medium text-green-800">{{ successMessage }}</span>
          </div>
          <div class="mt-3 flex gap-2">
            <router-link to="/search" class="inline-flex items-center gap-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm font-medium">
              开始搜索
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </router-link>
            <router-link to="/chat" class="inline-flex items-center gap-1 px-4 py-2 bg-white border border-green-600 text-green-600 rounded-lg hover:bg-green-50 transition text-sm font-medium">
              开始对话
            </router-link>
          </div>
        </div>

        <button
          type="submit"
          :disabled="isLoading || !username"
          class="w-full px-6 py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed font-medium shadow-lg hover:shadow-xl transition flex items-center justify-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          {{ isLoading ? '初始化中...' : '开始初始化' }}
        </button>
      </form>
    </div>

    <!-- Tips Section -->
    <div class="mt-8 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 text-sm">
      <h3 class="font-semibold text-gray-900 mb-3 flex items-center gap-2">
        <span class="text-xl">💡</span>
        使用提示
      </h3>
      <ul class="space-y-2 text-gray-700">
        <li class="flex items-start gap-2">
          <svg class="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <span><strong>快速模式</strong>适合首次使用，几分钟即可完成</span>
        </li>
        <li class="flex items-start gap-2">
          <svg class="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <span><strong>深度模式</strong>需要 OpenAI API Key，分类更智能准确</span>
        </li>
        <li class="flex items-start gap-2">
          <svg class="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <span><strong>智能搜索</strong>可以让 AI 理解"机器学习相关项目"这类自然语言查询</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const username = ref('')
const maxRepos = ref<number | null>(null)
const skipLlm = ref(true)
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
