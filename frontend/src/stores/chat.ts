import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatMessage } from '../types'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const sessionId = ref<string>(`session_${Date.now()}`)
  const isLoading = ref(false)

  async function sendMessage(content: string) {
    isLoading.value = true
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
    } finally {
      isLoading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    sessionId.value = `session_${Date.now()}`
  }

  return { messages, sessionId, isLoading, sendMessage, clearMessages }
})
