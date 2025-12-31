<template>
  <div class="space-y-8">
    <h1 class="text-3xl font-bold text-gray-900">趋势分析</h1>

    <!-- Loading state -->
    <div v-if="loading" class="text-center py-8 text-gray-500">
      加载中...
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
      {{ error }}
    </div>

    <!-- Normal content -->
    <template v-else>
      <section>
      <h2 class="text-xl font-semibold mb-4">Star 时间线</h2>
      <div class="bg-white p-6 rounded-lg shadow-sm">
        <div v-if="timeline.length === 0" class="text-gray-500">
          暂无数据
        </div>
        <div v-else class="space-y-2">
          <div v-for="point in timeline" :key="point.month" class="flex justify-between">
            <span>{{ point.month }}</span>
            <span class="font-semibold">{{ point.count }} 个项目</span>
          </div>
        </div>
      </div>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-4">语言趋势</h2>
      <div class="bg-white p-6 rounded-lg shadow-sm">
        <div v-if="languageTrends.length === 0" class="text-gray-500">
          暂无数据
        </div>
        <div v-else class="space-y-2">
          <div v-for="(item, index) in languageTrends.slice(0, 10)" :key="index" class="flex justify-between">
            <span>{{ item.language }} ({{ item.month }})</span>
            <span class="font-semibold">{{ item.count }}</span>
          </div>
        </div>
      </div>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-4">主题演变</h2>
      <div class="bg-white p-6 rounded-lg shadow-sm">
        <div v-if="categoryEvolution.length === 0" class="text-gray-500">
          暂无数据
        </div>
        <div v-else class="space-y-2">
          <div v-for="(item, index) in categoryEvolution.slice(0, 10)" :key="index" class="flex justify-between">
            <span>{{ item.category }} ({{ item.month }})</span>
            <span class="font-semibold">{{ item.count }}</span>
          </div>
        </div>
      </div>
    </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface TimelinePoint {
  month: string
  count: number
}

interface TrendItem {
  language?: string
  category?: string
  month: string
  count: number
}

const timeline = ref<TimelinePoint[]>([])
const languageTrends = ref<TrendItem[]>([])
const categoryEvolution = ref<TrendItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  loading.value = true
  error.value = null

  try {
    const [timelineRes, langRes, catRes] = await Promise.all([
      fetch('/api/trends/timeline'),
      fetch('/api/trends/languages'),
      fetch('/api/trends/categories')
    ])

    if (!timelineRes.ok || !langRes.ok || !catRes.ok) {
      throw new Error('Failed to fetch trend data')
    }

    const timelineData = await timelineRes.json()
    const langData = await langRes.json()
    const catData = await catRes.json()

    // Basic validation
    if (!Array.isArray(timelineData) || !Array.isArray(langData) || !Array.isArray(catData)) {
      throw new Error('Invalid data format')
    }

    timeline.value = timelineData
    languageTrends.value = langData
    categoryEvolution.value = catData
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unknown error'
    console.error('Failed to load trends:', err)
  } finally {
    loading.value = false
  }
})
</script>
