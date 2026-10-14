/** Build-time API origin. Production never invents localhost or uses an unset value. */

const LOCAL_DEV_API = "http://localhost:8000"

export function resolveApiBaseUrl(raw: string | undefined, mode: string): string | null {
    const trimmed = (raw ?? "").trim().replace(/\/+$/, "")
    if (trimmed) return trimmed
    if (mode === "development" || mode === "test") return LOCAL_DEV_API
    return null
}

export function apiUrl(base: string, path: string): string {
    const suffix = path.startsWith("/") ? path : `/${path}`
    return `${base}${suffix}`
}
