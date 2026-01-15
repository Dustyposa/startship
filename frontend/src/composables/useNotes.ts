import { ref } from 'vue'
import { notesApi } from '@/api/user'
import type { Note } from '@/api/user'
import { useAsyncOperation } from './useAsyncOperation'

export function useNotes() {
  const notes = ref<Record<string, Note>>({})
  const { isLoading, error, execute, executeSilent } = useAsyncOperation()

  async function load() {
    await execute(async () => {
      const allNotes = await notesApi.getAll()
      notes.value = {}
      allNotes.forEach(note => {
        notes.value[note.repo_id] = note
      })
    }, 'Failed to load notes')
  }

  async function saveNote(repoId: string, note: string, rating: number) {
    await execute(async () => {
      const savedNote = await notesApi.upsert(repoId, { note, rating })
      notes.value[repoId] = savedNote
    }, 'Failed to save note')
  }

  async function getNote(repoId: string): Promise<Note | null> {
    // Check cache first
    if (notes.value[repoId]) {
      return notes.value[repoId]
    }
    // Otherwise fetch from API
    return await executeSilent(async () => {
      const note = await notesApi.get(repoId)
      if (note) notes.value[repoId] = note
      return note
    }, null)
  }

  async function deleteNote(repoId: string) {
    await execute(async () => {
      await notesApi.delete(repoId)
      delete notes.value[repoId]
    }, 'Failed to delete note')
  }

  async function getRating(repoId: string): Promise<number> {
    const note = await getNote(repoId)
    return note?.rating || 0
  }

  // Initialize
  load()

  return {
    notes,
    isLoading,
    error,
    load,
    saveNote,
    getNote,
    deleteNote,
    getRating
  }
}
