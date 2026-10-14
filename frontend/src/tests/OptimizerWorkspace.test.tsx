import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AnalysisResults } from '../components/AnalysisResults'
import OptimizerWorkspace from '../pages/OptimizerWorkspace'

const analysisPayload = {
    original_query: 'SELECT * FROM users',
    explanation: 'Demo explanation for the selected query.',
    suggestions: [],
    execution_plan: { node_type: 'Seq Scan', cost: 10, rows: 1 },
    optimized_query: 'SELECT id, name, email FROM users',
    analysis_source: 'demo',
    plan_origin: 'synthetic',
    database_connected: false,
    performance_measured: false,
}

function jsonResponse(body: unknown, status = 200): Response {
    return new Response(JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json' },
    })
}

function renderOptimizer(mode: 'optimizer' | 'generator' = 'optimizer') {
    return render(
        <MemoryRouter>
            <OptimizerWorkspace mode={mode} />
        </MemoryRouter>
    )
}

afterEach(() => {
    vi.unstubAllGlobals()
})

describe('AnalysisResults provenance', () => {
    it('labels a synthetic plan as an estimate', () => {
        render(<AnalysisResults result={analysisPayload} />)
        expect(screen.getByText('Estimated plan')).toBeInTheDocument()
        expect(screen.getByText(/not a plan from a database engine/i)).toBeInTheDocument()
        expect(screen.queryByText('Execution Plan')).not.toBeInTheDocument()
    })
})

describe('OptimizerWorkspace request handling', () => {
    it('shows the response source instead of always claiming Gemini', async () => {
        vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(analysisPayload)))
        renderOptimizer()

        fireEvent.click(screen.getByRole('button', { name: /Review query/i }))

        expect(await screen.findByText(/Demo ·/)).toBeInTheDocument()
        expect(screen.getByText('Estimated plan')).toBeInTheDocument()
        expect(screen.queryByText(/Gemini AI/)).not.toBeInTheDocument()
    })

    it('shows an HTTP 500 without rendering the analysis report', async () => {
        vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ detail: 'Analysis failed' }, 500)))
        renderOptimizer()

        fireEvent.click(screen.getByRole('button', { name: /Review query/i }))

        expect(await screen.findByRole('alert')).toHaveTextContent('Analysis failed')
        expect(screen.queryByText('Analysis Report')).not.toBeInTheDocument()
        expect(screen.queryByText('Optimization Suggestions')).not.toBeInTheDocument()
    })

    it('shows a network failure without crashing', async () => {
        vi.stubGlobal('fetch', vi.fn(async () => {
            throw new TypeError('Failed to fetch')
        }))
        renderOptimizer()

        fireEvent.click(screen.getByRole('button', { name: /Review query/i }))

        expect(await screen.findByRole('alert')).toHaveTextContent(/Could not reach the server/i)
        expect(screen.queryByText('Analysis Report')).not.toBeInTheDocument()
    })

    it('shows a safe validation message and does not echo the submitted query', async () => {
        const marker = 'secret-query-marker-should-not-echo'
        vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({
            detail: [
                { type: 'value_error', loc: ['body', 'query'], msg: 'Query exceeds the maximum length of 20000 characters.' },
            ],
        }, 422)))
        renderOptimizer()

        fireEvent.change(screen.getByPlaceholderText(/SELECT \* FROM users/i), {
            target: { value: marker },
        })
        fireEvent.click(screen.getByRole('button', { name: /Review query/i }))

        const alert = await screen.findByRole('alert')
        expect(alert).toHaveTextContent('Query exceeds the maximum length of 20000 characters.')
        expect(alert).not.toHaveTextContent(marker)
        expect(screen.queryByText('Analysis Report')).not.toBeInTheDocument()
    })

    it('handles a non-JSON error body', async () => {
        vi.stubGlobal('fetch', vi.fn(async () => new Response('bad gateway', { status: 502 })))
        renderOptimizer()

        fireEvent.click(screen.getByRole('button', { name: /Review query/i }))

        expect(await screen.findByRole('alert')).toHaveTextContent('Request failed (502).')
    })

    it('still renders a successful generation and its source', async () => {
        vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({
            query: 'SELECT id FROM users',
            explanation: 'Unique generation explanation',
            analysis_source: 'groq',
            plan_origin: 'none',
            database_connected: false,
            performance_measured: false,
        })))
        renderOptimizer('generator')

        fireEvent.click(screen.getByRole('button', { name: /Generate SQL Query/i }))

        expect(await screen.findByText('Unique generation explanation')).toBeInTheDocument()
        expect(screen.getByText(/Groq/)).toBeInTheDocument()
        expect(screen.queryByText(/Gemini AI/)).not.toBeInTheDocument()
    })
})
