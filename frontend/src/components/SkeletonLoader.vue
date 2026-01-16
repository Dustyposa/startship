<template>
  <transition name="fade">
    <div class="skeleton-pulse" :class="classes" :style="style">
      <div v-if="avatar" class="skeleton-avatar"></div>
      <div class="skeleton-content">
        <div v-if="title" class="skeleton-title"></div>
        <div v-for="i in lines" :key="i" class="skeleton-text"></div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  avatar?: boolean
  title?: boolean
  lines?: number
  width?: string
  height?: string
  variant?: 'text' | 'rect' | 'circle'
}

const props = withDefaults(defineProps<Props>(), {
  avatar: false,
  title: false,
  lines: 3,
  variant: 'text'
})

const classes = computed(() => ({
  'skeleton-avatar': props.variant === 'circle',
  'skeleton-rect': props.variant === 'rect',
  'skeleton-text': props.variant === 'text'
}))

const style = computed(() => ({
  width: props.width,
  height: props.height
}))
</script>

<style scoped>
.skeleton-pulse {
  background: #f0f0f0;
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
}

.dark .skeleton-pulse {
  background: #374151;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  flex-shrink: 0;
}

.skeleton-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-title {
  height: 20px;
  width: 60%;
  border-radius: 4px;
}

.skeleton-text {
  height: 16px;
  width: 100%;
  border-radius: 4px;
}

.skeleton-text:last-child {
  width: 80%;
}
</style>
