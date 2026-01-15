import axios from 'axios'

// Base API URL
const API_BASE = '/api/user'

// ==================== Types ====================

export interface Collection {
  id: string
  name: string
  icon?: string
  color?: string
  position: number
  created_at: string
  updated_at: string
}

export interface Tag {
  id: string
  name: string
  color: string
  created_at: string
  updated_at: string
}

export interface Note {
  repo_id: string
  note?: string
  rating?: number
  created_at: string
  updated_at: string
}

export interface CollectionCreate {
  name: string
  icon?: string
  color?: string
}

export interface CollectionUpdate {
  name?: string
  icon?: string
  color?: string
  position?: number
}

export interface TagCreate {
  name: string
  color?: string
}

export interface TagUpdate {
  name?: string
  color?: string
}

export interface NoteUpsert {
  note?: string
  rating?: number
}

// ==================== Collections API ====================

export const collectionsApi = {
  async getAll(): Promise<Collection[]> {
    const response = await axios.get<Collection[]>(`${API_BASE}/collections`)
    return response.data
  },

  async get(id: string): Promise<Collection> {
    const response = await axios.get<Collection>(`${API_BASE}/collections/${id}`)
    return response.data
  },

  async create(data: CollectionCreate): Promise<Collection> {
    const response = await axios.post<Collection>(`${API_BASE}/collections`, data)
    return response.data
  },

  async update(id: string, data: CollectionUpdate): Promise<Collection> {
    const response = await axios.put<Collection>(`${API_BASE}/collections/${id}`, data)
    return response.data
  },

  async delete(id: string): Promise<void> {
    await axios.delete(`${API_BASE}/collections/${id}`)
  },

  async addRepo(collectionId: string, repoId: string, position?: number): Promise<void> {
    await axios.post(`${API_BASE}/collections/${collectionId}/repos`, {
      repo_id: repoId,
      position
    })
  },

  async removeRepo(collectionId: string, repoId: string): Promise<void> {
    await axios.delete(`${API_BASE}/collections/${collectionId}/repos/${repoId}`)
  },

  async getRepos(collectionId: string): Promise<string[]> {
    const response = await axios.get<string[]>(`${API_BASE}/collections/${collectionId}/repos`)
    return response.data
  },

  async getCollectionForRepo(repoId: string): Promise<Collection | null> {
    try {
      const response = await axios.get<Collection>(`${API_BASE}/repos/${repoId}/collection`)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw error
    }
  }
}

// ==================== Tags API ====================

export const tagsApi = {
  async getAll(): Promise<Tag[]> {
    const response = await axios.get<Tag[]>(`${API_BASE}/tags`)
    return response.data
  },

  async get(id: string): Promise<Tag> {
    const response = await axios.get<Tag>(`${API_BASE}/tags/${id}`)
    return response.data
  },

  async create(data: TagCreate): Promise<Tag> {
    const response = await axios.post<Tag>(`${API_BASE}/tags`, data)
    return response.data
  },

  async update(id: string, data: TagUpdate): Promise<Tag> {
    const response = await axios.put<Tag>(`${API_BASE}/tags/${id}`, data)
    return response.data
  },

  async delete(id: string): Promise<void> {
    await axios.delete(`${API_BASE}/tags/${id}`)
  },

  async addToRepo(tagId: string, repoId: string): Promise<void> {
    await axios.post(`${API_BASE}/tags/${tagId}/repos`, { repo_id: repoId })
  },

  async removeFromRepo(tagId: string, repoId: string): Promise<void> {
    await axios.delete(`${API_BASE}/tags/${tagId}/repos/${repoId}`)
  },

  async getForRepo(repoId: string): Promise<Tag[]> {
    const response = await axios.get<Tag[]>(`${API_BASE}/repos/${repoId}/tags`)
    return response.data
  }
}

// ==================== Notes API ====================

export const notesApi = {
  async get(repoId: string): Promise<Note | null> {
    try {
      const response = await axios.get<Note>(`${API_BASE}/repos/${repoId}/note`)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw error
    }
  },

  async upsert(repoId: string, data: NoteUpsert): Promise<Note> {
    const response = await axios.put<Note>(`${API_BASE}/repos/${repoId}/note`, data)
    return response.data
  },

  async delete(repoId: string): Promise<void> {
    await axios.delete(`${API_BASE}/repos/${repoId}/note`)
  },

  async getAll(): Promise<Note[]> {
    const response = await axios.get<Note[]>(`${API_BASE}/notes`)
    return response.data
  }
}

// ==================== Combined API ====================

export const userApi = {
  collections: collectionsApi,
  tags: tagsApi,
  notes: notesApi
}

// ==================== Helper: Get collection for repo ====================
// Note: This helper is also available as collectionsApi.getCollectionForRepo
export async function getCollectionForRepo(repoId: string): Promise<Collection | null> {
  return await collectionsApi.getCollectionForRepo(repoId)
}
