import { fireEvent, render, screen, within } from "@testing-library/react"
import { useState } from "react"
import { describe, expect, it } from "vitest"
import { ProConnectionModal } from "../components/ProConnectionModal"

function Harness() {
    const [open, setOpen] = useState(false)
    return (
        <>
            <button type="button" onClick={() => setOpen(true)}>PRO</button>
            <ProConnectionModal isOpen={open} onClose={() => setOpen(false)} />
        </>
    )
}

function pressTab(shiftKey = false) {
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", shiftKey, bubbles: true, cancelable: true }))
}

describe("ProConnectionModal keyboard access", () => {
    it("keeps Tab and Shift+Tab inside the dialog and restores focus on Escape", () => {
        render(<Harness />)
        const opener = screen.getByRole("button", { name: "PRO" })
        opener.focus()
        fireEvent.click(opener)

        const dialog = screen.getByRole("dialog")
        expect(dialog).toHaveFocus()
        expect(dialog).toHaveAttribute("aria-modal", "true")
        expect(dialog).toHaveAttribute("aria-labelledby", "pro-modal-title")

        const controls = within(dialog).getAllByRole("button")
        expect(controls.map((control) => control.getAttribute("aria-label") || control.textContent?.trim())).toEqual([
            "Close",
            "Copy to clipboard",
            "Copy to clipboard",
            "Copy to clipboard",
            "View Docs",
        ])

        pressTab()
        expect(controls[0]).toHaveFocus()
        pressTab()
        expect(controls[1]).toHaveFocus()
        pressTab()
        expect(controls[2]).toHaveFocus()
        pressTab()
        expect(controls[3]).toHaveFocus()
        pressTab()
        expect(controls[4]).toHaveFocus()
        pressTab()
        expect(controls[0]).toHaveFocus()

        pressTab(true)
        expect(controls[4]).toHaveFocus()
        pressTab(true)
        expect(controls[3]).toHaveFocus()
        pressTab(true)
        expect(controls[2]).toHaveFocus()
        pressTab(true)
        expect(controls[1]).toHaveFocus()
        pressTab(true)
        expect(controls[0]).toHaveFocus()
        pressTab(true)
        expect(controls[4]).toHaveFocus()

        controls[0].focus()
        fireEvent.click(controls[0])
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
        expect(opener).toHaveFocus()

        opener.focus()
        fireEvent.click(opener)
        expect(screen.getByRole("dialog")).toBeInTheDocument()
        fireEvent.keyDown(document, { key: "Escape" })
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
        expect(opener).toHaveFocus()
    })
})
