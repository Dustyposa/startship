import axios from 'axios'

// Base API URL
const API_BASE = '/api/sync'

// ==================== Types ====================

export interface SyncStatus {
  last_sync_at: string | null
  sync_type: string | null
  total_repos: number
  pending_updates: number
  deleted_repos: number
}

export interface ManualSyncRequest {
  reanalyze?: boolean
  full_sync?: boolean
}

export interface ManualSyncResponse {
  success: boolean
  message: string
  sync_type: string
}

export interface SyncHistory {
  id: number
  sync_type: string
  started_at: string
  completed_at: string | null
  stats_added: number
  stats_updated: number
  stats_deleted: number
  stats_failed: number
  error_message: string | null
}

export interface DeletedRepo {
  name_with_owner: string
  description: string | null
  primary_language: string | null
  stargazer_count: number
  starred_at: string
  last_synced_at: string | null
}

export interface SyncHistoryResponse {
  results: SyncHistory[]
}

export interface DeletedReposResponse {
  results: DeletedRepo[]
  total: number
}

// ==================== Sync API ====================

export const syncApi = {
  async getStatus(): Promise<SyncStatus> {
    const response = await axios.get<SyncStatus>(`${API_BASE}/status`)
    return response.data
  },

  async manualSync(request: ManualSyncRequest = {}): Promise<ManualSyncResponse> {
    const response = await axios.post<ManualSyncResponse>(`${API_BASE}/manual`, request)
    return response.data
  },

  async getHistory(limit: number = 20): Promise<SyncHistoryResponse> {
    const response = await axios.get<SyncHistoryResponse>(`${API_BASE}/history`, {
      params: { limit }
    })
    return response.data
  },

  async getDeletedRepos(limit: number = 50): Promise<DeletedReposResponse> {
    const response = await axios.get<DeletedReposResponse>(`${API_BASE}/repos/deleted`, {
      params: { limit }
    })
    return response.data
  },

  async restoreRepo(nameWithOwner: string): Promise<{ success: boolean; message: string }> {
    const response = await axios.post<{ success: boolean; message: string }>(
      `${API_BASE}/repo/${encodeURIComponent(nameWithOwner)}/restore`
    )
    return response.data
  },

  async reanalyzeRepo(nameWithOwner: string): Promise<{ success: boolean; message: string; status: string }> {
    const response = await axios.post<{ success: boolean; message: string; status: string }>(
      `${API_BASE}/repo/${encodeURIComponent(nameWithOwner)}/reanalyze`
    )
    return response.data
  }
}
