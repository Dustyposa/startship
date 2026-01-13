import { ref } from 'vue'
import { storage } from '@/utils/storage'
import { STORAGE_KEYS, type TechProfile } from '@/types/collections'

interface Repo {
  name_with_owner: string
  primary_language?: string
  categories?: string[]
  stargazer_count: number
  starred_at?: string
  pushed_at?: string
  description?: string
}

export function useProfile() {
  const profile = ref<TechProfile | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  function load() {
    profile.value = storage.get<TechProfile>(STORAGE_KEYS.PROFILE) || null
  }

  async function generate(repos: Repo[]) {
    isLoading.value = true
    error.value = null

    try {
      const langCounts = new Map<string, number>()
      repos.forEach(repo => {
        if (repo.primary_language) {
          langCounts.set(repo.primary_language, (langCounts.get(repo.primary_language) || 0) + 1)
        }
      })

      const techStack = Array.from(langCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([lang]) => lang)

      const domainCounts = new Map<string, number>()
      repos.forEach(repo => {
        repo.categories?.forEach(cat => {
          domainCounts.set(cat, (domainCounts.get(cat) || 0) + 1)
        })
      })

      const domains = Array.from(domainCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([domain]) => domain)

      const trends: TechProfile['trends'] = []
      if (repos.some(r => r.starred_at)) {
        const monthlyData = new Map<string, Map<string, number>>()
        repos.forEach(repo => {
          if (repo.starred_at && repo.primary_language) {
            const month = repo.starred_at.slice(0, 7)
            if (!monthlyData.has(month)) monthlyData.set(month, new Map())
            monthlyData.get(month)!.set(repo.primary_language, (monthlyData.get(month)!.get(repo.primary_language) || 0) + 1)
          }
        })
        monthlyData.forEach((langData, period) => {
          const topLang = Array.from(langData.entries()).sort((a, b) => b[1] - a[1])[0]
          if (topLang) trends.push({ period, top_language: topLang[0], new_domains: [] })
        })
        trends.slice(-6)
      }

      const avgStars = repos.reduce((sum, r) => sum + r.stargazer_count, 0) / repos.length
      let learningStage: 'beginner' | 'intermediate' | 'advanced'
      if (avgStars < 1000) learningStage = 'beginner'
      else if (avgStars < 10000) learningStage = 'intermediate'
      else learningStage = 'advanced'

      const insights: string[] = []
      if (techStack.length > 0) insights.push(`主要技术栈: ${techStack.slice(0, 3).join(', ')}`)
      if (domains.length > 0) insights.push(`关注领域: ${domains.join(', ')}`)
      if (trends.length >= 2) {
        const recent = trends[trends.length - 1]
        const old = trends[0]
        if (recent.top_language !== old.top_language) insights.push(`近期兴趣从 ${old.top_language} 转向 ${recent.top_language}`)
      }

      profile.value = {
        tech_stack: techStack,
        domains,
        trends,
        learning_stage: learningStage,
        insights,
        last_analyzed: new Date().toISOString()
      }
      save()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
    } finally {
      isLoading.value = false
    }
  }

  function save() {
    if (profile.value) storage.set(STORAGE_KEYS.PROFILE, profile.value)
  }

  load()

  return {
    profile,
    isLoading,
    error,
    load,
    generate,
    save
  }
}
