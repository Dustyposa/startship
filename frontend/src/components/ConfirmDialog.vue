<template>
  <BaseModal
    :show="show"
    :title="title"
    :size="size"
    @close="handleCancel"
  >
    <div class="space-y-4">
      <!-- Icon and Message -->
      <div class="flex items-start gap-3">
        <div v-if="icon" class="flex-shrink-0 text-2xl">{{ icon }}</div>
        <div class="flex-1">
          <p v-if="message" class="text-gray-700 dark:text-gray-300">{{ message }}</p>
          <p v-if="subMessage" class="text-sm text-gray-600 dark:text-gray-400 mt-1">{{ subMessage }}</p>
        </div>
      </div>

      <!-- Warning/Info Box -->
      <div v-if="warning" class="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
        <div class="flex items-start gap-2">
          <svg class="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
          </svg>
          <span class="text-sm text-yellow-800 dark:text-yellow-200">{{ warning }}</span>
        </div>
      </div>

      <!-- Details (optional) -->
      <div v-if="details" class="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded">
        {{ details }}
      </div>
    </div>

    <!-- Actions -->
    <template #footer>
      <div class="flex justify-end gap-3 mt-6">
        <button
          v-if="showCancel"
          @click="handleCancel"
          class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
          :disabled="loading"
        >
          {{ cancelText }}
        </button>
        <button
          @click="handleConfirm"
          class="px-4 py-2 rounded-lg transition flex items-center gap-2"
          :class="confirmButtonClass"
          :disabled="loading"
        >
          <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>{{ confirmText }}</span>
        </button>
      </div>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseModal from './BaseModal.vue'

interface Props {
  show: boolean
  title: string
  message?: string
  subMessage?: string
  icon?: string
  warning?: string
  details?: string
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
  type?: 'danger' | 'warning' | 'info' | 'success'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  confirmText: '确认',
  cancelText: '取消',
  showCancel: true,
  type: 'danger',
  size: 'md',
  loading: false
})

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const confirmButtonClass = computed(() => {
  const baseClass = 'font-medium'
  const typeClasses = {
    danger: 'bg-red-600 text-white hover:bg-red-700 disabled:bg-red-400',
    warning: 'bg-yellow-600 text-white hover:bg-yellow-700 disabled:bg-yellow-400',
    info: 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400',
    success: 'bg-green-600 text-white hover:bg-green-700 disabled:bg-green-400'
  }
  return `${baseClass} ${typeClasses[props.type]}`
})

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  if (!props.loading) {
    emit('cancel')
  }
}
</script>
