<template>
  <div v-if="repo" class="max-w-4xl mx-auto">
    <div class="bg-white rounded-lg shadow-sm p-6">
      <div class="flex justify-between items-start mb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ repo.name_with_owner }}</h1>
          <p v-if="repo.description" class="text-gray-600 mt-2">{{ repo.description }}</p>
        </div>
        <a
          :href="`https://github.com/${repo.name_with_owner}`"
          target="_blank"
          class="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
        >
          查看 GitHub
        </a>
      </div>

      <div class="flex gap-4 mb-6">
        <span v-if="repo.primary_language" class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
          {{ repo.primary_language }}
        </span>
        <span class="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">
          ⭐ {{ repo.stargazer_count }}
        </span>
      </div>

      <div v-if="repo.summary" class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 mb-2">简介</h2>
        <p class="text-gray-700">{{ repo.summary }}</p>
      </div>

      <div v-if="repo.categories?.length" class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 mb-2">分类</h2>
        <div class="flex gap-2 flex-wrap">
          <span
            v-for="cat in repo.categories"
            :key="cat"
            class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
          >
            {{ cat }}
          </span>
        </div>
      </div>

      <div v-if="repo.tech_stack?.length" class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 mb-2">技术栈</h2>
        <div class="flex gap-2 flex-wrap">
          <span
            v-for="tech in repo.tech_stack"
            :key="tech"
            class="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm"
          >
            {{ tech }}
          </span>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="isLoading" class="text-center py-12">
    <div class="text-gray-600">加载中...</div>
  </div>

  <div v-else class="text-center py-12">
    <div class="text-gray-600">仓库未找到</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useReposStore } from '../stores/repos'
import type { Repository } from '../types'

const route = useRoute()
const reposStore = useReposStore()

const repo = ref<Repository | null>(null)
const isLoading = ref(true)

onMounted(async () => {
  const { owner, name } = route.params
  const nameWithOwner = `${owner}/${name}`

  const data = await reposStore.loadRepo(nameWithOwner)
  repo.value = data
  isLoading.value = false
})
</script>
