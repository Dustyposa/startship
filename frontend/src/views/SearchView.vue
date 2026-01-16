<template>
  <div class="space-y-6">
    <!-- Repo Count -->
    <div v-if="repos.length > 0" class="text-sm text-gray-600 dark:text-gray-400">
      找到 <span class="font-semibold text-gray-900 dark:text-white">{{ repos.length }}</span> 个仓库
    </div>

    <!-- Language Distribution Chart -->
    <div v-if="repos.length > 0 && languageDistribution.length > 0" class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3">当前结果语言分布</h3>
      <div class="flex flex-col sm:flex-row items-center justify-center gap-6">
        <PieChart
          :data="languageDistribution"
          :size="160"
          :donut="true"
          :donut-radius="50"
          :is-dark="isDark"
        />
      </div>
    </div>

    <!-- Related Recommendations (Graph-based) -->
    <div v-if="relatedRepos.length > 0" class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        关联推荐
        <span class="text-xs font-normal text-gray-500 dark:text-gray-400">基于知识图谱</span>
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div
          v-for="repo in relatedRepos"
          :key="repo.name_with_owner"
          @click="goToRepo(repo.name_with_owner)"
          class="p-3 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 cursor-pointer transition border border-gray-200 dark:border-gray-600"
        >
          <h4 class="font-medium text-sm text-gray-900 dark:text-white mb-1 truncate" :title="repo.name_with_owner">{{ repo.name_with_owner }}</h4>
          <p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">{{ repo.description || repo.summary }}</p>
          <div class="flex items-center gap-2">
            <span class="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded">
              ⭐ {{ formatStarCount(repo.stargazer_count) }}
            </span>
            <span v-if="repo.primary_language" class="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
              {{ repo.primary_language }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Search and Filters -->
    <div class="space-y-4">
      <!-- Search Bar -->
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

      <!-- Filters Row -->
      <div class="flex gap-4 flex-wrap items-center">
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

        <!-- Spacer -->
        <div class="flex-1"></div>

        <!-- Export Dropdown Button -->
        <div class="relative" v-if="repos.length > 0">
          <button
            @click="showExportMenu = !showExportMenu"
            class="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
            title="导出数据"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span>导出</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div
            v-if="showExportMenu"
            class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10"
          >
            <button
              @click="exportToCSV"
              class="w-full px-4 py-2 text-left text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center gap-2"
            >
              <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
              </svg>
              导出为 CSV
            </button>
            <button
              @click="exportToJSON"
              class="w-full px-4 py-2 text-left text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center gap-2"
            >
              <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              导出为 JSON
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <RepoCardSkeleton v-for="i in 6" :key="i" />
    </div>

    <!-- Results Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="repo in repos"
        :key="repo.name_with_owner"
        class="repo-card bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm hover:shadow-md cursor-pointer transition border relative flex flex-col"
        :class="repoCollections[repo.name_with_owner] ? 'border-yellow-400 dark:border-yellow-500' : 'border-gray-200 dark:border-gray-700'"
      >
        <!-- Quick Actions (Top Right) -->
        <div class="absolute top-2 right-2 flex gap-1">
          <button
            @click.stop="openModal('quickNote', repo.name_with_owner)"
            class="repo-action-icon"
            :class="repoNotes[repo.name_with_owner] ? 'repo-action-active' : ''"
            title="笔记"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            @click.stop="openModal('quickTag', repo.name_with_owner)"
            class="repo-action-icon"
            :class="repoTags[repo.name_with_owner]?.length ? 'repo-action-active' : ''"
            title="标签"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
          </button>
          <button
            @click.stop="openModal('collection', repo.name_with_owner)"
            class="repo-action-icon"
            :class="repoCollections[repo.name_with_owner] ? 'repo-action-active' : ''"
            title="收藏"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
          </button>
        </div>

        <div @click="goToRepo(repo.name_with_owner)" class="flex-1 flex flex-col">
          <h3 class="font-bold text-gray-900 dark:text-white mb-2 pr-24 truncate" :title="repo.name_with_owner">{{ repo.name_with_owner }}</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3 flex-1">{{ repo.description || repo.summary }}</p>

          <div class="flex items-center justify-between gap-2">
            <div class="flex gap-2 flex-wrap">
              <span class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded">
                ⭐ {{ formatStarCount(repo.stargazer_count) }}
              </span>
              <span v-if="repo.starred_at" class="text-xs px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded">
                ⭐ {{ formatRelativeTime(repo.starred_at) }}
              </span>
            </div>

            <!-- Language Indicator -->
            <LanguageBarChart v-if="repo.languages && repo.languages.length > 0" :languages="repo.languages" :limit="3" />
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination Controls -->
    <div v-if="repos.length > 0" class="flex items-center justify-center gap-4 py-6">
      <button
        @click="prevPage"
        :disabled="currentPage === 1 || isLoadingPage"
        class="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition disabled:opacity-50 disabled:cursor-not-allowed text-gray-900 dark:text-white"
      >
        上一页
      </button>

      <span class="text-gray-900 dark:text-white">
        第
        <input
          type="number"
          :value="currentPage"
          @change="goToPage(Number(($event.target as HTMLInputElement).value))"
          @keyup.enter="goToPage(Number(($event.target as HTMLInputElement).value))"
          min="1"
          class="w-16 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white text-center"
        />
        页
      </span>

      <button
        @click="nextPage"
        :disabled="repos.length < pageSize || isLoadingPage"
        class="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition disabled:opacity-50 disabled:cursor-not-allowed text-gray-900 dark:text-white"
      >
        下一页
      </button>

      <div v-if="isLoadingPage" class="flex items-center gap-2">
        <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 dark:border-blue-400"></div>
        <span class="text-gray-600 dark:text-gray-400 text-sm">加载中...</span>
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
import PieChart from '@/components/PieChart.vue'
import LanguageBarChart from '@/components/LanguageBarChart.vue'
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

const showExportMenu = ref(false)

// Pagination
const currentPage = ref(1)
const pageSize = 30
const isLoadingPage = ref(false)

// Cache for repo data (collections, tags, notes)
const repoCollections = ref<Record<string, Collection>>({})
const repoTags = ref<Record<string, Tag[]>>({})
const repoNotes = ref<Record<string, { rating?: number }>>({})
const collectionRepoCounts = ref<Record<string, number>>({})

const repos = computed(() => reposStore.repos)
const isLoading = computed(() => reposStore.isLoading)

// Related repos from graph-based recommendations
const relatedRepos = ref<any[]>([])

// Dark mode detection
const isDark = computed(() => {
  if (typeof window !== 'undefined') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ||
           document.documentElement.classList.contains('dark')
  }
  return false
})

// Language distribution from search results
const languageDistribution = computed(() => {
  const langMap = new Map<string, number>()

  for (const repo of repos.value) {
    if (repo.primary_language) {
      langMap.set(repo.primary_language, (langMap.get(repo.primary_language) || 0) + 1)
    }
  }

  return Array.from(langMap.entries())
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8)
})

async function loadRepoMetadata(reposToLoad = repos.value) {
  const promises: Promise<void>[] = []

  for (const repo of reposToLoad) {
    promises.push(
      (async () => {
        const coll = await collectionsApi.getCollectionForRepo(repo.name_with_owner)
        if (coll) repoCollections.value[repo.name_with_owner] = coll

        const tags = await getTagsForRepo(repo.name_with_owner)
        if (tags.length > 0) repoTags.value[repo.name_with_owner] = tags

        const note = await getNote(repo.name_with_owner)
        if (note?.rating) repoNotes.value[repo.name_with_owner] = note
      })()
    )
  }

  await Promise.all(promises)
}

async function loadAllCollectionCounts() {
  await Promise.all(
    collections.value.map(async (collection) => {
      const repos = await getReposInCollection(collection.id)
      collectionRepoCounts.value[collection.id] = repos.length
    })
  )
}

function handleEscape(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (modals.value.quickNote) closeModal('quickNote')
    if (modals.value.quickTag) closeModal('quickTag')
    if (modals.value.collection.show) closeModal('collection')
    showExportMenu.value = false
  }
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  const exportButton = target.closest('.relative')
  if (!exportButton && showExportMenu.value) {
    showExportMenu.value = false
  }
}

onMounted(async () => {
  await handleSearch()
  await loadAllCollectionCounts()
  window.addEventListener('keydown', handleEscape)
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleEscape)
  window.removeEventListener('click', handleClickOutside)
})

async function handleSearch() {
  currentPage.value = 1
  await loadPage(1)
}

async function loadPage(page: number) {
  isLoadingPage.value = true
  const offset = (page - 1) * pageSize

  try {
    const response = await fetch(
      `/api/search?q=${encodeURIComponent(searchQuery.value)}&limit=${pageSize}&offset=${offset}` +
      `&languages=${selectedLanguage.value || ''}` +
      `&owner_type=${selectedOwnerType.value || ''}` +
      `&is_active=${isActive.value}` +
      `&is_new=${isNew.value}` +
      `&exclude_archived=${excludeArchived.value}` +
      `&include_related=true`
    )
    const data = await response.json()
    const newRepos = data.results || []

    // Update store with new page data
    reposStore.repos = newRepos

    // Load related repos (only on first page)
    if (page === 1 && data.related) {
      relatedRepos.value = data.related
    } else if (page > 1) {
      relatedRepos.value = []
    }

    // Load metadata for repos
    await loadRepoMetadata(newRepos)
  } catch (err) {
    console.error('Failed to load page:', err)
  } finally {
    isLoadingPage.value = false
  }
}

function goToPage(page: number) {
  currentPage.value = page
  loadPage(page)
}

function nextPage() {
  goToPage(currentPage.value + 1)
}

function prevPage() {
  if (currentPage.value > 1) {
    goToPage(currentPage.value - 1)
  }
}

function goToRepo(nameWithOwner: string) {
  const [owner, name] = nameWithOwner.split('/')
  router.push(`/repo/${owner}/${name}`)
}

function openModal(type: 'quickNote' | 'quickTag' | 'collection', repoId?: string) {
  if (type === 'collection' && repoId) {
    modals.value.collection = { show: true, repoId }
    loadAllCollectionCounts()
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
    showExportMenu.value = false
    success('导出成功', { timeout: 2000 })
  } catch (err) {
    showError('导出失败，请稍后重试')
  }
}

const exportToCSV = () => {
  try {
    exportCSV(repos.value, getExportFilename())
    showExportMenu.value = false
    success('导出成功', { timeout: 2000 })
  } catch (err) {
    showError('导出失败，请稍后重试')
  }
}
</script>

<style scoped>
/* Repository Card Actions */
.repo-action-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgb(243 244 246);
  border-radius: 6px;
  color: rgb(107 114 128);
  transition: all 0.2s;
}

.dark .repo-action-icon {
  background: rgb(55 65 81);
  color: rgb(156 163 175);
}

.repo-action-icon:hover {
  background: rgb(229 231 235);
  transform: scale(1.05);
}

.dark .repo-action-icon:hover {
  background: rgb(75 85 99);
}

.repo-action-active {
  color: rgb(37 99 235);
  background: rgb(239 246 255);
}

.dark .repo-action-active {
  color: rgb(96 165 250);
  background: rgb(30 58 138);
}
</style>
