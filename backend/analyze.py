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
    
    try:
        # Use async generation to avoid blocking the event loop
        response = await model.generate_content_async(prompt)
        text = response.text.strip()

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
        
    except Exception as e:
        print(f"Gemini Error: {e}")
        return AnalysisResult(
            original_query=query,
            execution_plan=PlanNode(node_type="ERROR", cost=0, rows=0, relation_name="error"),
            suggestions=[],
            optimized_query="ERROR",
            explanation=f"AI Analysis Failed: {str(e)}"
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
