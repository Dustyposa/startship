<template>
  <div class="trend-indicator">
    <svg
      v-if="trend === 'up'"
      class="w-5 h-5 text-green-500"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
    <svg
      v-else-if="trend === 'down'"
      class="w-5 h-5 text-red-500"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
    </svg>
    <span v-else class="text-gray-400 text-lg leading-none">&mdash;</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  trend: 'up' | 'down' | 'neutral'
}>()
</script>

<style scoped>
.trend-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
