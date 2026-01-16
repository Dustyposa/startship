import { ref, watch } from 'vue'

function getInitialDarkMode(): boolean {
  // Check localStorage first
  const saved = localStorage.getItem('darkMode')
  if (saved !== null) {
    return saved === 'true'
  }
  // Fall back to system preference
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function useDark() {
  // Initialize immediately with stored/system preference
  const isDark = ref(getInitialDarkMode())

  // Apply initial dark mode
  applyDarkMode(isDark.value)

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
