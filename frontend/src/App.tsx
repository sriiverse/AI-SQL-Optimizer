import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import { useEffect } from "react"
import LandingPage from "./pages/LandingPage"
import OptimizerWorkspace from "./pages/OptimizerWorkspace"

const BACKEND_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"
const PING_INTERVAL_MS = 9 * 60 * 1000 // Every 9 minutes — just under Render's 10-min sleep timeout

function App() {
  useEffect(() => {
    // Keep-alive: ping the backend health endpoint to prevent Render cold starts
    const ping = () => {
      fetch(`${BACKEND_URL}/health`).catch(() => {
        // Silently ignore failures — this is just a background warmup ping
      })
    }

    // Ping immediately on load, then on a fixed interval
    ping()
    const interval = setInterval(ping, PING_INTERVAL_MS)

    return () => clearInterval(interval)
  }, [])

  return (
    <Router>
      <div className="dark min-h-screen bg-background text-foreground font-sans antialiased selection:bg-primary/20">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/optimizer" element={<OptimizerWorkspace mode="optimizer" />} />
          <Route path="/generator" element={<OptimizerWorkspace mode="generator" />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
