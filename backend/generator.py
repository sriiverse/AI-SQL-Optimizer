from models import TextToSqlResponse
import os
import re
import google.generativeai as genai

async def generate_sql_with_gemini(schema: str, question: str, dialect: str, model: genai.GenerativeModel) -> TextToSqlResponse:
    """
    Uses a pre-initialized Google Gemini model to generate SQL/MongoDB from natural language + schema.
    Runs asynchronously to avoid blocking the FastAPI event loop.
    """
    if dialect == "mongodb":
        prompt = f"""
You are a world-class MongoDB Aggregation Pipeline Engineer with deep expertise in MongoDB 5.0+ features.

Context (Collection Schema / Sample Documents):
{schema}

Question: {question}

## CRITICAL RULES — YOU MUST FOLLOW ALL OF THEM:

### Completeness
1. You MUST address EVERY requirement stated in the question. Never silently omit a lookup, calculation, or filter.
2. If the question asks for N things, your pipeline must produce all N things. Skipping even one is unacceptable.

### Operator Correctness
3. `$graphLookup` is a PIPELINE STAGE ONLY. NEVER place it inside `$map`, `$addFields`, `$project`, or any expression context. It will throw a runtime error. To traverse relationships, wrap `$graphLookup` inside a `$lookup` sub-pipeline.
4. Use `$lookup` with `let` + `pipeline` syntax for all correlated joins — NOT simple `localField`/`foreignField` when filtering is needed inside the sub-query.
5. Use `$setWindowFields` for ALL rolling/cumulative calculations (running totals, moving averages, rolling stddev). Requires MongoDB 5.0+.
6. For cumulative running totals always use: `window: {{ documents: ["unbounded", "current"] }}`.
7. For log-return volatility or stddev: use `$stdDevPop` inside `$setWindowFields` with a range window.

### Self-Referencing Hierarchies
8. To walk a self-referencing collection (e.g. parent_id → id), use `$graphLookup` as a top-level stage. Set `maxDepth` appropriately. Always include `depthField` for ordering the path.

### Multiple Collections
9. If the question references data from multiple collections, you MUST include a `$lookup` stage for EACH collection. Never assume data is already present in the root document.

### Computed Fields on Related Documents (CRITICAL)
10. If you need to filter or flag ancestor/related documents using a computed value (e.g. filtering ancestors by a calculated accuracy score), you MUST re-compute that value INSIDE the sub-pipeline or $lookup for those related documents. NEVER reference a computed field that only exists on the root document and assume it is available on joined/ancestor documents. Always compute independently per related document.

### Date Filters Inside Nested Arrays
11. When filtering embedded array elements by a date condition (e.g. audits in the last 12 months, events in the last 30 days), you MUST apply the date $match INSIDE the array element filter — not just on top-level fields. Use `$filter` on the array with BOTH a date condition AND the logic condition combined in a `$and`. Example: to find failed audits in the last 12 months, filter `audit_history` where `audited_at >= 12 months ago AND passed == false`.

### Flag Projection — Never Leave Flags Unprojected
12. Every flag computed from joined/looked-up data (e.g. reliability_score < 60, compliance_score < 70, score < threshold) MUST be explicitly included in the final `$project` stage or inside the relevant sub-document output. Never compute a flag inside a `$lookup` sub-pipeline and then fail to surface it in the final output.

### Array Count Conditions (e.g. "more than N elements matching X")
13. To identify documents where a sub-array has more than N elements matching a condition, you MUST:
    Step A — Use `$addFields` with `$filter` to materialise the matching sub-array into a new field.
    Step B — Use `$size` on that filtered field.
    Step C — Use `$match` on the computed size field.
    NEVER count inline without materialising the filtered array first into an `$addFields` stage.

### Operator / Actor — Event Correlation
14. If the question asks to correlate an actor (operator, user, trader) with events they performed (e.g. "flag operators who handled more damaged/expired events"), you MUST add a `$lookup` from the actors array/collection into the events collection, grouping by actor_id AND event_type, then join that result back. Never skip this correlation — do not just project the actor list without event data.

### Time-Window Metrics
15. When computing time-series metrics for a specific window (last 8 weeks, last 30 days, etc.), you MUST add a `$match` stage at the START of the relevant pipeline or sub-pipeline to restrict documents to only that time window BEFORE any `$group` or `$setWindowFields`. Never group across all time and assume the window is implied.

### Requirement Checklist Before Output
Before writing the pipeline, mentally verify:
- [ ] All required collections are looked up
- [ ] All grouping/aggregation calculations are present
- [ ] All filtering conditions are applied (including date ranges inside nested arrays)
- [ ] All sorting requirements are met
- [ ] All flag fields are projected in the final output
- [ ] No `$graphLookup` appears inside an expression (only as a pipeline stage)
- [ ] Computed fields on ancestors/related docs are re-computed inside their own sub-pipeline
- [ ] Time-series stages begin with a time-restricting $match
- [ ] Operator/actor-event correlations have an explicit $lookup to the events collection

## Output Format (plain text, no markdown backticks):
QUERY: <the complete MongoDB aggregation pipeline starting with db.collection.aggregate([...])>
Explanation: <step-by-step explanation of each pipeline stage and design decisions>
"""
    else:
        prompt = f"""
You are an expert {dialect} SQL Engineer with deep knowledge of query optimization and advanced SQL features.

Context (Database Schema):
{schema}

Question: {question}

## CRITICAL RULES — YOU MUST FOLLOW ALL OF THEM:

### Completeness
1. You MUST address EVERY part of the question. If the question asks for N things, your query must return all N things.
2. Never silently omit a JOIN, subquery, filter, or calculation. Skipping any requirement is unacceptable.

### Query Design
3. Use CTEs (WITH clauses) for any multi-step logic to improve readability and maintainability.
4. Use window functions (ROW_NUMBER, RANK, LAG, LEAD, SUM OVER, AVG OVER) where appropriate instead of correlated subqueries.
5. Always apply WHERE/HAVING filters that are explicitly or implicitly required by the question.
6. Use proper {dialect}-specific syntax only. Do not mix dialects.

### Correctness
7. Never SELECT columns that don't exist in the schema.
8. Ensure all JOINs use correct columns and produce the expected cardinality.
9. If the question involves ranking or top-N per group, use window functions, not subqueries where possible.

## Output Format (plain text, no markdown backticks):
SQL: <the complete {dialect} query>
Explanation: <step-by-step explanation of the query logic and design decisions>
"""

    try:
        response = await model.generate_content_async(prompt)
        text = response.text.strip()

        query_part = ""
        exp_part = ""

        lines = text.split('\n')
        current_section = None

        for line in lines:
            stripped = line.strip().lower()
            # Accept both QUERY: (MongoDB) and SQL: (relational) prefixes
            if stripped.startswith("query:") or stripped.startswith("sql:") or stripped.startswith("mongodb:"):
                current_section = "query"
                query_part += line.split(":", 1)[1].strip() + "\n"
                continue
            elif stripped.startswith("explanation:"):
                current_section = "exp"
                exp_part += line.split(":", 1)[1].strip() + " "
                continue

            if current_section == "query":
                query_part += line + "\n"
            elif current_section == "exp":
                exp_part += line + " "

        # Fallback 1: try to extract from a code fence block
        if not query_part.strip():
            code_fence_match = re.search(r'```(?:js|javascript|sql|mongodb)?\n(.*?)```', text, re.DOTALL | re.IGNORECASE)
            if code_fence_match:
                query_part = code_fence_match.group(1).strip()
                exp_part = "Generated based on your question and schema."

        # Fallback 2: use the full response if it looks like a query
        if not query_part.strip():
            query_indicators = ["select", "db.", "aggregate", "with ", "insert", "update", "delete"]
            if any(indicator in text.lower() for indicator in query_indicators):
                query_part = text
                exp_part = "Generated based on your question."
            else:
                # True fallback to demo
                if dialect == "mongodb":
                    return generate_mongodb_demo(schema, question)
                else:
                    return generate_sql_demo(schema, question)

        # Clean up any stray backticks
        query_part = re.sub(r'```(?:js|javascript|sql|mongodb)?', '', query_part)
        query_part = query_part.replace('```', '').strip()

        return TextToSqlResponse(
            query=query_part,
            explanation=exp_part.strip() or "Query generated successfully."
        )

    except Exception as e:
        print(f"Gemini Error: {e}")
        return TextToSqlResponse(
            query="ERROR",
            explanation=f"AI Generation Failed: {str(e)}"
        )


def _extract_first_collection(schema: str) -> str:
    """
    Attempts to extract the first collection/table name from a schema string.
    Works for both JSON sample schemas and SQL DDL.
    """
    # Look for db.<collection> pattern
    mongo_match = re.search(r'//\s*[Cc]ollection:\s*(\w+)', schema)
    if mongo_match:
        return mongo_match.group(1)

    # Look for CREATE TABLE <name>
    sql_match = re.search(r'CREATE\s+TABLE\s+(\w+)', schema, re.IGNORECASE)
    if sql_match:
        return sql_match.group(1)

    return "collection"


def generate_sql_demo(schema: str, question: str) -> TextToSqlResponse:
    """
    Fallback SQL demo — pattern-matches intent and returns a realistic query.
    Note: AI was unavailable; this is a demonstration query only.
    """
    q = question.lower()
    table = _extract_first_collection(schema)

    if "sales" in q or "revenue" in q:
        generated_sql = f"SELECT SUM(amount) AS total_revenue FROM {table} WHERE date > NOW() - INTERVAL '30 days';"
        explanation = f"[Demo Mode — AI unavailable] Aggregated revenue from '{table}' for the last 30 days."

    elif "join" in q or "orders" in q:
        generated_sql = f"""SELECT u.name, COUNT(o.id) AS order_count
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY u.name
ORDER BY order_count DESC;"""
        explanation = "[Demo Mode — AI unavailable] Joined users and orders to count orders per user."

    elif "analytics" in q or "performance" in q:
        generated_sql = f"""WITH Stats AS (
    SELECT
        region,
        category,
        SUM(amount)      AS total_revenue,
        AVG(latency_ms)  AS avg_latency
    FROM {table}
    WHERE created_at >= NOW() - INTERVAL '24 hours'
    GROUP BY region, category
)
SELECT * FROM Stats
WHERE total_revenue > 10000
ORDER BY avg_latency ASC;"""
        explanation = "[Demo Mode — AI unavailable] CTE aggregating revenue and latency by region and category."

    else:
        generated_sql = f"SELECT * FROM {table} LIMIT 100;"
        explanation = f"[Demo Mode — AI unavailable] Basic query against '{table}'. Provide your schema and question to get an AI-generated query."

    return TextToSqlResponse(query=generated_sql.strip(), explanation=explanation)


def generate_mongodb_demo(schema: str, question: str) -> TextToSqlResponse:
    """
    Fallback MongoDB demo — pattern-matches intent and returns a realistic pipeline.
    Uses the actual collection name extracted from the schema where possible.
    Note: AI was unavailable; this is a demonstration pipeline only.
    """
    q = question.lower()
    collection = _extract_first_collection(schema)

    if any(k in q for k in ["last", "recent", "today", "week", "month", "days"]):
        pipeline = f'''db.{collection}.aggregate([
  // Step 1: Filter to recent documents (leverages date index)
  {{ $match: {{
      created_at: {{ $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }}
  }}}},
  // Step 2: Group and aggregate
  {{ $group: {{
      _id: "$category",
      total: {{ $sum: "$amount" }},
      count: {{ $sum: 1 }}
  }}}},
  // Step 3: Sort descending
  {{ $sort: {{ total: -1 }} }},
  {{ $limit: 10 }}
])'''
        explanation = f"[Demo Mode — AI unavailable] Filtered '{collection}' to last 30 days, grouped by category, sorted by total descending."

    elif any(k in q for k in ["join", "lookup", "related", "belongs"]):
        pipeline = f'''db.{collection}.aggregate([
  {{ $match: {{ status: "active" }} }},
  {{ $lookup: {{
      from: "related_collection",
      let: {{ ref_id: "$_id" }},
      pipeline: [
        {{ $match: {{ $expr: {{ $eq: ["$parent_id", "$$ref_id"] }} }} }},
        {{ $sort: {{ created_at: -1 }} }},
        {{ $limit: 5 }}
      ],
      as: "related_docs"
  }}}},
  {{ $match: {{ "related_docs.0": {{ $exists: true }} }} }},
  {{ $project: {{ name: 1, status: 1, related_docs: 1 }} }}
])'''
        explanation = f"[Demo Mode — AI unavailable] Looked up related documents for active '{collection}' records using correlated $lookup sub-pipeline."

    elif any(k in q for k in ["group", "count", "sum", "average", "avg", "total"]):
        pipeline = f'''db.{collection}.aggregate([
  {{ $match: {{ created_at: {{ $gte: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000) }} }} }},
  {{ $group: {{
      _id: "$category",
      avg_value:   {{ $avg: "$value" }},
      total_count: {{ $sum: 1 }},
      total_sum:   {{ $sum: "$amount" }}
  }}}},
  {{ $match: {{ total_count: {{ $gte: 5 }} }} }},
  {{ $sort: {{ total_sum: -1 }} }}
])'''
        explanation = f"[Demo Mode — AI unavailable] Grouped '{collection}' by category, computed averages and sums, filtered groups with fewer than 5 documents."

    elif any(k in q for k in ["top", "best", "highest", "most", "rank"]):
        pipeline = f'''db.{collection}.aggregate([
  {{ $match: {{ created_at: {{ $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) }} }} }},
  {{ $group: {{
      _id: "$item_id",
      interaction_count: {{ $sum: 1 }},
      unique_users: {{ $addToSet: "$user_id" }}
  }}}},
  {{ $addFields: {{ unique_user_count: {{ $size: "$unique_users" }} }} }},
  {{ $sort: {{ interaction_count: -1 }} }},
  {{ $limit: 10 }}
])'''
        explanation = f"[Demo Mode — AI unavailable] Top 10 items from '{collection}' in the last 7 days ranked by interaction count with unique user deduplication."

    else:
        pipeline = f'''db.{collection}.aggregate([
  {{ $match: {{ status: "active" }} }},
  {{ $project: {{ _id: 0, name: 1, status: 1, created_at: 1 }} }},
  {{ $limit: 100 }}
])'''
        explanation = f"[Demo Mode — AI unavailable] Basic query on '{collection}'. Provide your full schema and question to receive an AI-generated pipeline."

    return TextToSqlResponse(query=pipeline.strip(), explanation=explanation)
