import { describe, it, expect, beforeEach, vi } from 'vitest'
import { storage } from '../storage'

describe('storage', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('should get value from localStorage', () => {
    localStorage.setItem('gh_test_key', '"test_value"')
    const result = storage.get('test_key')
    expect(result).toBe('test_value')
  })

  it('should set value to localStorage', () => {
    storage.set('test_key', 'test_value')
    expect(localStorage.getItem('gh_test_key')).toBe('"test_value"')
  })

  it('should remove value from localStorage', () => {
    storage.set('test_key', 'test_value')
    storage.remove('test_key')
    expect(localStorage.getItem('gh_test_key')).toBeNull()
  })

  it('should return null for non-existent key', () => {
    const result = storage.get('non_existent')
    expect(result).toBeNull()
  })

  it('should handle complex objects', () => {
    const obj = { id: 1, name: 'test', nested: { key: 'value' } }
    storage.set('test_obj', obj)
    const result = storage.get('test_obj')
    expect(result).toEqual(obj)
  })

  it('should clear all prefixed values', () => {
    storage.set('test1', 'value1')
    storage.set('test2', 'value2')
    localStorage.setItem('other_key', 'should_remain')  // Without prefix

    storage.clear()

    expect(localStorage.getItem('gh_test1')).toBeNull()
    expect(localStorage.getItem('gh_test2')).toBeNull()
    expect(localStorage.getItem('other_key')).toBe('should_remain')  // Unprefixed key remains
  })
})
