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
        <span class="text-sm text-gray-600 dark:text-gray-400">{{ repos.length }}</span>
        <button
          @click="exportToCSV"
          class="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          title="导出为 CSV"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
          </svg>
        </button>
        <button
          @click="exportToJSON"
          class="p-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
          title="导出为 JSON"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
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
      <label class="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white cursor-pointer" title="活跃维护">
        <input type="checkbox" v-model="isActive" class="rounded">
        <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </label>

      <label class="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white cursor-pointer" title="新项目">
        <input type="checkbox" v-model="isNew" class="rounded">
        <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </label>

      <label class="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white cursor-pointer" title="排除归档">
        <input type="checkbox" v-model="excludeArchived" class="rounded">
        <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
        </svg>
      </label>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <RepoCardSkeleton v-for="i in 6" :key="i" />
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
        <div class="flex gap-1.5 mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <button
            @click.stop="openModal('quickNote', repo.name_with_owner)"
            class="p-1.5 rounded-lg transition"
            :class="repoNotes[repo.name_with_owner] ? 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20' : 'text-gray-500 dark:text-gray-400 hover:text-yellow-600 dark:hover:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20'"
            title="笔记"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            @click.stop="openModal('quickTag', repo.name_with_owner)"
            class="p-1.5 rounded-lg transition"
            :class="repoTags[repo.name_with_owner]?.length ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20' : 'text-gray-500 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20'"
            title="标签"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
          </button>
          <button
            @click.stop="openModal('collection', repo.name_with_owner)"
            class="p-1.5 rounded-lg transition"
            :class="repoCollections[repo.name_with_owner] ? 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20' : 'text-gray-500 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20'"
            title="收藏"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Quick Note Modal -->
    <BaseModal
      :show="!!modals.quickNote"
      :title="`笔记 - ${modals.quickNote}`"
      @close="closeModal('quickNote')"
    >
      <NoteEditor
        v-if="modals.quickNote"
        :repo-id="modals.quickNote"
        @update="closeModal('quickNote')"
      />
    </BaseModal>

    <!-- Quick Tag Modal -->
    <BaseModal
      :show="!!modals.quickTag"
      :title="`标签 - ${modals.quickTag}`"
      @close="closeModal('quickTag')"
    >
      <TagManager
        v-if="modals.quickTag"
        :repo-id="modals.quickTag"
        @update="closeModal('quickTag')"
      />
    </BaseModal>

    <!-- Collection Selector Modal -->
    <BaseModal
      :show="modals.collection.show"
      :title="`添加到收藏夹 - ${modals.collection.repoId}`"
      @close="closeModal('collection')"
    >
      <EmptyState
        v-if="collections.length === 0"
        icon="📁"
        title="还没有收藏夹"
        message="先去创建一个收藏夹吧！"
      />
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
    </BaseModal>

    <!-- Empty State -->
    <EmptyState
      v-if="!isLoading && repos.length === 0"
      icon="🔍"
      title="没有找到匹配的仓库"
      message="尝试调整搜索条件或筛选器"
    />
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
import { useToast } from '@/composables/useToast'
import { collectionsApi } from '@/api/user'
import type { Collection, Tag } from '@/api/user'
import NoteEditor from '@/components/NoteEditor.vue'
import TagManager from '@/components/TagManager.vue'
import BaseModal from '@/components/BaseModal.vue'
import RepoCardSkeleton from '@/components/RepoCardSkeleton.vue'
import EmptyState from '@/components/EmptyState.vue'
import { formatStarCount, formatRelativeTime } from '@/utils/format'

const router = useRouter()
const route = useRoute()
const reposStore = useReposStore()
const { exportToJSON: exportJSON, exportToCSV: exportCSV } = useExport()
const { collections, addRepoToCollection, getReposInCollection } = useCollections()
const { getAllTags, getTagsForRepo } = useTags()
const { getNote } = useNotes()
const { success, error: showError } = useToast()

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

    // Show success message
    const collectionName = coll?.name || '收藏夹'
    success(`已添加到 ${collectionName}`, { timeout: 2000 })
  }
}

function getExportFilename() {
  return `repos-${searchQuery.value || 'all'}-${new Date().toISOString().slice(0, 10)}`
}

const exportToJSON = () => {
  try {
    exportJSON(repos.value, getExportFilename())
    success('导出成功', { timeout: 2000 })
  } catch (err) {
    showError('导出失败，请稍后重试')
  }
}

const exportToCSV = () => {
  try {
    exportCSV(repos.value, getExportFilename())
    success('导出成功', { timeout: 2000 })
  } catch (err) {
    showError('导出失败，请稍后重试')
  }
}
</script>
