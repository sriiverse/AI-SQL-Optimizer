from models import AnalysisResult, PlanNode, Suggestion
import random
import os
import json
import google.generativeai as genai

async def analyze_query_with_gemini(query: str, dialect: str, model: genai.GenerativeModel) -> AnalysisResult:
    """
    Uses a pre-initialized Google Gemini model to analyze the SQL query.
    Runs asynchronously to avoid blocking the FastAPI event loop.
    """
    if dialect == "mongodb":
        prompt = f"""
    You are an expert MongoDB Database Engineer. Analyze the following MongoDB query or aggregation pipeline for performance issues.

    Query / Pipeline: {query}

    Provide your analysis in the following JSON format ONLY:
    {{
        "execution_plan_summary": {{
            "node_type": "Primary operation (e.g., COLLSCAN, IXSCAN, $lookup, $group)",
            "cost": 123.45,
            "rows": 100,
            "relation_name": "Collection name involved"
        }},
        "suggestions": [
            {{
                "title": "Short title of the problem",
                "description": "Detailed explanation of why this pipeline stage or query is inefficient",
                "impact": "High/Medium/Low",
                "sql_snippet": "Optimized MongoDB query or pipeline stage snippet"
            }}
        ],
        "optimized_query": "The fully rewritten optimized MongoDB query or aggregation pipeline",
        "explanation": "A concise summary of why the pipeline was inefficient and how the changes improve it (e.g., COLLSCAN → IXSCAN, reducing $lookup depth, adding index hints)."
    }}

    Do not include markdown backticks around the JSON. Just return the raw JSON string.
    """
    else:
        prompt = f"""
    You are an expert {dialect} Database Administrator. Analyze the following SQL query for performance issues.
    
    Query: {query}
    
    Provide your analysis in the following JSON format ONLY:
    {{
        "execution_plan_summary": {{
            "node_type": "Primary operation (e.g., Seq Scan, Index Scan)",
            "cost": 123.45,
            "rows": 100,
            "relation_name": "Table name involved"
        }},
        "suggestions": [
            {{
                "title": "Short title of the problem",
                "description": "Detailed explanation of why this is inefficient",
                "impact": "High/Medium/Low",
                "sql_snippet": "Optimized SQL snippet or command"
            }}
        ],
        "optimized_query": "The fully rewritten optimized SQL query",
        "explanation": "A concise summary of why the query was slow and how the changes improve it."
    }}
    
    Do not include markdown backticks around the JSON. Just return the raw JSON string.
    """
    
    text = ""
    try:
        # Use async generation to avoid blocking the event loop
        response = await model.generate_content_async(prompt)
        text = response.text.strip()
    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str:
            print("Gemini Rate Limit Hit. Falling back to Groq Llama-3-70b...")
            groq_key = os.environ.get("GROQ_API_KEY")
            if groq_key:
                try:
                    import groq
                    client = groq.AsyncGroq(api_key=groq_key)
                    completion = await client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=2000
                    )
                    text = completion.choices[0].message.content.strip()
                except Exception as groq_err:
                    print(f"Groq Fallback Error: {groq_err}")
                    return AnalysisResult(
                        original_query=query,
                        execution_plan=PlanNode(node_type="ERROR", cost=0, rows=0, relation_name="error"),
                        suggestions=[],
                        optimized_query="ERROR",
                        explanation=f"AI Analysis Failed (Gemini gave 429, Groq fallback also failed): {str(groq_err)}"
                    )
            else:
                return AnalysisResult(
                    original_query=query,
                    execution_plan=PlanNode(node_type="ERROR", cost=0, rows=0, relation_name="error"),
                    suggestions=[],
                    optimized_query="ERROR",
                    explanation=f"AI Analysis Failed (Gemini Quota Exceeded, and GROQ_API_KEY not set): {str(e)}"
                )
        else:
            print(f"Gemini Error: {e}")
            return AnalysisResult(
                original_query=query,
                execution_plan=PlanNode(node_type="ERROR", cost=0, rows=0, relation_name="error"),
                suggestions=[],
                optimized_query="ERROR",
                explanation=f"AI Analysis Failed: {str(e)}"
            )

    try:
        # Clean up if model adds markdown formatting
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text.strip())
        
        plan_data = data.get("execution_plan_summary", {})
        root_node = PlanNode(
            node_type=plan_data.get("node_type", "Unknown Scan"),
            cost=float(plan_data.get("cost", 100.0)),
            rows=int(plan_data.get("rows", 0)),
            relation_name=plan_data.get("relation_name", "unknown")
        )
        
        suggestions_data = data.get("suggestions", [])
        suggestions = [
            Suggestion(
                title=s.get("title", "Optimization Tip"),
                description=s.get("description", ""),
                impact=s.get("impact", "Medium"),
                sql_snippet=s.get("sql_snippet", "")
            ) for s in suggestions_data
        ]
        
        return AnalysisResult(
            original_query=query,
            execution_plan=root_node,
            suggestions=suggestions,
            optimized_query=data.get("optimized_query", query),
            explanation=data.get("explanation", "Analysis complete.")
        )
        
    except Exception as parse_e:
        print(f"Parsing response error: {parse_e}")
        return AnalysisResult(
            original_query=query,
            execution_plan=PlanNode(node_type="ERROR", cost=0, rows=0, relation_name="error"),
            suggestions=[],
            optimized_query="ERROR",
            explanation=f"Error parsing AI response: {str(parse_e)}"
        )

def analyze_query_demo(query: str) -> AnalysisResult:
    """
    Simulates a PostgreSQL EXPLAIN ANALYZE result and AI optimization suggestions.
    This allows the portfolio project to be demonstrated without a live DB connection or API key.
    """
    query_lower = query.lower()
    
    root_node = PlanNode(
        node_type="Seq Scan" if "where" not in query_lower or "select *" in query_lower else "Index Scan",
        cost=1250.0 if "select *" in query_lower else 45.0,
        rows=10000 if "select *" in query_lower else 50,
        relation_name="users" if "users" in query_lower else "unknown_table",
    )
    
    suggestions = []
    
    if "select *" in query_lower:
        suggestions.append(Suggestion(
            title="Avoid SELECT *",
            description="Selecting all columns causes unnecessary I/O overhead. Specify only the columns you need.",
            impact="High",
            sql_snippet="SELECT id, name, email FROM ..."
        ))
        
    if "where" not in query_lower and "limit" not in query_lower:
        suggestions.append(Suggestion(
            title="Unbounded Query",
            description="Querying without WHERE or LIMIT can retrieve the entire table, causing performance issues.",
            impact="High",
            sql_snippet="LIMIT 100"
        ))
        
    if "like '%" in query_lower:
        suggestions.append(Suggestion(
            title="Inefficient Wildcard",
            description="Leading wildcards (e.g. LIKE '%term') prevent index usage. Consider Full Text Search.",
            impact="Medium",
            sql_snippet="to_tsvector(...)"
        ))

    if not suggestions:
        suggestions.append(Suggestion(
            title="Query looks efficient",
            description="The execution plan uses indexes effectively. Consider caching if QPS is high.",
            impact="Low"
        ))

    return AnalysisResult(
        original_query=query,
        execution_plan=root_node,
        suggestions=suggestions,
        optimized_query=query.replace("*", "id, name, email") if "select *" in query_lower else query,
        explanation="The query uses a Sequential Scan which is slow on large datasets. Optimization suggests targeting specific columns and adding indexes."
    )


def analyze_pipeline_demo(query: str) -> AnalysisResult:
    """
    Simulates MongoDB aggregation pipeline analysis for demo/fallback mode.
    Pattern-matches common MongoDB antipatterns and returns realistic suggestions.
    """
    q = query.lower()
    suggestions = []

    # Detect COLLSCAN risk: $group or $sort before any $match
    has_match   = "$match" in q
    has_group   = "$group" in q
    has_sort    = "$sort" in q
    has_lookup  = "$lookup" in q
    has_unwind  = "$unwind" in q
    has_limit   = "$limit" in q
    has_project = "$project" in q
    has_index   = "hint" in q or "$indexstats" in q

    # Determine primary scan type
    if not has_match:
        node_type = "COLLSCAN"
        cost = 8500.0
        rows = 100000
    elif has_lookup:
        node_type = "$lookup + IXSCAN"
        cost = 420.0
        rows = 1500
    else:
        node_type = "IXSCAN"
        cost = 45.0
        rows = 80

    # Guess collection name
    import re
    coll_match = re.search(r'db\.([\w]+)\.', query)
    collection = coll_match.group(1) if coll_match else "unknown_collection"

    root_node = PlanNode(
        node_type=node_type,
        cost=cost,
        rows=rows,
        relation_name=collection
    )

    if not has_match:
        suggestions.append(Suggestion(
            title="Missing $match Stage (Full Collection Scan)",
            description="Your pipeline has no $match stage before $group or $sort. MongoDB will perform a full COLLSCAN on every document in the collection before aggregating, which is extremely expensive on large collections.",
            impact="High",
            sql_snippet='{ $match: { status: "active", created_at: { $gte: new Date(Date.now() - 30*24*60*60*1000) } } }'
        ))

    if has_lookup and not has_match:
        suggestions.append(Suggestion(
            title="Unbounded $lookup Join",
            description="A $lookup stage without a preceding $match will join every document in the source collection to the foreign collection. Add a $match before $lookup to reduce the input document count and avoid a cross-collection nested loop scan.",
            impact="High",
            sql_snippet='// Add before $lookup:\n{ $match: { user_id: { $in: targetUserIds } } }'
        ))

    if has_unwind and not has_limit:
        suggestions.append(Suggestion(
            title="$unwind Without $limit (Document Explosion)",
            description="$unwind on a large array field multiplies your document count by the array length. Without a $limit downstream, this can produce millions of intermediate documents. Add $limit or pre-filter with $match on the array.",
            impact="High",
            sql_snippet='{ $unwind: { path: "$items", includeArrayIndex: "idx" } },\n{ $limit: 10000 }'
        ))

    if has_group and not has_project:
        suggestions.append(Suggestion(
            title="Missing $project After $group",
            description="After $group, all non-grouped fields are dropped. Explicitly $project only the fields you need to avoid passing large intermediate documents to subsequent stages.",
            impact="Medium",
            sql_snippet='{ $project: { _id: 1, total: 1, count: 1 } }'
        ))

    if has_sort and not has_index:
        suggestions.append(Suggestion(
            title="$sort Without Index Hint",
            description="A $sort stage without a supporting index will perform an in-memory sort. For large result sets this can exceed MongoDB's 100MB memory limit. Add a compound index on your sort fields or use allowDiskUse.",
            impact="Medium",
            sql_snippet='db.collection.createIndex({ created_at: -1, user_id: 1 })\n// or use: .aggregate([...], { allowDiskUse: true })'
        ))

    if not suggestions:
        suggestions.append(Suggestion(
            title="Pipeline looks well-structured",
            description="The pipeline uses $match early to filter documents and indexes appear to be in use. Consider adding .explain('executionStats') in your MongoDB shell to verify IXSCAN usage.",
            impact="Low"
        ))

    optimized = query
    if not has_match:
        optimized = 'db.' + collection + '''.aggregate([\n  { $match: { /* add your filter here */ } },\n''' + query.split('.aggregate([', 1)[-1] if '.aggregate(' in query else query

    return AnalysisResult(
        original_query=query,
        execution_plan=root_node,
        suggestions=suggestions,
        optimized_query=optimized,
        explanation=f"The pipeline starts with a {node_type} on '{collection}'. {'Moving $match before $group and $lookup stages will dramatically reduce intermediate document counts and enable index usage.' if not has_match else 'Consider adding index hints and projecting only required fields after $group stages.'}"
    )
