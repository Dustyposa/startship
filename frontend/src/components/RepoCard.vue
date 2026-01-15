<template>
  <div
    class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm hover:shadow-md cursor-pointer transition border"
    :class="isInCollection ? 'border-yellow-400 dark:border-yellow-500' : 'border-gray-200 dark:border-gray-700'"
    @click="$emit('click', repo.name_with_owner)"
  >
    <div class="cursor-pointer">
      <h3 class="font-bold text-gray-900 dark:text-white">{{ repo.name_with_owner }}</h3>
      <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{{ repo.description || repo.summary }}</p>

      <div class="flex gap-2 mt-2 flex-wrap">
        <span v-if="repo.primary_language" class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
          {{ repo.primary_language }}
        </span>
        <span class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded">
          ⭐ {{ formatStarCount(repo.stargazer_count) }}
        </span>
        <span v-if="repo.starred_at" class="text-xs px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded">
          ⭐ {{ formatRelativeTime(repo.starred_at) }}
        </span>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="flex gap-2 mt-3 pt-3 border-t border-gray-200 dark:border-gray-700" @click.stop>
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Repository } from '@/types'
import { formatStarCount, formatRelativeTime } from '@/utils/format'

defineProps<{
  repo: Repository
  isInCollection?: boolean
}>()

defineEmits<{
  (e: 'click', nameWithOwner: string): void
}>()
</script>
