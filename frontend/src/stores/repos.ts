import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Repository, SearchFilters } from '../types'

export const useReposStore = defineStore('repos', () => {
  const repos = ref<Repository[]>([])
  const categories = ref<Record<string, number>>({})
  const isLoading = ref(false)

  async function searchRepos(filters: SearchFilters) {
    isLoading.value = true
    try {
      const params = new URLSearchParams()
      if (filters.categories?.length) {
        params.append('categories', filters.categories.join(','))
      }
      if (filters.languages?.length) {
        params.append('languages', filters.languages.join(','))
      }
      if (filters.minStars) {
        params.append('min_stars', filters.minStars.toString())
      }
      if (filters.maxStars) {
        params.append('max_stars', filters.maxStars.toString())
      }

      const response = await fetch(`/api/search?${params}`)
      const data = await response.json()
      repos.value = data.results || []
    } finally {
      isLoading.value = false
    }
  }

  async function loadCategories() {
    const response = await fetch('/api/categories')
    const data = await response.json()
    categories.value = data.categories || {}
  }

  async function loadRepo(nameWithOwner: string) {
    const response = await fetch(`/api/repo/${nameWithOwner}`)
    if (!response.ok) return null
    return await response.json()
  }

  return { repos, categories, isLoading, searchRepos, loadCategories, loadRepo }
})
