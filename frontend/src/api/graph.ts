import axios from 'axios'

export interface GraphEdge {
  source: string
  target: string
  type: string
  weight: number
  metadata?: string
}

export async function getRepoEdges(repo: string, edgeTypes?: string): Promise<GraphEdge[]> {
  const params = edgeTypes ? `?edge_types=${edgeTypes}` : ''
  const response = await axios.get(`/api/graph/nodes/${repo}/edges${params}`)
  return response.data
}

export async function rebuildGraph(): Promise<{status: string, edges_count: number}> {
  const response = await axios.post('/api/graph/rebuild')
  return response.data
}

export async function getGraphStatus(): Promise<any> {
  const response = await axios.get('/api/graph/status')
  return response.data
}
