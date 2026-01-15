import { ref } from 'vue'
import { collectionsApi } from '@/api/user'
import type { Collection } from '@/api/user'
import { useAsyncOperation } from './useAsyncOperation'

export function useCollections() {
  const collections = ref<Collection[]>([])
  const { isLoading, error, execute, executeSilent } = useAsyncOperation()

  async function load() {
    const result = await execute(() => collectionsApi.getAll(), 'Failed to load collections')
    if (result) collections.value = result
  }

  async function createCollection(name: string, icon?: string, color?: string): Promise<Collection | null> {
    return await execute(async () => {
      const newCollection = await collectionsApi.create({ name, icon, color })
      collections.value.push(newCollection)
      return newCollection
    }, 'Failed to create collection')
  }

  async function updateCollection(id: string, updates: Partial<Collection>) {
    await execute(async () => {
      const updated = await collectionsApi.update(id, updates)
      const index = collections.value.findIndex(c => c.id === id)
      if (index !== -1) collections.value[index] = updated
    }, 'Failed to update collection')
  }

  async function deleteCollection(id: string) {
    await execute(async () => {
      await collectionsApi.delete(id)
      collections.value = collections.value.filter(c => c.id !== id)
    }, 'Failed to delete collection')
  }

  async function addRepoToCollection(repoId: string, collectionId: string, position?: number) {
    await execute(
      () => collectionsApi.addRepo(collectionId, repoId, position),
      'Failed to add repo to collection'
    )
  }

  async function removeRepoFromCollection(repoId: string, collectionId: string) {
    await execute(
      () => collectionsApi.removeRepo(collectionId, repoId),
      'Failed to remove repo from collection'
    )
  }

  async function getReposInCollection(collectionId: string): Promise<string[]> {
    return await executeSilent(
      () => collectionsApi.getRepos(collectionId),
      []
    )
  }

  async function getCollectionForRepo(repoId: string): Promise<Collection | null> {
    return await executeSilent(
      () => collectionsApi.getCollectionForRepo(repoId),
      null
    )
  }

  async function reorderCollections(newOrder: Collection[]) {
    await execute(async () => {
      await Promise.all(
        newOrder.map((coll, index) =>
          collectionsApi.update(coll.id, { position: index })
        )
      )
      collections.value = newOrder
    }, 'Failed to reorder collections')
  }

  // Initialize
  load()

  return {
    collections,
    isLoading,
    error,
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
