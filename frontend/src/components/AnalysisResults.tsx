import { motion } from "framer-motion"
import { Activity, AlertTriangle, CheckCircle, TrendingUp, Code2 } from "lucide-react"

// Types matching the backend response
type Suggestion = {
    title: string
    description: string
    impact: "High" | "Medium" | "Low"
    sql_snippet?: string
}

type AnalysisResult = {
    original_query: string
    explanation: string
    suggestions: Suggestion[]
    execution_plan: any
    optimized_query?: string
}

const impactConfig = {
    High: { border: "border-red-500/30", bg: "bg-red-500/5", badge: "border-red-500/30 text-red-400", icon: <AlertTriangle className="h-4 w-4 text-red-400" /> },
    Medium: { border: "border-amber-500/30", bg: "bg-amber-500/5", badge: "border-amber-500/30 text-amber-400", icon: <TrendingUp className="h-4 w-4 text-amber-400" /> },
    Low: { border: "border-green-500/30", bg: "bg-green-500/5", badge: "border-green-500/30 text-green-400", icon: <CheckCircle className="h-4 w-4 text-green-400" /> },
}

export function AnalysisResults({ result }: { result: AnalysisResult }) {
    return (
        <div className="space-y-6">

            {/* ── AI Explanation Card ── */}
            <motion.div
                initial={{ opacity: 0, y: 20, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 24 }}
                className="p-5 rounded-xl border border-indigo-500/25 bg-indigo-500/8 shadow-lg"
            >
                <div className="flex items-center gap-2 mb-3 text-indigo-400">
                    <motion.div
                        animate={{ rotate: [0, 8, -8, 0] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                    >
                        <Activity className="h-5 w-5" />
                    </motion.div>
                    <h3 className="font-semibold text-sm tracking-wide">AI Analysis</h3>
                </div>
                <p className="text-sm text-gray-300 leading-relaxed">{result.explanation}</p>
            </motion.div>

            {/* ── Optimization Suggestions ── */}
            {result.suggestions.length > 0 && (
                <div className="space-y-3">
                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest px-1">
                        Optimization Suggestions
                    </h3>
                    {result.suggestions.map((sugg, idx) => {
                        const cfg = impactConfig[sugg.impact] ?? impactConfig.Low
                        return (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, x: -24, scale: 0.97 }}
                                animate={{ opacity: 1, x: 0, scale: 1 }}
                                transition={{
                                    type: "spring",
                                    stiffness: 320,
                                    damping: 26,
                                    delay: idx * 0.07,
                                }}
                                whileHover={{ scale: 1.012, transition: { type: "spring", stiffness: 400, damping: 20 } }}
                                className={`p-4 rounded-xl border ${cfg.border} ${cfg.bg} shadow-md cursor-default`}
                            >
                                <div className="flex justify-between items-start mb-2 gap-3">
                                    <h4 className="font-semibold text-sm flex items-center gap-2">
                                        {cfg.icon}
                                        {sugg.title}
                                    </h4>
                                    <span className={`flex-shrink-0 text-[10px] px-2.5 py-1 rounded-full border font-medium ${cfg.badge}`}>
                                        {sugg.impact} Impact
                                    </span>
                                </div>
                                <p className="text-xs text-gray-400 mb-3 leading-relaxed">{sugg.description}</p>
                                {sugg.sql_snippet && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: "auto" }}
                                        transition={{ delay: idx * 0.07 + 0.15, duration: 0.3 }}
                                        className="bg-black/60 p-3 rounded-lg border border-white/10 overflow-x-auto"
                                    >
                                        <div className="flex items-center gap-1.5 mb-2 text-gray-600">
                                            <Code2 className="h-3 w-3" />
                                            <span className="text-[10px] font-mono uppercase tracking-wider">SQL</span>
                                        </div>
                                        <code className="text-xs font-mono text-indigo-300 whitespace-pre-wrap">{sugg.sql_snippet}</code>
                                    </motion.div>
                                )}
                            </motion.div>
                        )
                    })}
                </div>
            )}

            {/* ── Optimized Query ── */}
            {result.optimized_query && result.optimized_query !== result.original_query && (
                <motion.div
                    initial={{ opacity: 0, y: 20, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ type: "spring", stiffness: 260, damping: 22, delay: (result.suggestions.length * 0.07) + 0.1 }}
                    className="p-5 rounded-xl border border-green-500/25 bg-green-500/6 shadow-lg"
                >
                    <div className="flex items-center gap-2 mb-3">
                        <motion.div
                            animate={{ scale: [1, 1.15, 1] }}
                            transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
                        >
                            <CheckCircle className="h-5 w-5 text-green-400" />
                        </motion.div>
                        <h3 className="text-sm font-semibold text-green-400 tracking-wide">Recommended Query</h3>
                    </div>
                    <div className="bg-black/60 rounded-xl border border-white/10 overflow-x-auto">
                        <pre className="text-xs font-mono text-gray-300 p-4 whitespace-pre-wrap leading-relaxed">
                            {result.optimized_query}
                        </pre>
                    </div>
                </motion.div>
            )}
        </div>
    )
}
