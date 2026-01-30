import { motion } from "framer-motion"
import { useNavigate } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Zap, Code2 } from "lucide-react"

export default function LandingPage() {
    const navigate = useNavigate()

    return (
        <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-[#030014] selection:bg-purple-500/30">

            {/* 1. Background Layers */}

            {/* Stars/Noise Texture */}
            <div className="absolute inset-0 z-0 opacity-20 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] brightness-100 contrast-150 mix-blend-overlay"></div>

            {/* Main Glow Orbs */}
            <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-purple-600/20 blur-[100px] mix-blend-screen animate-pulse"></div>
            <div className="absolute top-[20%] right-[-10%] w-[600px] h-[600px] rounded-full bg-indigo-600/20 blur-[120px] mix-blend-screen opacity-50"></div>
            <div className="absolute bottom-[-20%] left-[20%] w-[500px] h-[500px] rounded-full bg-blue-600/20 blur-[100px] mix-blend-screen"></div>

            {/* Tech Grid */}
            <div className="absolute inset-0 z-0 bg-grid-white/[0.02] bg-[size:50px_50px]"></div>

            {/* Circuit Lines (Decorative) */}
            <svg className="absolute top-0 left-0 w-full h-full z-0 opacity-20 pointer-events-none" xmlns="http://www.w3.org/2000/svg">
                <path d="M0 100 Q 250 50 500 100 T 1000 100" fill="none" stroke="url(#circuit-grad)" strokeWidth="2" />
                <defs>
                    <linearGradient id="circuit-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="transparent" />
                        <stop offset="50%" stopColor="#6366f1" />
                        <stop offset="100%" stopColor="transparent" />
                    </linearGradient>
                </defs>
            </svg>

            {/* Contact Info (Top Right) */}
            <div className="absolute top-6 right-6 z-50 flex gap-4">
                <motion.a
                    href="mailto:sudhanshutheking183@gmail.com"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-3 bg-white/5 backdrop-blur-md rounded-full border border-white/10 hover:bg-white/10 hover:border-red-500/50 hover:shadow-[0_0_20px_rgba(239,68,68,0.3)] transition-all group"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-400 group-hover:text-red-400 shadow-sm"><rect width="20" height="16" x="2" y="4" rx="2" /><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" /></svg>
                </motion.a>

                <motion.a
                    href="https://www.linkedin.com/in/sudhanshu-sinha-4619a429a/"
                    target="_blank"
                    rel="noreferrer"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-3 bg-white/5 backdrop-blur-md rounded-full border border-white/10 hover:bg-white/10 hover:border-blue-500/50 hover:shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all group"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-400 group-hover:text-blue-400 shadow-sm"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" /><rect width="4" height="12" x="2" y="9" /><circle cx="4" cy="4" r="2" /></svg>
                </motion.a>
            </div>

            {/* Main Content Area */}
            <div className="relative z-10 flex flex-col items-center justify-center w-full max-w-6xl px-4 mt-[-50px]">

                {/* Badge */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="mb-8"
                >
                    <span className="px-4 py-1.5 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-300 text-[10px] md:text-xs font-mono tracking-[0.2em] uppercase shadow-[0_0_15px_rgba(168,85,247,0.2)]">
                        AI Powered Database Engineering
                    </span>
                </motion.div>

                {/* Heading */}
                <motion.h1
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.8, delay: 0.1 }}
                    className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight text-center mb-6 leading-tight"
                >
                    <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-300 via-indigo-300 to-purple-300 drop-shadow-[0_0_25px_rgba(99,102,241,0.3)]">
                        Optimize SQL Queries
                    </span>
                    <br />
                    <span className="text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">
                        at the Speed of Thought
                    </span>
                </motion.h1>

                {/* Subheading */}
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.8, delay: 0.3 }}
                    className="text-lg md:text-xl text-indigo-200/60 text-center max-w-3xl mb-12 leading-relaxed"
                >
                    Leverage advanced AI to dissect execution plans, identify bottlenecks,
                    and rewrite inefficient queries instantly.
                </motion.p>

                {/* Floating Code Card Visual */}
                <div className="relative w-full max-w-3xl mb-12 group perspective-1000">

                    {/* Glow beneath card */}
                    <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-blue-500 blur-[80px] opacity-20 group-hover:opacity-30 transition-opacity duration-500"></div>

                    <motion.div
                        initial={{ opacity: 0, y: 40, rotateX: 20 }}
                        animate={{ opacity: 1, y: 0, rotateX: 0 }}
                        transition={{ duration: 1, delay: 0.4, type: "spring" }}
                        className="relative bg-[#0a0a0b]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl overflow-hidden ring-1 ring-white/10"
                    >
                        {/* Window Controls */}
                        <div className="flex items-center gap-2 mb-4">
                            <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50"></div>
                            <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50"></div>
                            <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50"></div>
                            <div className="ml-auto text-xs text-white/20 font-mono">query_optimizer.sql</div>
                        </div>

                        {/* Mock Code */}
                        <div className="font-mono text-sm leading-relaxed text-gray-400">
                            <p><span className="text-purple-400">SELECT</span> * <span className="text-purple-400">FROM</span> large_transactions t</p>
                            <p><span className="text-purple-400">JOIN</span> users u <span className="text-purple-400">ON</span> u.id = t.user_id</p>
                            <p><span className="text-purple-400">WHERE</span> t.amount {">"} <span className="text-orange-400">10000</span></p>
                            <p><span className="text-purple-400">ORDER BY</span> t.created_at <span className="text-purple-400">DESC</span>;</p>
                        </div>

                        {/* Scan Line Animation */}
                        <motion.div
                            className="absolute top-0 left-0 right-0 h-[100px] bg-gradient-to-b from-transparent via-indigo-500/10 to-transparent z-10 pointer-events-none"
                            animate={{ top: ["-20%", "120%"] }}
                            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                        />
                    </motion.div>

                    {/* Back Stacked Cards for Depth */}
                    <div className="absolute inset-0 bg-white/5 rounded-2xl transform translate-y-4 scale-[0.95] -z-10 blur-[1px]"></div>
                    <div className="absolute inset-0 bg-white/5 rounded-2xl transform translate-y-8 scale-[0.9] -z-20 blur-[2px]"></div>
                </div>

                {/* Buttons */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.6 }}
                    className="flex flex-col sm:flex-row gap-6 relative z-30"
                >
                    <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                        <Button
                            className="bg-transparent border border-transparent shadow-[0_0_50px_rgba(168,85,247,0.4)] relative group overflow-hidden px-8 py-6 rounded-xl"
                            onClick={() => navigate("/optimizer")}
                        >
                            {/* Custom Gradient Button Background */}
                            <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 opacity-80 group-hover:opacity-100 transition-opacity"></div>
                            <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>

                            <div className="relative flex items-center gap-2 text-white font-semibold text-lg tracking-wide">
                                <Zap className="w-5 h-5 fill-white" /> Start Optimizing
                            </div>
                        </Button>
                    </motion.div>

                    <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                        <Button
                            className="bg-white/5 border border-white/10 hover:bg-white/10 px-8 py-6 rounded-xl backdrop-blur-md"
                            onClick={() => navigate("/generator")}
                        >
                            <div className="flex items-center gap-2 text-gray-200 font-medium text-lg tracking-wide">
                                <Code2 className="w-5 h-5 opacity-70" /> Text-to-SQL
                            </div>
                        </Button>
                    </motion.div>
                </motion.div>

            </div>

            {/* Footer Credit (Bottom Left) */}
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, delay: 1 }}
                className="absolute bottom-8 left-8 z-50 flex items-center gap-3"
            >
                <div className="h-[1px] w-12 bg-gradient-to-r from-transparent to-indigo-500"></div>
                <span className="text-[10px] md:text-xs font-mono text-indigo-300/40 uppercase tracking-[0.2em] hover:text-indigo-300 transition-colors cursor-default">
                    Part of <span className="text-white font-bold glow-text">SRIIVERSEAI</span>
                </span>
                <span className="text-[10px] md:text-xs font-mono text-indigo-300/40 uppercase tracking-[0.2em]">
                    | Built by <span className="text-white font-bold">Sudhanshu Sinha</span>
                </span>
            </motion.div>

        </div>
    )
}
