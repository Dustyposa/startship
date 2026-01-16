<template>
  <div class="space-y-3">
    <div class="flex items-center gap-3">
      <span class="text-sm text-gray-600 dark:text-gray-400">评分:</span>
      <RatingStars :rating="localRating" @update:rating="updateRating" />
    </div>
    <div>
      <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">
        笔记 (支持 Markdown):
      </label>
      <textarea
        v-model="localNote"
        @blur="save"
        placeholder="添加个人笔记..."
        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
        rows="4"
      />
    </div>
    <div v-if="localNote" class="border-t border-gray-200 dark:border-gray-700 pt-3">
      <span class="text-xs text-gray-500 dark:text-gray-400">预览:</span>
      <div class="mt-2 prose dark:prose-invert max-w-none text-sm" v-html="renderedNote" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import RatingStars from './RatingStars.vue'
import { useNotes } from '@/composables/useNotes'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  repoId: string
}>()

const emit = defineEmits<{
  (e: 'update'): void
}>()

const { getNote, saveNote } = useNotes()
const { success } = useToast()

const localNote = ref('')
const localRating = ref(0)
const isLoading = ref(true)
const saveTimeout = ref<number | null>(null)

onMounted(async () => {
  const note = await getNote(props.repoId)
  if (note) {
    localNote.value = note.note || ''
    localRating.value = note.rating || 0
  }
  isLoading.value = false
})

const renderedNote = ref('')

watch(localNote, () => {
  const html = marked(localNote.value || '')
  renderedNote.value = DOMPurify.sanitize(html)
}, { immediate: true })

function updateRating(rating: number) {
  localRating.value = rating
  save()
  success('评分已更新', { timeout: 1500 })
}

async function save() {
  // Debounce save and show success message
  if (saveTimeout.value) {
    clearTimeout(saveTimeout.value)
  }

  saveTimeout.value = window.setTimeout(async () => {
    await saveNote(props.repoId, localNote.value, localRating.value)
    if (localNote.value) {
      success('笔记已保存', { timeout: 1500 })
    }
    emit('update')
  }, 500)
}
</script>
