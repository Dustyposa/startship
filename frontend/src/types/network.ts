export interface NetworkNode {
  id: string
  name: string
  size: number
  color: string
  starCount: number
  categories: string[]
  language: string | null
}

export interface NetworkEdge {
  source: string
  target: string
  strength: number
}

export interface NetworkResponse {
  nodes: NetworkNode[]
  edges: NetworkEdge[]
}
