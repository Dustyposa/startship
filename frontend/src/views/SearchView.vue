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
      <!-- Language Filter -->
      <select v-model="selectedLanguage" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white">
        <option value="">所有语言</option>
        <option value="Python">Python</option>
        <option value="JavaScript">JavaScript</option>
        <option value="TypeScript">TypeScript</option>
        <option value="Go">Go</option>
        <option value="Rust">Rust</option>
        <option value="Java">Java</option>
        <option value="C++">C++</option>
      </select>

      <!-- Owner Type Filter -->
      <select v-model="selectedOwnerType" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white">
        <option value="">所有类型</option>
        <option value="Organization">🏢 组织</option>
        <option value="User">👤 个人</option>
      </select>

      <!-- Derived Tag Filters -->
      <label class="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white cursor-pointer">
        <input type="checkbox" v-model="isActive" class="rounded">
        <span>🟢 活跃维护</span>
      </label>

      <label class="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white cursor-pointer">
        <input type="checkbox" v-model="isNew" class="rounded">
        <span>🆕 新项目</span>
      </label>

      <label class="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white cursor-pointer">
        <input type="checkbox" v-model="excludeArchived" class="rounded">
        <span>排除归档</span>
      </label>
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
        class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm hover:shadow-md cursor-pointer transition border"
        :class="repoCollections[repo.name_with_owner] ? 'border-yellow-400 dark:border-yellow-500' : 'border-gray-200 dark:border-gray-700'"
      >
        <div @click="goToRepo(repo.name_with_owner)">
          <h3 class="font-bold text-gray-900 dark:text-white">{{ repo.name_with_owner }}</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{{ repo.description || repo.summary }}</p>

          <div class="flex gap-2 mt-2 flex-wrap">
            <span v-if="repo.primary_language" class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
              {{ repo.primary_language }}
            </span>
            <span class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded">
              ⭐ {{ formatStarCount(repo.stargazer_count) }}
            </span>
            <span v-if="repo.starred_at" class="text-xs px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded">
              ⭐ {{ formatRelativeTime(repo.starred_at) }}
            </span>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="flex gap-2 mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <button
            @click.stop="openModal('quickNote', repo.name_with_owner)"
            class="px-3 py-1.5 text-xs font-medium rounded-lg transition"
            :class="repoNotes[repo.name_with_owner] ? 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20' : 'text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20'"
            title="添加笔记"
          >
            笔记
          </button>
          <button
            @click.stop="openModal('quickTag', repo.name_with_owner)"
            class="px-3 py-1.5 text-xs font-medium rounded-lg transition"
            :class="repoTags[repo.name_with_owner]?.length ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20' : 'text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20'"
            title="管理标签"
          >
            标签
          </button>
          <button
            @click.stop="openModal('collection', repo.name_with_owner)"
            class="px-3 py-1.5 text-xs font-medium rounded-lg transition"
            :class="repoCollections[repo.name_with_owner] ? 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20' : 'text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20'"
            title="添加到收藏夹"
          >
            {{ repoCollections[repo.name_with_owner] ? '已收藏' : '收藏' }}
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
                {{ collectionRepoCounts[collection.id] || 0 }} 个仓库
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useReposStore } from '../stores/repos'
import { useExport } from '../composables/useExport'
import { useCollections } from '@/composables/useCollections'
import { useTags } from '@/composables/useTags'
import { useNotes } from '@/composables/useNotes'
import { collectionsApi } from '@/api/user'
import type { Collection, Tag } from '@/api/user'
import NoteEditor from '@/components/NoteEditor.vue'
import TagManager from '@/components/TagManager.vue'
import { formatStarCount, formatRelativeTime } from '@/utils/format'

const router = useRouter()
const route = useRoute()
const reposStore = useReposStore()
const { exportToJSON: exportJSON, exportToCSV: exportCSV } = useExport()
const { collections, addRepoToCollection, getReposInCollection } = useCollections()
const { getAllTags, getTagsForRepo } = useTags()
const { getNote } = useNotes()

const searchQuery = ref((route.query.q as string) || '')
const selectedLanguage = ref('')
const selectedOwnerType = ref('')
const isActive = ref(false)
const isNew = ref(false)
const excludeArchived = ref(true)

const modals = ref({
  quickNote: null as string | null,
  quickTag: null as string | null,
  collection: { show: false, repoId: null as string | null }
})

// Cache for repo data (collections, tags, notes)
const repoCollections = ref<Record<string, Collection>>({})
const repoTags = ref<Record<string, Tag[]>>({})
const repoNotes = ref<Record<string, { rating?: number }>>({})
const collectionRepoCounts = ref<Record<string, number>>({})

const repos = computed(() => reposStore.repos)
const isLoading = computed(() => reposStore.isLoading)

// Load collection repo counts
async function loadCollectionCounts() {
  const promises: Promise<void>[] = []
  for (const collection of collections.value) {
    promises.push(
      (async () => {
        const repos = await getReposInCollection(collection.id)
        collectionRepoCounts.value[collection.id] = repos.length
      })()
    )
  }
  await Promise.all(promises)
}

function handleEscape(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (modals.value.quickNote) closeModal('quickNote')
    if (modals.value.quickTag) closeModal('quickTag')
    if (modals.value.collection.show) closeModal('collection')
  }
}

onMounted(async () => {
  await handleSearch()
  await loadCollectionCounts()
  window.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleEscape)
})

async function loadRepoMetadata() {
  const promises: Promise<void>[] = []

  for (const repo of repos.value) {
    promises.push(
      (async () => {
        // Get collection
        const coll = await collectionsApi.getCollectionForRepo(repo.name_with_owner)
        if (coll) repoCollections.value[repo.name_with_owner] = coll

        // Get tags
        const tags = await getTagsForRepo(repo.name_with_owner)
        if (tags.length > 0) repoTags.value[repo.name_with_owner] = tags

        // Get note rating
        const note = await getNote(repo.name_with_owner)
        if (note?.rating) repoNotes.value[repo.name_with_owner] = note
      })()
    )
  }

  await Promise.all(promises)
}

async function handleSearch() {
  await reposStore.searchRepos({
    query: searchQuery.value,
    languages: selectedLanguage.value ? [selectedLanguage.value] : undefined,
    ownerType: selectedOwnerType.value || undefined,
    isActive: isActive.value || undefined,
    isNew: isNew.value || undefined,
    excludeArchived: excludeArchived.value
  })
  // Load metadata after search completes
  await loadRepoMetadata()
}

function goToRepo(nameWithOwner: string) {
  const [owner, name] = nameWithOwner.split('/')
  router.push(`/repo/${owner}/${name}`)
}

function openModal(type: 'quickNote' | 'quickTag' | 'collection', repoId?: string) {
  if (type === 'collection' && repoId) {
    modals.value.collection = { show: true, repoId }
    loadCollectionCounts()
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

async function selectCollection(collectionId: string) {
  const { repoId } = modals.value.collection
  if (repoId) {
    await addRepoToCollection(repoId, collectionId)
    // Update the count
    const repos = await getReposInCollection(collectionId)
    collectionRepoCounts.value[collectionId] = repos.length
    // Update repo collections cache
    const coll = collections.value.find(c => c.id === collectionId)
    if (coll) repoCollections.value[repoId] = coll
    closeModal('collection')
  }
}

function getExportFilename() {
  return `repos-${searchQuery.value || 'all'}-${new Date().toISOString().slice(0, 10)}`
}

const exportToJSON = () => exportJSON(repos.value, getExportFilename())
const exportToCSV = () => exportCSV(repos.value, getExportFilename())
</script>
