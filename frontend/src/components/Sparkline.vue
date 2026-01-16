<template>
  <svg
    :viewBox="`0 0 ${width} ${height}`"
    :width="width"
    :height="height"
    class="sparkline"
    preserveAspectRatio="none"
  >
    <defs>
      <linearGradient :id="gradientId" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" :stop-color="color" stop-opacity="0.3"/>
        <stop offset="100%" :stop-color="color" stop-opacity="0"/>
      </linearGradient>
    </defs>

    <path
      v-if="showArea"
      :d="areaPath"
      :fill="`url(#${gradientId})`"
      stroke="none"
    />

    <path
      :d="linePath"
      :stroke="color"
      :stroke-width="strokeWidth"
      fill="none"
      stroke-linecap="round"
      stroke-linejoin="round"
    />

    <circle
      v-if="showDot"
      :cx="lastPoint.x"
      :cy="lastPoint.y"
      :r="dotRadius"
      :fill="color"
    />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  data: number[]
  color: string
  width?: number
  height?: number
  strokeWidth?: number
  showArea?: boolean
  showDot?: boolean
  dotRadius?: number
}>(), {
  width: 64,
  height: 32,
  strokeWidth: 2,
  showArea: true,
  showDot: true,
  dotRadius: 2
})

// Unique ID for gradient (stable across renders)
const gradientId = `sparkline-gradient-${Math.random().toString(36).slice(2, 11)}`

const points = computed(() => {
  if (props.data.length === 0) return []

  const min = Math.min(...props.data)
  const max = Math.max(...props.data)
  const range = max - min || 1

  return props.data.map((value, index) => ({
    x: (index / (props.data.length - 1 || 1)) * props.width,
    y: props.height - ((value - min) / range) * props.height
  }))
})

const formatPath = (points: typeof points.value) => {
  return points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ')
}

const linePath = computed(() => {
  if (points.value.length === 0) return ''
  return formatPath(points.value)
})

const areaPath = computed(() => {
  if (points.value.length === 0) return ''
  return `${formatPath(points.value)} L ${props.width} ${props.height} L 0 Z`
})

const lastPoint = computed(() => points.value[points.value.length - 1])
</script>

<style scoped>
.sparkline {
  display: block;
  overflow: visible;
}
</style>
