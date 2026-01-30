import { motion } from "framer-motion"
import { Activity, AlertTriangle, CheckCircle } from "lucide-react"

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
    execution_plan: any // specialized type omitted for brevity
    optimized_query?: string
}

export function AnalysisResults({ result }: { result: AnalysisResult }) {
    return (
        <div className="space-y-6 overflow-y-auto h-full pr-2">

            {/* Explanation Card */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-5 rounded-lg border border-indigo-500/20 bg-indigo-500/5"
            >
                <div className="flex items-center gap-2 mb-2 text-indigo-400">
                    <Activity className="h-5 w-5" />
                    <h3 className="font-semibold">AI Analysis</h3>
                </div>
                <p className="text-sm text-gray-300 leading-relaxed">
                    {result.explanation}
                </p>
            </motion.div>

            {/* Suggestions */}
            <div className="space-y-4">
                <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Optimization Suggestions</h3>
                {result.suggestions.map((sugo, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className={`p-4 rounded-lg border ${sugo.impact === "High" ? "border-red-500/30 bg-red-500/5" :
                            sugo.impact === "Medium" ? "border-amber-500/30 bg-amber-500/5" :
                                "border-green-500/30 bg-green-500/5"
                            }`}
                    >
                        <div className="flex justify-between items-start mb-2">
                            <h4 className="font-medium text-sm flex items-center gap-2">
                                {sugo.impact === "High" && <AlertTriangle className="h-4 w-4 text-red-400" />}
                                {sugo.impact === "Low" && <CheckCircle className="h-4 w-4 text-green-400" />}
                                {sugo.title}
                            </h4>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${sugo.impact === "High" ? "border-red-500/30 text-red-400" :
                                sugo.impact === "Medium" ? "border-amber-500/30 text-amber-400" :
                                    "border-green-500/30 text-green-400"
                                }`}>
                                {sugo.impact} Impact
                            </span>
                        </div>
                        <p className="text-xs text-muted-foreground mb-3">{sugo.description}</p>
                        {sugo.sql_snippet && (
                            <div className="bg-black/50 p-2 rounded border border-white/10">
                                <code className="text-xs font-mono text-indigo-300">{sugo.sql_snippet}</code>
                            </div>
                        )}
                    </motion.div>
                ))}
            </div>

            {/* Optimized Query Preview */}
            {result.optimized_query && result.optimized_query !== result.original_query && (
                <div className="p-4 rounded-lg border border-green-500/20 bg-green-500/5 mt-4">
                    <h3 className="text-sm font-medium text-green-400 mb-2">Recommended Query</h3>
                    <pre className="text-xs font-mono text-gray-300 overflow-x-auto whitespace-pre-wrap">
                        {result.optimized_query}
                    </pre>
                </div>
            )}
        </div>
    )
}
