import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatMessage } from '../types'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const sessionId = ref<string>(`${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function sendMessage(content: string) {
    isLoading.value = true
    error.value = null
    try {
      const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId.value,
          message: content,
          use_rag: false
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `Server error: ${response.status}`)
      }

      const data = await response.json()

      messages.value.push({
        role: 'user',
        content,
        timestamp: new Date().toISOString()
      })
      messages.value.push({
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString()
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to send message'
      error.value = message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    sessionId.value = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    error.value = null
  }

  return { messages, sessionId, isLoading, error, sendMessage, clearMessages }
})
