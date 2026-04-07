import { useMemo } from 'react'

interface ExplainTreeNode {
  id: string | number
  name: string
  detail: string
  children: ExplainTreeNode[]
}

interface ExplainTreeProps {
  explain_plan: any
  dialect: string
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

function convertSqliteToTree(flatNodes: any[]): ExplainTreeNode | null {
  if (!Array.isArray(flatNodes) || flatNodes.length === 0) return null

  // Create a map of id to node
  const nodeMap: Map<string | number, ExplainTreeNode> = new Map()

  // First pass: create all nodes
  flatNodes.forEach((node: any) => {
    const treeNode: ExplainTreeNode = {
      id: node.id,
      name: extractNameFromDetail(node.detail),
      detail: node.detail,
      children: []
    }
    nodeMap.set(node.id, treeNode)
  })

  // Second pass: assign children
  let root: ExplainTreeNode | null = null
  flatNodes.forEach((node: any) => {
    const treeNode = nodeMap.get(node.id)
    if (!treeNode) return

    if (node.parent === 0 || !nodeMap.has(node.parent)) {
      // This is a root node
      root = treeNode
    } else {
      const parentNode = nodeMap.get(node.parent)
      if (parentNode) {
        parentNode.children.push(treeNode)
      }
    }
  })

  // If we didn't find a root, return the first node as fallback
  if (!root && flatNodes.length > 0) {
    return nodeMap.get(flatNodes[0].id) || null
  }

  return root
}

function convertPostgreSQLToTree(plan: any): ExplainTreeNode | null {
  if (!plan) return null

  const buildNode = (p: any): ExplainTreeNode => {
    const nodeType = p['Node Type'] || p.node_type || 'Unknown'
    const alias = p.Alias ? ` (${p.Alias})` : ''
    const name = `${nodeType}${alias}`

    let detail = ''
    if (p['Startup Cost'] !== undefined && p['Total Cost'] !== undefined) {
      detail += `Cost: ${p['Startup Cost']}..${p['Total Cost']}`
    }
    if (p['Plan Rows'] !== undefined) {
      detail += `, Rows: ${p['Plan Rows']}`
    }
    if (p['Plan Width'] !== undefined) {
      detail += `, Width: ${p['Plan Width']}`
    }
    if (p['Filter']) {
      detail += `, Filter: ${p['Filter']}`
    }

    const children: ExplainTreeNode[] = []
    if (p.Plans && Array.isArray(p.Plans)) {
      p.Plans.forEach((subplan: any) => {
        const child = buildNode(subplan)
        if (child) children.push(child)
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
  const match = detail.match(/^([^\(]+)/)
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
