import { motion } from "framer-motion"
import { Sparkles, Copy, Check } from "lucide-react"
import { useState } from "react"
import { Button } from "./ui/button"

type GeneratorResponse = {
    query: string
    explanation: string
}

export function GeneratorResults({ result }: { result: GeneratorResponse }) {
    const [copied, setCopied] = useState(false)

    const handleCopy = () => {
        navigator.clipboard.writeText(result.query)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className="space-y-6 h-full">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-6 rounded-xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/30 to-black/30 shadow-[0_0_50px_-12px_rgba(79,70,229,0.2)]"
            >
                <div className="flex items-center gap-2 mb-4 text-indigo-400">
                    <Sparkles className="h-5 w-5" />
                    <h3 className="font-semibold">Generated SQL</h3>
                </div>

                <div className="relative group">
                    <div className="absolute top-2 right-2">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={handleCopy}
                            className="h-8 w-8 text-muted-foreground hover:text-white"
                        >
                            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                        </Button>
                    </div>
                    <pre className="p-4 rounded-lg bg-black/50 border border-white/10 font-mono text-sm text-gray-200 overflow-x-auto whitespace-pre-wrap">
                        {result.query}
                    </pre>
                </div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="p-5 rounded-lg border border-white/10 bg-white/5"
            >
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Reasoning</h4>
                <p className="text-sm text-gray-300 leading-relaxed">
                    {result.explanation}
                </p>
            </motion.div>
        </div>
    )
}
