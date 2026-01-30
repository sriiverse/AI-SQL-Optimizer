import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import LandingPage from "./pages/LandingPage"
import OptimizerWorkspace from "./pages/OptimizerWorkspace"

function App() {
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
