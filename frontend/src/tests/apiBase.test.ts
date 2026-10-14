import { describe, expect, it } from 'vitest'
import { apiUrl, resolveApiBaseUrl } from '../lib/apiBase'

describe('resolveApiBaseUrl', () => {
    it('returns null for a production build when the variable is missing', () => {
        expect(resolveApiBaseUrl(undefined, 'production')).toBeNull()
        expect(resolveApiBaseUrl('   ', 'production')).toBeNull()
    })

    it('uses the configured origin and drops a trailing slash', () => {
        expect(resolveApiBaseUrl(' https://api.example.com/ ', 'production')).toBe(
            'https://api.example.com'
        )
    })

    it('keeps local vite dev and vitest on localhost when unset', () => {
        expect(resolveApiBaseUrl(undefined, 'development')).toBe('http://localhost:8000')
        expect(resolveApiBaseUrl(undefined, 'test')).toBe('http://localhost:8000')
    })

    it('builds analyze, generate, and health URLs from that origin', () => {
        const base = resolveApiBaseUrl('https://api.example.com/', 'production')
        expect(base).not.toBeNull()
        expect(apiUrl(base as string, '/analyze')).toBe('https://api.example.com/analyze')
        expect(apiUrl(base as string, '/generate-sql')).toBe('https://api.example.com/generate-sql')
        expect(apiUrl(base as string, '/health')).toBe('https://api.example.com/health')
        expect(apiUrl(base as string, '/analyze')).not.toContain('undefined')
    })
})
