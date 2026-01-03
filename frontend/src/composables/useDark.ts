import { ref, watch, onMounted } from 'vue'

export function useDark() {
  const isDark = ref(false)

  // Check localStorage and system preference on mount
  onMounted(() => {
    const saved = localStorage.getItem('darkMode')
    if (saved !== null) {
      // Use saved preference
      isDark.value = saved === 'true'
    } else {
      // Use system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      isDark.value = prefersDark
    }

    // Apply immediately
    applyDarkMode(isDark.value)
  })

  // Watch for changes and update DOM
  watch(isDark, (value) => {
    localStorage.setItem('darkMode', String(value))
    applyDarkMode(value)
  })

  function applyDarkMode(dark: boolean) {
    if (dark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  function toggle() {
    isDark.value = !isDark.value
  }

  return {
    isDark,
    toggle
  }
}
