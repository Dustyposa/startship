import { ref, computed } from 'vue'
import { storage } from '@/utils/storage'
import { STORAGE_KEYS, type Tag, type RepoTag } from '@/types/collections'

// Default tag colors
const DEFAULT_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'
]

export function useTags() {
  const tags = ref<Tag[]>([])
  const repoTags = ref<RepoTag[]>([])

  // Load from storage
  function load() {
    tags.value = storage.get<Tag[]>(STORAGE_KEYS.TAGS) || []
    repoTags.value = storage.get<RepoTag[]>(STORAGE_KEYS.REPO_TAGS) || []
  }

  // Create tag
  function createTag(name: string, color?: string) {
    const newTag: Tag = {
      id: `tag-${Date.now()}`,
      name,
      color: color || DEFAULT_COLORS[tags.value.length % DEFAULT_COLORS.length],
      created_at: new Date().toISOString()
    }
    tags.value.push(newTag)
    save()
    return newTag
  }

  // Update tag
  function updateTag(id: string, updates: Partial<Tag>) {
    const index = tags.value.findIndex(t => t.id === id)
    if (index !== -1) {
      tags.value[index] = { ...tags.value[index], ...updates }
      save()
    }
  }

  // Delete tag
  function deleteTag(id: string) {
    tags.value = tags.value.filter(t => t.id !== id)
    // Also remove all repo associations
    repoTags.value = repoTags.value.filter(rt => rt.tag_id !== id)
    save()
  }

  // Add tag to repo
  function addTagToRepo(repoId: string, tagId: string) {
    // Check if already exists
    const exists = repoTags.value.some(rt => rt.repo_id === repoId && rt.tag_id === tagId)
    if (exists) return

    const newAssoc: RepoTag = {
      repo_id: repoId,
      tag_id: tagId
    }
    repoTags.value.push(newAssoc)
    save()
  }

  // Remove tag from repo
  function removeTagFromRepo(repoId: string, tagId: string) {
    repoTags.value = repoTags.value.filter(
      rt => !(rt.repo_id === repoId && rt.tag_id === tagId)
    )
    save()
  }

  // Get tags for repo
  function getTagsForRepo(repoId: string): Tag[] {
    const tagIds = repoTags.value
      .filter(rt => rt.repo_id === repoId)
      .map(rt => rt.tag_id)

    return tags.value.filter(t => tagIds.includes(t.id))
  }

  // Batch add tags to repo
  function addTagsToRepo(repoId: string, tagIds: string[]) {
    tagIds.forEach(tagId => addTagToRepo(repoId, tagId))
  }

  // Get or create tag by name
  function getOrCreateTag(name: string, color?: string): Tag {
    let tag = tags.value.find(t => t.name === name)
    if (!tag) {
      tag = createTag(name, color)
    }
    return tag
  }

  // Save to storage
  function save() {
    storage.set(STORAGE_KEYS.TAGS, tags.value)
    storage.set(STORAGE_KEYS.REPO_TAGS, repoTags.value)
  }

  // Initialize
  load()

  return {
    tags,
    repoTags,
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
