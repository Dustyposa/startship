<template>
  <div class="space-y-8">
    <!-- Onboarding Banner for First-Time Users -->
    <transition name="slide-down">
      <div v-if="showOnboarding" class="relative overflow-hidden bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-8 text-white shadow-lg">
        <div class="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-white opacity-10 rounded-full"></div>
        <div class="absolute bottom-0 left-0 -mb-4 -ml-4 w-32 h-32 bg-white opacity-10 rounded-full"></div>

      <div class="relative z-10">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-4">
              <span class="text-4xl">👋</span>
              <div>
                <h2 class="text-2xl font-bold">欢迎使用 GitHub Star Helper!</h2>
                <p class="text-blue-100">智能管理你的星标仓库，发现技术宝藏</p>
              </div>
            </div>

            <div class="grid md:grid-cols-3 gap-4 mb-6">
              <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div class="text-2xl mb-2">🔍</div>
                <h3 class="font-semibold mb-1">智能搜索</h3>
                <p class="text-sm text-blue-100">按分类、语言快速筛选</p>
              </div>
              <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div class="text-2xl mb-2">💬</div>
                <h3 class="font-semibold mb-1">AI 对话</h3>
                <p class="text-sm text-blue-100">自然语言查询仓库</p>
              </div>
              <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div class="text-2xl mb-2">🕸️</div>
                <h3 class="font-semibold mb-1">关系网络</h3>
                <p class="text-sm text-blue-100">可视化项目关联</p>
              </div>
            </div>

            <div class="flex flex-wrap gap-3">
              <router-link
                to="/init"
                @click="dismissOnboarding"
                class="px-6 py-3 bg-white text-blue-600 font-semibold rounded-lg hover:bg-blue-50 transition shadow-lg"
              >
                🚀 立即开始初始化
              </router-link>
              <button
                @click="dismissOnboarding"
                class="px-6 py-3 bg-white/10 backdrop-blur-sm text-white font-semibold rounded-lg hover:bg-white/20 transition"
              >
                稍后再说
              </button>
            </div>
          </div>

          <button
            @click="dismissOnboarding"
            class="ml-4 p-2 hover:bg-white/10 rounded-lg transition"
            aria-label="关闭"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
    </transition>

    <!-- Sync Status Section -->
    <section v-if="!showOnboarding">
      <SyncStatus />
    </section>

    <!-- Empty State for Non-Initialized Users -->
    <transition name="fade">
      <div v-if="stats.total_repositories === 0 && !showOnboarding" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-12 text-center">
        <div class="text-6xl mb-4">📭</div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">还没有数据</h2>
        <p class="text-gray-600 dark:text-gray-400 mb-6">请先初始化系统，从你的 GitHub 星标仓库中获取数据</p>
        <router-link
          to="/init"
          class="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition shadow-lg"
        >
          <span>前往初始化</span>
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </router-link>
      </div>
    </transition>

    <!-- Hero Section -->
    <transition name="fade">
      <section v-if="stats.total_repositories > 0" class="relative text-center py-8 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-800 rounded-xl">
        <!-- Animated Repos -->
        <template v-for="(item, index) in animatedRepos" :key="`${item.repo.name_with_owner}-${index}`">
          <div
            class="absolute hidden lg:block transition-all duration-500 ease-out"
            :class="item.side === 'left' ? 'left-12' : 'right-12'"
            :style="{ top: `${item.position}%` }"
          >
            <router-link
              v-if="showAnimation"
              :to="`/repo/${encodeURIComponent(item.repo.name_with_owner)}`"
              class="block repo-animate floating-left text-sm font-medium transition-colors"
              :class="item.side === 'left'
                ? 'text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300'
                : 'text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300'"
              :style="{ animationDelay: `${index * 0.15}s` }"
            >
              {{ item.repo.name_with_owner }}
            </router-link>
          </div>
        </template>

        <!-- Center Content -->
        <div class="relative z-10">
          <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            ⭐ GitHub Star Helper
          </h1>
          <p class="text-lg text-gray-600 dark:text-gray-300 mb-6">
            智能分析你的 GitHub 星标仓库，发现技术宝藏
          </p>
          <div class="flex gap-3 justify-center flex-wrap">
            <router-link
              to="/search"
              class="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              🔍 搜索仓库
            </router-link>
            <router-link
              to="/chat"
              class="px-5 py-2.5 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition flex items-center gap-2"
            >
              💬 智能对话
              <span class="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">Beta</span>
            </router-link>
            <router-link
              to="/network"
              class="px-5 py-2.5 border border-purple-600 text-purple-600 rounded-lg hover:bg-purple-50 transition flex items-center gap-2"
            >
              🕸️ 关系网络
              <span class="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">Beta</span>
            </router-link>
          </div>
        </div>
      </section>
    </transition>

    <!-- Quick Stats -->
    <transition name="fade">
      <section v-if="stats.total_repositories > 0">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">📊 数据概览</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border-l-4 border-blue-500">
            <div class="flex items-end justify-between">
              <div>
                <div class="text-2xl font-bold text-blue-600">{{ displayStats.totalRepos }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400">总仓库数</div>
              </div>
              <Sparkline v-if="sparklineData.repos.length > 1" :data="sparklineData.repos" color="#3b82f6" class="w-16 h-8" />
            </div>
          </div>
          <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border-l-4 border-green-500">
            <div class="flex items-end justify-between">
              <div>
                <div class="text-2xl font-bold text-green-600">{{ displayStats.totalLanguages }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400">语言数量</div>
              </div>
              <Sparkline v-if="sparklineData.languages.length > 1" :data="sparklineData.languages" color="#22c55e" class="w-16 h-8" />
            </div>
          </div>
          <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border-l-4 border-purple-500">
            <div class="flex items-end justify-between">
              <div>
                <div class="text-2xl font-bold text-purple-600">{{ displayStats.topLanguage }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400">主要语言</div>
              </div>
              <TrendIndicator :trend="sparklineData.topLanguageTrend" />
            </div>
          </div>
          <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border-l-4 border-orange-500">
            <div class="flex items-end justify-between">
              <div>
                <div class="text-2xl font-bold text-orange-600">{{ displayStats.totalConversations }}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400">对话数</div>
              </div>
              <Sparkline v-if="sparklineData.conversations.length > 1" :data="sparklineData.conversations" color="#f97316" class="w-16 h-8" />
            </div>
          </div>
        </div>
      </section>
    </transition>

    <!-- Feature Cards -->
    <transition name="fade">
      <section v-if="stats.total_repositories > 0">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">🚀 快速功能</h2>
        <transition-group name="list" tag="div" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Search Card -->
          <router-link to="/search" class="block group h-full" key="search">
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 h-full flex flex-col">
              <div class="text-4xl mb-3">🔍</div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">仓库搜索</h3>
              <p class="text-gray-600 dark:text-gray-400 text-sm flex-1">按分类、语言、星标数搜索你的仓库</p>
              <div class="mt-4 text-blue-600 text-sm group-hover:underline">立即搜索 →</div>
            </div>
          </router-link>

          <!-- Chat Card -->
          <router-link to="/chat" class="block group h-full" key="chat">
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 h-full flex flex-col">
              <div class="flex items-start justify-between">
                <div class="text-4xl mb-3">💬</div>
                <span class="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded dark:bg-yellow-900 dark:text-yellow-200">Beta</span>
              </div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">智能对话</h3>
              <p class="text-gray-600 dark:text-gray-400 text-sm flex-1">自然语言查询，智能意图识别</p>
              <div class="mt-4 text-blue-600 text-sm group-hover:underline">开始对话 →</div>
            </div>
          </router-link>

          <!-- Network Card -->
          <router-link to="/network" class="block group h-full" key="network">
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 h-full flex flex-col">
              <div class="flex items-start justify-between">
                <div class="text-4xl mb-3">🕸️</div>
                <span class="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded dark:bg-yellow-900 dark:text-yellow-200">Beta</span>
              </div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">关系网络</h3>
              <p class="text-gray-600 dark:text-gray-400 text-sm flex-1">可视化仓库之间的关联关系</p>
              <div class="mt-4 text-blue-600 text-sm group-hover:underline">查看网络 →</div>
            </div>
          </router-link>

          <!-- Trends Card -->
          <router-link to="/trends" class="block group h-full" key="trends">
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 h-full flex flex-col">
              <div class="flex items-start justify-between">
                <div class="text-4xl mb-3">📈</div>
                <span class="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded dark:bg-yellow-900 dark:text-yellow-200">Beta</span>
              </div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">趋势分析</h3>
              <p class="text-gray-600 dark:text-gray-400 text-sm flex-1">Star 时间线、语言趋势、主题演变</p>
              <div class="mt-4 text-blue-600 text-sm group-hover:underline">查看趋势 →</div>
            </div>
          </router-link>

          <!-- Init Card -->
          <router-link to="/init" class="block group h-full" key="init">
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 h-full flex flex-col">
              <div class="text-4xl mb-3">⚙️</div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">数据初始化</h3>
              <p class="text-gray-600 dark:text-gray-400 text-sm flex-1">从 GitHub 同步你的星标仓库</p>
              <div class="mt-4 text-blue-600 text-sm group-hover:underline">管理数据 →</div>
            </div>
          </router-link>

          <!-- About Card -->
          <div class="bg-gradient-to-br from-blue-500 to-purple-600 p-6 rounded-lg shadow-sm text-white h-full flex flex-col" key="about">
            <div class="text-4xl mb-3">ℹ️</div>
            <h3 class="text-lg font-semibold mb-2">关于</h3>
            <p class="text-sm opacity-90 flex-1">基于 AI 的 GitHub 星标仓库管理和分析工具，帮助你发现和组织技术资源。</p>
            <div class="text-sm opacity-75">Stage 4: 网络可视化</div>
          </div>
        </transition-group>
      </section>
    </transition>

    <!-- Top Languages -->
    <transition name="fade">
      <section v-if="topLanguages.length > 0">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">🔥 热门语言</h2>
        <transition-group name="tag" tag="div" class="flex flex-wrap gap-2">
          <router-link
            v-for="count in topLanguages"
            :key="count[0]"
            :to="`/search?languages=${encodeURIComponent(count[0])}`"
            class="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 hover:text-blue-600 transition-all duration-200 hover:scale-105 text-gray-900 dark:text-white"
          >
            {{ count[0] }} <span class="text-gray-500 dark:text-gray-400">({{ count[1] }})</span>
          </router-link>
        </transition-group>
      </section>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import SyncStatus from '../components/SyncStatus.vue'
import Sparkline from '../components/Sparkline.vue'
import TrendIndicator from '../components/TrendIndicator.vue'

interface Stats {
  total_repositories: number
  total_conversations: number
  languages: Record<string, number>
  top_language: string | null
}

interface TimelinePoint {
  month: string
  count: number
}

interface Repo {
  name_with_owner: string
  description: string | null
  stargazer_count: number
  starred_at: string
}

const stats = ref<Stats>({
  total_repositories: 0,
  total_conversations: 0,
  languages: {},
  top_language: null
})

const showOnboarding = ref(false)
const timelineData = ref<TimelinePoint[]>([])
const languageTrendData = ref<Record<string, TimelinePoint[]>>({})

// Animated repos state
const recentRepos = ref<Repo[]>([])

interface AnimatedRepo {
  repo: Repo
  position: number
  side: 'left' | 'right'
}

const animatedRepos = ref<AnimatedRepo[]>([])
const showAnimation = ref(false)
let animationInterval: ReturnType<typeof setInterval> | null = null

const sparklineData = computed(() => {
  // Last 6 months of repository counts
  const reposData = timelineData.value.slice(-6).map(p => p.count)

  // Calculate top language trend
  const topLang = stats.value.top_language
  const topLangData = topLang ? (languageTrendData.value[topLang] || []) : []
  const topLangTrend = topLangData.length >= 2
    ? (topLangData[topLangData.length - 1].count > topLangData[topLangData.length - 2].count ? 'up' : 'down')
    : 'neutral'

  // Total languages over time (sum of all language counts per month)
  const languagesByMonth: Record<string, number> = {}
  for (const trends of Object.values(languageTrendData.value)) {
    for (const point of trends) {
      languagesByMonth[point.month] = (languagesByMonth[point.month] || 0) + point.count
    }
  }
  const languagesData = Object.values(languagesByMonth).slice(-6)

  return {
    repos: reposData,
    languages: languagesData,
    conversations: [], // No real data yet - YAGNI
    topLanguageTrend: topLangTrend
  }
})

// Check if user has seen onboarding
const hasSeenOnboarding = () => {
  return localStorage.getItem('hasSeenOnboarding') === 'true'
}

// Dismiss onboarding
const dismissOnboarding = () => {
  localStorage.setItem('hasSeenOnboarding', 'true')
  showOnboarding.value = false
}

const displayStats = computed(() => ({
  totalRepos: stats.value.total_repositories,
  totalLanguages: Object.keys(stats.value.languages || {}).length,
  totalConversations: stats.value.total_conversations,
  topLanguage: stats.value.top_language || '-'
}))

const topLanguages = computed(() => {
  const entries = Object.entries(stats.value.languages || {})
  return entries
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
})

onMounted(async () => {
  try {
    const [statsRes, timelineRes, langRes] = await Promise.all([
      fetch('/api/stats'),
      fetch('/api/trends/timeline'),
      fetch('/api/trends/languages')
    ])

    const [statsData, timeline, langTrends] = await Promise.all([
      statsRes.json(),
      timelineRes.json(),
      langRes.json()
    ])

    stats.value = statsData.data || stats.value
    timelineData.value = timeline || []

    // Group language trends by language
    const langMap: Record<string, TimelinePoint[]> = {}
    for (const item of langTrends) {
      if (item.language) {
        if (!langMap[item.language]) {
          langMap[item.language] = []
        }
        langMap[item.language].push({ month: item.month, count: item.count })
      }
    }
    languageTrendData.value = langMap

    // Only show onboarding if first time visit AND no data yet
    // If user already has repositories, they've already initialized - mark as seen
    if (stats.value.total_repositories > 0) {
      // Has data - mark onboarding as seen automatically
      localStorage.setItem('hasSeenOnboarding', 'true')
      // Fetch recent repos for animation
      await fetchRecentRepos()
      // Show animation after data is loaded
      showAnimation.value = true
      startAnimation()
    } else if (!hasSeenOnboarding()) {
      // No data and first visit - show onboarding
      showOnboarding.value = true
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
})

// Fetch top 40 most recently starred repos
async function fetchRecentRepos() {
  try {
    const response = await fetch('/api/search?limit=40&sort=starred_at&sort_order=DESC')
    const data = await response.json()
    recentRepos.value = data.results || []
    pickRandomRepos()
  } catch (error) {
    console.error('Failed to fetch recent repos:', error)
  }
}

// Pick unique random indices from recent repos
function pickUniqueIndices(count: number, max: number): number[] {
  const indices = new Set<number>()
  while (indices.size < count) {
    indices.add(Math.floor(Math.random() * max))
  }
  return Array.from(indices)
}

// Calculate non-overlapping vertical positions
function calculatePositions(count: number): number[] {
  const positions: number[] = []
  const range = 60
  const start = 20

  if (count === 2) {
    positions.push(start + Math.random() * (range / 2 - 10))
    positions.push(start + range / 2 + 10 + Math.random() * (range / 2 - 10))
  } else if (count === 3) {
    const sectionSize = range / 3
    for (let i = 0; i < 3; i++) {
      positions.push(start + i * sectionSize + Math.random() * (sectionSize - 10))
    }
  }

  return positions
}

// Pick 2-3 random repos for each side
function pickRandomRepos() {
  if (recentRepos.value.length < 4) return

  const maxIndex = Math.min(40, recentRepos.value.length)
  const leftCount = Math.random() > 0.5 ? 3 : 2
  const rightCount = Math.random() > 0.5 ? 3 : 2

  const leftIndices = pickUniqueIndices(leftCount, maxIndex)
  const rightIndices = pickUniqueIndices(rightCount, maxIndex)
  const leftPositions = calculatePositions(leftCount)
  const rightPositions = calculatePositions(rightCount)

  const results: AnimatedRepo[] = []

  for (let i = 0; i < leftIndices.length; i++) {
    results.push({
      repo: recentRepos.value[leftIndices[i]],
      position: leftPositions[i],
      side: 'left'
    })
  }

  for (let i = 0; i < rightIndices.length; i++) {
    results.push({
      repo: recentRepos.value[rightIndices[i]],
      position: rightPositions[i],
      side: 'right'
    })
  }

  animatedRepos.value = results
}

// Start animation interval (every 3 seconds)
function startAnimation() {
  if (animationInterval) clearInterval(animationInterval)
  animationInterval = setInterval(() => {
    pickRandomRepos()
  }, 3000)
}

onUnmounted(() => {
  if (animationInterval) {
    clearInterval(animationInterval)
    animationInterval = null
  }
})
</script>

<style scoped>
/* Slide down transition */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.4s ease;
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* List transition for cards */
.list-enter-active,
.list-leave-active {
  transition: all 0.4s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.list-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Stagger list items */
.list-move {
  transition: transform 0.4s ease;
}

/* Tag transition */
.tag-enter-active,
.tag-leave-active {
  transition: all 0.2s ease;
}

.tag-enter-from {
  opacity: 0;
  transform: scale(0.8);
}

.tag-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

.tag-move {
  transition: transform 0.2s ease;
}

/* Repo entrance animation */
@keyframes repo-entrance {
  0% {
    opacity: 0;
    transform: translateY(10px) scale(0.9);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.repo-animate {
  animation: repo-entrance 0.6s ease-out forwards;
}

/* Floating animation (same for both sides) */
@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-6px);
  }
}

.floating-left,
.floating-right {
  animation: repo-entrance 0.6s ease-out forwards, float 3s ease-in-out 0.6s infinite;
}
</style>
