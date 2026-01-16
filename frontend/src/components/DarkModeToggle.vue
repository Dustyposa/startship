<template>
  <button
    @click="onClick"
    class="dark-mode-toggle"
    :class="{ 'dark': isDark }"
    :aria-label="isDark ? '切换到亮色模式' : '切换到暗色模式'"
    :title="isDark ? '切换到亮色模式' : '切换到暗色模式'"
  >
    <span class="toggle-slider">
      <span v-if="!isDark" class="icon sun-icon">☀️</span>
      <span v-else class="icon moon-icon">🌙</span>
    </span>
  </button>
</template>

<script setup lang="ts">
defineProps<{
  isDark: boolean
}>()

const emit = defineEmits<{
  (e: 'click'): void
}>()

function onClick() {
  emit('click')
}
</script>

<style scoped>
.dark-mode-toggle {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 24px;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.dark-mode-toggle:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.dark-mode-toggle.dark {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.dark-mode-toggle.dark:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.toggle-slider {
  position: relative;
  width: 40px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  font-size: 16px;
  line-height: 1;
  transition: all 0.3s ease;
  color: #ffffff;
}

.sun-icon {
  filter: drop-shadow(0 0 6px rgba(255, 200, 0, 0.8));
}

.moon-icon {
  filter: drop-shadow(0 0 6px rgba(200, 220, 255, 0.8));
}
</style>
