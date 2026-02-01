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
        // Check for the gradient text title
        expect(screen.getByText(/Optimize SQL Queries/i)).toBeInTheDocument()
        expect(screen.getByText(/at the Speed of Thought/i)).toBeInTheDocument()
    })

    it('renders the CTA button', () => {
        render(
            <MemoryRouter>
                <LandingPage />
            </MemoryRouter>
        )
        const button = screen.getByText(/Start Optimizing/i)
        expect(button).toBeInTheDocument()
    })
})
