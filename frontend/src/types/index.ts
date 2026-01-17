export interface Repository {
  name_with_owner: string
  name: string
  owner: string
  description: string | null
  primary_language: string | null
  languages?: LanguageInfo[]  // All languages with percentages
  categories: string[]  // Deprecated - kept for backward compatibility
  stargazer_count: number
  summary: string | null
  starred_at?: string | null
  url?: string
  homepage_url?: string | null
  fork_count?: number
  topics?: string[]
  // New GitHub metadata fields
  pushed_at?: string | null
  created_at?: string | null
  archived?: boolean
  visibility?: string
  owner_type?: string | null
  organization?: string | null
}

export interface LanguageInfo {
  name: string
  size: number
  percent: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface SearchFilters {
  query?: string
  categories?: string[]  // Deprecated - kept for backward compatibility
  languages?: string[]
  minStars?: number
  maxStars?: number
  // New filter dimensions
  isActive?: boolean  // Active: pushed within 7 days
  isNew?: boolean  // New: created within 6 months
  ownerType?: string  // Owner type: "Organization" or "User"
  excludeArchived?: boolean  // Exclude archived repos
}
