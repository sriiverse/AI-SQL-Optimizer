import { motion } from "framer-motion"
import { Clock, TrendingDown, DollarSign, Activity } from "lucide-react"

// Types for history entry
type HistoryEntry = {
    id: number
    query: string
    dialect: string
    original_cost: number
    optimized_cost: number
    cost_savings: number
    execution_time_ms: number
    timestamp: string
    explanation: string
    suggestions: Array<{
        title: string
        description: string
        impact: "High" | "Medium" | "Low"
        sql_snippet?: string
    }>
    optimized_query?: string
}

export function HistorySidebar({ history }: { history: HistoryEntry[] }) {
    if (history.length === 0) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 24 }}
                className="p-4 rounded-xl border border-gray-600/30 bg-gray-600/10"
            >
                <div className="text-center py-4">
                    <Activity className="h-5 w-5 text-gray-400 mb-2" />
                    <p className="text-sm text-gray-400">No history yet</p>
                </div>
            </motion.div>
        )
    }

    return (
        <motion.div
            initial={{ opacity: 0, x: -24, scale: 0.97 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 24 }}
            className="space-y-3"
        >
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest">
                Query History
            </h3>
            
            <div className="space-y-2">
                {history.map((entry) => (
                    <motion.div
                        key={entry.id}
                        initial={{ opacity: 0, y: 8, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{
                            type: "spring",
                            stiffness: 320,
                            damping: 26,
                            delay: entry.id * 0.03,
                        }}
                        className="p-3 rounded-lg border border-gray-600/20 bg-gray-600/5 cursor-pointer hover:bg-gray-600/10 transition-colors"
                    >
                        <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <Clock className="h-3 w-3 text-gray-400" />
                                    <span className="text-xs text-gray-300">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                                </div>
                                
                                <p className="text-xs text-gray-300 line-clamp-1 truncate">
                                    {entry.query.length > 50 
                                        ? entry.query.substring(0, 50) + "..." 
                                        : entry.query}
                                </p>
                                
                                <div className="flex items-center gap-3 text-xs mt-1">
                                    <div className="flex items-center gap-1">
                                        <DollarSign className="h-3 w-3 text-green-400" />
                                        <span className="font-mono">{entry.original_cost.toFixed(6)}</span>
                                    </div>
                                    
                                    <div className="flex items-center gap-1">
                                        <TrendingDown className="h-3 w-3 text-red-400" />
                                        <span className="font-mono text-green-500">
                                            -{entry.cost_savings.toFixed(6)}
                                        </span>
                                    </div>
                                    
                                    <div className="flex items-center gap-1">
                                        <Activity className="h-3 w-3 text-blue-400" />
                                        <span className="font-mono">{entry.execution_time_ms.toFixed(1)}ms</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="text-right text-xs">
                                <span className="px-2 py-0.5 rounded-full bg-gray-600/20 text-gray-300">
                                    {entry.dialect}
                                </span>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </motion.div>
    )
}