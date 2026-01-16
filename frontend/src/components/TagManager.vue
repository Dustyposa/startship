<template>
  <div class="flex flex-wrap gap-2">
    <span
      v-for="tag in selectedTags"
      :key="tag.id"
      class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm text-white"
      :style="{ backgroundColor: tag.color }"
    >
      {{ tag.name }}
      <button @click="removeTag(tag.id)" type="button" class="hover:opacity-70">
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </span>
    <div class="relative">
      <input
        v-if="showInput"
        ref="inputRef"
        v-model="newTagName"
        @blur="addTag"
        @keyup.enter="addTag"
        @keyup.esc="showInput = false"
        type="text"
        placeholder="标签名..."
        class="w-24 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        v-else
        @click="showInput = true"
        type="button"
        class="px-2 py-1 text-sm border border-dashed border-gray-400 dark:border-gray-600 rounded text-gray-600 dark:text-gray-400 hover:border-blue-500 hover:text-blue-500 transition"
      >
        + 添加标签
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { useTags } from '@/composables/useTags'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import type { Tag } from '@/types/collections'

const props = defineProps<{
  repoId: string
}>()

const emit = defineEmits<{
  (e: 'update'): void
}>()

const { tags, getTagsForRepo, addTagToRepo, removeTagFromRepo, getOrCreateTag } = useTags()
const { confirmRemove } = useConfirm()
const { success, error: showError } = useToast()

const selectedTags = ref<Tag[]>([])
const showInput = ref(false)
const newTagName = ref('')
const inputRef = ref<HTMLInputElement>()

onMounted(async () => {
  selectedTags.value = await getTagsForRepo(props.repoId)
})

watch(() => props.repoId, async () => {
  selectedTags.value = await getTagsForRepo(props.repoId)
})

async function removeTag(tagId: string) {
  const tag = selectedTags.value.find(t => t.id === tagId)
  if (!tag) return

  const confirmed = await confirmRemove('标签', tag.name)
  if (confirmed) {
    await removeTagFromRepo(props.repoId, tagId)
    selectedTags.value = await getTagsForRepo(props.repoId)
    emit('update')
    success(`已移除标签 "${tag.name}"`, { timeout: 2000 })
  }
}

async function addTag() {
  const name = newTagName.value.trim()
  if (!name) {
    showInput.value = false
    return
  }

  try {
    const tag = await getOrCreateTag(name)
    await addTagToRepo(props.repoId, tag.id)
    selectedTags.value = await getTagsForRepo(props.repoId)
    newTagName.value = ''
    showInput.value = false
    emit('update')
    success(`已添加标签 "${tag.name}"`, { timeout: 2000 })
  } catch (err) {
    showError('添加标签失败，请稍后重试')
  }
}

watch(showInput, async (show) => {
  if (show) {
    await nextTick()
    inputRef.value?.focus()
  }
})
</script>
