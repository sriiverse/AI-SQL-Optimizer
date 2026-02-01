import os
import asyncio
import asyncpg
import time
from tabulate import tabulate

# Configuration provided via Env Vars
DB_DSN = os.environ.get("DB_DSN", "postgresql://user:password@localhost:5432/dbname")

async def get_query_cost(conn, query):
    try:
        # Run EXPLAIN (FORMAT JSON) to get estimated cost
        result = await conn.fetchval(f"EXPLAIN (FORMAT JSON) {query}")
        plan = result[0]['Plan']
        return plan['Total Cost'], plan['Startup Cost']
    except Exception as e:
        print(f"Error executing EXPLAIN: {e}")
        return None, None

async def benchmark_queries(original_query, optimized_query):
    print(f"--- 📊 Benchmarking Queries ---")
    print(f"Connecting to: {DB_DSN}")
    
    try:
        conn = await asyncpg.connect(DB_DSN)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Tip: Set DB_DSN environment variable to a valid PostgreSQL connection string.")
        return

    print("\n1️⃣ Analyzing Original Query...")
    orig_total, orig_start = await get_query_cost(conn, original_query)
    
    print("2️⃣ Analyzing Optimized Query...")
    opt_total, opt_start = await get_query_cost(conn, optimized_query)
    
    await conn.close()
    
    if orig_total is None or opt_total is None:
        print("❌ Could not compare queries due to syntax or execution errors.")
        return

    # Calculate Improvement
    improvement = ((orig_total - opt_total) / orig_total) * 100
    
    data = [
        ["Original", orig_start, orig_total],
        ["Optimized", opt_start, opt_total]
    ]
    
    print("\nResults:")
    print(tabulate(data, headers=["Query", "Startup Cost", "Total Cost"], tablefmt="grid"))
    
    print(f"\n🚀 Cost Reduction: {improvement:.2f}%")
    if improvement > 0:
        print("✅ The optimized query is theoretically faster!")
    else:
        print("⚠️ The optimized query might not be better. Check indexes.")

if __name__ == "__main__":
    # Example usage
    q1 = "SELECT * FROM users WHERE created_at::date = '2023-01-01'"
    q2 = "SELECT * FROM users WHERE created_at >= '2023-01-01 00:00:00' AND created_at < '2023-01-02 00:00:00'"
    
    asyncio.run(benchmark_queries(q1, q2))
