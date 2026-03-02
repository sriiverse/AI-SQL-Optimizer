import { motion } from "framer-motion"
import type { Variants } from "framer-motion"
import { useNavigate } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Zap, Code2, Mail, Linkedin } from "lucide-react"

export default function LandingPage() {
    const navigate = useNavigate()

    // Animation Variants
    const containerVariants: Variants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.15, delayChildren: 0.2 }
        }
    }

    const itemVariants: Variants = {
        hidden: { opacity: 0, y: 20 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { type: "spring", stiffness: 100, damping: 20 }
        }
    }

    return (
        // The container needs a very dark indigo base
        <div className="relative h-[100dvh] flex flex-col items-center justify-center overflow-hidden bg-[#020014] selection:bg-purple-500/30 font-sans text-white">

            {/* ─── 1. Background Layers (Hyper-Space / Cyber-Grid) ─── */}
            <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">

                {/* Deep Background Glow */}
                <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-blue-700/20 blur-[130px] rounded-full"></div>
                <div className="absolute bottom-[20%] left-1/2 -translate-x-1/2 w-[600px] h-[500px] bg-purple-700/20 blur-[150px] rounded-full"></div>

                {/* ─── Animated SVG Cyber Circuit Lines ─── */}
                <div className="circuit-container opacity-80">
                    <svg viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice" className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <linearGradient id="neonGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" style={{ stopColor: '#00f7ff', stopOpacity: 1 }} />
                                <stop offset="100%" style={{ stopColor: '#bd00ff', stopOpacity: 1 }} />
                            </linearGradient>
                        </defs>

                        {/* Top Left Flow */}
                        <g className="circuit-line flow-fast">
                            <path className="base-wire" d="M 0 300 L 300 300 L 400 400 L 700 400" />
                            <path className="current-flow flow-fast" d="M 0 300 L 300 300 L 400 400 L 700 400" />
                        </g>

                        {/* Middle Left Flow */}
                        <g className="circuit-line flow-slow flow-delay-1">
                            <path className="base-wire" d="M 0 600 L 200 600 L 350 450 L 600 450" />
                            <path className="current-flow flow-slow flow-delay-1" d="M 0 600 L 200 600 L 350 450 L 600 450" />
                        </g>

                        {/* Bottom Left Flow */}
                        <g className="circuit-line flow-delay-2">
                            <path className="base-wire" d="M 0 900 L 400 900 L 550 750 L 800 750" />
                            <path className="current-flow flow-delay-2" d="M 0 900 L 400 900 L 550 750 L 800 750" />
                        </g>

                        {/* Top Right Flow */}
                        <g className="circuit-line flow-slow flow-delay-2">
                            <path className="base-wire" d="M 1920 250 L 1600 250 L 1450 400 L 1100 400" />
                            <path className="current-flow flow-slow flow-delay-2" d="M 1920 250 L 1600 250 L 1450 400 L 1100 400" />
                        </g>

                        {/* Middle Right Flow */}
                        <g className="circuit-line flow-fast">
                            <path className="base-wire" d="M 1920 550 L 1700 550 L 1600 450 L 1300 450" />
                            <path className="current-flow flow-fast" d="M 1920 550 L 1700 550 L 1600 450 L 1300 450" />
                        </g>

                        {/* Bottom Right Flow */}
                        <g className="circuit-line flow-delay-1">
                            <path className="base-wire" d="M 1920 850 L 1500 850 L 1350 700 L 1000 700" />
                            <path className="current-flow flow-delay-1" d="M 1920 850 L 1500 850 L 1350 700 L 1000 700" />
                        </g>

                        {/* Top Down Left */}
                        <g className="circuit-line flow-fast flow-delay-1">
                            <path className="base-wire" d="M 500 0 L 500 150 L 600 250 L 600 600" />
                            <path className="current-flow flow-fast flow-delay-1" d="M 500 0 L 500 150 L 600 250 L 600 600" />
                        </g>

                        {/* Top Down Right */}
                        <g className="circuit-line flow-slow">
                            <path className="base-wire" d="M 1400 0 L 1400 200 L 1300 300 L 1300 750" />
                            <path className="current-flow flow-slow" d="M 1400 0 L 1400 200 L 1300 300 L 1300 750" />
                        </g>
                    </svg>
                </div>

                {/* Subtle Grid overlay for texture */}
                <div className="absolute inset-0 z-0 bg-grid-white/[0.02] bg-[size:50px_50px]"></div>
            </div>

            {/* ─── Contact Info (Top Right) ─── */}
            <div className="absolute top-6 right-6 z-50 flex gap-4">
                <motion.a
                    href="mailto:sudhanshutheking183@gmail.com"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-3 bg-white/5 backdrop-blur-md rounded-full border border-white/10 hover:bg-white/10 transition-colors flex items-center justify-center"
                >
                    <Mail className="w-5 h-5 text-gray-400 hover:text-white transition-colors" />
                </motion.a>
                <motion.a
                    href="https://www.linkedin.com/in/sudhanshu-sinha-4619a429a/"
                    target="_blank"
                    rel="noreferrer"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-3 bg-white/5 backdrop-blur-md rounded-full border border-white/10 hover:bg-white/10 transition-colors flex items-center justify-center"
                >
                    <Linkedin className="w-5 h-5 text-gray-400 hover:text-white transition-colors" />
                </motion.a>
            </div>

            {/* ─── Main Content Area ─── */}
            <div className="relative z-10 flex flex-col items-center justify-center w-full max-w-5xl px-4 mt-[-60px]">

                {/* Heading */}
                <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="text-center mb-4"
                >
                    <motion.h1
                        variants={itemVariants}
                        className="text-[3rem] md:text-[4rem] lg:text-[5.5rem] font-extrabold tracking-tight leading-[1.05] drop-shadow-2xl"
                    >
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#5eead4] via-[#60a5fa] to-[#c084fc] drop-shadow-[0_0_30px_rgba(96,165,250,0.4)]">
                            Optimize Database
                        </span>
                        <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c084fc] to-[#e879f9] drop-shadow-[0_0_30px_rgba(192,132,252,0.4)] block mt-1">
                            Queries
                        </span>
                    </motion.h1>

                    <motion.h2 variants={itemVariants} className="text-[2rem] md:text-[2.75rem] lg:text-[3.5rem] font-extrabold tracking-tight mt-[-5px]">
                        <span className="text-white drop-shadow-[0_0_20px_rgba(255,255,255,0.3)]">
                            at the Speed of Thought
                        </span>
                    </motion.h2>
                </motion.div>

                {/* Subheading */}
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 1, delay: 0.5 }}
                    className="text-[1rem] md:text-[1.1rem] text-gray-300 text-center max-w-2xl mb-8 font-medium tracking-wide drop-shadow-md"
                >
                    Leverage advanced AI to dissect execution plans, identify bottlenecks, and rewrite inefficient queries instantly.
                </motion.p>

                {/* ─── Neon Code Card ─── */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 1, delay: 0.7, type: "spring", stiffness: 100 }}
                    className="relative w-full max-w-[750px] mb-10"
                >
                    {/* Massive Glowing Shadow behind the exact border gradient */}
                    <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-[#06b6d4] via-[#4f46e5] to-[#ec4899] opacity-60 blur-2xl"></div>

                    {/* The Neon Border Wrapper */}
                    <div className="relative rounded-2xl bg-gradient-to-r from-[#06b6d4] via-[#9333ea] to-[#ec4899] p-[3px] shadow-[0_0_15px_rgba(236,72,153,0.5)]">

                        {/* The Inner Black Card */}
                        <div className="relative bg-[#0b061d] rounded-[14px] overflow-hidden h-full w-full">

                            {/* Editor Header */}
                            <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#120a2e]/50">
                                <div className="flex gap-2">
                                    <div className="w-3 h-3 rounded-full bg-[#ef4444] shadow-[0_0_5px_rgba(239,68,68,0.5)]"></div>
                                    <div className="w-3 h-3 rounded-full bg-[#eab308] shadow-[0_0_5px_rgba(234,179,8,0.5)]"></div>
                                    <div className="w-3 h-3 rounded-full bg-[#22c55e] shadow-[0_0_5px_rgba(34,197,94,0.5)]"></div>
                                </div>
                                <div className="text-[11px] text-gray-500 font-mono tracking-widest uppercase">query_optimizer.sql</div>
                            </div>

                            {/* Code Area */}
                            <div className="p-6 font-mono text-[13px] sm:text-[14px] leading-[1.7] text-gray-300">
                                <p><span className="text-[#c084fc]">SELECT</span> * <span className="text-[#c084fc]">FROM</span> large_transactions t</p>
                                <p><span className="text-[#c084fc]">JOIN</span> users u <span className="text-[#c084fc]">ON</span> u.id = t.user_id</p>
                                <p><span className="text-[#c084fc]">WHERE</span> t.amount {">"} <span className="text-[#fca5a5]">10000</span></p>
                                <p><span className="text-[#c084fc]">ORDER BY</span> t.created_at <span className="text-[#c084fc]">DESC</span>;</p>
                            </div>

                            {/* Inner subtle glow */}
                            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-purple-900/10 pointer-events-none"></div>
                        </div>
                    </div>
                </motion.div>

                {/* ─── CTA Buttons ─── */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.9 }}
                    className="flex flex-col sm:flex-row gap-5 relative z-30"
                >
                    <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                        <Button
                            className="h-[54px] px-8 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-bold text-[16px] tracking-wide border border-white/10 hover:from-purple-500 hover:to-indigo-500 transition-all shadow-[0_0_30px_rgba(139,92,246,0.3)] flex items-center gap-3"
                            onClick={() => navigate("/optimizer")}
                        >
                            <Zap className="w-5 h-5 fill-white" /> Start Optimizing
                        </Button>
                    </motion.div>

                    <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                        <Button
                            className="h-[54px] px-8 rounded-2xl bg-[#120a2e]/60 border border-white/10 text-white font-semibold text-[16px] tracking-wide hover:bg-white/10 backdrop-blur-md transition-all flex items-center gap-3"
                            onClick={() => navigate("/generator")}
                        >
                            <Code2 className="w-5 h-5 opacity-80" /> Text-to-Query
                        </Button>
                    </motion.div>
                </motion.div>

            </div>

            {/* ─── Footer Credit (Bottom Left) ─── */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1, delay: 1.2 }}
                className="absolute bottom-8 left-8 z-50 flex items-center gap-3"
            >
                <div className="h-[1px] w-12 bg-gradient-to-r from-transparent to-[#00f7ff] shadow-[0_0_5px_#00f7ff]"></div>
                <span className="text-[10px] sm:text-[11px] font-mono text-gray-400 tracking-[0.2em]">
                    PART OF <span className="text-white font-bold ml-1 hover:text-[#00f7ff] transition-colors drop-shadow-[0_0_5px_rgba(0,247,255,0.5)]">SRIIVERSEAI</span>
                </span>
                <span className="w-[1px] h-3 bg-white/20 mx-1"></span>
                <span className="text-[10px] sm:text-[11px] font-mono text-gray-400 tracking-[0.2em]">
                    BUILT BY <span className="text-white font-bold ml-1">SUDHANSHU SINHA</span>
                </span>
            </motion.div>

        </div>
    )
} 
