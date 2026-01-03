import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { NetworkResponse } from '../types/network'

export const useApiStore = defineStore('api', () => {
  const error = ref<string | null>(null)

  async function fetchNetworkGraph(): Promise<NetworkResponse> {
    error.value = null
    try {
      const response = await axios.get<NetworkResponse>('/api/network/graph')
      return response.data
    } catch (err: unknown) {
      let message = 'Failed to load network data'
      if (axios.isAxiosError(err)) {
        message = err.response?.data?.detail || err.message || message
      } else if (err instanceof Error) {
        message = err.message
      }
      console.error('Error fetching network graph:', err)
      error.value = message
      throw err
    }
  }

  return { error, fetchNetworkGraph }
})
