<template>
  <div class="max-w-4xl mx-auto">
    <div class="bg-white rounded-lg shadow-sm">
      <div class="p-4 border-b flex justify-between items-center">
        <h2 class="text-lg font-bold">AI 助手</h2>
        <button
          @click="clearMessages"
          class="text-sm text-gray-600 hover:text-gray-900"
        >
          清空对话
        </button>
      </div>

      <div ref="messagesContainer" class="h-96 overflow-y-auto p-4 space-y-4">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="[
            'flex',
            msg.role === 'user' ? 'justify-end' : 'justify-start'
          ]"
        >
          <div
            :class="[
              'max-w-md px-4 py-2 rounded-lg',
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-900'
            ]"
          >
            {{ msg.content }}
          </div>
        </div>

        <div v-if="isLoading" class="flex justify-start">
          <div class="bg-gray-100 px-4 py-2 rounded-lg">
            <div class="flex gap-1">
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="p-4 border-t">
        <form @submit.prevent="handleSubmit" class="flex gap-2">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="输入你的问题..."
            class="flex-1 px-4 py-2 border rounded-lg"
            :disabled="isLoading"
          />
          <button
            type="submit"
            :disabled="isLoading || !inputMessage.trim()"
            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
          >
            发送
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, computed } from 'vue'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)

async function handleSubmit() {
  if (!inputMessage.value.trim() || isLoading.value) return

  const content = inputMessage.value
  inputMessage.value = ''

  await chatStore.sendMessage(content)

  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function clearMessages() {
  chatStore.clearMessages()
}

onMounted(() => {
  // Load existing session if any
})
</script>
