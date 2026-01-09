import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useCollections } from '../useCollections'
import { storage } from '@/utils/storage'
import type { Collection } from '@/types/collections'

vi.mock('@/utils/storage')

describe('useCollections', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should load collections from storage', () => {
    const mockCollections: Collection[] = [
      { id: '1', name: 'Learning', position: 0, created_at: '2024-01-01' },
      { id: '2', name: 'Work', position: 1, created_at: '2024-01-02' }
    ]
    vi.mocked(storage.get).mockReturnValue(mockCollections)

    const { collections } = useCollections()
    expect(collections.value).toEqual(mockCollections)
  })

  it('should create a new collection', () => {
    vi.mocked(storage.get).mockReturnValue([])

    const { collections, createCollection } = useCollections()
    createCollection('New Collection')

    expect(collections.value).toHaveLength(1)
    expect(collections.value[0].name).toBe('New Collection')
    expect(storage.set).toHaveBeenCalled()
  })

  it('should delete a collection', () => {
    const mockCollections: Collection[] = [
      { id: '1', name: 'Test', position: 0, created_at: '2024-01-01' }
    ]
    vi.mocked(storage.get).mockReturnValue(mockCollections)

    const { collections, deleteCollection } = useCollections()
    deleteCollection('1')

    expect(collections.value).toHaveLength(0)
    expect(storage.set).toHaveBeenCalled()
  })

  it('should add repo to collection', () => {
    vi.mocked(storage.get).mockReturnValue([])

    const { addRepoToCollection } = useCollections()
    addRepoToCollection('owner/repo', 'collection-id', 0)

    expect(storage.set).toHaveBeenCalled()
  })

  it('should remove repo from collection', () => {
    vi.mocked(storage.get).mockReturnValue([
      { repo_id: 'owner/repo', collection_id: 'coll-1', position: 0 }
    ])

    const { removeRepoFromCollection } = useCollections()
    removeRepoFromCollection('owner/repo', 'coll-1')

    expect(storage.set).toHaveBeenCalled()
  })

  it('should update a collection', () => {
    const mockCollections: Collection[] = [
      { id: '1', name: 'Old Name', position: 0, created_at: '2024-01-01' }
    ]
    vi.mocked(storage.get).mockReturnValue(mockCollections)

    const { collections, updateCollection } = useCollections()
    updateCollection('1', { name: 'New Name' })

    expect(collections.value[0].name).toBe('New Name')
    expect(storage.set).toHaveBeenCalled()
  })

  it('should get repos in collection', () => {
    vi.mocked(storage.get).mockReturnValue([])
    vi.mocked(storage.get).mockReturnValueOnce([])
    vi.mocked(storage.get).mockReturnValueOnce([
      { repo_id: 'owner/repo1', collection_id: 'coll-1', position: 0 },
      { repo_id: 'owner/repo2', collection_id: 'coll-1', position: 1 },
      { repo_id: 'owner/repo3', collection_id: 'coll-2', position: 0 }
    ])

    const { getReposInCollection } = useCollections()
    const repos = getReposInCollection('coll-1')

    expect(repos).toEqual(['owner/repo1', 'owner/repo2'])
  })

  it('should get collection for repo', () => {
    const mockCollections: Collection[] = [
      { id: 'coll-1', name: 'Test', position: 0, created_at: '2024-01-01' }
    ]
    vi.mocked(storage.get).mockReturnValueOnce(mockCollections)
    vi.mocked(storage.get).mockReturnValueOnce([
      { repo_id: 'owner/repo', collection_id: 'coll-1', position: 0 }
    ])

    const { getCollectionForRepo } = useCollections()
    const collection = getCollectionForRepo('owner/repo')

    expect(collection?.name).toBe('Test')
  })

  it('should reorder collections', () => {
    const mockCollections: Collection[] = [
      { id: '1', name: 'A', position: 0, created_at: '2024-01-01' },
      { id: '2', name: 'B', position: 1, created_at: '2024-01-02' }
    ]
    vi.mocked(storage.get).mockReturnValue(mockCollections)

    const { collections, reorderCollections } = useCollections()
    const newOrder = [...mockCollections].reverse()
    reorderCollections(newOrder)

    expect(collections.value[0].id).toBe('2')
    expect(collections.value[0].position).toBe(0)
    expect(collections.value[1].id).toBe('1')
    expect(collections.value[1].position).toBe(1)
  })
})
