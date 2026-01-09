import { ref } from 'vue'
import { storage } from '@/utils/storage'
import { STORAGE_KEYS, type Collection, type RepoCollection } from '@/types/collections'

export function useCollections() {
  const collections = ref<Collection[]>([])
  const repoCollections = ref<RepoCollection[]>([])

  // Load from storage
  function load() {
    collections.value = storage.get<Collection[]>(STORAGE_KEYS.COLLECTIONS) || []
    repoCollections.value = storage.get<RepoCollection[]>(STORAGE_KEYS.REPO_COLLECTIONS) || []
    // Sort by position
    collections.value.sort((a, b) => a.position - b.position)
  }

  // Create collection
  function createCollection(name: string, icon?: string, color?: string) {
    const newCollection: Collection = {
      id: `coll-${Date.now()}`,
      name,
      icon,
      color,
      position: collections.value.length,
      created_at: new Date().toISOString()
    }
    collections.value.push(newCollection)
    save()
    return newCollection
  }

  // Update collection
  function updateCollection(id: string, updates: Partial<Collection>) {
    const index = collections.value.findIndex(c => c.id === id)
    if (index !== -1) {
      collections.value[index] = { ...collections.value[index], ...updates }
      save()
    }
  }

  // Delete collection
  function deleteCollection(id: string) {
    collections.value = collections.value.filter(c => c.id !== id)
    // Also remove all repo associations
    repoCollections.value = repoCollections.value.filter(rc => rc.collection_id !== id)
    save()
  }

  // Add repo to collection
  function addRepoToCollection(repoId: string, collectionId: string, position?: number) {
    // Remove from existing position first
    removeRepoFromCollection(repoId)

    const newAssoc: RepoCollection = {
      repo_id: repoId,
      collection_id: collectionId,
      position: position ?? repoCollections.value.length
    }
    repoCollections.value.push(newAssoc)
    save()
  }

  // Remove repo from collection
  function removeRepoFromCollection(repoId: string, collectionId?: string) {
    if (collectionId) {
      repoCollections.value = repoCollections.value.filter(
        rc => !(rc.repo_id === repoId && rc.collection_id === collectionId)
      )
    } else {
      repoCollections.value = repoCollections.value.filter(rc => rc.repo_id !== repoId)
    }
    save()
  }

  // Get repos in collection
  function getReposInCollection(collectionId: string): string[] {
    return repoCollections.value
      .filter(rc => rc.collection_id === collectionId)
      .sort((a, b) => a.position - b.position)
      .map(rc => rc.repo_id)
  }

  // Get collection for repo
  function getCollectionForRepo(repoId: string): Collection | null {
    const assoc = repoCollections.value.find(rc => rc.repo_id === repoId)
    if (!assoc) return null
    return collections.value.find(c => c.id === assoc.collection_id) || null
  }

  // Reorder collections
  function reorderCollections(newOrder: Collection[]) {
    newOrder.forEach((coll, index) => {
      coll.position = index
    })
    collections.value = newOrder
    save()
  }

  // Save to storage
  function save() {
    storage.set(STORAGE_KEYS.COLLECTIONS, collections.value)
    storage.set(STORAGE_KEYS.REPO_COLLECTIONS, repoCollections.value)
  }

  // Initialize
  load()

  return {
    collections,
    repoCollections,
    load,
    createCollection,
    updateCollection,
    deleteCollection,
    addRepoToCollection,
    removeRepoFromCollection,
    getReposInCollection,
    getCollectionForRepo,
    reorderCollections
  }
}
