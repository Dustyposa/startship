<template>
  <div class="max-w-4xl mx-auto">
    <div class="bg-white rounded-lg shadow-sm">
      <div class="p-4 border-b flex justify-between items-center">
        <h2 class="text-lg font-bold flex items-center gap-2">
          <span class="text-2xl">🤖</span>
          AI 助手
        </h2>
        <button
          @click="clearMessages"
          class="text-sm px-3 py-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition"
        >
          🗑️ 清空
        </button>
      </div>

      <div ref="messagesContainer" class="h-[500px] overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-gray-50 to-white">
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
              'max-w-[80%] px-4 py-3 rounded-lg shadow-sm',
              msg.role === 'user'
                ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white'
                : 'bg-white text-gray-900 border border-gray-200'
            ]"
          >
            <div class="whitespace-pre-wrap break-words leading-relaxed">{{ msg.content }}</div>
            <div
              v-if="msg.role === 'assistant' && isStreaming && index === messages.length - 1 && msg.content"
              class="inline-block w-2 h-5 bg-blue-500 animate-pulse ml-1 align-middle"
            ></div>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="isLoading && (!isStreaming || messages.length === 0 || messages[messages.length - 1].role === 'user')" class="flex justify-start">
          <div class="bg-gray-100 px-4 py-3 rounded-lg border border-gray-200">
            <div class="flex gap-1 items-center">
              <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
              <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="messages.length === 0 && !isLoading" class="flex flex-col items-center justify-center h-full text-center space-y-4">
          <div class="text-6xl">💬</div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">开始对话</h3>
            <p class="text-gray-600 text-sm">你可以问我关于你的 GitHub 星标仓库的任何问题</p>
            <div class="mt-4 space-y-2">
              <button
                @click="sendQuickQuestion('按语言统计我的仓库')"
                class="block w-full px-4 py-2 text-left text-sm bg-gray-100 hover:bg-blue-50 text-gray-700 hover:text-blue-600 rounded-lg transition"
              >
                📊 按语言统计我的仓库
              </button>
              <button
                @click="sendQuickQuestion('搜索一些机器学习相关的项目')"
                class="block w-full px-4 py-2 text-left text-sm bg-gray-100 hover:bg-blue-50 text-gray-700 hover:text-blue-600 rounded-lg transition"
              >
                🔍 搜索机器学习项目
              </button>
              <button
                @click="sendQuickQuestion('推荐一些值得关注的仓库')"
                class="block w-full px-4 py-2 text-left text-sm bg-gray-100 hover:bg-blue-50 text-gray-700 hover:text-blue-600 rounded-lg transition"
              >
                ⭐ 推荐值得关注的仓库
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="p-4 border-t bg-white">
        <form @submit.prevent="handleSubmit" class="flex gap-2">
          <input
            ref="inputRef"
            v-model="inputMessage"
            type="text"
            placeholder="输入你的问题... (Enter 发送)"
            class="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
            :disabled="isLoading"
          />
          <button
            type="submit"
            :disabled="isLoading || !inputMessage.trim()"
            class="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition flex items-center gap-2"
          >
            <span v-if="!isLoading">发送</span>
            <span v-else>发送中...</span>
            <svg v-if="!isLoading" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
        <p class="text-xs text-gray-500 mt-2">
          💡 提示：对话历史已自动保存，刷新页面不会丢失
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, computed, watch } from 'vue'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const shouldAutoScroll = ref(true)

const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)
const isStreaming = computed(() => chatStore.isStreaming)

// Auto-scroll to bottom when new messages arrive
watch(messages, async () => {
  if (shouldAutoScroll.value) {
    await nextTick()
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }
}, { deep: true })

// Detect if user is scrolling up
function handleScroll() {
  if (!messagesContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
  shouldAutoScroll.value = isAtBottom
}

async function handleSubmit() {
  if (!inputMessage.value.trim() || isLoading.value) return

  const content = inputMessage.value
  inputMessage.value = ''
  shouldAutoScroll.value = true

  await chatStore.sendMessage(content)

  // Focus input after sending
  await nextTick()
  inputRef.value?.focus()
}

async function sendQuickQuestion(question: string) {
  inputMessage.value = question
  await handleSubmit()
}

function clearMessages() {
  if (confirm('确定要清空所有对话记录吗？')) {
    chatStore.clearMessages()
  }
}

onMounted(() => {
  // Focus input on mount
  inputRef.value?.focus()

  // Attach scroll listener
  if (messagesContainer.value) {
    messagesContainer.value.addEventListener('scroll', handleScroll)
  }
})
</script>
