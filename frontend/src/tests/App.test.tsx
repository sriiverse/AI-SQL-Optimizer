import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LandingPage from '../pages/LandingPage'
import { describe, it, expect } from 'vitest'

describe('LandingPage', () => {
    it('renders the main title', () => {
        render(
            <MemoryRouter>
                <LandingPage />
            </MemoryRouter>
        )
        const title = screen.getByRole('heading', { level: 1 })
        expect(title).toHaveTextContent(/Review Database/i)
        expect(title).toHaveTextContent(/Queries/i)
        expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent(/Suggestions, not measurements/i)
        expect(screen.getByText(/does not connect to a database or measure execution time/i)).toBeInTheDocument()
        expect(screen.queryByText(/execution plans/i)).not.toBeInTheDocument()
        expect(screen.queryByText(/Speed of Thought/i)).not.toBeInTheDocument()
    })

    it('renders the CTA button', () => {
        render(
            <MemoryRouter>
                <LandingPage />
            </MemoryRouter>
        )
        expect(screen.getByRole('button', { name: /Review a query/i })).toBeInTheDocument()
        expect(screen.queryByRole('button', { name: /Start Optimizing/i })).not.toBeInTheDocument()
    })
})
