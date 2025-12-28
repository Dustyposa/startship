import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const username = ref<string | null>(null)
  const isAuthenticated = ref(false)

  function setUsername(name: string) {
    username.value = name
    localStorage.setItem('github_username', name)
  }

  function loadFromStorage() {
    const stored = localStorage.getItem('github_username')
    if (stored) {
      username.value = stored
      isAuthenticated.value = true
    }
  }

  function logout() {
    username.value = null
    isAuthenticated.value = false
    localStorage.removeItem('github_username')
  }

  return { username, isAuthenticated, setUsername, loadFromStorage, logout }
})
