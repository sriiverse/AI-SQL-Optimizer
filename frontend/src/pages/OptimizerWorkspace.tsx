import { useState, useRef, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../components/ui/button"
import { AnalysisResults } from "../components/AnalysisResults"
import { GeneratorResults } from "../components/GeneratorResults"
import { ArrowLeft, Play, Wand2, Database, Sparkles, ShieldAlert } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface OptimizerWorkspaceProps {
    mode: "optimizer" | "generator"
}

const OPTIMIZER_STEPS = [
    { icon: "🔍", text: "Parsing your query structure..." },
    { icon: "🔗", text: "Identifying join patterns and index candidates..." },
    { icon: "📊", text: "Running cost estimation on execution paths..." },
    { icon: "⚡", text: "Cross-referencing optimization strategies..." },
    { icon: "🛠️", text: "Crafting your personalized recommendations..." },
    { icon: "✨", text: "Please have patience — we're making sure your wait is worth it." },
]

const GENERATOR_STEPS = [
    { icon: "📖", text: "Reading your schema context..." },
    { icon: "🧠", text: "Understanding the natural language intent..." },
    { icon: "🔗", text: "Mapping relationships between tables..." },
    { icon: "⚙️", text: "Constructing optimal query logic..." },
    { icon: "🧪", text: "Validating syntax for your target dialect..." },
    { icon: "✨", text: "Almost done — making sure your wait is worth it." },
]

const DIALECTS = [
    { id: "postgresql", name: "PostgreSQL", icon: "🐘" },
    { id: "mysql", name: "MySQL", icon: "🐬" },
    { id: "sqlite", name: "SQLite", icon: "📦" },
    { id: "mongodb", name: "MongoDB", icon: "🍃" },
]

const MONGODB_STEPS = [
    { icon: "🍃", text: "Parsing your collection schema..." },
    { icon: "🔗", text: "Analyzing document relationships and references..." },
    { icon: "📊", text: "Evaluating aggregation pipeline stages..." },
    { icon: "⚡", text: "Checking index coverage for query fields..." },
    { icon: "🛠️", text: "Optimizing pipeline for performance..." },
    { icon: "✨", text: "Please have patience — we're making sure your wait is worth it." },
]

// Spring physics preset for bouncy panel entrances
const springIn = (delay = 0) => ({
    initial: { opacity: 0, y: 28, scale: 0.97 },
    animate: { opacity: 1, y: 0, scale: 1 },
    transition: {
        type: "spring" as const,
        stiffness: 280,
        damping: 22,
        delay,
    },
})

const slideLeft = (delay = 0) => ({
    initial: { opacity: 0, x: -32, scale: 0.97 },
    animate: { opacity: 1, x: 0, scale: 1 },
    transition: { type: "spring" as const, stiffness: 300, damping: 24, delay },
})

const slideRight = (delay = 0) => ({
    initial: { opacity: 0, x: 32, scale: 0.97 },
    animate: { opacity: 1, x: 0, scale: 1 },
    transition: { type: "spring" as const, stiffness: 300, damping: 24, delay },
})

export default function OptimizerWorkspace({ mode }: OptimizerWorkspaceProps) {
    const navigate = useNavigate()
    const outputRef = useRef<HTMLDivElement>(null)

    // Joint State
    const [dialect, setDialect] = useState("postgresql")
    const isMongo = dialect === "mongodb"

    // Optimizer State
    const [sqlQuery, setSqlQuery] = useState<any>("SELECT * FROM users WHERE active = true")
    const [analysisResult, setAnalysisResult] = useState<any>(null)

    // Generator State
    const [schemaInput, setSchemaInput] = useState<string>("CREATE TABLE users (id INT, name TEXT, active BOOLEAN);")
    const [questionInput, setQuestionInput] = useState<string>("Show me all active users")
    const [generatorResult, setGeneratorResult] = useState<any>(null)

    const [loading, setLoading] = useState(false)

    const scrollToOutput = () => {
        setTimeout(() => {
            outputRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
        }, 200)
    }

    const handleAnalyze = async () => {
        setLoading(true)
        setAnalysisResult(null)
        try {
            const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/analyze`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: sqlQuery, dialect })
            })
            const data = await res.json()
            setAnalysisResult(data)
            scrollToOutput()
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleGenerate = async () => {
        setLoading(true)
        setGeneratorResult(null)
        try {
            const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/generate-sql`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ schema_def: schemaInput, question: questionInput, dialect })
            })
            const data = await res.json()
            setGeneratorResult(data)
            scrollToOutput()
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const hasResult = mode === "optimizer" ? !!analysisResult : !!generatorResult

    return (
        <div className="relative min-h-screen flex flex-col bg-[#030014] text-white selection:bg-purple-500/30 font-sans">

            {/* Background ambient glows */}
            <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-purple-600/15 blur-[130px] animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-blue-600/15 blur-[120px]" />
                <div className="absolute top-[40%] left-[50%] w-[300px] h-[300px] rounded-full bg-pink-600/10 blur-[100px]" />
                <div className="absolute inset-0 opacity-[0.08] bg-[url('https://grainy-gradients.vercel.app/noise.svg')] brightness-100 contrast-150 mix-blend-overlay" />
            </div>

            {/* ─── Sticky Header ─── */}
            <header className="h-auto border-b border-white/10 flex-none bg-[#030014]/85 backdrop-blur-md z-50 sticky top-0 shadow-[0_1px_0_rgba(255,255,255,0.06)]">
                {/* Main header row */}
                <div className="flex items-center justify-between px-4 md:px-6 h-16">
                    <div className="flex items-center gap-3">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => navigate("/")}
                            className="hover:bg-white/10 text-gray-400 hover:text-white transition-all hover:scale-110 active:scale-95"
                        >
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                        <div className="flex flex-col">
                            <h1 className="font-bold text-lg tracking-wide bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                                {mode === "optimizer"
                                    ? (isMongo ? "Pipeline Review" : "Query Optimizer")
                                    : (isMongo ? "Text-to-MongoDB" : "Text-to-SQL Generator")}
                            </h1>
                            <span className="text-[10px] text-gray-500 font-mono tracking-wider uppercase">AI Powered Engine</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Dialect Selector */}
                        <span className="text-xs text-gray-500 uppercase tracking-widest hidden md:block">Dialect:</span>
                        <div className="flex bg-white/5 p-1 rounded-lg border border-white/10">
                            {DIALECTS.map((d) => (
                                <button
                                    key={d.id}
                                    onClick={() => setDialect(d.id)}
                                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${dialect === d.id
                                        ? "bg-gradient-to-r from-purple-500/25 to-blue-500/25 text-blue-200 border border-blue-500/30 shadow-[0_0_12px_rgba(59,130,246,0.25)] scale-105"
                                        : "text-gray-400 hover:bg-white/5 hover:text-gray-200 hover:scale-105"
                                        }`}
                                >
                                    <span>{d.icon}</span>
                                    <span className="hidden md:inline">{d.name}</span>
                                </button>
                            ))}
                        </div>

                        {/* Mode Switcher */}
                        <div className="flex bg-white/5 p-1 rounded-lg border border-white/10">
                            <button
                                onClick={() => navigate("/optimizer")}
                                className={`text-xs px-4 py-1.5 rounded-md transition-all duration-200 ${mode === "optimizer" ? "bg-white/10 text-white shadow-sm scale-105" : "text-gray-500 hover:text-gray-300"}`}
                            >
                                Optimizer
                            </button>
                            <button
                                onClick={() => navigate("/generator")}
                                className={`text-xs px-4 py-1.5 rounded-md transition-all duration-200 ${mode === "generator" ? "bg-white/10 text-white shadow-sm scale-105" : "text-gray-500 hover:text-gray-300"}`}
                            >
                                Generator
                            </button>
                        </div>
                    </div>
                </div>

                {/* Privacy Warning — inside header, never overlaps content */}
                <div className="px-4 md:px-6 pb-2.5">
                    <div className="flex items-center gap-2.5 text-xs text-amber-400/80 bg-amber-500/8 border border-amber-500/20 rounded-lg px-4 py-2">
                        <ShieldAlert className="h-3.5 w-3.5 flex-shrink-0 text-amber-500" />
                        <span>Your schema is sent to Google Gemini for analysis. <strong className="text-amber-300">Avoid sharing real PII or production credentials.</strong></span>
                    </div>
                </div>
            </header>

            {/* ─── Main Scrollable Content ─── */}
            <div className="relative z-10 flex-1 overflow-y-auto">
                <div className="max-w-[1600px] mx-auto px-4 md:px-6 py-6 space-y-6">

                    {/* ═══════════════════════════════════════ */}
                    {/* INPUT SECTION                          */}
                    {/* ═══════════════════════════════════════ */}

                    {mode === "optimizer" ? (
                        /* ── Optimizer: full-width SQL editor ── */
                        <motion.div {...springIn(0)} className="space-y-4">
                            <div className="flex flex-col gap-2 bg-white/[0.04] backdrop-blur-sm border border-white/10 rounded-2xl p-5 shadow-2xl ring-1 ring-white/5 min-h-[320px]">
                                <label className="text-sm font-semibold text-blue-300/90 flex items-center gap-2 mb-1">
                                    <Database className="h-4 w-4" />
                                    {isMongo ? "MongoDB Query / Pipeline" : "Input SQL Query"}
                                </label>
                                <textarea
                                    className="w-full h-[300px] bg-black/60 border border-white/10 rounded-xl p-4 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 font-mono text-sm text-gray-200 placeholder:text-gray-600 shadow-inner transition-all duration-200 leading-relaxed"
                                    placeholder={isMongo ? "db.collection.aggregate([\n  { $match: { ... } },\n  { $group: { ... } }\n])" : "SELECT * FROM users WHERE ..."}
                                    value={sqlQuery}
                                    onChange={(e) => setSqlQuery(e.target.value)}
                                    spellCheck={false}
                                />
                            </div>

                            {/* Analyze Button */}
                            <motion.div
                                whileHover={{ scale: 1.015 }}
                                whileTap={{ scale: 0.97 }}
                                transition={{ type: "spring", stiffness: 400, damping: 20 }}
                            >
                                <Button
                                    onClick={handleAnalyze}
                                    disabled={loading}
                                    className="w-full h-13 text-base font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 border-0 shadow-[0_0_24px_rgba(79,70,229,0.45)] transition-shadow hover:shadow-[0_0_40px_rgba(79,70,229,0.65)] rounded-xl"
                                    variant="default"
                                >
                                    {loading ? (
                                        <div className="flex items-center gap-3">
                                            <div className="h-4 w-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                                            <span>Analyzing Engine...</span>
                                        </div>
                                    ) : (
                                        <><Play className="mr-2 h-5 w-5 fill-white" /> Analyze Execution Plan</>
                                    )}
                                </Button>
                            </motion.div>
                        </motion.div>
                    ) : (
                        /* ── Generator: Schema LEFT | Question RIGHT ── */
                        <div className="space-y-4">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

                                {/* Left: Schema */}
                                <motion.div
                                    {...slideLeft(0)}
                                    className="flex flex-col gap-2 bg-white/[0.04] backdrop-blur-sm border border-white/10 rounded-2xl p-5 shadow-2xl ring-1 ring-white/5 min-h-[320px]"
                                >
                                    <label className="text-sm font-semibold text-blue-300/90 flex items-center gap-2 mb-1">
                                        <Database className="h-4 w-4" />
                                        {isMongo ? "Collection Schema / Sample Docs" : "Schema Context"}
                                        <span className="ml-auto text-[10px] text-gray-500 font-mono font-normal uppercase tracking-wider">
                                            {isMongo ? "JSON / BSON" : "SQL DDL"}
                                        </span>
                                    </label>
                                    <textarea
                                        className="flex-1 bg-black/60 border border-white/10 rounded-xl p-4 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 font-mono text-sm text-gray-200 placeholder:text-gray-600 shadow-inner transition-all duration-200 min-h-[260px] leading-relaxed"
                                        placeholder={isMongo ? '{\n  "_id": "ObjectId",\n  "name": "String",\n  "email": "String"\n}' : "CREATE TABLE users (\n  id INT PRIMARY KEY,\n  name TEXT\n);"}
                                        value={schemaInput}
                                        onChange={(e) => setSchemaInput(e.target.value)}
                                        spellCheck={false}
                                    />
                                </motion.div>

                                {/* Right: Question */}
                                <motion.div
                                    {...slideRight(0.08)}
                                    className="flex flex-col gap-2 bg-white/[0.04] backdrop-blur-sm border border-white/10 rounded-2xl p-5 shadow-2xl ring-1 ring-white/5 min-h-[320px]"
                                >
                                    <label className="text-sm font-semibold text-purple-300/90 flex items-center gap-2 mb-1">
                                        <Sparkles className="h-4 w-4" />
                                        Natural Language Question
                                        <span className="ml-auto text-[10px] text-gray-500 font-mono font-normal uppercase tracking-wider">Plain English</span>
                                    </label>
                                    <textarea
                                        className="flex-1 bg-black/60 border border-white/10 rounded-xl p-4 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/40 focus:border-purple-500/40 font-sans text-base text-gray-200 placeholder:text-gray-600 shadow-inner transition-all duration-200 min-h-[260px] leading-relaxed"
                                        placeholder="e.g. Find all users who placed more than 5 orders in the last quarter, grouped by country and ordered by total spend..."
                                        value={questionInput}
                                        onChange={(e) => setQuestionInput(e.target.value)}
                                    />
                                </motion.div>
                            </div>

                            {/* Generate Button — full width below both panes */}
                            <motion.div
                                {...springIn(0.14)}
                                whileHover={{ scale: 1.015 }}
                                whileTap={{ scale: 0.97 }}
                                transition={{ type: "spring", stiffness: 400, damping: 20 }}
                            >
                                <Button
                                    onClick={handleGenerate}
                                    disabled={loading}
                                    className="w-full h-13 text-base font-semibold bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 border-0 shadow-[0_0_24px_rgba(236,72,153,0.4)] transition-shadow hover:shadow-[0_0_40px_rgba(236,72,153,0.65)] rounded-xl"
                                    variant="default"
                                >
                                    {loading ? (
                                        <div className="flex items-center gap-3">
                                            <div className="h-4 w-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                                            <span>Generating Logic...</span>
                                        </div>
                                    ) : (
                                        <><Wand2 className="mr-2 h-5 w-5" /> {isMongo ? "Generate Pipeline" : "Generate SQL Query"}</>
                                    )}
                                </Button>
                            </motion.div>
                        </div>
                    )}

                    {/* ═══════════════════════════════════════ */}
                    {/* OUTPUT SECTION — appears below inputs  */}
                    {/* ═══════════════════════════════════════ */}

                    <AnimatePresence mode="wait">
                        {loading && (
                            <LoadingPanel mode={mode} isMongo={isMongo} />
                        )}

                        {!loading && hasResult && (
                            <div
                                ref={outputRef}
                                className="bg-[#0a0a0f]/70 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl ring-1 ring-white/5 overflow-hidden"
                            >
                                {/* Output panel header */}
                                <div className="h-14 border-b border-white/10 flex items-center justify-between px-6 bg-white/[0.04]">
                                    <div className="flex items-center gap-2.5">
                                        <motion.div
                                            animate={{ scale: [1, 1.3, 1] }}
                                            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                                            className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]"
                                        />
                                        <h2 className="text-xs font-bold text-gray-300 uppercase tracking-widest">
                                            {mode === "optimizer" ? "Analysis Report" : "Generated Output"}
                                        </h2>
                                    </div>
                                    <span className="text-[10px] text-gray-600 font-mono">Gemini AI · {new Date().toLocaleTimeString()}</span>
                                </div>

                                {/* Scrollable results */}
                                <div className="p-6 custom-scrollbar">
                                    {mode === "optimizer" && analysisResult && <AnalysisResults result={analysisResult} />}
                                    {mode === "generator" && generatorResult && <GeneratorResults result={generatorResult} isMongo={isMongo} />}
                                </div>
                            </div>
                        )}

                        {!loading && !hasResult && (
                            <motion.div
                                key="empty"
                                {...springIn(0.3)}
                                exit={{ opacity: 0, scale: 0.96 }}
                                className="bg-white/[0.02] border border-dashed border-white/10 rounded-2xl p-16 flex flex-col items-center gap-4 text-gray-600"
                            >
                                <motion.div
                                    animate={{ y: [0, -8, 0] }}
                                    transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
                                    className="w-20 h-20 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10"
                                >
                                    <Sparkles className="h-8 w-8 text-gray-500" />
                                </motion.div>
                                <p className="font-mono text-sm">
                                    {mode === "optimizer"
                                        ? "Paste your SQL above and hit Analyze"
                                        : "Fill in your schema & question, then hit Generate"}
                                </p>
                                <p className="text-xs text-gray-700">Results will appear here</p>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Bottom padding */}
                    <div className="h-8" />
                </div>
            </div>

            {/* Custom scrollbar styles */}
            <style>{`
                .custom-scrollbar::-webkit-scrollbar { width: 5px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 10px; }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.28); }
                .h-13 { height: 3.25rem; }
            `}</style>
        </div>
    )
}

// ─── Rotating Loading Panel ─────────────────────────────────────────────────
function LoadingPanel({ mode, isMongo }: { mode: "optimizer" | "generator"; isMongo: boolean }) {
    const steps = isMongo
        ? MONGODB_STEPS
        : mode === "optimizer" ? OPTIMIZER_STEPS : GENERATOR_STEPS
    const [stepIdx, setStepIdx] = useState(0)

    useEffect(() => {
        setStepIdx(0)
        const interval = setInterval(() => {
            setStepIdx((prev) => (prev < steps.length - 1 ? prev + 1 : prev))
        }, 3200)
        return () => clearInterval(interval)
    }, [steps.length])

    const current = steps[stepIdx]
    const isLast = stepIdx === steps.length - 1

    return (
        <motion.div
            key="loader"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="bg-white/[0.04] border border-white/10 rounded-2xl px-8 py-14 flex flex-col items-center gap-8 shadow-2xl"
        >
            {/* Dual-ring spinner */}
            <div className="relative">
                <div className="h-16 w-16 border-4 border-t-purple-500 border-r-blue-500 border-b-pink-500 border-l-transparent rounded-full animate-spin" />
                <div className="absolute inset-0 border-4 border-white/5 rounded-full" />
                <div
                    className="absolute inset-2 border-2 border-t-pink-400/50 border-transparent rounded-full animate-spin"
                    style={{ animationDirection: "reverse", animationDuration: "0.75s" }}
                />
                {/* Center icon */}
                <div className="absolute inset-0 flex items-center justify-center text-lg">
                    <AnimatePresence mode="wait">
                        <motion.span
                            key={stepIdx}
                            initial={{ opacity: 0, scale: 0.5 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.5 }}
                            transition={{ duration: 0.25 }}
                        >
                            {current.icon}
                        </motion.span>
                    </AnimatePresence>
                </div>
            </div>

            {/* Rotating message */}
            <div className="text-center space-y-3 max-w-sm">
                <AnimatePresence mode="wait">
                    <motion.p
                        key={stepIdx}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.4, ease: "easeInOut" }}
                        className={`text-sm font-medium leading-relaxed ${isLast ? "text-purple-300" : "text-gray-300"}`}
                    >
                        {current.text}
                    </motion.p>
                </AnimatePresence>
                <p className="text-[11px] text-gray-600 font-mono tracking-wide animate-pulse">
                    Powered by Gemini AI
                </p>
            </div>

            {/* Step progress dots */}
            <div className="flex items-center gap-2">
                {steps.map((_, i) => (
                    <motion.div
                        key={i}
                        animate={{
                            width: i === stepIdx ? 20 : 6,
                            backgroundColor: i < stepIdx
                                ? "#a855f7"   /* completed: purple */
                                : i === stepIdx
                                    ? "#818cf8"   /* active: indigo */
                                    : "rgba(255,255,255,0.12)", /* pending: dim */
                        }}
                        transition={{ type: "spring", stiffness: 300, damping: 24 }}
                        className="h-1.5 rounded-full"
                    />
                ))}
            </div>
        </motion.div>
    )
}
