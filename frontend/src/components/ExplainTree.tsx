import { useMemo } from 'react'

interface ExplainTreeNode {
  id: string | number
  name: string
  detail: string
  children: ExplainTreeNode[]
}

interface ExplainTreeProps {
  explain_plan: unknown
  dialect: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

export function ExplainTree({ explain_plan, dialect }: ExplainTreeProps) {
  const root = useMemo(() => {
    if (!explain_plan) return null

    if (dialect === 'sqlite') {
      return convertSqliteToTree(explain_plan)
    } else if (dialect === 'postgresql' || dialect === 'postgres') {
      return convertPostgreSQLToTree(explain_plan)
    } else if (dialect === 'mysql') {
      // For MySQL, we can treat similar to PostgreSQL for now
      return convertPostgreSQLToTree(explain_plan)
    } else {
      // For MongoDB or others, we don't have a tree yet
      return null
    }
  }, [explain_plan, dialect])

  if (!root) return null

  return (
    <div className="space-y-2">
      <ExplainTreeNode node={root} />
    </div>
  )
}

function planId(value: unknown): string | number | null {
  return typeof value === "string" || typeof value === "number" ? value : null
}

function convertSqliteToTree(flatNodes: unknown): ExplainTreeNode | null {
  if (!Array.isArray(flatNodes) || flatNodes.length === 0) return null

  // Create a map of id to node
  const nodeMap: Map<string | number, ExplainTreeNode> = new Map()
  const rows: { id: string | number; parent: unknown }[] = []

  // First pass: create all nodes
  flatNodes.forEach((item: unknown) => {
    if (!isRecord(item)) return
    const id = planId(item.id)
    if (id === null) return
    const detail = typeof item.detail === "string" ? item.detail : ""
    const treeNode: ExplainTreeNode = {
      id,
      name: extractNameFromDetail(detail),
      detail,
      children: []
    }
    nodeMap.set(id, treeNode)
    rows.push({ id, parent: item.parent })
  })

  // Second pass: assign children
  let root: ExplainTreeNode | null = null
  rows.forEach((node) => {
    const treeNode = nodeMap.get(node.id)
    if (!treeNode) return
    const parent = planId(node.parent)

    if (parent === null || parent === 0 || !nodeMap.has(parent)) {
      // This is a root node
      root = treeNode
    } else {
      const parentNode = nodeMap.get(parent)
      if (parentNode) {
        parentNode.children.push(treeNode)
      }
    }
  })

  // If we didn't find a root, return the first node as fallback
  if (!root && rows.length > 0) {
    return nodeMap.get(rows[0].id) || null
  }

  return root
}

function convertPostgreSQLToTree(plan: unknown): ExplainTreeNode | null {
  if (!isRecord(plan)) return null

  const buildNode = (p: Record<string, unknown>): ExplainTreeNode => {
    const labeledType = p['Node Type']
    const summaryType = p.node_type
    const nodeType = (typeof labeledType === "string" && labeledType)
      || (typeof summaryType === "string" && summaryType)
      || 'Unknown'
    const alias = typeof p.Alias === "string" && p.Alias ? ` (${p.Alias})` : ''
    const name = `${nodeType}${alias}`

    let detail = ''
    if (p['Startup Cost'] !== undefined && p['Total Cost'] !== undefined) {
      detail += `Cost: ${String(p['Startup Cost'])}..${String(p['Total Cost'])}`
    }
    if (p['Plan Rows'] !== undefined) {
      detail += `, Rows: ${String(p['Plan Rows'])}`
    }
    if (p['Plan Width'] !== undefined) {
      detail += `, Width: ${String(p['Plan Width'])}`
    }
    if (typeof p['Filter'] === "string" && p['Filter']) {
      detail += `, Filter: ${p['Filter']}`
    }

    const children: ExplainTreeNode[] = []
    if (Array.isArray(p.Plans)) {
      p.Plans.forEach((subplan: unknown) => {
        if (!isRecord(subplan)) return
        children.push(buildNode(subplan))
      })
    }

    return {
      id: Math.random().toString(36).substr(2, 9),
      name,
      detail,
      children
    }
  }

  return buildNode(plan)
}

function extractNameFromDetail(detail: string): string {
  // Extract the main operation from the detail string
  // Example: "Seq Scan on users  (cost=0.00..1.10 rows=100 width=4)"
  // We want: "Seq Scan on users"
  const match = detail.match(/^([^(]+)/)
  if (match) {
    return match[1].trim()
  }
  return detail.split('(')[0].trim() || 'Operation'
}

function ExplainTreeNode({ node }: { node: ExplainTreeNode }) {
  return (
    <div className="flex items-start gap-3 pl-2 pt-1">
      <div className="h-3 w-3 border-l-2 border-purple-500 pl-1 mt-0.5" />
      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2 text-sm font-medium">
          <span className="text-purple-400">{node.name}</span>
          <span className="text-gray-400">•</span>
          <span className="text-gray-500">{node.detail}</span>
        </div>
        {node.children.length > 0 && (
          <div className="pl-4 border-l-2 border-purple-500/30">
            {node.children.map((child, index) => (
              <ExplainTreeNode key={index} node={child} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
