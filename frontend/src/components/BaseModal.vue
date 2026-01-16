<template>
  <Transition name="modal">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="$emit('close')"
    >
      <div
        class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col animate-fade-in"
        :class="sizeClass"
      >
        <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ title }}</h3>
          <button
            @click="$emit('close')"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
            aria-label="关闭"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-6 overflow-y-auto flex-1">
          <slot />
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  show: boolean
  title: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'lg'
})

defineEmits<{
  (e: 'close'): void
}>()

const sizeClass = computed(() => {
  return {
    sm: 'max-w-md',
    md: 'max-w-2xl',
    lg: 'max-w-lg',
    xl: 'max-w-4xl'
  }[props.size]
})
</script>
