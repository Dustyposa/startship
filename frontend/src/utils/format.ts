/**
 * Format star count like GitHub (1k, 2.5k, etc.)
 */
export function formatStarCount(count: number | null | undefined): string {
  if (count === null || count === undefined || isNaN(count)) {
    return 'N/A'
  }

  if (count < 1000) {
    return count.toString()
  }

  const suffixes = ['', 'k', 'M', 'B', 'T']
  const suffixIndex = Math.floor(Math.log10(count) / 3)
  const divisor = Math.pow(1000, suffixIndex)

  const shortValue = suffixIndex === 1
    ? parseFloat((count / divisor).toPrecision(3))
    : Math.floor(count / divisor)

  return shortValue + suffixes[suffixIndex]
}

/**
 * Format date to relative time (e.g., "2 days ago", "3 months ago")
 */
export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'

  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'N/A'

  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return 'just now'

  const intervals = [
    { unit: 'year', seconds: 31536000 },
    { unit: 'month', seconds: 2592000 },
    { unit: 'week', seconds: 604800 },
    { unit: 'day', seconds: 86400 },
    { unit: 'hour', seconds: 3600 },
    { unit: 'minute', seconds: 60 }
  ]

  for (const { unit, seconds: secondsInUnit } of intervals) {
    const value = Math.floor(seconds / secondsInUnit)
    if (value >= 1) {
      return `${value} ${unit}${value > 1 ? 's' : ''} ago`
    }
  }

  return 'just now'
}

/**
 * Format date to locale string
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'

  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'N/A'

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
