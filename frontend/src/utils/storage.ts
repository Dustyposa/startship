const PREFIX = 'gh_'

export const storage = {
  get<T = unknown>(key: string): T | null {
    try {
      const item = localStorage.getItem(PREFIX + key)
      if (item === null) return null
      return JSON.parse(item) as T
    } catch (error) {
      console.error(`Error reading from localStorage: ${key}`, error)
      return null
    }
  },

  set<T = unknown>(key: string, value: T): void {
    try {
      localStorage.setItem(PREFIX + key, JSON.stringify(value))
    } catch (error) {
      console.error(`Error writing to localStorage: ${key}`, error)
    }
  },

  remove(key: string): void {
    try {
      localStorage.removeItem(PREFIX + key)
    } catch (error) {
      console.error(`Error removing from localStorage: ${key}`, error)
    }
  },

  clear(): void {
    try {
      const keys = Object.keys(localStorage)
      keys.forEach(key => {
        if (key.startsWith(PREFIX)) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error('Error clearing localStorage', error)
    }
  }
}
