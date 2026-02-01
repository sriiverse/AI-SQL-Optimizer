import Editor, { useMonaco } from "@monaco-editor/react"
import { useEffect } from "react"

interface SqlEditorProps {
    value: string
    onChange: (value: string | undefined) => void
    readOnly?: boolean
}

export function SqlEditor({ value, onChange, readOnly = false }: SqlEditorProps) {
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
                },
            })
            monaco.editor.setTheme("custom-dark")
        }
    }, [monaco])

    return (
        <div className="h-full w-full border border-white/10 rounded-lg overflow-hidden bg-black/50">
            <Editor
                height="100%"
                defaultLanguage="sql"
                value={value}
                onChange={onChange}
                options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    scrollBeyondLastLine: false,
                    readOnly: readOnly,
                    fontFamily: "Geist Mono, JetBrains Mono, monospace",
                    padding: { top: 16 },
                }}
                theme="custom-dark"
            />
        </div>
    )
}
