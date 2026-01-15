import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useTags } from '../useTags'
import { tagsApi } from '@/api/user'
import type { Tag } from '@/api/user'

vi.mock('@/api/user')

describe('useTags', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(tagsApi.getAll).mockResolvedValue([])
  })

  it('should load tags from API', async () => {
    const mockTags: Tag[] = [
      { id: '1', name: 'Frontend', color: '#3b82f6', created_at: '2024-01-01', updated_at: '2024-01-01' }
    ]
    vi.mocked(tagsApi.getAll).mockResolvedValue(mockTags)

    const { tags } = useTags()
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(tags.value).toEqual(mockTags)
  })

  it('should create a new tag', async () => {
    const newTag: Tag = {
      id: '1',
      name: 'Python',
      color: '#3776ab',
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    }
    vi.mocked(tagsApi.create).mockResolvedValue(newTag)

    const { tags, createTag } = useTags()
    await new Promise(resolve => setTimeout(resolve, 0))
    tags.value = []

    const result = await createTag('Python', '#3776ab')

    expect(result).toEqual(newTag)
    expect(tags.value).toHaveLength(1)
    expect(tags.value[0].name).toBe('Python')
    expect(tagsApi.create).toHaveBeenCalledWith({ name: 'Python', color: '#3776ab' })
  })

  it('should use default color when creating tag without color', async () => {
    const newTag: Tag = {
      id: '1',
      name: 'Test',
      color: '#3b82f6',
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    }
    vi.mocked(tagsApi.create).mockResolvedValue(newTag)

    const { tags, createTag } = useTags()
    await new Promise(resolve => setTimeout(resolve, 0))
    tags.value = []

    await createTag('Test')

    expect(tags.value).toHaveLength(1)
    expect(tags.value[0].color).toBe('#3b82f6')
  })

  it('should delete a tag', async () => {
    const mockTags: Tag[] = [
      { id: '1', name: 'Test', color: '#000', created_at: '2024-01-01', updated_at: '2024-01-01' }
    ]
    vi.mocked(tagsApi.getAll).mockResolvedValue(mockTags)
    vi.mocked(tagsApi.delete).mockResolvedValue(undefined)

    const { tags, deleteTag } = useTags()
    await new Promise(resolve => setTimeout(resolve, 0))
    await deleteTag('1')

    expect(tags.value).toHaveLength(0)
    expect(tagsApi.delete).toHaveBeenCalledWith('1')
  })

  it('should add tag to repo', async () => {
    vi.mocked(tagsApi.addToRepo).mockResolvedValue(undefined)

    const { addTagToRepo } = useTags()
    await addTagToRepo('owner/repo', 'tag-id')

    expect(tagsApi.addToRepo).toHaveBeenCalledWith('tag-id', 'owner/repo')
  })

  it('should get tags for repo', async () => {
    const mockTags: Tag[] = [
      { id: 't1', name: 'Test', color: '#000', created_at: '2024-01-01', updated_at: '2024-01-01' }
    ]
    vi.mocked(tagsApi.getForRepo).mockResolvedValue(mockTags)

    const { getTagsForRepo } = useTags()
    const tags = await getTagsForRepo('owner/repo')

    expect(tags).toHaveLength(1)
    expect(tags[0].name).toBe('Test')
    expect(tagsApi.getForRepo).toHaveBeenCalledWith('owner/repo')
  })

  it('should update a tag', async () => {
    const updatedTag: Tag = {
      id: '1',
      name: 'New Name',
      color: '#000',
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    }
    vi.mocked(tagsApi.update).mockResolvedValue(updatedTag)
    vi.mocked(tagsApi.getAll).mockResolvedValue([
      { id: '1', name: 'Old Name', color: '#000', created_at: '2024-01-01', updated_at: '2024-01-01' }
    ])

    const { tags, updateTag } = useTags()
    await new Promise(resolve => setTimeout(resolve, 0))
    await updateTag('1', { name: 'New Name' })

    expect(tags.value[0].name).toBe('New Name')
    expect(tagsApi.update).toHaveBeenCalledWith('1', { name: 'New Name' })
  })

  it('should remove tag from repo', async () => {
    vi.mocked(tagsApi.removeFromRepo).mockResolvedValue(undefined)

    const { removeTagFromRepo } = useTags()
    await removeTagFromRepo('owner/repo', 'tag-1')

    expect(tagsApi.removeFromRepo).toHaveBeenCalledWith('tag-1', 'owner/repo')
  })

  it('should batch add tags to repo', async () => {
    vi.mocked(tagsApi.addToRepo).mockResolvedValue(undefined)

    const { addTagsToRepo } = useTags()
    await addTagsToRepo('owner/repo', ['tag-1', 'tag-2'])

    expect(tagsApi.addToRepo).toHaveBeenCalledTimes(2)
    expect(tagsApi.addToRepo).toHaveBeenCalledWith('tag-1', 'owner/repo')
    expect(tagsApi.addToRepo).toHaveBeenCalledWith('tag-2', 'owner/repo')
  })

  it('should get or create tag - existing tag', async () => {
    const mockTags: Tag[] = [
      { id: '1', name: 'Python', color: '#3776ab', created_at: '2024-01-01', updated_at: '2024-01-01' }
    ]
    vi.mocked(tagsApi.getAll).mockResolvedValue(mockTags)

    const { getOrCreateTag } = useTags()
    await new Promise(resolve => setTimeout(resolve, 0))
    const tag = await getOrCreateTag('Python')

    expect(tag.name).toBe('Python')
    expect(tag).toEqual(mockTags[0])
  })

  it('should create new tag if not exists', async () => {
    const newTag: Tag = {
      id: '1',
      name: 'NewTag',
      color: '#ff0000',
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    }
    vi.mocked(tagsApi.getAll).mockResolvedValue([])
    vi.mocked(tagsApi.create).mockResolvedValue(newTag)

    const { tags, getOrCreateTag } = useTags()
    await new Promise(resolve => setTimeout(resolve, 0))
    const tag = await getOrCreateTag('NewTag', '#ff0000')

    expect(tags.value).toHaveLength(1)
    expect(tag.name).toBe('NewTag')
    expect(tagsApi.create).toHaveBeenCalledWith({ name: 'NewTag', color: '#ff0000' })
  })
})
