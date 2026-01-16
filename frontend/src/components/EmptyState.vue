<template>
  <div class="empty-state">
    <div v-if="icon" class="empty-state-icon">{{ icon }}</div>
    <svg v-else class="empty-state-icon-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
    </svg>
    <h3 v-if="title" class="empty-state-title">{{ title }}</h3>
    <p v-if="message" class="empty-state-message">{{ message }}</p>
    <slot v-if="$slots.default" />
  </div>
</template>

<script setup lang="ts">
interface Props {
  icon?: string
  title?: string
  message?: string
}

withDefaults(defineProps<Props>(), {
  icon: '',
  title: '',
  message: ''
})
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #6b7280;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.dark .empty-state {
  color: #9ca3af;
}

.empty-state-icon {
  font-size: 3rem;
  line-height: 1;
}

.empty-state-icon-svg {
  width: 4rem;
  height: 4rem;
  opacity: 0.5;
}

.empty-state-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.dark .empty-state-title {
  color: #f9fafb;
}

.empty-state-message {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
  max-width: 400px;
}

.dark .empty-state-message {
  color: #9ca3af;
}
</style>
