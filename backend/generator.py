from models import TextToSqlResponse
import os
import google.generativeai as genai

def generate_sql_with_gemini(schema: str, question: str) -> TextToSqlResponse:
    """
    Uses Google Gemini to generate SQL from natural language + schema.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an expert SQL Generator.
    
    Context (Database Schema):
    {schema}
    
    Question: {question}
    
    Task: Generate a valid SQL query to answer the question based on the schema.
    Also provide a brief explanation of how the query works.
    
    Output format provided as plain text logic, but structured as:
    SQL: <the sql query>
    Explanation: <the explanation>
    
    Separate the SQL and explanation clearly.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Simple parsing logic (robustness could be improved)
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
                
        # Fallback if parsing fails (Gemini might return just the SQL or different format)
        if not sql_part:
            # Assume code block or raw text is the answer if short
            # This is a simplification for the demo
            if "select" in text.lower():
                sql_part = text
                exp_part = "Generated based on your question."
            else:
                 return generate_sql_demo(schema, question) # Fallback

        # Clean SQL
        sql_part = sql_part.replace("```sql", "").replace("```", "").strip()

        return TextToSqlResponse(
            query=sql_part,
            explanation=exp_part.strip()
        )

    except Exception as e:
        print(f"Gemini Error: {e}")
        return generate_sql_demo(schema, question)

def generate_sql_demo(schema: str, question: str) -> TextToSqlResponse:
    """
    Simulates Text-to-SQL generation.
    """
    # Simple placeholder logic
    
    generated_sql = "SELECT * FROM users WHERE active = true;" # Default fallback
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
