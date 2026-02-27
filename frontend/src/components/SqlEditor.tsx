import Editor, { useMonaco } from "@monaco-editor/react"
import { useEffect } from "react"

interface SqlEditorProps {
    value: string
    onChange: (value: string | undefined) => void
    readOnly?: boolean
    language?: string
    height?: string
}

export function SqlEditor({
    value,
    onChange,
    readOnly = false,
    language = "sql",
    height = "280px",
}: SqlEditorProps) {
    const monaco = useMonaco()

    useEffect(() => {
        if (monaco) {
            monaco.editor.defineTheme("custom-dark", {
                base: "vs-dark",
                inherit: true,
                rules: [],
                colors: {
                    "editor.background": "#09090b",
                    "editor.lineHighlightBackground": "#18181b",
                    "editor.foreground": "#e4e4e7",
                },
            })
            monaco.editor.setTheme("custom-dark")
        }
    }, [monaco])

    return (
        <div style={{ height }} className="w-full border border-white/10 rounded-lg overflow-hidden bg-black/50">
            <Editor
                height={height}
                language={language}
                value={value}
                onChange={onChange}
                options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    scrollBeyondLastLine: false,
                    readOnly,
                    fontFamily: "Geist Mono, JetBrains Mono, Consolas, monospace",
                    padding: { top: 12 },
                    wordWrap: "off",
                    // automaticLayout intentionally OFF — causes ResizeObserver loop & scroll lag
                    automaticLayout: false,
                    overviewRulerLanes: 0,
                    renderLineHighlight: "line",
                    scrollbar: {
                        vertical: "auto",
                        horizontal: "auto",
                        useShadows: false,
                        verticalScrollbarSize: 6,
                        horizontalScrollbarSize: 6,
                    },
                }}
                theme="custom-dark"
            />
        </div>
    )
}
