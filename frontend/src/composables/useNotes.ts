import { ref } from 'vue'
import { storage } from '@/utils/storage'
import { STORAGE_KEYS, type Note } from '@/types/collections'

export function useNotes() {
  const notes = ref<Record<string, Note>>({})

  // Load from storage
  function load() {
    notes.value = storage.get<Record<string, Note>>(STORAGE_KEYS.NOTES) || {}
  }

  // Save note for repo
  function saveNote(repoId: string, note: string, rating: number) {
    const now = new Date().toISOString()
    const existing = notes.value[repoId]

    if (existing) {
      // Update existing
      notes.value[repoId] = {
        ...existing,
        note,
        rating,
        updated_at: now
      }
    } else {
      // Create new
      notes.value[repoId] = {
        repo_id: repoId,
        note,
        rating,
        created_at: now,
        updated_at: now
      }
    }
    save()
  }

  // Get note for repo
  function getNote(repoId: string): Note | null {
    return notes.value[repoId] || null
  }

  // Delete note for repo
  function deleteNote(repoId: string) {
    delete notes.value[repoId]
    save()
  }

  // Get rating for repo
  function getRating(repoId: string): number {
    return notes.value[repoId]?.rating || 0
  }

  // Save to storage
  function save() {
    storage.set(STORAGE_KEYS.NOTES, notes.value)
  }

  // Initialize
  load()

  return {
    notes,
    load,
    saveNote,
    getNote,
    deleteNote,
    getRating
  }
}
