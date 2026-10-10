from typing import Optional

from models import AnalysisResult, PlanNode, Suggestion, reported_provenance
from provider_timeout import ProviderTimeout, await_provider
from safety_config import analysis_timeout_seconds
import logging
import math
import os
import json
import google.generativeai as genai

logger = logging.getLogger(__name__)


def _analysis_error(query: str, explanation: str) -> AnalysisResult:
    return AnalysisResult(
        original_query=query,
        execution_plan=PlanNode(),
        suggestions=[],
        optimized_query="ERROR",
        explanation=explanation,
        **reported_provenance("error", "none"),
    )


def _optional_text(value) -> Optional[str]:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _optional_float(value) -> Optional[float]:
    """A finite number supplied by the model. Missing and invalid values stay unset."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            return None
    else:
        return None
    if not math.isfinite(number):
        return None
    return number


def _optional_rows(value) -> Optional[int]:
    """A non-negative integer row count. Missing and invalid values stay unset."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        number = value
    elif isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            return None
        number = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            number = int(text)
        except ValueError:
            return None
    else:
        return None
    if number < 0:
        return None
    return number


def _plan_node_from_summary(plan_data) -> PlanNode:
    if not isinstance(plan_data, dict):
        plan_data = {}
    return PlanNode(
        node_type=_optional_text(plan_data.get("node_type")),
        cost=_optional_float(plan_data.get("cost")),
        rows=_optional_rows(plan_data.get("rows")),
        relation_name=_optional_text(plan_data.get("relation_name")),
    )


def _suggestions_from_payload(raw) -> list:
    if not isinstance(raw, list):
        return []
    suggestions = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        impact = _optional_text(item.get("impact"))
        if impact not in {"High", "Medium", "Low"}:
            impact = None
        suggestions.append(
            Suggestion(
                title=_optional_text(item.get("title")) or "Optimization note",
                description=item.get("description") if isinstance(item.get("description"), str) else "",
                impact=impact,
                sql_snippet=item.get("sql_snippet") if isinstance(item.get("sql_snippet"), str) else None,
            )
        )
    return suggestions

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
    source = "gemini"
    timeout = analysis_timeout_seconds()
    try:
        # One async Gemini attempt. wait_for is the deadline, and the SDK
        # timeout asks that same attempt to abort. A timeout is not a quota
        # error, so it does not start the Groq fallback.
        response = await await_provider(
            model.generate_content_async(prompt, request_options={"timeout": timeout}),
            timeout,
        )
        text = response.text.strip()
    except ProviderTimeout:
        logger.warning("Gemini analysis timed out")
        return _analysis_error(query, "AI analysis timed out.")
    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str:
            logger.warning("Gemini rate limit hit. Attempting Groq fallback.")
            groq_key = os.environ.get("GROQ_API_KEY")
            if groq_key:
                try:
                    import groq
                    client = groq.AsyncGroq(api_key=groq_key, timeout=timeout)
                    completion = await await_provider(
                        client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2,
                            max_tokens=2000,
                            timeout=timeout,
                        ),
                        timeout,
                    )
                    text = completion.choices[0].message.content.strip()
                    source = "groq"
                except ProviderTimeout:
                    logger.warning("Groq analysis fallback timed out")
                    return _analysis_error(query, "AI analysis timed out.")
                except Exception:
                    logger.exception("Groq fallback failed after a Gemini quota error")
                    return _analysis_error(
                        query,
                        "AI analysis failed after the fallback provider returned an error.",
                    )
            else:
                logger.warning("Gemini quota exceeded and GROQ_API_KEY is not set")
                return _analysis_error(
                    query,
                    "AI analysis failed because the primary provider was unavailable and no fallback provider is configured.",
                )
        else:
            logger.exception("Gemini analysis failed")
            return _analysis_error(query, "AI analysis failed.")

    try:
        # Clean up if model adds markdown formatting
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        data = json.loads(text.strip())
        if not isinstance(data, dict):
            raise ValueError("model response was not an object")

        optimized_query = data.get("optimized_query")
        if not isinstance(optimized_query, str) or not optimized_query.strip():
            optimized_query = query
        explanation = data.get("explanation")
        if not isinstance(explanation, str) or not explanation.strip():
            explanation = "The model did not provide an explanation."

        # A parsed model reply is an estimate. It is never an engine plan,
        # even when cost or row count is absent.
        return AnalysisResult(
            original_query=query,
            execution_plan=_plan_node_from_summary(data.get("execution_plan_summary")),
            suggestions=_suggestions_from_payload(data.get("suggestions")),
            optimized_query=optimized_query,
            explanation=explanation,
            **reported_provenance(source, "synthetic"),
        )
        
    except Exception:
        logger.exception("Failed to parse analysis response")
        return _analysis_error(query, "The model response could not be read.")

def analyze_query_demo(query: str) -> AnalysisResult:
    """Keyword notes for a demo. This does not produce a database plan or metrics."""
    query_lower = query.lower()

    root_node = PlanNode()
    
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
            title="No keyword patterns matched",
            description="This demo only checks a few query keywords. It did not inspect an execution plan or measure performance.",
        ))

    return AnalysisResult(
        original_query=query,
        execution_plan=root_node,
        suggestions=suggestions,
        optimized_query=query.replace("*", "id, name, email") if "select *" in query_lower else query,
        explanation="Demo keyword check only. No database was contacted, and no cost, row count, or execution time was measured.",
        **reported_provenance("demo", "synthetic"),
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

    root_node = PlanNode()

    if not has_match:
        suggestions.append(Suggestion(
            title="Missing $match Stage (Full Collection Scan)",
            description="This demo found no $match before later stages. It did not run the pipeline or measure a collection scan.",
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
            title="No keyword patterns matched",
            description="This demo only checks a few pipeline keywords. It did not inspect an execution plan or measure performance.",
        ))

    optimized = query
    if not has_match and ".aggregate(" in query:
        optimized = query

    return AnalysisResult(
        original_query=query,
        execution_plan=root_node,
        suggestions=suggestions,
        optimized_query=optimized,
        explanation="Demo keyword check only. No database was contacted, and no cost, row count, or execution time was measured.",
        **reported_provenance("demo", "synthetic"),
    )
