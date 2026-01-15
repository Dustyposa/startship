import { ref } from 'vue'
import { tagsApi } from '@/api/user'
import type { Tag } from '@/api/user'
import { useAsyncOperation } from './useAsyncOperation'

const DEFAULT_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'
]

export function useTags() {
  const tags = ref<Tag[]>([])
  const { isLoading, error, execute, executeSilent } = useAsyncOperation()

  async function load() {
    const result = await execute(() => tagsApi.getAll(), 'Failed to load tags')
    if (result) tags.value = result
  }

  async function createTag(name: string, color?: string): Promise<Tag | null> {
    return await execute(async () => {
      const newTag = await tagsApi.create({
        name,
        color: color || DEFAULT_COLORS[tags.value.length % DEFAULT_COLORS.length]
      })
      tags.value.push(newTag)
      return newTag
    }, 'Failed to create tag')
  }

  async function updateTag(id: string, updates: Partial<Tag>) {
    await execute(async () => {
      const updated = await tagsApi.update(id, updates)
      const index = tags.value.findIndex(t => t.id === id)
      if (index !== -1) tags.value[index] = updated
    }, 'Failed to update tag')
  }

  async function deleteTag(id: string) {
    await execute(async () => {
      await tagsApi.delete(id)
      tags.value = tags.value.filter(t => t.id !== id)
    }, 'Failed to delete tag')
  }

  async function addTagToRepo(repoId: string, tagId: string) {
    await execute(
      () => tagsApi.addToRepo(tagId, repoId),
      'Failed to add tag to repo'
    )
  }

  async function removeTagFromRepo(repoId: string, tagId: string) {
    await execute(
      () => tagsApi.removeFromRepo(tagId, repoId),
      'Failed to remove tag from repo'
    )
  }

  async function getTagsForRepo(repoId: string): Promise<Tag[]> {
    return await executeSilent(
      () => tagsApi.getForRepo(repoId),
      []
    )
  }

  async function addTagsToRepo(repoId: string, tagIds: string[]) {
    await execute(async () => {
      await Promise.all(tagIds.map(tagId => tagsApi.addToRepo(tagId, repoId)))
    }, 'Failed to add tags to repo')
  }

  async function getOrCreateTag(name: string, color?: string): Promise<Tag> {
    let tag = tags.value.find(t => t.name === name)
    if (!tag) {
      tag = await createTag(name, color)
      if (!tag) {
        throw new Error('Failed to create tag')
      }
    }
    return tag
  }

  // Initialize
  load()

  return {
    tags,
    isLoading,
    error,
    load,
    createTag,
    updateTag,
    deleteTag,
    addTagToRepo,
    removeTagFromRepo,
    getTagsForRepo,
    addTagsToRepo,
    getOrCreateTag
  }
}
