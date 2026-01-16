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
    <BaseModal
      :show="!!selectedCollection"
      :title="selectedCollection ? `${selectedCollection.icon || ''} ${selectedCollection.name}` : ''"
      size="xl"
      @close="closeModal"
    >
      <div v-if="isLoading" class="space-y-3">
        <div v-for="i in 5" :key="i" class="flex items-center justify-between p-3">
          <div class="flex-1">
            <SkeletonLoader variant="rect" :width="200" :height="20" />
            <SkeletonLoader variant="rect" :width="150" :height="16" class="mt-2" />
          </div>
          <SkeletonLoader variant="circle" :width="20" :height="20" />
        </div>
      </div>
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
      <EmptyState
        v-else
        icon="📭"
        title="收藏夹是空的"
        message="这个收藏夹还没有添加仓库"
      />
    </BaseModal>

    <!-- All Repos Modal -->
    <BaseModal
      :show="showAllRepos"
      title="📦 全部仓库"
      size="xl"
      @close="closeModal"
    >
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
    </BaseModal>

    <!-- Create Collection Dialog -->
    <BaseModal
      :show="showCreateDialog"
      title="新建文件夹"
      @close="showCreateDialog = false"
    >
      <form @submit.prevent="handleCreate">
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-700 dark:text-gray-300 mb-1">
              名称 <span class="text-red-500">*</span>
            </label>
            <input
              v-model="newCollectionName"
              type="text"
              required
              minlength="1"
              maxlength="50"
              placeholder="输入收藏夹名称"
              class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 transition"
              :class="nameValidationClass"
            />
            <div class="flex justify-between mt-1">
              <span v-if="newCollectionName && newCollectionName.length < 1" class="text-xs text-red-500">名称不能为空</span>
              <span v-else-if="newCollectionName && newCollectionName.length > 50" class="text-xs text-red-500">名称不能超过50个字符</span>
              <span v-else-if="newCollectionName" class="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
                看起来不错
              </span>
              <span v-else></span>
              <span class="text-xs text-gray-400">{{ newCollectionName.length }}/50</span>
            </div>
          </div>
          <div>
            <label class="block text-sm text-gray-700 dark:text-gray-300 mb-1">图标 (emoji)</label>
            <input
              v-model="newCollectionIcon"
              type="text"
              placeholder="📁"
              maxlength="2"
              class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 transition"
              :class="iconValidationClass"
            />
            <div class="flex justify-between mt-1">
              <span v-if="newCollectionIcon && !isEmoji(newCollectionIcon)" class="text-xs text-orange-500 flex items-center gap-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
                建议使用 emoji
              </span>
              <span v-else-if="newCollectionIcon" class="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
                {{ newCollectionIcon }}
              </span>
              <span v-else></span>
              <span class="text-xs text-gray-400">{{ newCollectionIcon.length }}/2</span>
            </div>
          </div>
        </div>
        <div class="mt-6 flex justify-end gap-3">
          <button type="button" @click="showCreateDialog = false" class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">取消</button>
          <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition" :disabled="isLoading || !isFormValid">
            {{ isLoading ? '创建中...' : '创建' }}
          </button>
        </div>
      </form>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCollections } from '@/composables/useCollections'
import { useReposStore } from '@/stores/repos'
import type { Collection } from '@/api/user'
import BaseModal from '@/components/BaseModal.vue'
import CollectionCardSkeleton from '@/components/CollectionCardSkeleton.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import EmptyState from '@/components/EmptyState.vue'

const { collections, isLoading, createCollection, deleteCollection, removeRepoFromCollection, getReposInCollection, load } = useCollections()
const reposStore = useReposStore()

const selectedCollection = ref<Collection & { repoCount?: number } | null>(null)
const showAllRepos = ref(false)
const showCreateDialog = ref(false)
const newCollectionName = ref('')
const newCollectionIcon = ref('')
const collectionRepos = ref<string[]>([])

const allRepos = computed(() => reposStore.repos)

// Form validation
const nameValidationClass = computed(() => {
  const name = newCollectionName.value
  if (!name) return 'border-gray-300 dark:border-gray-600'
  if (name.length < 1 || name.length > 50) return 'border-red-500 focus:ring-red-500'
  return 'border-green-500 focus:ring-green-500'
})

const iconValidationClass = computed(() => {
  const icon = newCollectionIcon.value
  if (!icon) return 'border-gray-300 dark:border-gray-600'
  return 'border-gray-300 dark:border-gray-600'
})

const isFormValid = computed(() => {
  return newCollectionName.value.length >= 1 && newCollectionName.value.length <= 50
})

// Check if a string is likely an emoji
function isEmoji(str: string): boolean {
  // Emoji regex pattern - matches most emoji including combined emojis
  const emojiRegex = /^(\p{Emoji}|\p{Emoji_Component})+$/u
  return emojiRegex.test(str) && str.length <= 2
}

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
