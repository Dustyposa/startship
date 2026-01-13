import { onMounted, onUnmounted } from 'vue'

export function useKeyboard(shortcuts: Record<string, () => void>) {
  function handleKeyDown(event: KeyboardEvent) {
    const key = event.key

    // Cmd/Ctrl + K
    if ((event.metaKey || event.ctrlKey) && key === 'k') {
      event.preventDefault()
      shortcuts['cmd+k']?.()
    }

    // Cmd/Ctrl + N
    if ((event.metaKey || event.ctrlKey) && key === 'n') {
      event.preventDefault()
      shortcuts['cmd+n']?.()
    }

    // Escape
    if (key === 'Escape') {
      shortcuts['escape']?.()
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
  })
}
