import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../components/ui/button"
import { SqlEditor } from "../components/SqlEditor"
import { AnalysisResults } from "../components/AnalysisResults"
import { GeneratorResults } from "../components/GeneratorResults"
import { ArrowLeft, Play, Wand2, Database, Sparkles, Copy, Check } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface OptimizerWorkspaceProps {
    mode: "optimizer" | "generator"
}

const DIALECTS = [
    { id: "postgresql", name: "PostgreSQL", icon: "🐘" },
    { id: "mysql", name: "MySQL", icon: "🐬" },
    { id: "sqlite", name: "SQLite", icon: "📦" }
]

export default function OptimizerWorkspace({ mode }: OptimizerWorkspaceProps) {
    const navigate = useNavigate()

    // Joint State
    const [dialect, setDialect] = useState("postgresql")

    // Optimizer State
    const [sqlQuery, setSqlQuery] = useState<any>("SELECT * FROM users WHERE active = true")
    const [analysisResult, setAnalysisResult] = useState<any>(null)

    // Generator State
    const [schemaInput, setSchemaInput] = useState<string>("CREATE TABLE users (id INT, name TEXT, active BOOLEAN);")
    const [questionInput, setQuestionInput] = useState<string>("Show me all active users")
    const [generatorResult, setGeneratorResult] = useState<any>(null)

    const [loading, setLoading] = useState(false)

    const handleAnalyze = async () => {
        setLoading(true)
        try {
            const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/analyze`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: sqlQuery, dialect })
            })
            const data = await res.json()
            setAnalysisResult(data)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleGenerate = async () => {
        setLoading(true)
        try {
            const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/generate-sql`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ schema_def: schemaInput, question: questionInput, dialect })
            })
            const data = await res.json()
            setGeneratorResult(data)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="relative min-h-screen flex flex-col bg-[#030014] text-white selection:bg-purple-500/30 overflow-hidden font-sans">

            {/* Background Effects (Matching Landing Page) */}
            <div className="absolute inset-0 z-0 opacity-20 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] brightness-100 contrast-150 mix-blend-overlay pointer-events-none"></div>
            <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-purple-600/20 blur-[100px] mix-blend-screen animate-pulse pointer-events-none"></div>
            <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-blue-600/20 blur-[100px] mix-blend-screen pointer-events-none"></div>

            {/* Header */}
            <header className="h-16 border-b border-white/10 flex-none flex items-center justify-between px-6 bg-[#030014]/80 backdrop-blur-md z-50 sticky top-0">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => navigate("/")} className="hover:bg-white/10 text-gray-400 hover:text-white">
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div className="flex flex-col">
                        <h1 className="font-bold text-lg tracking-wide bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                            {mode === "optimizer" ? "Query Optimizer" : "Text-to-SQL Generator"}
                        </h1>
                        <span className="text-[10px] text-gray-500 font-mono tracking-wider uppercase">AI Powered Engine</span>
                    </div>
                </div>

                {/* Dialect Selector */}
                <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 uppercase tracking-widest hidden md:block">Target Dialect:</span>
                    <div className="flex bg-white/5 p-1 rounded-lg border border-white/10">
                        {DIALECTS.map((d) => (
                            <button
                                key={d.id}
                                onClick={() => setDialect(d.id)}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-300 ${dialect === d.id
                                        ? "bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-blue-200 border border-blue-500/30 shadow-[0_0_10px_rgba(59,130,246,0.2)]"
                                        : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
                                    }`}
                            >
                                <span>{d.icon}</span>
                                <span className="hidden md:inline">{d.name}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Mode Switcher */}
                <div className="flex bg-white/5 p-1 rounded-lg border border-white/10 ml-4">
                    <button
                        onClick={() => navigate("/optimizer")}
                        className={`text-xs px-4 py-1.5 rounded-md transition-all ${mode === "optimizer" ? "bg-white/10 text-white shadow-sm" : "text-gray-500 hover:text-gray-300"}`}
                    >
                        Optimizer
                    </button>
                    <button
                        onClick={() => navigate("/generator")}
                        className={`text-xs px-4 py-1.5 rounded-md transition-all ${mode === "generator" ? "bg-white/10 text-white shadow-sm" : "text-gray-500 hover:text-gray-300"}`}
                    >
                        Generator
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:overflow-hidden relative z-10">
                <div className="flex flex-col lg:grid lg:grid-cols-2 gap-6 h-auto lg:h-full max-w-8xl mx-auto">

                    {/* Left Panel: Input */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.5 }}
                        className="flex flex-col gap-4 h-[600px] lg:h-full min-h-0 order-1"
                    >
                        {mode === "optimizer" ? (
                            <>
                                <div className="flex-1 min-h-0 flex flex-col gap-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 shadow-xl">
                                    <label className="text-sm font-medium text-blue-300/80 flex items-center gap-2 mb-2">
                                        <Database className="h-4 w-4" /> Input SQL Query
                                    </label>
                                    <div className="flex-1 relative rounded-lg overflow-hidden border border-white/10 bg-black/50">
                                        <SqlEditor value={sqlQuery} onChange={(val) => setSqlQuery(val || "")} />
                                    </div>
                                </div>
                                <Button
                                    onClick={handleAnalyze}
                                    disabled={loading}
                                    className="w-full h-12 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 border-0 shadow-[0_0_20px_rgba(79,70,229,0.4)] transition-all active:scale-[0.98]"
                                    variant="default"
                                >
                                    {loading ? (
                                        <div className="flex items-center gap-2">
                                            <div className="h-4 w-4 border-2 border-white/50 border-t-white rounded-full animate-spin" />
                                            <span>Analyzing Engine...</span>
                                        </div>
                                    ) : (
                                        <><Play className="mr-2 h-5 w-5 fill-white" /> Analyze Execution Plan</>
                                    )}
                                </Button>
                            </>
                        ) : (
                            // Generator Mode Inputs
                            <>
                                <div className="h-1/3 min-h-[200px] flex flex-col gap-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 shadow-xl">
                                    <label className="text-sm font-medium text-blue-300/80 mb-2 flex items-center gap-2">
                                        <Database className="w-4 h-4" /> Schema Context
                                    </label>
                                    <div className="flex-1 relative rounded-lg overflow-hidden border border-white/10 bg-black/50">
                                        <SqlEditor value={schemaInput} onChange={(val) => setSchemaInput(val || "")} />
                                    </div>
                                </div>
                                <div className="flex-1 min-h-[200px] flex flex-col gap-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 shadow-xl">
                                    <label className="text-sm font-medium text-purple-300/80 mb-2 flex items-center gap-2">
                                        <Sparkles className="w-4 h-4" /> Natural Language Question
                                    </label>
                                    <textarea
                                        className="flex-1 bg-black/50 border border-white/10 rounded-lg p-4 resize-none focus:outline-none focus:ring-1 focus:ring-purple-500/50 font-sans text-base md:text-lg text-gray-200 placeholder:text-gray-600 shadow-inner"
                                        placeholder="e.g. Find users who placed more than 5 orders in 2023..."
                                        value={questionInput}
                                        onChange={(e) => setQuestionInput(e.target.value)}
                                    />
                                </div>
                                <Button
                                    onClick={handleGenerate}
                                    disabled={loading}
                                    className="w-full h-12 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 border-0 shadow-[0_0_20px_rgba(236,72,153,0.4)] transition-all active:scale-[0.98]"
                                    variant="default"
                                >
                                    {loading ? (
                                        <div className="flex items-center gap-2">
                                            <div className="h-4 w-4 border-2 border-white/50 border-t-white rounded-full animate-spin" />
                                            <span>Generating Logic...</span>
                                        </div>
                                    ) : (
                                        <><Wand2 className="mr-2 h-5 w-5" /> Generate SQL Query</>
                                    )}
                                </Button>
                            </>
                        )}
                    </motion.div>

                    {/* Right Panel: Results */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                        className="bg-[#0a0a0b]/60 backdrop-blur-xl rounded-2xl border border-white/10 p-0 h-[600px] lg:h-full min-h-0 overflow-hidden relative order-2 shadow-2xl ring-1 ring-white/5 flex flex-col"
                    >
                        {/* Panel Header */}
                        <div className="h-14 border-b border-white/10 flex items-center justify-between px-6 bg-white/5">
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${loading ? "bg-yellow-400 animate-pulse" : "bg-green-400"}`}></div>
                                <h2 className="text-xs font-bold text-gray-300 uppercase tracking-widest">
                                    {mode === "optimizer" ? "Analysis Report" : "Generated Output"}
                                </h2>
                            </div>
                            {/* Copy Button Placeholder (Optional enhancement can be added to individual result components) */}
                        </div>

                        {/* Scrollable Content Area */}
                        <div className="flex-1 overflow-y-auto custom-scrollbar relative p-6">
                            <AnimatePresence mode="wait">
                                {loading ? (
                                    <motion.div
                                        key="loader"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="absolute inset-0 flex flex-col items-center justify-center gap-6"
                                    >
                                        <div className="relative">
                                            <div className="h-16 w-16 border-4 border-t-purple-500 border-r-blue-500 border-b-pink-500 border-l-transparent rounded-full animate-spin"></div>
                                            <div className="absolute inset-0 border-4 border-white/10 rounded-full"></div>
                                        </div>
                                        <p className="text-sm text-gray-400 animate-pulse font-mono">Processing Request...</p>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="content"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ duration: 0.3 }}
                                        className="h-full"
                                    >
                                        {mode === "optimizer" && analysisResult && <AnalysisResults result={analysisResult} />}
                                        {mode === "generator" && generatorResult && <GeneratorResults result={generatorResult} />}

                                        {!analysisResult && !generatorResult && (
                                            <div className="h-full flex flex-col items-center justify-center text-gray-600 space-y-4">
                                                <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                                                    <Sparkles className="h-8 w-8 text-gray-500" />
                                                </div>
                                                <p className="font-mono text-sm">Waiting for input to start...</p>
                                            </div>
                                        )}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </motion.div>

                </div>
            </div>

            {/* Styles for custom scrollbar */}
            <style>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: rgba(255, 255, 255, 0.05);
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(255, 255, 255, 0.3);
                }
            `}</style>
        </div>
    )
}
