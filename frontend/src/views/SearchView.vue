<template>
  <div class="space-y-6">
    <!-- Search Header with Export -->
    <div class="flex flex-col gap-4">
      <div class="flex gap-4">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索仓库..."
          class="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
          @keyup.enter="handleSearch"
        />
        <button
          @click="handleSearch"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          🔍 搜索
        </button>
      </div>

      <!-- Export Buttons (shown when has results) -->
      <div v-if="repos.length > 0" class="flex gap-2 items-center">
        <span class="text-sm text-gray-600 dark:text-gray-400">导出结果 ({{ repos.length }} 个):</span>
        <button
          @click="exportToCSV"
          class="px-4 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-1"
          title="导出为 CSV"
        >
          📄 CSV
        </button>
        <button
          @click="exportToJSON"
          class="px-4 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center gap-1"
          title="导出为 JSON"
        >
          📋 JSON
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex gap-4 flex-wrap">
      <select v-model="selectedCategory" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white">
        <option value="">所有分类</option>
        <option v-for="(count, cat) in categories" :key="cat" :value="cat">
          {{ cat }} ({{ count }})
        </option>
      </select>

      <select v-model="selectedLanguage" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white">
        <option value="">所有语言</option>
        <option value="Python">Python</option>
        <option value="JavaScript">JavaScript</option>
        <option value="TypeScript">TypeScript</option>
        <option value="Go">Go</option>
        <option value="Rust">Rust</option>
      </select>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-8">
      <div class="text-gray-600 dark:text-gray-400">加载中...</div>
    </div>

    <!-- Results Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="repo in repos"
        :key="repo.name_with_owner"
        class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm hover:shadow-md cursor-pointer transition border border-gray-200 dark:border-gray-700"
        @click="goToRepo(repo.name_with_owner)"
      >
        <h3 class="font-bold text-gray-900 dark:text-white">{{ repo.name_with_owner }}</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{{ repo.description || repo.summary }}</p>
        <div class="flex gap-2 mt-2">
          <span v-if="repo.primary_language" class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
            {{ repo.primary_language }}
          </span>
          <span class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded">
            ⭐ {{ repo.stargazer_count }}
          </span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!isLoading && repos.length === 0" class="text-center py-8 text-gray-600 dark:text-gray-400">
      没有找到匹配的仓库
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useReposStore } from '../stores/repos'
import { useExport } from '../composables/useExport'

const router = useRouter()
const reposStore = useReposStore()
const { exportToJSON, exportToCSV } = useExport()

const searchQuery = ref('')
const selectedCategory = ref('')
const selectedLanguage = ref('')

const repos = computed(() => reposStore.repos)
const categories = computed(() => reposStore.categories)
const isLoading = computed(() => reposStore.isLoading)

onMounted(() => {
  reposStore.loadCategories()
  handleSearch()
})

function handleSearch() {
  reposStore.searchRepos({
    query: searchQuery.value,
    categories: selectedCategory.value ? [selectedCategory.value] : undefined,
    languages: selectedLanguage.value ? [selectedLanguage.value] : undefined
  })
}

function goToRepo(nameWithOwner: string) {
  const [owner, name] = nameWithOwner.split('/')
  router.push(`/repo/${owner}/${name}`)
}

function exportToJSON() {
  const filename = `repos-${searchQuery.value || 'all'}-${new Date().toISOString().slice(0, 10)}`
  exportToJSON(repos.value, filename)
}

function exportToCSV() {
  const filename = `repos-${searchQuery.value || 'all'}-${new Date().toISOString().slice(0, 10)}`
  exportToCSV(repos.value, filename)
}
</script>
