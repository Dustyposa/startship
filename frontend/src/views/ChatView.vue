<template>
  <div class="max-w-4xl mx-auto">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
      <div class="p-4 border-b dark:border-gray-700 flex justify-between items-center">
        <h2 class="text-lg font-bold flex items-center gap-2 text-gray-900 dark:text-white">
          <span class="text-2xl">🤖</span>
          AI 助手
          <span class="px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 text-xs font-medium rounded">Beta</span>
        </h2>
        <button
          @click="clearMessages"
          class="text-sm px-3 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
        >
          🗑️ 清空
        </button>
      </div>

      <div ref="messagesContainer" class="h-[500px] overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
        >
          <div :class="getMessageClasses(msg.role)">
            <div class="whitespace-pre-wrap break-words leading-relaxed">{{ msg.content }}</div>
            <div
              v-if="msg.role === 'assistant' && isStreaming && index === messages.length - 1 && msg.content"
              class="inline-block w-2 h-5 bg-blue-500 animate-pulse ml-1 align-middle"
            ></div>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="showLoadingIndicator" class="flex justify-start">
          <div class="bg-gray-100 dark:bg-gray-700 px-4 py-3 rounded-lg border border-gray-200 dark:border-gray-600">
            <div class="flex gap-1 items-center">
              <div v-for="i in 3" :key="i" class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" :style="{ animationDelay: `${(i - 1) * 0.1}s` }"></div>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="messages.length === 0 && !isLoading" class="flex flex-col items-center justify-center h-full text-center space-y-4">
          <div class="text-6xl">💬</div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">开始对话</h3>
            <p class="text-gray-600 dark:text-gray-400 text-sm">你可以问我关于你的 GitHub 星标仓库的任何问题</p>
            <div class="mt-4 space-y-2">
              <button
                v-for="question in quickQuestions"
                :key="question.text"
                @click="sendQuickQuestion(question.text)"
                class="quick-question-btn"
              >
                {{ question.icon }} {{ question.displayText }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="p-4 border-t dark:border-gray-700 bg-white dark:bg-gray-800">
        <form @submit.prevent="handleSubmit" class="flex gap-2">
          <input
            ref="inputRef"
            v-model="inputMessage"
            type="text"
            placeholder="输入你的问题... (Enter 发送)"
            class="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
            :disabled="isLoading"
          />
          <button
            type="submit"
            :disabled="isLoading || !inputMessage.trim()"
            :class="getSubmitButtonClasses()"
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
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'

const chatStore = useChatStore()
const { confirmClear } = useConfirm()
const { success } = useToast()
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const shouldAutoScroll = ref(true)

// Quick questions data for empty state
const quickQuestions = [
  { icon: '📊', text: '按语言统计我的仓库', displayText: '按语言统计我的仓库' },
  { icon: '🔍', text: '搜索一些机器学习相关的项目', displayText: '搜索机器学习项目' },
  { icon: '⭐', text: '推荐一些值得关注的仓库', displayText: '推荐值得关注的仓库' },
] as const

const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)
const isStreaming = computed(() => chatStore.isStreaming)

// Show loading indicator when loading but not streaming, or when last message is from user
const showLoadingIndicator = computed(() => {
  return isLoading.value && (!isStreaming.value || messages.value.length === 0 || messages.value[messages.value.length - 1].role === 'user')
})

// Message bubble styling classes
function getMessageClasses(role: string): string {
  const base = 'max-w-[80%] px-4 py-3 rounded-lg shadow-sm'
  return role === 'user'
    ? `${base} bg-gradient-to-br from-blue-600 to-blue-700 text-white`
    : `${base} bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 border border-gray-200 dark:border-gray-600`
}

// Submit button classes with dark mode support
function getSubmitButtonClasses(): string {
  const base = 'px-6 py-2.5 rounded-lg transition flex items-center gap-2 font-medium'
  const enabled = 'bg-blue-600 text-white dark:bg-blue-500 dark:text-gray-900 hover:bg-blue-700 dark:hover:bg-blue-400'
  const disabled = 'disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:text-gray-500 dark:disabled:text-gray-400 disabled:cursor-not-allowed'
  return `${base} ${enabled} ${disabled}`
}

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

async function clearMessages() {
  const confirmed = await confirmClear('对话记录')
  if (confirmed) {
    chatStore.clearMessages()
    success('对话记录已清空', { timeout: 2000 })
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

<style scoped>
.quick-question-btn {
  @apply block w-full px-4 py-2 text-left text-sm bg-gray-100 dark:bg-gray-700 hover:bg-blue-50 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 hover:text-blue-600 rounded-lg transition;
}
</style>
