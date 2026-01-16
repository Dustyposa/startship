<template>
  <div class="pie-chart-container">
    <svg :viewBox="`-100 -100 200 200`" :width="size" :height="size">
      <g v-for="(slice, index) in slices" :key="index">
        <!-- Pie slice -->
        <path
          :d="getSlicePath(slice.startAngle, slice.endAngle)"
          :fill="slice.color"
          :stroke="isDark ? '#1f2937' : '#fff'"
          stroke-width="2"
          class="hover:opacity-80 transition-opacity cursor-pointer"
          @mouseenter="hoveredIndex = index"
          @mouseleave="hoveredIndex = -1"
        />
        <!-- Label (only shown if slice is large enough) -->
        <text
          v-if="slice.percent > 5"
          :x="getLabelPosition(slice.startAngle, slice.endAngle).x"
          :y="getLabelPosition(slice.startAngle, slice.endAngle).y"
          text-anchor="middle"
          dominant-baseline="middle"
          class="text-xs font-medium fill-white pointer-events-none"
          :class="{ 'dark:fill-gray-900': slice.color === '#fbbf24' || slice.color === '#f87171' }"
        >
          {{ slice.percent }}%
        </text>
      </g>
      <!-- Center hole for donut chart (optional) -->
      <circle v-if="donut" cx="0" cy="0" :r="donutRadius" :fill="isDark ? '#1f2937' : '#fff'" />
    </svg>

    <!-- Legend -->
    <div v-if="showLegend" class="legend">
      <div
        v-for="(item, index) in slices"
        :key="index"
        class="legend-item"
        :class="{ 'font-bold': hoveredIndex === index }"
      >
        <span class="legend-color" :style="{ backgroundColor: item.color }"></span>
        <span class="legend-label">{{ item.label }}</span>
        <span class="legend-value">{{ item.count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface PieData {
  label: string
  value: number
  color?: string
}

const props = withDefaults(defineProps<{
  data: PieData[]
  size?: number
  donut?: boolean
  donutRadius?: number
  showLegend?: boolean
  isDark?: boolean
}>(), {
  size: 200,
  donut: true,
  donutRadius: 60,
  showLegend: true,
  isDark: false
})

const hoveredIndex = ref(-1)

const colorPalette = [
  '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'
]

const total = computed(() => props.data.reduce((sum, item) => sum + item.value, 0))

const slices = computed(() => {
  let currentAngle = -90
  const result = []

  for (let i = 0; i < props.data.length; i++) {
    const item = props.data[i]
    const percent = total.value > 0 ? (item.value / total.value) * 100 : 0
    const angle = (percent / 100) * 360

    result.push({
      label: item.label,
      value: item.value,
      count: item.value,
      percent: Math.round(percent * 10) / 10,
      color: item.color || colorPalette[i % colorPalette.length],
      startAngle: currentAngle,
      endAngle: currentAngle + angle
    })

    currentAngle += angle
  }

  return result.sort((a, b) => b.value - a.value)
})

function getSlicePath(startAngle: number, endAngle: number): string {
  const start = polarToCartesian(0, 0, 100, endAngle)
  const end = polarToCartesian(0, 0, 100, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? 0 : 1

  return [
    'M', start.x, start.y,
    'A', 100, 100, 0, largeArcFlag, 0, end.x, end.y,
    'L', 0, 0,
    'Z'
  ].join(' ')
}

function polarToCartesian(centerX: number, centerY: number, radius: number, angleInDegrees: number) {
  const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0
  return {
    x: centerX + (radius * Math.cos(angleInRadians)),
    y: centerY + (radius * Math.sin(angleInRadians))
  }
}

function getLabelPosition(startAngle: number, endAngle: number) {
  const midAngle = (startAngle + endAngle) / 2
  const radius = props.donut ? (100 + props.donutRadius) / 2 : 65
  return polarToCartesian(0, 0, radius, midAngle)
}
</script>

<style scoped>
.pie-chart-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: #6b7280;
  transition: opacity 0.15s;
}

.dark .legend-item {
  color: #9ca3af;
}

.legend-item:hover {
  opacity: 0.7;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-label {
  font-weight: 500;
}

.legend-value {
  color: #9ca3af;
}

.dark .legend-value {
  color: #6b7280;
}
</style>
