import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Repository, SearchFilters } from '../types'

export const useReposStore = defineStore('repos', () => {
  const repos = ref<Repository[]>([])
  const categories = ref<Record<string, number>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function searchRepos(filters: SearchFilters) {
    isLoading.value = true
    error.value = null
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

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `Server error: ${response.status}`)
      }

      const data = await response.json()
      repos.value = data.results || []
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to search repositories'
      error.value = message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function loadCategories() {
    error.value = null
    try {
      const response = await fetch('/api/categories')

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `Server error: ${response.status}`)
      }

      const data = await response.json()
      categories.value = data.categories || {}
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load categories'
      error.value = message
      throw err
    }
  }

  async function loadRepo(nameWithOwner: string) {
    const response = await fetch(`/api/repo/${nameWithOwner}`)
    if (!response.ok) return null
    return await response.json()
  }

  return { repos, categories, isLoading, error, searchRepos, loadCategories, loadRepo }
})
