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
          搜索
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
          CSV
        </button>
        <button
          @click="exportToJSON"
          class="px-4 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center gap-1"
          title="导出为 JSON"
        >
          JSON
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
      >
        <div @click="goToRepo(repo.name_with_owner)">
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

        <!-- Quick Actions -->
        <div class="flex gap-2 mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <button
            @click.stop="openModal('quickNote', repo.name_with_owner)"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition"
            title="添加笔记"
          >
            笔记
          </button>
          <button
            @click.stop="openModal('quickTag', repo.name_with_owner)"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition"
            title="管理标签"
          >
            标签
          </button>
          <button
            @click.stop="openModal('collection', repo.name_with_owner)"
            class="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition"
            title="添加到收藏夹"
          >
            收藏
          </button>
        </div>
      </div>
    </div>

    <!-- Quick Note Modal -->
    <div
      v-if="modals.quickNote"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="closeModal('quickNote')"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            笔记 - {{ modals.quickNote }}
          </h3>
          <button
            @click="closeModal('quickNote')"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <NoteEditor
          :repo-id="modals.quickNote"
          @update="closeModal('quickNote')"
        />
      </div>
    </div>

    <!-- Quick Tag Modal -->
    <div
      v-if="modals.quickTag"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="closeModal('quickTag')"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            标签 - {{ modals.quickTag }}
          </h3>
          <button
            @click="closeModal('quickTag')"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <TagManager
          :repo-id="modals.quickTag"
          @update="closeModal('quickTag')"
        />
      </div>
    </div>

    <!-- Collection Selector Modal -->
    <div
      v-if="modals.collection.show"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="closeModal('collection')"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            添加到收藏夹 - {{ modals.collection.repoId }}
          </h3>
          <button
            @click="closeModal('collection')"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div v-if="collections.length === 0" class="text-center py-8 text-gray-600 dark:text-gray-400">
          还没有收藏夹，先去创建一个吧！
        </div>
        <div v-else class="space-y-2">
          <button
            v-for="collection in collections"
            :key="collection.id"
            @click="selectCollection(collection.id)"
            class="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition text-left"
          >
            <span class="text-2xl">{{ collection.icon || '📁' }}</span>
            <div>
              <div class="font-medium text-gray-900 dark:text-white">{{ collection.name }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {{ getReposInCollection(collection.id).length }} 个仓库
              </div>
            </div>
          </button>
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
import { useRouter, useRoute } from 'vue-router'
import { useReposStore } from '../stores/repos'
import { useExport } from '../composables/useExport'
import { useCollections } from '@/composables/useCollections'
import NoteEditor from '@/components/NoteEditor.vue'
import TagManager from '@/components/TagManager.vue'

const router = useRouter()
const route = useRoute()
const reposStore = useReposStore()
const { exportToJSON: exportJSON, exportToCSV: exportCSV } = useExport()
const { collections, addRepoToCollection, getReposInCollection } = useCollections()

const searchQuery = ref((route.query.q as string) || '')
const selectedCategory = ref('')
const selectedLanguage = ref('')

const modals = ref({
  quickNote: null as string | null,
  quickTag: null as string | null,
  collection: { show: false, repoId: null as string | null }
})

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

function openModal(type: 'quickNote' | 'quickTag' | 'collection', repoId?: string) {
  if (type === 'collection' && repoId) {
    modals.value.collection = { show: true, repoId }
  } else if (type === 'quickNote' || type === 'quickTag') {
    modals.value[type] = repoId || null
  }
}

function closeModal(type: 'quickNote' | 'quickTag' | 'collection') {
  if (type === 'collection') {
    modals.value.collection = { show: false, repoId: null }
  } else {
    modals.value[type] = null
  }
}

function selectCollection(collectionId: string) {
  const { repoId } = modals.value.collection
  if (repoId) {
    addRepoToCollection(repoId, collectionId)
    closeModal('collection')
  }
}

function getExportFilename() {
  return `repos-${searchQuery.value || 'all'}-${new Date().toISOString().slice(0, 10)}`
}

const exportToJSON = () => exportJSON(repos.value, getExportFilename())
const exportToCSV = () => exportCSV(repos.value, getExportFilename())
</script>
