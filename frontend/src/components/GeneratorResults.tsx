import { motion } from "framer-motion"
import { Sparkles, Copy, Check, Code2, GitBranch } from "lucide-react"
import React, { useState } from "react"

type GeneratorResponse = {
    query: string
    explanation: string
}

// ── Lightweight syntax highlighter ──────────────────────────────────────────
function highlight(line: string): React.ReactElement {
    // Token patterns in priority order
    const tokens: { regex: RegExp; className: string }[] = [
        // Comments
        { regex: /(\/\/.*$)/, className: "text-gray-500 italic" },
        // MongoDB $ operators and keywords
        { regex: /(\$\w+)/g, className: "text-blue-400 font-semibold" },
        // SQL keywords
        {
            regex: /\b(SELECT|FROM|WHERE|JOIN|ON|GROUP BY|ORDER BY|HAVING|WITH|AS|UNION|ALL|INSERT|UPDATE|DELETE|LIMIT|DISTINCT|LEFT|RIGHT|INNER|OUTER|AND|OR|NOT|IN|EXISTS|BY|SET|INTO|VALUES|CASE|WHEN|THEN|ELSE|END|RECURSIVE)\b/gi,
            className: "text-violet-400 font-semibold"
        },
        // Strings
        { regex: /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, className: "text-green-400" },
        // Numbers
        { regex: /\b(\d+(?:\.\d+)?)\b/g, className: "text-orange-300" },
        // Braces / brackets
        { regex: /([{}[\]()])/g, className: "text-yellow-300/80" },
        // ObjectId, ISODate, new Date
        { regex: /\b(ObjectId|ISODate|new Date|Date\.now)\b/g, className: "text-cyan-400" },
        // Function calls
        { regex: /\b([a-zA-Z_]\w*)\s*(?=\()/g, className: "text-sky-300" },
    ]

    // Split by first matching token, recursively colour
    const parts: React.ReactElement[] = []
    let rest = line
    let idx = 0

    // Simple greedy token scan
    while (rest.length > 0) {
        let earliest: { start: number; end: number; cls: string } | null = null

        for (const { regex, className } of tokens) {
            regex.lastIndex = 0
            const m = regex.exec(rest)
            if (m && (earliest === null || m.index < earliest.start)) {
                earliest = { start: m.index, end: m.index + m[0].length, cls: className }
            }
        }

        if (!earliest) {
            parts.push(<span key={idx++}>{rest}</span>)
            break
        }

        if (earliest.start > 0) {
            parts.push(<span key={idx++}>{rest.slice(0, earliest.start)}</span>)
        }
        parts.push(
            <span key={idx++} className={earliest.cls}>
                {rest.slice(earliest.start, earliest.end)}
            </span>
        )
        rest = rest.slice(earliest.end)
    }

    return <>{parts}</>
}

// ── Code viewer with line numbers ────────────────────────────────────────────
function normalizeCode(raw: string): string {
    // Normalize Windows line endings
    let code = raw.replace(/\r\n/g, "\n").replace(/\r/g, "\n")
    // If the model returned a single-line blob with no newlines,
    // attempt a basic pretty-print by inserting newlines at key positions
    if (!code.includes("\n") && code.length > 80) {
        code = code
            .replace(/\{/g, "{\n  ")
            .replace(/\}/g, "\n}")
            .replace(/\[/g, "[\n  ")
            .replace(/\],/g, "\n],")
            .replace(/\],\s*\{/g, "],\n{")
            .replace(/,\s*\$/g, ",\n  $")
            .replace(/\n  \n/g, "\n")
    }
    return code
}

function CodeBlock({ code }: { code: string }) {
    const lines = normalizeCode(code).split("\n")
    return (
        <div className="flex font-mono text-[12.5px] leading-6 overflow-x-auto overflow-y-auto max-h-[580px] custom-scrollbar select-text">
            {/* Line numbers gutter */}
            <div
                className="select-none flex flex-col items-end pr-4 pl-4 text-gray-600 border-r border-white/10 bg-black/30 sticky left-0 shrink-0"
                aria-hidden
            >
                {lines.map((_, i) => (
                    <span key={i} className="leading-6">{i + 1}</span>
                ))}
            </div>

            {/* Code content */}
            <div className="flex-1 pl-5 pr-6 py-0 min-w-max">
                {lines.map((line, i) => (
                    <div key={i} className="leading-6 hover:bg-white/[0.03] whitespace-pre">
                        {highlight(line)}
                    </div>
                ))}
            </div>
        </div>
    )
}

// ── Main component ────────────────────────────────────────────────────────────
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

    const TitleIcon = isMongo ? GitBranch : Code2

    return (
        <div className="space-y-5">

            {/* ── Code Block ── */}
            <motion.div
                initial={{ opacity: 0, y: 16, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: "spring", stiffness: 280, damping: 22 }}
                className="rounded-xl border border-indigo-500/25 bg-[#0d0d14] shadow-[0_0_50px_-12px_rgba(79,70,229,0.25)] overflow-hidden"
            >
                {/* Editor header bar */}
                <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10 bg-[#111118]">
                    <div className="flex items-center gap-3">
                        {/* Traffic-light dots */}
                        <div className="flex items-center gap-1.5">
                            <span className="w-3 h-3 rounded-full bg-red-500/80" />
                            <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
                            <span className="w-3 h-3 rounded-full bg-green-500/80" />
                        </div>
                        <div className="flex items-center gap-2 text-indigo-400 ml-2">
                            <TitleIcon className="h-3.5 w-3.5" />
                            <span className="text-[11px] font-semibold tracking-wider text-gray-400">
                                {isMongo ? "pipeline.js" : "query.sql"}
                            </span>
                        </div>
                    </div>

                    {/* Copy button */}
                    <motion.button
                        onClick={handleCopy}
                        whileHover={{ scale: 1.08 }}
                        whileTap={{ scale: 0.93 }}
                        transition={{ type: "spring", stiffness: 400, damping: 20 }}
                        className={`flex items-center gap-1.5 text-[11px] font-medium px-3 py-1 rounded-md border transition-all duration-200 ${copied
                            ? "bg-green-500/15 border-green-500/30 text-green-400"
                            : "bg-white/5 border-white/12 text-gray-400 hover:border-indigo-500/40 hover:text-indigo-300"
                            }`}
                    >
                        {copied
                            ? <><Check className="h-3 w-3" /> Copied!</>
                            : <><Copy className="h-3 w-3" /> Copy</>
                        }
                    </motion.button>
                </div>

                {/* Syntax-highlighted code with line numbers */}
                <CodeBlock code={result.query} />
            </motion.div>

            {/* ── Reasoning ── */}
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
