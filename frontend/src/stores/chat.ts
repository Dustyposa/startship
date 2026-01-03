import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatMessage } from '../types'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const sessionId = ref<string>(`${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const isLoading = ref(false)
  const isStreaming = ref(false)
  const error = ref<string | null>(null)

  // Load chat history from localStorage on mount
  const saved = localStorage.getItem('chat_history')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length > 0) {
        messages.value = parsed
      }
    } catch (e) {
      console.error('Failed to load chat history:', e)
    }
  }

  // Save to localStorage whenever messages change
  function saveHistory() {
    localStorage.setItem('chat_history', JSON.stringify(messages.value))
  }

  async function sendMessage(content: string) {
    isLoading.value = true
    isStreaming.value = true
    error.value = null

    // Add user message
    messages.value.push({
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    })
    saveHistory()

    // Create placeholder for assistant response
    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    }
    messages.value.push(assistantMessage)
    saveHistory()

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId.value,
          message: content,
          use_rag: false
        })
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process SSE lines
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()

            if (data === '[DONE]') {
              isStreaming.value = false
              isLoading.value = false
              break
            }

            try {
              const parsed = JSON.parse(data)

              if (parsed.type === 'content') {
                // Typewriter effect: append character by character
                const newContent = parsed.content || ''
                const currentLength = assistantMessage.content.length

                // Add content with slight delay for typewriter effect
                await typeWriterEffect(assistantMessage, newContent)
              } else if (parsed.type === 'done') {
                isStreaming.value = false
                isLoading.value = false
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to send message'
      error.value = message
      assistantMessage.content = `❌ ${message}`
      isStreaming.value = false
      isLoading.value = false
      throw err
    } finally {
      saveHistory()
    }
  }

  // Typewriter effect function
  async function typeWriterEffect(message: ChatMessage, newContent: string) {
    const chars = newContent.split('')
    for (const char of chars) {
      message.content += char
      // Small delay for each character
      await new Promise(resolve => setTimeout(resolve, 5))
    }
  }

  function clearMessages() {
    messages.value = []
    sessionId.value = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    error.value = null
    localStorage.removeItem('chat_history')
  }

  return { messages, sessionId, isLoading, isStreaming, error, sendMessage, clearMessages }
})
