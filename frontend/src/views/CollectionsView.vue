<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white">我的收藏</h1>
      <div class="flex gap-3">
        <button @click="showCreateDialog = true" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
          + 新建文件夹
        </button>
      </div>
    </div>

    <!-- Collections Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="collection in collections"
        :key="collection.id"
        class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition cursor-pointer"
        @click="openCollection(collection)"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-2">
            <span v-if="collection.icon" class="text-2xl">{{ collection.icon }}</span>
            <h3 class="font-semibold text-gray-900 dark:text-white">{{ collection.name }}</h3>
          </div>
          <button @click.stop="handleDeleteCollection(collection.id)" class="text-gray-400 hover:text-red-500 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">{{ collection.repoCount || 0 }} 个仓库</p>
      </div>

      <!-- All Repos / Uncategorized -->
      <div
        class="bg-gray-50 dark:bg-gray-800/50 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 p-4 hover:border-blue-500 transition cursor-pointer"
        @click="openAllRepos()"
      >
        <div class="flex items-center gap-2">
          <span class="text-2xl">📦</span>
          <h3 class="font-semibold text-gray-700 dark:text-gray-300">全部仓库</h3>
        </div>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">{{ allRepos.length }} 个仓库</p>
      </div>
    </div>

    <!-- Collection Detail Modal -->
    <div v-if="selectedCollection" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="closeModal">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
        <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <div class="flex items-center gap-2">
            <span v-if="selectedCollection.icon" class="text-2xl">{{ selectedCollection.icon }}</span>
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ selectedCollection.name }}</h2>
          </div>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[60vh]">
          <!-- Loading state -->
          <div v-if="isLoading" class="text-center py-8 text-gray-600 dark:text-gray-400">
            <svg class="animate-spin h-8 w-8 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p>加载中...</p>
          </div>
          <!-- Repository list -->
          <div v-else-if="collectionRepos.length > 0" class="space-y-3">
            <div
              v-for="repoId in collectionRepos"
              :key="repoId"
              class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            >
              <div class="flex-1">
                <router-link
                  :to="`/repo/${repoId.split('/')[0]}/${repoId.split('/')[1]}`"
                  class="font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400"
                  @click="closeModal"
                >
                  {{ repoId }}
                </router-link>
              </div>
              <button
                @click="removeRepoFromCollectionClick(repoId)"
                class="text-gray-400 hover:text-red-500 transition"
                title="从收藏夹移除"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>
          <!-- Empty state -->
          <div v-else class="text-center py-8 text-gray-600 dark:text-gray-400">
            <svg class="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
            </svg>
            <p>这个收藏夹还没有仓库</p>
          </div>
        </div>
      </div>
    </div>

    <!-- All Repos Modal -->
    <div v-if="showAllRepos" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="closeModal">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
        <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">📦 全部仓库</h2>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[60vh]">
          <div class="space-y-3">
            <div
              v-for="repo in allRepos"
              :key="repo.name_with_owner"
              class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            >
              <div class="flex-1">
                <router-link
                  :to="`/repo/${repo.owner}/${repo.name}`"
                  class="font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400"
                  @click="closeModal"
                >
                  {{ repo.name_with_owner }}
                </router-link>
                <p v-if="repo.description" class="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-1">{{ repo.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Collection Dialog -->
    <div v-if="showCreateDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showCreateDialog = false">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4 text-gray-900 dark:text-white">新建文件夹</h2>
        <form @submit.prevent="handleCreate">
          <div class="space-y-4">
            <div>
              <label class="block text-sm text-gray-700 dark:text-gray-300 mb-1">名称</label>
              <input v-model="newCollectionName" type="text" required class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm text-gray-700 dark:text-gray-300 mb-1">图标 (emoji)</label>
              <input v-model="newCollectionIcon" type="text" placeholder="📁" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div class="mt-6 flex justify-end gap-3">
            <button type="button" @click="showCreateDialog = false" class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">取消</button>
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition" :disabled="isLoading">
              {{ isLoading ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCollections } from '@/composables/useCollections'
import { useReposStore } from '@/stores/repos'
import type { Collection } from '@/api/user'

const { collections, isLoading, createCollection, deleteCollection, removeRepoFromCollection, getReposInCollection, load } = useCollections()
const reposStore = useReposStore()

const selectedCollection = ref<Collection & { repoCount?: number } | null>(null)
const showAllRepos = ref(false)
const showCreateDialog = ref(false)
const newCollectionName = ref('')
const newCollectionIcon = ref('')
const collectionRepos = ref<string[]>([])

const allRepos = computed(() => reposStore.repos)

// Load collections with repo counts on mount
onMounted(async () => {
  await load()
  for (const coll of collections.value) {
    const repos = await getReposInCollection(coll.id)
    coll.repoCount = repos.length
  }
})

async function openCollection(collection: Collection) {
  selectedCollection.value = collection
  collectionRepos.value = await getReposInCollection(collection.id)
}

function openAllRepos() {
  showAllRepos.value = true
}

function closeModal() {
  selectedCollection.value = null
  showAllRepos.value = false
  collectionRepos.value = []
}

async function handleCreate() {
  const result = await createCollection(newCollectionName.value, newCollectionIcon.value || undefined)
  if (result) {
    newCollectionName.value = ''
    newCollectionIcon.value = ''
    showCreateDialog.value = false
  }
}

async function handleDeleteCollection(id: string) {
  if (!confirm('确定要删除这个收藏夹吗？')) return
  await deleteCollection(id)
}

async function removeRepoFromCollectionClick(repoId: string) {
  if (!selectedCollection.value) return
  await removeRepoFromCollection(repoId, selectedCollection.value.id)
  collectionRepos.value = collectionRepos.value.filter(id => id !== repoId)
  if (selectedCollection.value.repoCount !== undefined) {
    selectedCollection.value.repoCount--
  }
}
</script>
