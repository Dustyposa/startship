<template>
  <div class="space-y-3">
    <!-- Current Collection -->
    <div v-if="currentCollection" class="flex items-center gap-2">
      <span class="text-sm text-gray-600 dark:text-gray-400">已收藏到:</span>
      <span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm" :style="{ backgroundColor: currentCollection.color + '20', color: currentCollection.color }">
        <span v-if="currentCollection.icon">{{ currentCollection.icon }}</span>
        {{ currentCollection.name }}
      </span>
      <button
        @click="removeFromCollection"
        class="text-xs text-red-500 hover:text-red-700 dark:hover:text-red-400"
        title="从收藏夹移除"
      >
        移除
      </button>
    </div>

    <!-- Add to Collection -->
    <div v-else class="flex items-center gap-2">
      <span class="text-sm text-gray-600 dark:text-gray-400">未收藏</span>
      <button
        v-if="collections.length > 0"
        @click="showSelector = true"
        class="px-2 py-1 text-xs border border-dashed border-gray-400 dark:border-gray-600 rounded text-gray-600 dark:text-gray-400 hover:border-blue-500 hover:text-blue-500 transition"
      >
        + 添加到收藏夹
      </button>
      <span v-else class="text-xs text-gray-400">暂无收藏夹</span>
    </div>

    <!-- Collection Selector Modal -->
    <div v-if="showSelector" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showSelector = false">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-4 w-full max-w-md">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-3">选择收藏夹</h3>
        <div class="space-y-2 max-h-60 overflow-y-auto">
          <div
            v-for="collection in collections"
            :key="collection.id"
            @click="addToCollection(collection.id)"
            class="flex items-center gap-2 p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition"
          >
            <span v-if="collection.icon">{{ collection.icon }}</span>
            <span class="text-gray-900 dark:text-white">{{ collection.name }}</span>
          </div>
        </div>
        <button
          @click="showSelector = false"
          class="mt-4 w-full px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition"
        >
          取消
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCollections } from '@/composables/useCollections'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import type { Collection } from '@/api/user'

const props = defineProps<{
  repoId: string
}>()

const { collections, getCollectionForRepo, addRepoToCollection, removeRepoFromCollection } = useCollections()
const { confirmRemove } = useConfirm()
const { success, error: showError } = useToast()

const currentCollection = ref<Collection | null>(null)
const showSelector = ref(false)

onMounted(async () => {
  currentCollection.value = await getCollectionForRepo(props.repoId)
})

async function addToCollection(collectionId: string) {
  try {
    await addRepoToCollection(props.repoId, collectionId)
    currentCollection.value = await getCollectionForRepo(props.repoId)
    showSelector.value = false
    const collection = collections.value.find(c => c.id === collectionId)
    success(`已添加到 ${collection?.name || '收藏夹'}`, { timeout: 2000 })
  } catch (err) {
    showError('添加失败，请稍后重试')
  }
}

async function removeFromCollection() {
  if (!currentCollection.value) return

  const confirmed = await confirmRemove('收藏夹', currentCollection.value.name)
  if (confirmed) {
    try {
      await removeRepoFromCollection(props.repoId, currentCollection.value.id)
      const collectionName = currentCollection.value.name
      currentCollection.value = null
      success(`已从 ${collectionName} 移除`, { timeout: 2000 })
    } catch (err) {
      showError('移除失败，请稍后重试')
    }
  }
}
</script>
