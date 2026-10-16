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

    it('shows a safe provider error instead of a Gemini 403', async () => {
        const leak = '403 CONSUMER_SUSPENDED key=AIzaSYFAKEKEYFORTESTONLY000000 consumer projects/999001'
        vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({
            original_query: 'SELECT * FROM orders',
            explanation: leak,
            suggestions: [],
            execution_plan: {},
            optimized_query: leak,
            analysis_source: 'error',
        })))
        renderOptimizer()

        fireEvent.click(screen.getByRole('button', { name: /Review query/i }))

        const alert = await screen.findByRole('alert')
        expect(alert).toHaveTextContent('The request could not be completed. Try again later.')
        expect(alert).not.toHaveTextContent('AIzaSYFAKEKEYFORTESTONLY000000')
        expect(alert).not.toHaveTextContent('CONSUMER_SUSPENDED')
        expect(alert).not.toHaveTextContent('projects/999001')
        expect(screen.queryByText('Analysis Report')).not.toBeInTheDocument()
    })

    it('hides a provider secret returned in an HTTP error body', async () => {
        vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({
            detail: '401 invalid api key gsk_FAKEGROQKEY999',
        }, 502)))
        renderOptimizer('generator')

        fireEvent.click(screen.getByRole('button', { name: /Generate SQL Query/i }))

        const alert = await screen.findByRole('alert')
        expect(alert).toHaveTextContent('The request could not be completed. Try again later.')
        expect(alert).not.toHaveTextContent('gsk_FAKEGROQKEY999')
        expect(screen.queryByText('Generated Output')).not.toBeInTheDocument()
    })

    it('hides a short unsafe HTTP detail that is not an application message', async () => {
        vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({
            detail: 'sk-live-shortsecret',
        }, 500)))
        renderOptimizer()

        fireEvent.click(screen.getByRole('button', { name: /Review query/i }))

        const alert = await screen.findByRole('alert')
        expect(alert).toHaveTextContent('The request could not be completed. Try again later.')
        expect(alert).not.toHaveTextContent('sk-live-shortsecret')
        expect(screen.queryByText('Analysis Report')).not.toBeInTheDocument()
    })

    it('does not render a statement that is followed by untrusted query or explanation lines', async () => {
        vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({
            query: 'SELECT id FROM users\nkey=AIzaSYFAKEKEYFORTESTONLY000000 projects/999001',
            explanation: 'Returns users.\nkey=AIzaSYFAKEKEYFORTESTONLY000000 projects/999001',
            analysis_source: 'gemini',
            plan_origin: 'none',
            database_connected: false,
            performance_measured: false,
        })))
        renderOptimizer('generator')

        fireEvent.click(screen.getByRole('button', { name: /Generate SQL Query/i }))

        const alert = await screen.findByRole('alert')
        expect(alert).toHaveTextContent('The request could not be completed. Try again later.')
        expect(alert).not.toHaveTextContent('AIzaSYFAKEKEYFORTESTONLY000000')
        expect(alert).not.toHaveTextContent('projects/999001')
        expect(screen.queryByText('Generated Output')).not.toBeInTheDocument()
        expect(screen.queryByText('SELECT id FROM users')).not.toBeInTheDocument()
    })

    it('does not render an unsafe body marked as a successful provider result', async () => {
        const leak = '403 CONSUMER_SUSPENDED key=AIzaSYFAKEKEYFORTESTONLY000000 consumer projects/999001 SELECT * FROM orders'
        vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({
            query: leak,
            explanation: leak,
            analysis_source: 'gemini',
            plan_origin: 'none',
            database_connected: false,
            performance_measured: false,
        })))
        renderOptimizer('generator')

        fireEvent.click(screen.getByRole('button', { name: /Generate SQL Query/i }))

        const alert = await screen.findByRole('alert')
        expect(alert).toHaveTextContent('The request could not be completed. Try again later.')
        expect(alert).not.toHaveTextContent('AIzaSYFAKEKEYFORTESTONLY000000')
        expect(alert).not.toHaveTextContent('projects/999001')
        expect(screen.queryByText('Generated Output')).not.toBeInTheDocument()
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
