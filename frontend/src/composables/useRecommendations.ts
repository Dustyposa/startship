import { ref } from 'vue'
import type { Repo } from '@/types/collections'

interface SimilarRepo {
  repo: Repo
  similarity: number
}

interface LearningPathStep {
  title: string
  repos: Repo[]
  description: string
}

export function useRecommendations() {
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  function calculateSimilarity(text1: string, text2: string): number {
    const words1 = new Set(text1.toLowerCase().split(/\W+/))
    const words2 = new Set(text2.toLowerCase().split(/\W+/))
    let intersection = 0
    words1.forEach(word => { if (words2.has(word)) intersection++ })
    const union = new Set([...words1, ...words2])
    return union.size > 0 ? intersection / union.size : 0
  }

  function findSimilar(targetRepo: Repo, allRepos: Repo[], limit = 5): SimilarRepo[] {
    const targetText = `${targetRepo.name_with_owner} ${targetRepo.description || ''} ${targetRepo.primary_language || ''}`
    const similarities = allRepos
      .filter(r => r.name_with_owner !== targetRepo.name_with_owner)
      .map(repo => {
        const repoText = `${repo.name_with_owner} ${repo.description || ''} ${repo.primary_language || ''}`
        let similarity = calculateSimilarity(targetText, repoText)
        if (targetRepo.primary_language === repo.primary_language) similarity *= 1.5
        const commonCategories = (targetRepo.categories || []).filter(c => (repo.categories || []).includes(c))
        similarity *= (1 + commonCategories.length * 0.2)
        return { repo, similarity: Math.min(similarity, 1) }
      })
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit)
    return similarities
  }

  function generateLearningPath(repos: Repo[]): LearningPathStep[] {
    const byLanguage = new Map<string, Repo[]>()
    repos.forEach(repo => {
      if (repo.primary_language) {
        if (!byLanguage.has(repo.primary_language)) byLanguage.set(repo.primary_language, [])
        byLanguage.get(repo.primary_language)!.push(repo)
      }
    })
    const steps: LearningPathStep[] = []
    byLanguage.forEach((langRepos, lang) => {
      const sorted = langRepos.sort((a, b) => a.stargazer_count - b.stargazer_count)
      const n = sorted.length
      steps.push({ title: `${lang} 入门`, repos: sorted.slice(0, Math.ceil(n * 0.3)), description: `从基础项目开始学习 ${lang}` })
      steps.push({ title: `${lang} 进阶`, repos: sorted.slice(Math.ceil(n * 0.3), Math.ceil(n * 0.7)), description: `掌握 ${lang} 的核心概念和常用库` })
      steps.push({ title: `${lang} 高级`, repos: sorted.slice(Math.ceil(n * 0.7)), description: `深入学习 ${lang} 的高级特性和最佳实践` })
    })
    return steps
  }

  return {
    isLoading,
    error,
    findSimilar,
    generateLearningPath
  }
}
