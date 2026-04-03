"""
Cost calculation utilities for SQL optimizer
"""

# Hourly cost rates for different database types (in USD)
DB_HOURLY_RATES = {
    "postgresql": 1.50,  # AWS RDS db.t3.medium equivalent
    "mysql": 1.20,  # AWS RDS db.t3.medium equivalent
    "sqlite": 0.00,  # Local file-based, no direct cost
    "mongodb": 2.00,  # AWS DocumentDB or MongoDB Atlas M5 equivalent
}


def calculate_execution_cost(execution_time_ms: float, dialect: str) -> float:
    """
    Calculate execution cost based on execution time and database type

    Args:
        execution_time_ms: Execution time in milliseconds
        dialect: Database dialect (postgresql, mysql, sqlite, mongodb)

    Returns:
        Cost in USD
    """
    if execution_time_ms <= 0:
        return 0.0

    # Get hourly rate for the dialect, default to PostgreSQL rate if not found
    hourly_rate = DB_HOURLY_RATES.get(dialect.lower(), DB_HOURLY_RATES["postgresql"])

    # Convert milliseconds to hours and calculate cost
    hours = execution_time_ms / (1000 * 60 * 60)  # ms to hours
    cost = hours * hourly_rate

    return round(cost, 6)  # Round to 6 decimal places for small costs


def format_cost(cost: float) -> str:
    """
    Format cost for display

    Args:
        cost: Cost in USD

    Returns:
        Formatted cost string
    """
    if cost == 0:
        return "$0.00"
    elif cost < 0.01:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"
