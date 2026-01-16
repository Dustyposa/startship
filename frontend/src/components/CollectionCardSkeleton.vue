<template>
  <div class="collection-skeleton-card">
    <div class="collection-skeleton-header">
      <SkeletonLoader variant="circle" :width="40" :height="40" class="collection-skeleton-icon" />
      <div class="collection-skeleton-header-content">
        <SkeletonLoader title :lines="0" :width="100" class="collection-skeleton-title" />
      </div>
    </div>
    <div class="collection-skeleton-count">
      <SkeletonLoader :lines="1" :width="60" />
    </div>
  </div>
</template>

<script setup lang="ts">
import SkeletonLoader from './SkeletonLoader.vue'
</script>

<style scoped>
.collection-skeleton-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 12px;
  border: 1px solid #e5e7eb;
}

.dark .collection-skeleton-card {
  background: #1f2937;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  border-color: #374151;
}

.collection-skeleton-header {
  display: flex;
  align-items: start;
  gap: 12px;
  justify-content: space-between;
}

.collection-skeleton-icon {
  flex-shrink: 0;
}

.collection-skeleton-header-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.collection-skeleton-title :deep(.skeleton-title) {
  margin: 0;
}

.collection-skeleton-count {
  margin-top: 8px;
}

.collection-skeleton-count :deep(.skeleton-text) {
  margin: 0;
}
</style>
