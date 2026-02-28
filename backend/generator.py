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

### $filter — Always Define `as`, Never Use `$$this`
16. Inside EVERY `$filter` expression, you MUST define the `as` parameter with an explicit variable name. NEVER use `$$this` as your element variable — it is not a valid iterator variable in `$filter`. Always write: `$filter: {{ input: ..., as: "elem", cond: {{ ... "$$elem.field" ... }} }}`. Using `$$this` without `as` will throw a runtime error.

### Percentile vs Rank — Use Correct Operator
17. `$rank` returns an ordinal position (1, 2, 3...), NOT a percentage. It CANNOT be used to determine "top 10%". To compute a percentile-based flag:
    - Use `$percent_rank` (MongoDB 5.0+) inside `$setWindowFields`: value will be 0.0 to 1.0.
    - Then flag with: `$lte: ["$percent_rank_value", 0.1]` for bottom 10% or `$gte` for top 10%.
    NEVER use `$rank` where a percentile is required.

### Symmetric Operations — Always Implement Both Sides
18. When the question references both directions of an operation (buy AND sell, inbound AND outbound, sent AND received), you MUST implement BOTH sides with separate `$lookup` or `$filter` stages. Never implement only one direction and omit the other. Both totals must appear in the final output.

### Cross-Collection Duration Calculations
19. When the question asks for average duration, elapsed time, or time-between-events that spans multiple documents or collections (e.g. average match duration from brackets.match_id → matches.started_at/ended_at), you MUST add a `$lookup` to join the related collection by ID and compute the duration as `$subtract: [ended_at, started_at]` on the joined documents. Never omit this join and leave duration uncomputed.

### Stage Placement — $setWindowFields Scope
20. `$setWindowFields` CANNOT be used inside a `$facet` branch, `$addFields`, or inside any expression like `$map` or `$let`. It IS allowed inside a `$lookup` sub-pipeline (e.g. for gap analysis) as long as it is a standalone pipeline stage.

### Stage Placement — $facet Output Shape
21. After a `$facet` stage, the output is a SINGLE document where each key contains an array of results. All subsequent stages operate on that single document, not on the original collection's documents. Never assume fields from before `$facet` are accessible as if `$facet` was not there — reference them via the facet key names.

### Zero Division Guard — Always Protect $divide
22. EVERY `$divide` expression MUST be zero-protected. Never write `$divide: [a, b]` without guarding `b`. Use:
    `$cond: [{{ $eq: [b, 0] }}, 0, {{ $divide: [a, b] }}]`
    OR: `$divide: [a, {{ $max: [b, 1] }}]`
    This applies in ALL contexts: $addFields, $project, $group, $setWindowFields, sub-pipelines.

### Nullable Field Guard — Always $ifNull Before $size or $avg
23. NEVER call `$size`, `$avg`, `$sum`, or `$max` directly on a field that might be null or missing. Always wrap with `$ifNull`:
    - `$size: {{ $ifNull: ["$array_field", []] }}`
    - `$avg: {{ $ifNull: ["$field", 0] }}`
    Calling `$size` on a null field throws a runtime error.

### $indexOfArray Safety — Guard the -1 Return Value
24. `$indexOfArray` returns -1 when the element is not found. If you then use that result as an index in `$arrayElemAt`, it returns the LAST element instead of null. Always guard: `$cond: [{{ $ne: [idx, -1] }}, {{ $arrayElemAt: [arr, idx] }}, null]`.

### Schema Field Validation — Only Use Fields That Exist
25. Before writing any `$lookup`, `$match`, or field access, verify that EVERY field you reference actually exists in the schema provided. NEVER invent a field (e.g. `zone_id` on `work_orders` if the schema shows only `incident_id` and `sensor_id`). If you need to join through an intermediate collection, perform a multi-hop join: A → B → C, not A → C with a nonexistent field.

### Embedded Array Field Access — $unwind or Array Expressions Required
26. A field inside an embedded array is NOT accessible as a top-level field. For example, if `subscriptions` is an array and you want to filter by `subscriptions.creator_id`, you MUST either:
    - `$unwind: "$subscriptions"` first, then `$match`, OR
    - Use `$filter` / `$elemMatch` inside an expression.
    Never access `"$subscriptions.creator_id"` as a simple field path on the root document.

### Defensively Guard All Possibly-Missing Fields
27. Any schema field marked as optional or that could be null (e.g. `resolved_at`, `parent_id`, `actual_arrival`) MUST be wrapped with `$ifNull` before arithmetic or comparison. Also use `$cond` to skip null documents in averages: `$avg: {{ $cond: [{{ $ne: ["$field", null] }}, "$field", null] }}`.

### Consecutive N-Day Detection — Time-Series Gap Analysis Only
28. "Sensor/device/user offline/inactive for more than N consecutive days" CANNOT be detected using a proxy field like `last_calibrated`, `last_active`, or `updated_at`. Those fields only tell you the last update time, not a gap in a continuous time series. This rule is NON-NEGOTIABLE — even if using a proxy seems simpler, it gives wrong results.
    The ONLY correct approach (use this exact pattern):
    ```
    // Step A: lookup all readings for the sensor, sorted by time
    {{ $lookup: {{ from: "readings", let: {{ sid: "$sensor_id" }},
      pipeline: [
        {{ $match: {{ $expr: {{ $eq: ["$sensor_id", "$$sid"] }} }} }},
        {{ $sort: {{ recorded_at: 1 }} }},
        // Step B: compute gap from previous reading using $shift
        {{ $setWindowFields: {{ sortBy: {{ recorded_at: 1 }},
          output: {{ gap_hours: {{ $dateDiff: {{
            startDate: {{ $shift: {{ output: "$recorded_at", by: -1 }} }},
            endDate: "$recorded_at", unit: "hour"
          }} }} }} }} }},
        // Step C: find max gap
        {{ $group: {{ _id: null, max_gap_hours: {{ $max: "$gap_hours" }} }} }}
      ], as: "gap_analysis" }}
    }},
    // Step D: flag as offline if max gap > 7*24 hours
    {{ $addFields: {{ is_offline_7d: {{ $gt: [{{ $arrayElemAt: ["$gap_analysis.max_gap_hours", 0] }}, 168] }} }} }}
    ```
    NEVER use last_calibrated, last_active, or any single timestamp field to infer consecutive gaps.

### Cross-Timestamp Window Correlation
29. When the question asks for data "in the X hours/days BEFORE each event" (e.g. readings in the 24h window before each incident), you MUST use a correlated `$lookup` with a time-bounded sub-pipeline:
    ```
    $lookup: {{
      from: "readings",
      let: {{ event_time: "$detected_at" }},
      pipeline: [
        {{ $match: {{ $expr: {{ $and: [
          {{ $gte: ["$recorded_at", {{ $subtract: ["$$event_time", 24*3600000] }}] }},
          {{ $lte: ["$recorded_at", "$$event_time"] }}
        ] }} }} }}
      ],
      as: "pre_event_readings"
    }}
    ```
    Never skip this and report "no weather context available".

### Array-of-IDs Graph Traversal — $graphLookup with Array startWith
30. When a document contains an array of related IDs (e.g. `linked_incident_ids: ["id1","id2"]`) that form a traversable graph, use `$graphLookup` with:
    - `startWith: "$linked_incident_ids"` (pass the ARRAY directly)
    - `connectFromField: "linked_incident_ids"`
    - `connectToField: "incident_id"` (or `_id`)
    NEVER put `$graphLookup` inside a `$map` or `$let` expression, as it is a pipeline STAGE, not an expression operator. If you need to run it per array element, you must `$unwind` the array first, perform `$graphLookup`, and then `$group` back.

### $week Is Not a Sliding Window
31. `$week` returns the ISO calendar week number (1–52). It CANNOT be used to compute relative windows like "last 8 weeks". Two readings 8 weeks apart may have consecutive `$week` values in the same year. For sliding time windows, compute relative week index using:
    `$floor: {{ $divide: [{{ $subtract: ["$$NOW", "$date_field"] }}, 7*24*3600000] }}`
    This gives 0 for current week, 1 for last week, etc. Never use `$week` for rolling window grouping.

### $lookup Sub-Pipeline Variable Scope — Always Declare `let`
32. A `$lookup` sub-pipeline runs in a SEPARATE scope and CANNOT access the outer document's fields directly. Any outer field you need inside the sub-pipeline MUST be declared in the `let` block and referenced as `$$variable_name`.
    WRONG — this silently fails (sub-pipeline cannot see `$zone_incidents`):
    `{{ $match: {{ $expr: {{ $in: ["$incident_id", "$zone_incidents.incident_id"] }} }} }}`
    CORRECT — declare it in `let` first:
    `$lookup: {{ from: "work_orders", let: {{ inc_ids: "$zone_incidents.incident_id" }}, pipeline: [{{ $match: {{ $expr: {{ $in: ["$incident_id", "$$inc_ids"] }} }} }}], as: "..." }}`
    Always pass every outer field through `let`. This applies even when the outer field is a computed/added field from a previous stage.

### Never Project Uncomputed Fields
33. In a `$project` stage, NEVER reference a field with `fieldName: 1` unless that field was either present in the original document schema OR explicitly computed in a prior `$addFields` / `$group` / `$lookup` stage. Before writing `$project`, trace every projected field back to where it was created. If it was not created upstream, either add the computation or remove the projection.
    WRONG: `{{ $project: {{ administrative_path: 1 }} }}` when no prior stage computed `administrative_path`.
    CORRECT: Add `{{ $addFields: {{ administrative_path: ... }} }}` before the `$project`.

### $setWindowFields Cannot Be an Expression Value
34. `$setWindowFields` is a pipeline STAGE. It cannot be the value of a field inside `$addFields`, `$project`, or any expression. This will crash at runtime.
    WRONG: `{{ $addFields: {{ my_field: {{ $setWindowFields: {{ ... }} }} }} }}`
    CORRECT: Use `$setWindowFields` as a standalone pipeline stage AFTER the `$addFields` that creates the base data.

### Requirement Checklist Before Output
Before writing the pipeline, mentally verify:
- [ ] All required collections are looked up
- [ ] All grouping/aggregation calculations are present
- [ ] All filtering conditions are applied (including date ranges inside nested arrays)
- [ ] All sorting requirements are met
- [ ] All flag fields are projected in the final output
- [ ] No `$graphLookup` appears inside an expression (only as a pipeline stage)
- [ ] `$setWindowFields` is never inside $facet, $addFields, or an expression (but IS allowed in $lookup)
- [ ] Computed fields on ancestors/related docs are re-computed inside their own sub-pipeline
- [ ] Time-series stages begin with a time-restricting $match
- [ ] Operator/actor-event correlations have an explicit $lookup to the events collection
- [ ] Every `$filter` has an explicit `as` parameter — no `$$this` used (even inside $map or $let)
- [ ] Percentile flags use `$percent_rank`, NOT `$rank`
- [ ] Both sides of symmetric operations (buy+sell, in+out) are implemented
- [ ] Duration calculations across collections use a $lookup to get timestamps
- [ ] Every `$divide` is zero-protected with `$cond` or `$max`
- [ ] Every `$size`/`$avg` on a possibly-null field is wrapped with `$ifNull`
- [ ] `$indexOfArray` results are guarded against -1
- [ ] All join fields exist in the schema — no invented field names
- [ ] Every outer field used inside a $lookup sub-pipeline is declared in `let` and accessed as `$$var`
- [ ] Every field referenced in `$project` was computed in a prior stage or exists in the schema
- [ ] Consecutive N-day detection uses time-series gap analysis, not a proxy field
- [ ] Pre-event window correlations use a correlated time-bounded $lookup
- [ ] Array-of-IDs graph traversal uses `$graphLookup` with array `startWith`
- [ ] Time windows use relative offsets, not `$week`

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

    text = ""
    try:
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
                        model="llama3-70b-8192",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=3000
                    )
                    text = completion.choices[0].message.content.strip()
                except Exception as groq_err:
                    print(f"Groq Fallback Error: {groq_err}")
                    return TextToSqlResponse(
                        query="ERROR",
                        explanation=f"AI Generation Failed (Gemini gave 429, Groq fallback also failed): {str(groq_err)}"
                    )
            else:
                return TextToSqlResponse(
                    query="ERROR",
                    explanation=f"AI Generation Failed (Gemini Quota Exceeded, and GROQ_API_KEY not set): {str(e)}"
                )
        else:
            print(f"Gemini Error: {e}")
            return TextToSqlResponse(
                query="ERROR",
                explanation=f"AI Generation Failed: {str(e)}"
            )

    try:
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

        # Run syntax validator for MongoDB queries
        warnings = validate_mongodb_query(query_part) if dialect == "mongodb" else []
        explanation = exp_part.strip() or "Query generated successfully."
        if warnings:
            warning_block = "\n\n⚠️ AUTO-DETECTED ISSUES:\n" + "\n".join(f"  • {w}" for w in warnings)
            explanation += warning_block

        return TextToSqlResponse(
            query=query_part,
            explanation=explanation
        )

    except Exception as parse_e:
        print(f"Parsing response error: {parse_e}")
        return TextToSqlResponse(
            query="ERROR",
            explanation=f"Error parsing AI response: {str(parse_e)}"
        )


def validate_mongodb_query(query: str) -> list[str]:
    """
    Post-generation static validator for MongoDB aggregation pipelines.
    Detects common runtime-breaking syntax errors before returning to the user.
    Returns a list of human-readable warning strings.
    """
    warnings = []

    # Check 1: $filter missing 'as' parameter ($$this misuse)
    # Robust depth-tracking approach: finds ALL $filter blocks at any nesting depth
    # and checks whether 'as' is declared before the first 'cond' within that block.
    filter_as_missing = False
    filter_depth = 0
    in_filter = False
    filter_buffer = []
    for line in query.split('\n'):
        stripped = line.strip()
        if '$filter' in stripped and not in_filter:
            in_filter = True
            filter_depth = stripped.count('{') - stripped.count('}')
            filter_buffer = [stripped]
        elif in_filter:
            filter_depth += stripped.count('{') - stripped.count('}')
            filter_buffer.append(stripped)
            if filter_depth <= 0:
                # End of this $filter block — check the collected buffer for 'as'
                block_text = ' '.join(filter_buffer)
                has_as = ('"as"' in block_text or "'as'" in block_text or
                          ' as:' in block_text or ',as:' in block_text or '{ as:' in block_text)
                has_this = '$$this' in block_text
                if has_this and not has_as:
                    filter_as_missing = True
                    break
                in_filter = False
                filter_depth = 0
                filter_buffer = []
    if filter_as_missing:
        warnings.append(
            '$filter block uses $$this without defining an "as" parameter. '
            '$$this is NOT a valid iterator variable in $filter. '
            'Add as: "elem" (or any name) and use $$elem.field in cond. '
            'This applies even when $filter is nested inside $map or $let.'
        )

    # Check 2: $dateSubtract / $dateAdd used directly as a $match value without $expr
    date_op_in_match = re.search(
        r'\$match\s*:\s*\{[^{}]*\$(gte|lte|gt|lt)\s*:\s*\{\s*\$(dateSubtract|dateAdd|subtract)\b',
        query, re.DOTALL
    )
    if date_op_in_match:
        warnings.append(
            '$dateSubtract/$dateAdd used directly in $match — wrap with $expr: '
            '{ $match: { $expr: { $gte: ["$field", { $dateSubtract: {...} }] } } }'
        )

    # Check 3: $graphLookup inside an expression context
    graphlookup_in_expr = re.search(
        r'(\$addFields|\$project|\$map|\$let)\s*:[^;]{0,500}\$graphLookup',
        query, re.DOTALL
    )
    if graphlookup_in_expr:
        warnings.append(
            '$graphLookup detected inside an expression context — it is a pipeline STAGE only. '
            'Move it to top-level or inside a $lookup sub-pipeline.'
        )

    # Check 4: $rank used where percentile semantics likely intended
    if re.search(r'["\']?\$rank["\']?\s*:', query) and \
       re.search(r'(percent|top\s*\d+\s*%|bottom\s*\d+\s*%)', query, re.IGNORECASE):
        warnings.append(
            '$rank returns an ordinal position, not a percentile (0–100%). '
            'Use $percent_rank inside $setWindowFields for true 0.0–1.0 percentile values.'
        )

    # Check 5: Truncated pipeline — mismatched brackets
    open_sq   = query.count('[')
    close_sq  = query.count(']')
    open_cu   = query.count('{')
    close_cu  = query.count('}')
    if abs(open_sq - close_sq) > 2 or abs(open_cu - close_cu) > 4:
        warnings.append(
            f'Pipeline may be truncated — brackets mismatched '
            f'([ {open_sq} vs ] {close_sq}, {{ {open_cu} vs }} {close_cu}). '
            'Consider splitting into smaller sub-queries.'
        )


    # Check 12: $setWindowFields used inside $addFields expression context (always a crash)
    # $setWindowFields is a pipeline STAGE — it cannot be a value inside $addFields
    addfields_window = False
    addfields_depth = 0
    in_addfields = False
    for line in query.split('\n'):
        stripped = line.strip()
        if '$addFields' in stripped and not in_addfields:
            in_addfields = True
            addfields_depth = stripped.count('{') - stripped.count('}')
        elif in_addfields:
            addfields_depth += stripped.count('{') - stripped.count('}')
            if '$setWindowFields' in stripped:
                addfields_window = True
                break
            if addfields_depth <= 0:
                in_addfields = False
                addfields_depth = 0
    if addfields_window:
        warnings.append(
            '$setWindowFields used inside $addFields — this is a runtime error. '
            '$setWindowFields is a pipeline stage, not an expression operator. '
            'Remove it from $addFields and place it as a standalone stage in the pipeline.'
        )

    # Check 11: Outer document field accessed directly inside $lookup sub-pipeline without let
    # Pattern: $match $expr references a "$fieldName" that looks like it comes from the outer doc
    # Heuristic: inner pipeline $match uses "$" + word that is NOT declared in a let block nearby
    lookup_blocks = re.findall(
        r'\$lookup\s*:\s*\{(.*?)\}\s*(?:,|\])',
        query, re.DOTALL
    )
    for block in lookup_blocks:
        # Find fields declared in let
        let_vars = set(re.findall(r'(\w+)\s*:\s*["\']?\$[\w.]+["\']?', 
                                   block[:block.find('pipeline')] if 'pipeline' in block else ''))
        # Find "$field" references in the pipeline section that are NOT $$vars
        pipeline_section = block[block.find('pipeline'):] if 'pipeline' in block else ''
        outer_field_refs = re.findall(r'(?<!\$)\$([a-zA-Z_]\w+(?:\.\w+)?)', pipeline_section)
        suspicious = [f for f in outer_field_refs 
                      if f not in let_vars 
                      and not f.startswith('$')
                      and len(f) > 1
                      and f not in ('expr', 'match', 'and', 'or', 'in', 'eq', 'ne', 'gt', 'lt', 
                                     'gte', 'lte', 'add', 'sum', 'avg', 'size', 'filter',
                                     'concat', 'cond', 'ifNull', 'arrayElemAt', 'map',
                                     'group', 'sort', 'lookup', 'project', 'unwind', 'limit',
                                     'ROOT', 'NOW', 'REMOVE', 'KEEP')]
        if suspicious:
            warnings.append(
                f'$lookup sub-pipeline may reference outer document field(s) without declaring them in `let`: '
                f'{list(set(suspicious))[:3]}. '
                'Inner sub-pipelines cannot access outer fields directly. '
                'Declare them in the `let` block and use $$varName inside the pipeline.'
            )
            break  # One warning is enough

    # Check 7: $divide without zero-protection ($max or $cond guard)
    # Pattern: $divide: [x, "$field"] where the denominator is not wrapped
    unguarded_divides = re.findall(r'\$divide\s*:\s*\[([^\]]{0,200})\]', query, re.DOTALL)
    for div_expr in unguarded_divides:
        has_guard = ('$max' in div_expr or '$cond' in div_expr or
                     '$ifNull' in div_expr or 'NULLIF' in div_expr.upper())
        if not has_guard and ('$' in div_expr):
            warnings.append(
                '$divide used without zero-protection on a variable denominator. '
                'Wrap as: $cond: [{ $eq: [denom, 0] }, 0, { $divide: [num, denom] }] '
                'or $divide: [num, { $max: [denom, 1] }]'
            )
            break  # Warn once

    # Check 8: $size on a field without $ifNull guard
    # Pattern: "$size": "$field_name" (direct, no $ifNull wrapping)
    raw_size = re.search(r'["\']?\$size["\']?\s*:\s*["\$][a-zA-Z_]', query)
    if raw_size:
        warnings.append(
            '$size called directly on a field reference without $ifNull — if the field is null or '
            'missing this will throw a runtime error. Use: $size: { $ifNull: ["$field", []] }'
        )

    # Check 9: $indexOfArray result used directly as $arrayElemAt index without -1 guard
    if '$indexOfArray' in query and '$arrayElemAt' in query:
        # Check if there is no $ne or $cond between them as a guard
        if not re.search(r'\$indexOfArray.{0,200}\$ne.{0,50}-1', query, re.DOTALL):
            warnings.append(
                '$indexOfArray result may be passed to $arrayElemAt without a -1 guard. '
                'When the element is not found, $indexOfArray returns -1, making $arrayElemAt '
                'return the last element. Guard with: $cond: [{ $ne: [idx, -1] }, { $arrayElemAt: [arr, idx] }, null]'
            )

    # Check 10: $week used for sliding time-window grouping (not calendar-aware use)
    if re.search(r'\$week\b', query) and re.search(r'(last\s*\d+\s*week|week.*window|rolling)', query, re.IGNORECASE):
        warnings.append(
            '$week returns an ISO calendar week number (1–52), not a relative sliding window offset. '
            'For rolling N-week windows use: $floor: { $divide: [{ $subtract: ["$$NOW", "$date"] }, 604800000] } '
            'to get week offset (0 = current week, 1 = last week, etc.)'
        )

    return warnings


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
