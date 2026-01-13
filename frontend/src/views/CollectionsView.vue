<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white">我的收藏</h1>
      <div class="flex gap-3">
        <button
          @click="handleExport"
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
        >
          导出数据
        </button>
        <label class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition cursor-pointer">
          导入数据
          <input
            type="file"
            accept=".json"
            @change="handleImport"
            class="hidden"
          />
        </label>
        <button @click="showCreateDialog = true" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
          + 新建文件夹
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="collection in collections"
        :key="collection.id"
        class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition cursor-pointer"
        @click="selectedCollection = collection"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-2">
            <span v-if="collection.icon" class="text-2xl">{{ collection.icon }}</span>
            <h3 class="font-semibold text-gray-900 dark:text-white">{{ collection.name }}</h3>
          </div>
          <button @click.stop="deleteCollection(collection.id)" class="text-gray-400 hover:text-red-500 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">{{ getRepoCount(collection.id) }} 个仓库</p>
      </div>

      <div
        class="bg-gray-50 dark:bg-gray-800/50 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 p-4 hover:border-blue-500 transition cursor-pointer"
        @click="selectedCollection = null"
      >
        <div class="flex items-center gap-2">
          <span class="text-2xl">📦</span>
          <h3 class="font-semibold text-gray-700 dark:text-gray-300">全部仓库</h3>
        </div>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">{{ uncategorizedCount }} 个未分类</p>
      </div>
    </div>

    <div v-if="selectedCollection !== undefined" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="selectedCollection = undefined">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
        <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ selectedCollection?.name || '全部仓库' }}</h2>
          <button @click="selectedCollection = undefined" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[60vh]">
          <p class="text-gray-600 dark:text-gray-400">仓库列表将在此显示</p>
        </div>
      </div>
    </div>

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
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">创建</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useCollections } from '@/composables/useCollections'
import { useReposStore } from '@/stores/repos'
import { useExport } from '@/composables/useExport'
import type { Collection } from '@/types/collections'

const { collections, createCollection, deleteCollection, getReposInCollection, load } = useCollections()
const reposStore = useReposStore()
const { exportUserData, importUserData } = useExport()

const selectedCollection = ref<Collection | null | undefined>(undefined)
const showCreateDialog = ref(false)
const newCollectionName = ref('')
const newCollectionIcon = ref('')

const allRepos = computed(() => reposStore.repos)
const categorizedRepos = computed(() => {
  const repoIds = new Set<string>()
  collections.value.forEach(coll => {
    getReposInCollection(coll.id).forEach(id => repoIds.add(id))
  })
  return repoIds
})

const uncategorizedCount = computed(() => {
  return allRepos.value.filter(repo => !categorizedRepos.value.has(repo.name_with_owner)).length
})

function getRepoCount(collectionId: string): number {
  return getReposInCollection(collectionId).length
}

function handleCreate() {
  createCollection(newCollectionName.value, newCollectionIcon.value || undefined)
  newCollectionName.value = ''
  newCollectionIcon.value = ''
  showCreateDialog.value = false
}

function handleExport() {
  try {
    exportUserData()
    console.log('数据导出成功')
  } catch (error) {
    console.error('导出失败:', error)
  }
}

async function handleImport(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    await importUserData(file)
    console.log('数据导入成功')
    // Reload collections to show imported data
    load()
  } catch (error) {
    console.error('导入失败:', error)
  } finally {
    // Reset file input
    target.value = ''
  }
}

</script>
