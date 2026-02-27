from models import TextToSqlResponse
import os
import google.generativeai as genai

async def generate_sql_with_gemini(schema: str, question: str, dialect: str, model: genai.GenerativeModel) -> TextToSqlResponse:
    """
    Uses a pre-initialized Google Gemini model to generate SQL from natural language + schema.
    Runs asynchronously to avoid blocking the FastAPI event loop.
    """
    if dialect == "mongodb":
        prompt = f"""
    You are an expert MongoDB Engineer.

    Context (Collection Schema / Sample Documents):
    {schema}

    Question: {question}

    Task: Generate a valid MongoDB aggregation pipeline or query (using db.collection.find() / db.collection.aggregate()) to answer the question based on the collection schema.
    Use proper MongoDB operator syntax ($match, $group, $lookup, $project, $sort, $limit, etc.).
    Also provide a brief explanation of how the pipeline works.

    Output format:
    SQL: <the MongoDB query or aggregation pipeline>
    Explanation: <the explanation>

    Separate the query and explanation clearly. Do not wrap in markdown backticks.
    """
    else:
        prompt = f"""
    You are an expert SQL Generator.
    
    Context (Database Schema):
    {schema}
    
    Question: {question}
    
    Task: Generate a valid {dialect} query to answer the question based on the schema.
    Use standard {dialect} syntax.
    Also provide a brief explanation of how the query works.
    
    Output format provided as plain text logic, but structured as:
    SQL: <the sql query>
    Explanation: <the explanation>
    
    Separate the SQL and explanation clearly.
    """
    
    try:
        # Use async generation to avoid blocking the event loop
        response = await model.generate_content_async(prompt)
        text = response.text.strip()
        
        sql_part = ""
        exp_part = ""
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            if line.strip().lower().startswith("sql:"):
                current_section = "sql"
                sql_part += line.split(":", 1)[1].strip() + " "
                continue
            elif line.strip().lower().startswith("explanation:"):
                current_section = "exp"
                exp_part += line.split(":", 1)[1].strip() + " "
                continue
                
            if current_section == "sql":
                sql_part += line + " "
            elif current_section == "exp":
                exp_part += line + " "
                
        # Fallback if parsing fails
        if not sql_part:
            if "select" in text.lower() or "db." in text.lower() or "aggregate" in text.lower():
                sql_part = text
                exp_part = "Generated based on your question."
            else:
                return generate_sql_demo(schema, question)

        # Clean SQL
        sql_part = sql_part.replace("```sql", "").replace("```", "").strip()

        return TextToSqlResponse(
            query=sql_part,
            explanation=exp_part.strip()
        )

    except Exception as e:
        print(f"Gemini Error: {e}")
        return TextToSqlResponse(
            query="ERROR",
            explanation=f"AI Generation Failed: {str(e)}"
        )

def generate_sql_demo(schema: str, question: str) -> TextToSqlResponse:
    """
    Simulates Text-to-SQL generation for demo/fallback mode.
    """
    generated_sql = "SELECT * FROM users WHERE active = true;"
    explanation = "I analyzed the schema and identified the 'users' table. I filtered by 'active = true' based on your question."

    if "sales" in question.lower():
        generated_sql = "SELECT SUM(amount) FROM sales WHERE date > NOW() - INTERVAL '30 days';"
        explanation = "Aggregated sales amount for the last 30 days."
    
    if "join" in question.lower() or "orders" in question.lower():
        generated_sql = """
SELECT u.name, COUNT(o.id) as order_count 
FROM users u 
JOIN orders o ON u.id = o.user_id 
GROUP BY u.name 
ORDER BY order_count DESC;"""
        explanation = "Joined users and orders to count orders per user, sorting by highest count."

    if "analytics" in question.lower() or "performance" in question.lower():
        generated_sql = """
WITH RegionStats AS (
    SELECT 
        r.region_name,
        p.category,
        SUM(s.amount) as total_revenue,
        AVG(s.latency_ms) as avg_latency
    FROM server_logs s
    JOIN regions r ON s.region_id = r.id
    JOIN products p ON s.product_id = p.id
    WHERE s.timestamp >= NOW() - INTERVAL '24 hours'
    GROUP BY r.region_name, p.category
)
SELECT * FROM RegionStats 
WHERE total_revenue > 10000 
ORDER BY avg_latency ASC;"""
        explanation = "Constructed a CTE 'RegionStats' to aggregate revenue and latency by region and category. Filtered for high-revenue regions and sorted by lowest latency for performance analysis."

    return TextToSqlResponse(
        query=generated_sql.strip(),
        explanation=explanation
    )


def generate_mongodb_demo(schema: str, question: str) -> TextToSqlResponse:
    """
    Simulates MongoDB aggregation pipeline generation for demo/fallback mode.
    Pattern-matches intent keywords in the question and returns a realistic pipeline.
    """
    q = question.lower()

    # --- Time-series / recent activity ---
    if any(k in q for k in ["last", "recent", "today", "week", "month", "days"]):
        pipeline = '''db.orders.aggregate([
  // Step 1: Filter to recent documents first (enables index usage)
  { $match: {
      placed_at: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
      status: "delivered"
  }},
  // Step 2: Unwind line items
  { $unwind: "$items" },
  // Step 3: Group by product
  { $group: {
      _id: "$items.product_id",
      total_revenue: { $sum: { $multiply: ["$items.unit_price", "$items.qty"] } },
      order_count:   { $sum: 1 }
  }},
  // Step 4: Sort by revenue descending
  { $sort: { total_revenue: -1 } },
  { $limit: 10 },
  // Step 5: Enrich with product details
  { $lookup: {
      from: "products",
      localField: "_id",
      foreignField: "_id",
      as: "product"
  }},
  { $unwind: "$product" },
  { $project: {
      name: "$product.name",
      category: "$product.category_path",
      total_revenue: 1,
      order_count: 1
  }}
])'''
        explanation = "Filtered orders to the last 30 days using an indexed $match, unwound line items, grouped by product to sum revenue, then enriched results with product details via $lookup. $match is placed first to leverage the placed_at index and avoid a COLLSCAN."

    # --- Join / lookup between collections ---
    elif any(k in q for k in ["join", "from", "with", "related", "lookup", "belongs"]):
        pipeline = '''db.users.aggregate([
  // Step 1: Filter qualifying users
  { $match: { "profile.tier": { $in: ["premium", "vip"] }, last_active: { $gte: new Date(Date.now() - 7*24*60*60*1000) } } },
  // Step 2: Join their orders
  { $lookup: {
      from: "orders",
      let: { uid: "$_id" },
      pipeline: [
        { $match: { $expr: { $eq: ["$user_id", "$$uid"] }, status: "delivered" } },
        { $sort: { placed_at: -1 } },
        { $limit: 5 }
      ],
      as: "recent_orders"
  }},
  // Step 3: Only users with at least one order
  { $match: { "recent_orders.0": { $exists: true } } },
  { $project: {
      username: 1,
      tier: "$profile.tier",
      country: "$profile.country",
      recent_orders: 1
  }}
])'''
        explanation = "Used a $lookup with a correlated sub-pipeline (let/pipeline syntax) to fetch only delivered orders per user, avoiding a full orders collection scan. Pre-filtered users with $match before the $lookup to minimize the number of join evaluations."

    # --- Grouping / aggregation / count / sum / average ---
    elif any(k in q for k in ["group", "count", "sum", "average", "avg", "total", "aggregate"]):
        pipeline = '''db.reviews.aggregate([
  // Filter to verified reviews with meaningful sentiment
  { $match: { verified_purchase: true, posted_at: { $gte: new Date(Date.now() - 90*24*60*60*1000) } } },
  // Group per product
  { $group: {
      _id: "$product_id",
      avg_rating:        { $avg: "$rating" },
      avg_sentiment:     { $avg: "$sentiment_score" },
      review_count:      { $sum: 1 },
      helpful_votes:     { $sum: "$helpful_votes" }
  }},
  // Only products with enough reviews to be statistically significant
  { $match: { review_count: { $gte: 5 } } },
  { $sort: { avg_sentiment: -1 } },
  { $limit: 20 },
  { $lookup: {
      from: "products",
      localField: "_id",
      foreignField: "_id",
      as: "product"
  }},
  { $unwind: "$product" },
  { $project: { "product.name": 1, avg_rating: 1, avg_sentiment: 1, review_count: 1 } }
])'''
        explanation = "Filtered to verified recent reviews, grouped by product to compute average rating and AI sentiment score, then eliminated products with fewer than 5 reviews to avoid statistical noise. Enriched with product names via a final $lookup."

    # --- Top N / ranking / leaderboard ---
    elif any(k in q for k in ["top", "best", "highest", "most", "rank", "leaderboard"]):
        pipeline = '''db.events.aggregate([
  { $match: {
      event_type: { $in: ["purchase", "add_to_cart"] },
      occurred_at: { $gte: new Date(Date.now() - 7*24*60*60*1000) }
  }},
  { $group: {
      _id: "$product_id",
      interaction_count: { $sum: 1 },
      unique_users: { $addToSet: "$user_id" }
  }},
  { $addFields: { unique_user_count: { $size: "$unique_users" } } },
  { $sort: { interaction_count: -1 } },
  { $limit: 10 },
  { $lookup: { from: "products", localField: "_id", foreignField: "_id", as: "product" } },
  { $unwind: "$product" },
  { $project: {
      "product.name": 1, "product.price": 1,
      interaction_count: 1, unique_user_count: 1
  }}
])'''
        explanation = "Matched purchase and cart events from the last 7 days, grouped by product to count interactions and unique users ($addToSet for deduplication), sorted by interaction count, and enriched with product metadata."

    # --- Default: general find with filter ---
    else:
        pipeline = '''db.users.aggregate([
  { $match: { "profile.tier": "premium", last_active: { $gte: new Date(Date.now() - 30*24*60*60*1000) } } },
  { $project: { username: 1, email: 1, tier: "$profile.tier", country: "$profile.country", _id: 0 } },
  { $limit: 100 }
])'''
        explanation = "Filtered the users collection using an indexed $match on tier and last_active, then projected only the required fields to minimize network payload. $limit prevents unbounded result sets."

    return TextToSqlResponse(
        query=pipeline.strip(),
        explanation=explanation
    )
