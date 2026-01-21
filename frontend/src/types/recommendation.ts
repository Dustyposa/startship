/** Recommendation source types */
export type RecommendationSource = 'author' | 'ecosystem' | 'collection' | 'semantic'

/** Recommendation response */
export interface Recommendation {
  name_with_owner: string
  name: string
  owner: string
  description?: string
  final_score: number
  sources: RecommendationSource[]
  graph_score?: number
  semantic_score?: number
}

/** Source display labels */
export const SOURCE_LABELS: Record<RecommendationSource, string> = {
  author: '同一作者',
  ecosystem: '技术栈',
  collection: '收藏夹',
  semantic: '语义相似'
}
