import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Repository, SearchFilters } from '../types'

export const useReposStore = defineStore('repos', () => {
  const repos = ref<Repository[]>([])
  const categories = ref<Record<string, number>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function handleResponse(response: Response): Promise<any> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Server error: ${response.status}`)
    }
    return await response.json()
  }

  async function searchRepos(filters: SearchFilters) {
    isLoading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      params.append('q', filters.query || '')
      if (filters.categories?.length) params.append('categories', filters.categories.join(','))
      if (filters.languages?.length) params.append('languages', filters.languages.join(','))
      if (filters.minStars) params.append('min_stars', filters.minStars.toString())
      if (filters.maxStars) params.append('max_stars', filters.maxStars.toString())

      const data = await handleResponse(await fetch(`/api/search?${params}`))
      repos.value = data.results || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to search repositories'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function loadCategories() {
    error.value = null

    try {
      const data = await handleResponse(await fetch('/api/categories'))
      categories.value = data.categories || {}
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load categories'
      throw err
    }
  }

  async function loadRepo(nameWithOwner: string) {
    try {
      return await handleResponse(await fetch(`/api/repo/${nameWithOwner}`))
    } catch {
      return null
    }
  }

  return { repos, categories, isLoading, error, searchRepos, loadCategories, loadRepo }
})
