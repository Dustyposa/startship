<template>
  <div class="repo-skeleton-card">
    <div class="repo-skeleton-header">
      <SkeletonLoader variant="rect" :width="60" :height="60" class="repo-skeleton-icon" />
      <div class="repo-skeleton-header-content">
        <SkeletonLoader title :lines="0" :width="120" class="repo-skeleton-title" />
        <SkeletonLoader :lines="1" :width="80" class="repo-skeleton-desc" />
      </div>
    </div>
    <div class="repo-skeleton-body">
      <SkeletonLoader :lines="2" />
    </div>
    <div class="repo-skeleton-tags">
      <SkeletonLoader v-for="i in 3" :key="i" variant="rect" :width="60" :height="24" />
    </div>
    <div class="repo-skeleton-footer">
      <SkeletonLoader variant="rect" :width="80" :height="28" />
    </div>
  </div>
</template>

<script setup lang="ts">
import SkeletonLoader from './SkeletonLoader.vue'
</script>

<style scoped>
.repo-skeleton-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dark .repo-skeleton-card {
  background: #1f2937;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.repo-skeleton-header {
  display: flex;
  gap: 12px;
}

.repo-skeleton-icon {
  flex-shrink: 0;
}

.repo-skeleton-header-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.repo-skeleton-title :deep(.skeleton-title),
.repo-skeleton-desc :deep(.skeleton-text) {
  margin: 0;
}

.repo-skeleton-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.repo-skeleton-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.repo-skeleton-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
