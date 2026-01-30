import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../components/ui/button"
import { SqlEditor } from "../components/SqlEditor"
import { AnalysisResults } from "../components/AnalysisResults"
import { GeneratorResults } from "../components/GeneratorResults"
import { ArrowLeft, Play, Wand2, Database } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface OptimizerWorkspaceProps {
    mode: "optimizer" | "generator"
}

export default function OptimizerWorkspace({ mode }: OptimizerWorkspaceProps) {
    const navigate = useNavigate()

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
                body: JSON.stringify({ query: sqlQuery })
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
                body: JSON.stringify({ schema_def: schemaInput, question: questionInput })
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
        <div className="flex flex-col h-[100dvh] bg-background">
            {/* Header */}
            <header className="h-14 border-b flex-none flex items-center justify-between px-4 bg-card/50 backdrop-blur z-50">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                    <h1 className="font-semibold text-sm md:text-base">{mode === "optimizer" ? "Query Optimizer" : "Text-to-SQL"}</h1>
                </div>
                <div className="flex bg-muted p-1 rounded-lg">
                    <button
                        onClick={() => navigate("/optimizer")}
                        className={`text-xs px-3 py-1 rounded-md transition-all ${mode === "optimizer" ? "bg-background shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
                    >
                        Optimizer
                    </button>
                    <button
                        onClick={() => navigate("/generator")}
                        className={`text-xs px-3 py-1 rounded-md transition-all ${mode === "generator" ? "bg-background shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
                    >
                        Generator
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto lg:overflow-hidden p-4 md:p-6">
                <div className="flex flex-col lg:grid lg:grid-cols-2 gap-6 h-auto lg:h-full">

                    {/* Left Panel: Input */}
                    <div className="flex flex-col gap-4 h-[500px] lg:h-full min-h-0 order-1">
                        {mode === "optimizer" ? (
                            <>
                                <div className="flex-1 min-h-0 flex flex-col gap-2">
                                    <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                                        <Database className="h-4 w-4" /> Input SQL Query
                                    </label>
                                    <SqlEditor value={sqlQuery} onChange={(val) => setSqlQuery(val || "")} />
                                </div>
                                <Button onClick={handleAnalyze} disabled={loading} className="w-full" variant="glow">
                                    {loading ? "Analyzing..." : <><Play className="mr-2 h-4 w-4" /> Analyze Plan</>}
                                </Button>
                            </>
                        ) : (
                            // Generator Mode Inputs
                            <>
                                <div className="h-1/3 min-h-[150px] flex flex-col gap-2">
                                    <label className="text-sm font-medium text-muted-foreground">Schema Context</label>
                                    <SqlEditor value={schemaInput} onChange={(val) => setSchemaInput(val || "")} />
                                </div>
                                <div className="flex-1 min-h-[150px] flex flex-col gap-2">
                                    <label className="text-sm font-medium text-muted-foreground">Natural Language Question</label>
                                    <textarea
                                        className="flex-1 bg-card border rounded-md p-4 resize-none focus:outline-none focus:ring-1 focus:ring-primary font-sans text-base md:text-lg"
                                        placeholder="e.g. Find users who placed more than 5 orders in 2023..."
                                        value={questionInput}
                                        onChange={(e) => setQuestionInput(e.target.value)}
                                    />
                                </div>
                                <Button onClick={handleGenerate} disabled={loading} className="w-full" variant="glow">
                                    {loading ? "Generating..." : <><Wand2 className="mr-2 h-4 w-4" /> Generate Query</>}
                                </Button>
                            </>
                        )}
                    </div>

                    {/* Right Panel: Results */}
                    <div className="bg-card/30 rounded-xl border border-white/5 p-6 h-[500px] lg:h-full min-h-0 overflow-hidden relative order-2 lg:order-2">
                        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-widest mb-4">
                            {mode === "optimizer" ? "Analysis Report" : "Generated Output"}
                        </h2>

                        <AnimatePresence mode="wait">
                            {loading ? (
                                <motion.div
                                    key="loader"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="absolute inset-0 flex items-center justify-center"
                                >
                                    <div className="flex flex-col items-center gap-4">
                                        <div className="h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                                        <p className="text-sm text-indigo-400 animate-pulse">Running AI Engine...</p>
                                    </div>
                                </motion.div>
                            ) : (
                                <motion.div
                                    key="content"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="h-full"
                                >
                                    {mode === "optimizer" && analysisResult && <AnalysisResults result={analysisResult} />}
                                    {mode === "generator" && generatorResult && <GeneratorResults result={generatorResult} />}

                                    {!analysisResult && !generatorResult && (
                                        <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-20">
                                            <Database className="h-16 w-16 mb-4" />
                                            <p>Waiting for input...</p>
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                </div>
            </div>
        </div>
    )
}
