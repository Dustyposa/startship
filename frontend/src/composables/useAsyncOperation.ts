import { ref } from 'vue'

/**
 * Shared async operation handler for composables.
 * Manages loading state, error handling, and execution.
 */
export function useAsyncOperation() {
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Execute an async operation with automatic loading/error handling.
   * @param operation The async function to execute
   * @param errorMessage Custom error message prefix
   * @returns The operation result or null/undefined on error
   */
  async function execute<T>(
    operation: () => Promise<T>,
    errorMessage: string = 'Operation failed'
  ): Promise<T | null> {
    isLoading.value = true
    error.value = null
    try {
      return await operation()
    } catch (err) {
      error.value = err instanceof Error ? err.message : errorMessage
      console.error(`Error: ${errorMessage}`, err)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Execute an async operation without error handling (for non-critical ops).
   * @param operation The async function to execute
   * @returns The operation result or default value on error
   */
  async function executeSilent<T>(
    operation: () => Promise<T>,
    defaultValue: T
  ): Promise<T> {
    try {
      return await operation()
    } catch (err) {
      console.error('Error in silent operation:', err)
      return defaultValue
    }
  }

  return {
    isLoading,
    error,
    execute,
    executeSilent
  }
}
