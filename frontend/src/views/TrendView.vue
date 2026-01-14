<template>
  <div class="space-y-8">
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-3">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">📈 趋势分析</h1>
        <span class="px-2 py-1 bg-yellow-100 text-yellow-800 text-sm font-medium rounded">Beta</span>
      </div>
      <button
        @click="exportData"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
      >
        <span>导出数据</span>
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-center py-12 text-gray-600 dark:text-gray-400">
      <div class="flex justify-center">
        <svg class="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
      <p class="mt-2">加载趋势数据中...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
      {{ error }}
    </div>

    <!-- Normal content -->
    <template v-else>
      <!-- Stats Overview -->
      <section class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div class="text-3xl font-bold text-blue-600">{{ totalStars }}</div>
          <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">总 Star 数</div>
        </div>
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div class="text-3xl font-bold text-green-600">{{ totalLanguages }}</div>
          <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">编程语言</div>
        </div>
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div class="text-3xl font-bold text-purple-600">{{ totalCategories }}</div>
          <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">技术分类</div>
        </div>
      </section>

      <!-- Star Timeline Chart -->
      <section class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">📅 Star 时间线</h2>
        <div v-if="timeline.length === 0" class="text-gray-500 dark:text-gray-400 text-center py-8">
          暂无数据
        </div>
        <div v-else ref="timelineChart" style="height: 300px"></div>
      </section>

      <!-- Language Distribution Pie Chart -->
      <section class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">🗂️ 语言分布</h2>
        <div v-if="languageData.length === 0" class="text-gray-500 dark:text-gray-400 text-center py-8">
          暂无数据
        </div>
        <div v-else ref="languageChart" style="height: 350px"></div>
      </section>

      <!-- Category Trends Bar Chart -->
      <section class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">🏷️ 分类趋势 (Top 10)</h2>
        <div v-if="categoryData.length === 0" class="text-gray-500 dark:text-gray-400 text-center py-8">
          暂无数据
        </div>
        <div v-else ref="categoryChart" style="height: 400px"></div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts/core'
import { useExport } from '../composables/useExport'

// Register ECharts components
echarts.use([
  LineChart,
  PieChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  CanvasRenderer
])

const { exportToJSON } = useExport()

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

const timelineChart = ref<HTMLElement>()
const languageChart = ref<HTMLElement>()
const categoryChart = ref<HTMLElement>()

const totalStars = computed(() => timeline.value.reduce((sum, p) => sum + p.count, 0))
const totalLanguages = computed(() => new Set(languageTrends.value.map(t => t.language)).size)
const totalCategories = computed(() => new Set(categoryEvolution.value.map(t => t.category)).size)

const languageData = computed(() => {
  const counts = new Map<string, number>()
  languageTrends.value.forEach(t => {
    if (t.language) {
      counts.set(t.language, (counts.get(t.language) || 0) + t.count)
    }
  })
  return Array.from(counts.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10)
})

const categoryData = computed(() => {
  const counts = new Map<string, number>()
  categoryEvolution.value.forEach(t => {
    if (t.category) {
      counts.set(t.category, (counts.get(t.category) || 0) + t.count)
    }
  })
  return Array.from(counts.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10)
})

function initCharts() {
  // Timeline Chart
  if (timelineChart.value && timeline.value.length > 0) {
    const chart = echarts.init(timelineChart.value)
    const option: EChartsOption = {
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: timeline.value.map(p => p.month),
        axisLabel: { rotate: 45 }
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: timeline.value.map(p => p.count),
        type: 'line',
        smooth: true,
        areaStyle: {},
        itemStyle: { color: '#3b82f6' }
      }]
    }
    chart.setOption(option)
  }

  // Language Pie Chart
  if (languageChart.value && languageData.value.length > 0) {
    const chart = echarts.init(languageChart.value)
    const option: EChartsOption = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center'
      },
      series: [{
        name: '编程语言',
        type: 'pie',
        radius: ['40%', '70%'],
        data: languageData.value,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
    chart.setOption(option)
  }

  // Category Bar Chart
  if (categoryChart.value && categoryData.value.length > 0) {
    const chart = echarts.init(categoryChart.value)
    const option: EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      xAxis: {
        type: 'category',
        data: categoryData.value.map(d => d.name),
        axisLabel: { rotate: 45 }
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: categoryData.value.map(d => d.value),
        type: 'bar',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#8b5cf6' },
            { offset: 1, color: '#6366f1' }
          ])
        }
      }]
    }
    chart.setOption(option)
  }
}

function exportData() {
  const data = {
    timeline: timeline.value,
    languageTrends: languageTrends.value,
    categoryEvolution: categoryEvolution.value,
    stats: {
      totalStars: totalStars.value,
      totalLanguages: totalLanguages.value,
      totalCategories: totalCategories.value
    }
  }
  exportToJSON([data], `trends-${new Date().toISOString().slice(0, 10)}`)
}

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

    if (!Array.isArray(timelineData) || !Array.isArray(langData) || !Array.isArray(catData)) {
      throw new Error('Invalid data format')
    }

    timeline.value = timelineData
    languageTrends.value = langData
    categoryEvolution.value = catData

    // Initialize charts after data is loaded
    setTimeout(() => initCharts(), 100)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unknown error'
    console.error('Failed to load trends:', err)
  } finally {
    loading.value = false
  }
})
</script>
