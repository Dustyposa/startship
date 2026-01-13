import { storage } from '@/utils/storage'
import { STORAGE_KEYS } from '@/types/collections'

interface ExportedUserData {
  collections?: unknown
  tags?: unknown
  notes?: unknown
  repo_collections?: unknown
  repo_tags?: unknown
  profile?: unknown
  exported_at: string
}

export function useExport() {
  function exportToJSON(data: any[], filename: string) {
    const json = JSON.stringify(data, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  function exportUserData() {
    const data: ExportedUserData = {
      [STORAGE_KEYS.COLLECTIONS]: storage.get(STORAGE_KEYS.COLLECTIONS),
      [STORAGE_KEYS.TAGS]: storage.get(STORAGE_KEYS.TAGS),
      [STORAGE_KEYS.NOTES]: storage.get(STORAGE_KEYS.NOTES),
      [STORAGE_KEYS.REPO_COLLECTIONS]: storage.get(STORAGE_KEYS.REPO_COLLECTIONS),
      [STORAGE_KEYS.REPO_TAGS]: storage.get(STORAGE_KEYS.REPO_TAGS),
      [STORAGE_KEYS.PROFILE]: storage.get(STORAGE_KEYS.PROFILE),
      exported_at: new Date().toISOString()
    }
    exportToJSON([data], `user-data-${new Date().toISOString().slice(0, 10)}`)
  }

  function importUserData(file: File): Promise<void> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result
        if (!result || typeof result !== 'string') {
          reject(new Error('Invalid file content'))
          return
        }

        try {
          const data = JSON.parse(result)
          if (Array.isArray(data) && data[0]) {
            const userData = data[0]
            // Basic validation - check if it's an object
            if (typeof userData !== 'object' || userData === null) {
              reject(new Error('Invalid data format'))
              return
            }
            // Merge with existing data
            if (userData.collections) storage.set(STORAGE_KEYS.COLLECTIONS, userData.collections)
            if (userData.tags) storage.set(STORAGE_KEYS.TAGS, userData.tags)
            if (userData.notes) storage.set(STORAGE_KEYS.NOTES, userData.notes)
            if (userData.repo_collections) storage.set(STORAGE_KEYS.REPO_COLLECTIONS, userData.repo_collections)
            if (userData.repo_tags) storage.set(STORAGE_KEYS.REPO_TAGS, userData.repo_tags)
            if (userData.profile) storage.set(STORAGE_KEYS.PROFILE, userData.profile)
            resolve()
          } else {
            reject(new Error('Invalid data format'))
          }
        } catch (err) {
          reject(err)
        }
      }
      reader.onerror = reject
      reader.readAsText(file)
    })
  }

  function exportToCSV(data: any[], filename: string) {
    if (data.length === 0) {
      throw new Error('No data to export')
    }

    // Get headers from first object
    const headers = Object.keys(data[0])

    // Convert data to CSV
    const csvRows = []
    csvRows.push(headers.join(','))

    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header]
        // Handle nested objects and arrays
        if (typeof value === 'object' && value !== null) {
          return `"${JSON.stringify(value).replace(/"/g, '""')}"`
        }
        // Escape quotes and wrap in quotes if contains comma
        const stringValue = String(value ?? '')
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`
        }
        return stringValue
      })
      csvRows.push(values.join(','))
    }

    const csvString = csvRows.join('\n')
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return {
    exportToJSON,
    exportToCSV,
    exportUserData,
    importUserData
  }
}
