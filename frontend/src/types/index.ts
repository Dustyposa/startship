export interface Repository {
  name_with_owner: string
  name: string
  owner: string
  description: string | null
  primary_language: string | null
  categories: string[]
  tech_stack: string[]
  stargazer_count: number
  summary: string | null
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface SearchFilters {
  query?: string
  categories?: string[]
  languages?: string[]
  minStars?: number
  maxStars?: number
}
