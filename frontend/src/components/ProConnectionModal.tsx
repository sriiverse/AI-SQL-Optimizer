import { motion, AnimatePresence } from "framer-motion"
import { CommandLineIcon, ServerIcon, ShieldCheckIcon, XMarkIcon, SparklesIcon, ChevronRightIcon, DocumentDuplicateIcon } from "@heroicons/react/24/outline"
import { useState } from "react"
import { Button } from "./ui/button"

interface ProModalProps {
    isOpen: boolean
    onClose: () => void
}

export function ProConnectionModal({ isOpen, onClose }: ProModalProps) {
    const [copiedContent, setCopiedContent] = useState<string | null>(null)

    if (!isOpen) return null

    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text)
        setCopiedContent(text)
        setTimeout(() => setCopiedContent(null), 2000)
    }

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
                {/* Backdrop backdrop-blur */}
                <motion.div
                    initial={{ opacity: 0, backdropFilter: "blur(0px)" }}
                    animate={{ opacity: 1, backdropFilter: "blur(12px)" }}
                    exit={{ opacity: 0, backdropFilter: "blur(0px)" }}
                    className="absolute inset-0 bg-black/60 transition-all duration-300"
                    onClick={onClose}
                />

                {/* Modal Container */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    transition={{ type: "spring", stiffness: 300, damping: 25 }}
                    className="relative w-full max-w-5xl bg-[#0a0a0f]/90 backdrop-blur-3xl border border-white/10 rounded-3xl shadow-[0_0_80px_rgba(139,92,246,0.15)] overflow-hidden flex flex-col md:flex-row"
                >
                    {/* Glowing Orbs behind the modal contents */}
                    <div className="absolute top-[-20%] left-[-10%] w-[300px] h-[300px] rounded-full bg-blue-600/20 blur-[100px] pointer-events-none" />
                    <div className="absolute bottom-[-20%] right-[-10%] w-[300px] h-[300px] rounded-full bg-purple-600/20 blur-[100px] pointer-events-none" />

                    {/* Left Column: The "Why" & Features */}
                    <div className="flex-1 p-8 md:p-10 border-r border-white/5 relative z-10 flex flex-col justify-center">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30">
                                <SparklesIcon className="w-6 h-6 text-purple-400" />
                            </div>
                            <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                                QueryForge <span className="text-purple-400 uppercase tracking-widest text-sm align-top ml-1">Pro</span>
                            </h2>
                        </div>

                        <p className="text-gray-300 leading-relaxed mb-8">
                            Unlock the true power of AI Database Intelligence. To protect your data, our PRO features run entirely on your local machine using our secure CLI Agent.
                        </p>

                        <div className="space-y-6">
                            <FeatureRow
                                icon={<ServerIcon className="w-5 h-5 text-blue-400" />}
                                title="Direct Localhost Connection"
                                desc="Connect to localhost:5432 securely without opening ports or exposing data to the internet."
                            />
                            <FeatureRow
                                icon={<CommandLineIcon className="w-5 h-5 text-pink-400" />}
                                title="Run True EXPLAIN Plans"
                                desc="Execute queries locally to get real-world millisecond timings and exact index usage."
                            />
                            <FeatureRow
                                icon={<ShieldCheckIcon className="w-5 h-5 text-green-400" />}
                                title="Zero Data Retention"
                                desc="Your passwords and production data never leave your laptop. Perfect for enterprise."
                            />
                        </div>
                    </div>

                    {/* Right Column: The "How" (Terminal UI) */}
                    <div className="flex-1 bg-black/40 p-8 md:p-10 relative z-10">
                        {/* Close button inside the right pane */}
                        <button
                            onClick={onClose}
                            className="absolute top-6 right-6 p-2 rounded-full hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                        >
                            <XMarkIcon className="w-6 h-6" />
                        </button>

                        <h3 className="text-lg font-semibold text-gray-200 mb-6 flex items-center gap-2">
                            Initialize Local Agent
                        </h3>

                        {/* Terminal Mockup */}
                        <div className="rounded-xl border border-white/10 bg-[#0d0d12] overflow-hidden shadow-2xl mb-8">
                            {/* Mac Window Controls */}
                            <div className="bg-white/5 px-4 py-3 border-b border-white/5 flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                                <div className="w-3 h-3 rounded-full bg-green-500/80" />
                                <span className="ml-4 text-xs text-gray-500 font-mono tracking-wider">agent ~ bash</span>
                            </div>

                            {/* Terminal Content */}
                            <div className="p-5 font-mono text-sm space-y-5">
                                <TerminalCommand
                                    step="1"
                                    cmd="npm install -g @queryforge/cli"
                                    copiedContent={copiedContent}
                                    onCopy={handleCopy}
                                />
                                <TerminalCommand
                                    step="2"
                                    cmd="queryforge login"
                                    desc="# Authenticates your local machine"
                                    copiedContent={copiedContent}
                                    onCopy={handleCopy}
                                />
                                <TerminalCommand
                                    step="3"
                                    cmd='queryforge connect --db "postgresql://user:pass@localhost:5432/db"'
                                    desc="# Establishes a secure WebSocket tunnel"
                                    copiedContent={copiedContent}
                                    onCopy={handleCopy}
                                />
                            </div>
                        </div>

                        {/* Status Footer */}
                        <div className="flex items-center justify-between p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
                            <div className="flex items-center gap-3">
                                <div className="relative flex h-3 w-3">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-3 w-3 bg-purple-500"></span>
                                </div>
                                <span className="text-sm font-medium text-purple-300">Waiting for CLI connection...</span>
                            </div>
                            <Button variant="outline" className="h-8 text-xs bg-white/5 border-white/10 text-gray-300 hover:bg-white/10">
                                View Docs <ChevronRightIcon className="w-3 h-3 ml-1" />
                            </Button>
                        </div>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}

function FeatureRow({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
    return (
        <div className="flex gap-4 group">
            <div className="p-3 rounded-xl bg-white/5 border border-white/10 group-hover:bg-white/10 transition-colors h-min">
                {icon}
            </div>
            <div>
                <h4 className="font-semibold text-gray-200 mb-1">{title}</h4>
                <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
            </div>
        </div>
    )
}

function TerminalCommand({ step, cmd, desc, copiedContent, onCopy }: { step: string; cmd: string; desc?: string; copiedContent: string | null; onCopy: (c: string) => void }) {
    const isCopied = copiedContent === cmd

    return (
        <div className="group relative">
            <div className="flex items-start gap-4">
                <span className="text-gray-600 select-none">{step}</span>
                <div className="flex-1">
                    <div className="flex items-center justify-between">
                        <span className="text-green-400 font-medium">
                            <span className="text-pink-500 mr-2">$</span>
                            {cmd}
                        </span>
                        <button
                            onClick={() => onCopy(cmd)}
                            className="p-1.5 rounded-md hover:bg-white/10 text-gray-500 hover:text-gray-300 transition-colors opacity-0 group-hover:opacity-100"
                            title="Copy to clipboard"
                        >
                            <DocumentDuplicateIcon className="w-4 h-4" />
                        </button>
                    </div>
                    {desc && <p className="text-gray-500 mt-1 text-xs">{desc}</p>}
                </div>
            </div>
            {isCopied && (
                <span className="absolute right-8 top-1 text-[10px] text-green-400 bg-green-400/10 px-2 py-0.5 rounded">
                    Copied!
                </span>
            )}
        </div>
    )
} 
