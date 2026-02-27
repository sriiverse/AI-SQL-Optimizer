import Editor, { useMonaco } from "@monaco-editor/react"
import { useEffect } from "react"

interface SqlEditorProps {
    value: string
    onChange: (value: string | undefined) => void
    readOnly?: boolean
    language?: string   // "sql" | "javascript" | "json" — drives syntax highlighting
}

export function SqlEditor({ value, onChange, readOnly = false, language = "sql" }: SqlEditorProps) {
    const monaco = useMonaco()

    useEffect(() => {
        if (monaco) {
            monaco.editor.defineTheme("custom-dark", {
                base: "vs-dark",
                inherit: true,
                rules: [],
                colors: {
                    "editor.background": "#09090b", // zinc-950
                    "editor.lineHighlightBackground": "#18181b",
                    "editor.foreground": "#e4e4e7",   // ensure text always visible
                },
            })
            monaco.editor.setTheme("custom-dark")
        }
    }, [monaco])

    return (
        <div className="h-full w-full border border-white/10 rounded-lg overflow-hidden bg-black/50">
            <Editor
                height="100%"
                language={language}
                value={value}
                onChange={onChange}
                options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    scrollBeyondLastLine: false,
                    readOnly: readOnly,
                    fontFamily: "Geist Mono, JetBrains Mono, monospace",
                    padding: { top: 16 },
                    wordWrap: "off",
                    automaticLayout: true,
                }}
                theme="custom-dark"
            />
        </div>
    )
}
