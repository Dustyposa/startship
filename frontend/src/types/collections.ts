// Folder/Collection
export interface Collection {
  id: string
  name: string
  icon?: string
  color?: string
  position: number
  created_at: string
}

// Tag
export interface Tag {
  id: string
  name: string
  color: string
  created_at: string
}

// Repository-Collection association
export interface RepoCollection {
  repo_id: string  // name_with_owner
  collection_id: string
  position: number
}

// Repository-Tag association
export interface RepoTag {
  repo_id: string
  tag_id: string
}

// Note and Rating
export interface Note {
  repo_id: string
  note: string
  rating: number  // 1-5
  created_at: string
  updated_at: string
}

// Tech Profile
export interface TechProfile {
  tech_stack: string[]
  domains: string[]
  trends: Array<{
    period: string
    top_language: string
    new_domains: string[]
  }>
  learning_stage: 'beginner' | 'intermediate' | 'advanced'
  insights: string[]
  last_analyzed: string
}

// Storage keys
export const STORAGE_KEYS = {
  COLLECTIONS: 'collections',
  TAGS: 'tags',
  REPO_COLLECTIONS: 'repo_collections',
  REPO_TAGS: 'repo_tags',
  NOTES: 'notes',
  PROFILE: 'profile'
} as const
