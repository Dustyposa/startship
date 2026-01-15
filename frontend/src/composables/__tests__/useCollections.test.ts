import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useCollections } from '../useCollections'
import { collectionsApi } from '@/api/user'
import type { Collection } from '@/api/user'

vi.mock('@/api/user')

describe('useCollections', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(collectionsApi.getAll).mockResolvedValue([])
  })

  it('should load collections from API', async () => {
    const mockCollections: Collection[] = [
      { id: '1', name: 'Learning', position: 0, created_at: '2024-01-01', updated_at: '2024-01-01' },
      { id: '2', name: 'Work', position: 1, created_at: '2024-01-02', updated_at: '2024-01-02' }
    ]
    vi.mocked(collectionsApi.getAll).mockResolvedValue(mockCollections)

    const { collections } = useCollections()
    // Wait for initial load
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(collections.value).toEqual(mockCollections)
  })

  it('should create a new collection', async () => {
    const newCollection: Collection = {
      id: '1',
      name: 'New Collection',
      position: 0,
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    }
    vi.mocked(collectionsApi.create).mockResolvedValue(newCollection)
    vi.mocked(collectionsApi.getAll).mockResolvedValue([newCollection])

    const { collections, createCollection } = useCollections()
    // Wait for initial load first
    await new Promise(resolve => setTimeout(resolve, 0))
    // Clear and mock the updated response
    collections.value = []
    vi.mocked(collectionsApi.getAll).mockResolvedValue([newCollection])

    const result = await createCollection('New Collection')

    expect(result).toEqual(newCollection)
    expect(collections.value).toHaveLength(1)
    expect(collections.value[0].name).toBe('New Collection')
    expect(collectionsApi.create).toHaveBeenCalledWith({ name: 'New Collection', icon: undefined, color: undefined })
  })

  it('should delete a collection', async () => {
    const mockCollections: Collection[] = [
      { id: '1', name: 'Test', position: 0, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ]
    vi.mocked(collectionsApi.getAll).mockResolvedValue(mockCollections)
    vi.mocked(collectionsApi.delete).mockResolvedValue(undefined)

    const { collections, deleteCollection } = useCollections()
    await new Promise(resolve => setTimeout(resolve, 0))
    await deleteCollection('1')

    expect(collections.value).toHaveLength(0)
    expect(collectionsApi.delete).toHaveBeenCalledWith('1')
  })

  it('should add repo to collection', async () => {
    vi.mocked(collectionsApi.addRepo).mockResolvedValue(undefined)

    const { addRepoToCollection } = useCollections()
    await addRepoToCollection('owner/repo', 'collection-id', 0)

    expect(collectionsApi.addRepo).toHaveBeenCalledWith('collection-id', 'owner/repo', 0)
  })

  it('should remove repo from collection', async () => {
    vi.mocked(collectionsApi.removeRepo).mockResolvedValue(undefined)

    const { removeRepoFromCollection } = useCollections()
    await removeRepoFromCollection('owner/repo', 'coll-1')

    expect(collectionsApi.removeRepo).toHaveBeenCalledWith('coll-1', 'owner/repo')
  })

  it('should update a collection', async () => {
    const updatedCollection: Collection = {
      id: '1',
      name: 'New Name',
      position: 0,
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    }
    vi.mocked(collectionsApi.update).mockResolvedValue(updatedCollection)
    vi.mocked(collectionsApi.getAll).mockResolvedValue([
      { id: '1', name: 'Old Name', position: 0, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ])

    const { collections, updateCollection } = useCollections()
    await new Promise(resolve => setTimeout(resolve, 0))
    await updateCollection('1', { name: 'New Name' })

    expect(collections.value[0].name).toBe('New Name')
    expect(collectionsApi.update).toHaveBeenCalledWith('1', { name: 'New Name' })
  })

  it('should get repos in collection', async () => {
    const repos = ['owner/repo1', 'owner/repo2']
    vi.mocked(collectionsApi.getRepos).mockResolvedValue(repos)

    const { getReposInCollection } = useCollections()
    const result = await getReposInCollection('coll-1')

    expect(result).toEqual(repos)
    expect(collectionsApi.getRepos).toHaveBeenCalledWith('coll-1')
  })

  it('should get collection for repo', async () => {
    const collection: Collection = {
      id: 'coll-1',
      name: 'Test',
      position: 0,
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    }
    vi.mocked(collectionsApi.getCollectionForRepo).mockResolvedValue(collection)

    const { getCollectionForRepo } = useCollections()
    const result = await getCollectionForRepo('owner/repo')

    expect(result?.name).toBe('Test')
    expect(collectionsApi.getCollectionForRepo).toHaveBeenCalledWith('owner/repo')
  })

  it('should reorder collections', async () => {
    const mockCollections: Collection[] = [
      { id: '1', name: 'A', position: 0, created_at: '2024-01-01', updated_at: '2024-01-01' },
      { id: '2', name: 'B', position: 1, created_at: '2024-01-02', updated_at: '2024-01-02' }
    ]
    vi.mocked(collectionsApi.getAll).mockResolvedValue(mockCollections)
    vi.mocked(collectionsApi.update).mockResolvedValue({} as Collection)

    const { collections, reorderCollections } = useCollections()
    await new Promise(resolve => setTimeout(resolve, 0))
    const newOrder = [...mockCollections].reverse()
    await reorderCollections(newOrder)

    expect(collections.value[0].id).toBe('2')
    expect(collectionsApi.update).toHaveBeenCalledTimes(2)
  })
})
