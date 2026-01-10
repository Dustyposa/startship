import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useTags } from '../useTags'
import { storage } from '@/utils/storage'
import type { Tag } from '@/types/collections'

vi.mock('@/utils/storage')

describe('useTags', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should load tags from storage', () => {
    const mockTags: Tag[] = [
      { id: '1', name: 'Frontend', color: '#3b82f6', created_at: '2024-01-01' }
    ]
    vi.mocked(storage.get).mockReturnValue(mockTags)

    const { tags } = useTags()
    expect(tags.value).toEqual(mockTags)
  })

  it('should create a new tag', () => {
    vi.mocked(storage.get).mockReturnValue([])

    const { tags, createTag } = useTags()
    createTag('Python', '#3776ab')

    expect(tags.value).toHaveLength(1)
    expect(tags.value[0].name).toBe('Python')
  })

  it('should delete a tag', () => {
    const mockTags: Tag[] = [
      { id: '1', name: 'Test', color: '#000', created_at: '2024-01-01' }
    ]
    vi.mocked(storage.get).mockReturnValue(mockTags)

    const { tags, deleteTag } = useTags()
    deleteTag('1')

    expect(tags.value).toHaveLength(0)
  })

  it('should add tag to repo', () => {
    vi.mocked(storage.get).mockReturnValue([])

    const { addTagToRepo } = useTags()
    addTagToRepo('owner/repo', 'tag-id')

    expect(storage.set).toHaveBeenCalled()
  })

  it('should get tags for repo', () => {
    vi.mocked(storage.get)
      .mockReturnValueOnce([{ id: 't1', name: 'Test', color: '#000', created_at: '2024-01-01' }])
      .mockReturnValueOnce([{ repo_id: 'owner/repo', tag_id: 't1' }])

    const { getTagsForRepo } = useTags()
    const tags = getTagsForRepo('owner/repo')

    expect(tags).toHaveLength(1)
    expect(tags[0].name).toBe('Test')
  })

  it('should update a tag', () => {
    const mockTags: Tag[] = [
      { id: '1', name: 'Old Name', color: '#000', created_at: '2024-01-01' }
    ]
    vi.mocked(storage.get).mockReturnValue(mockTags)

    const { tags, updateTag } = useTags()
    updateTag('1', { name: 'New Name' })

    expect(tags.value[0].name).toBe('New Name')
    expect(storage.set).toHaveBeenCalled()
  })

  it('should remove tag from repo', () => {
    vi.mocked(storage.get).mockReturnValue([])
    vi.mocked(storage.get).mockReturnValueOnce([
      { repo_id: 'owner/repo', tag_id: 'tag-1', position: 0 }
    ])

    const { removeTagFromRepo } = useTags()
    removeTagFromRepo('owner/repo', 'tag-1')

    expect(storage.set).toHaveBeenCalled()
  })

  it('should batch add tags to repo', () => {
    vi.mocked(storage.get).mockReturnValue([])

    const { addTagsToRepo } = useTags()
    addTagsToRepo('owner/repo', ['tag-1', 'tag-2'])

    expect(storage.set).toHaveBeenCalled()
  })

  it('should get or create tag', () => {
    const mockTags: Tag[] = [
      { id: '1', name: 'Python', color: '#3776ab', created_at: '2024-01-01' }
    ]
    vi.mocked(storage.get).mockReturnValue(mockTags)

    const { getOrCreateTag } = useTags()
    const tag = getOrCreateTag('Python')

    expect(tag.name).toBe('Python')
    expect(tag).toEqual(mockTags[0])
  })

  it('should create new tag if not exists', () => {
    vi.mocked(storage.get).mockReturnValue([])

    const { tags, getOrCreateTag } = useTags()
    const tag = getOrCreateTag('NewTag', '#ff0000')

    expect(tags.value).toHaveLength(1)
    expect(tag.name).toBe('NewTag')
  })
})
