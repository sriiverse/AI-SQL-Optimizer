import { motion } from "framer-motion"
import { Sparkles, Copy, Check, Code2, GitBranch } from "lucide-react"
import { useState } from "react"

type GeneratorResponse = {
    query: string
    explanation: string
}

export function GeneratorResults({
    result,
    isMongo = false,
}: {
    result: GeneratorResponse
    isMongo?: boolean
}) {
    const [copied, setCopied] = useState(false)

    const handleCopy = () => {
        navigator.clipboard.writeText(result.query)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const titleLabel = isMongo ? "Generated Pipeline" : "Generated SQL"
    const TitleIcon = isMongo ? GitBranch : Code2

    return (
        <div className="space-y-5">

            {/* ── Code Block ── */}
            <motion.div
                initial={{ opacity: 0, y: 16, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: "spring", stiffness: 280, damping: 22 }}
                className="rounded-xl border border-indigo-500/25 bg-gradient-to-br from-indigo-950/30 to-black/40 shadow-[0_0_50px_-12px_rgba(79,70,229,0.25)] overflow-hidden"
            >
                {/* Code block header bar */}
                <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10 bg-white/[0.04]">
                    <div className="flex items-center gap-2 text-indigo-400">
                        <TitleIcon className="h-4 w-4" />
                        <span className="text-xs font-semibold tracking-wide">{titleLabel}</span>
                    </div>

                    {/* Traffic-light dots (decorative) */}
                    <div className="flex items-center gap-4">
                        <div className="hidden sm:flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
                            <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
                            <span className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
                        </div>

                        {/* Copy button — in header, never overlaps code */}
                        <motion.button
                            onClick={handleCopy}
                            whileHover={{ scale: 1.08 }}
                            whileTap={{ scale: 0.93 }}
                            transition={{ type: "spring", stiffness: 400, damping: 20 }}
                            className={`flex items-center gap-1.5 text-[11px] font-medium px-3 py-1 rounded-md border transition-all duration-200 ${copied
                                    ? "bg-green-500/15 border-green-500/30 text-green-400"
                                    : "bg-white/5 border-white/15 text-gray-400 hover:border-indigo-500/40 hover:text-indigo-300"
                                }`}
                        >
                            {copied
                                ? <><Check className="h-3 w-3" /> Copied!</>
                                : <><Copy className="h-3 w-3" /> Copy</>
                            }
                        </motion.button>
                    </div>
                </div>

                {/* Scrollable code area — proper monospace, line-by-line */}
                <div className="overflow-x-auto overflow-y-auto max-h-[520px] custom-scrollbar">
                    <pre className="p-5 font-mono text-[13px] leading-relaxed text-gray-200 whitespace-pre min-w-max">
                        {result.query}
                    </pre>
                </div>
            </motion.div>

            {/* ── Reasoning / Explanation ── */}
            <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 260, damping: 22, delay: 0.15 }}
                className="p-5 rounded-xl border border-white/10 bg-white/[0.04]"
            >
                <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="h-4 w-4 text-purple-400" />
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Reasoning</h4>
                </div>
                <p className="text-sm text-gray-300 leading-relaxed">{result.explanation}</p>
            </motion.div>
        </div>
    )
}
