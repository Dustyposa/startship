<template>
  <div class="language-indicator relative flex items-center gap-1 group">
    <div
      v-for="(lang, index) in displayLanguages"
      :key="index"
      class="flex items-center"
    >
      <div
        class="w-2 h-2 rounded-full flex-shrink-0"
        :style="{ backgroundColor: getColor(lang.name) }"
      ></div>
    </div>
    <span v-if="languages.length > 3" class="text-xs text-gray-500 dark:text-gray-400">
      +{{ languages.length - 3 }}
    </span>

    <!-- Tooltip showing all languages -->
    <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
      <div class="space-y-1">
        <div v-for="lang in sortedLanguages" :key="lang.name" class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full flex-shrink-0" :style="{ backgroundColor: getColor(lang.name) }"></div>
          <span>{{ lang.name }}</span>
          <span class="text-gray-300">{{ lang.percent.toFixed(1) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Language {
  name: string
  size: number
  percent: number
}

interface Props {
  languages: Language[]
  limit?: number
}

const props = withDefaults(defineProps<Props>(), {
  limit: 3
})

// Top N languages by percentage for display dots
const displayLanguages = computed(() => {
  return props.languages
    .sort((a, b) => b.percent - a.percent)
    .slice(0, props.limit)
})

// All languages sorted for tooltip
const sortedLanguages = computed(() => {
  return props.languages.sort((a, b) => b.percent - a.percent)
})

// Color mapping for common languages
const colorMap: Record<string, string> = {
  'Python': '#3572A5',
  'JavaScript': '#f1e05a',
  'TypeScript': '#2b7489',
  'Java': '#b07219',
  'Go': '#00ADD8',
  'Rust': '#dea584',
  'C++': '#f34b7d',
  'C': '#555555',
  'C#': '#239120',
  'Ruby': '#701516',
  'PHP': '#4F5D95',
  'Swift': '#F05138',
  'Kotlin': '#A97BFF',
  'Dart': '#00B4AB',
  'HTML': '#e34c26',
  'CSS': '#563d7c',
  'Shell': '#89e051',
  'Vue': '#41b883',
  'React': '#61dafb',
  'Scala': '#DC322F',
  'R': '#198CE7',
  'MATLAB': '#e16737',
  'Jupyter Notebook': '#DA5B0B'
}

function getColor(language: string): string {
  return colorMap[language] || '#888888'
}
</script>

<style scoped>
.language-indicator {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
</style>

