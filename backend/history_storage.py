"""
History storage for SQL optimizer using SQLite
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict
from models import AnalysisResult


class HistoryStorage:
    def __init__(self, db_path: str = "query_history.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                dialect TEXT NOT NULL,
                original_cost REAL,
                optimized_cost REAL,
                cost_savings REAL,
                execution_time_ms REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                explanation TEXT,
                suggestions TEXT,
                optimized_query TEXT
            )
        """)

        conn.commit()
        conn.close()

    def add_entry(
        self,
        result: AnalysisResult,
        optimized_result: Optional[AnalysisResult] = None,
        dialect: str = "postgresql",
    ):
        """
        Add a query execution to history

        Args:
            result: AnalysisResult for the original query
            optimized_result: AnalysisResult for the optimized query (if available)
            dialect: Database dialect used
        """
        if not isinstance(result, AnalysisResult):
            result = AnalysisResult.model_validate(result)
        if optimized_result is not None and not isinstance(optimized_result, AnalysisResult):
            optimized_result = AnalysisResult.model_validate(optimized_result)

        # Store a cost only for a synthetic estimate that actually included a
        # number. Missing costs stay null. This service never measures runtime,
        # so execution_time_ms stays null and an engine plan is not recorded.
        if result.plan_origin == "none" or result.analysis_source == "error":
            original_cost = None
            optimized_query = None
        else:
            optimized_query = result.optimized_query
            if result.plan_origin == "synthetic" and result.execution_plan.cost is not None:
                original_cost = result.execution_plan.cost
            else:
                original_cost = None

        optimized_cost = None
        if (
            optimized_result is not None
            and optimized_result.plan_origin == "synthetic"
            and optimized_result.analysis_source != "error"
            and optimized_result.execution_plan.cost is not None
        ):
            optimized_cost = optimized_result.execution_plan.cost
            if optimized_query is None:
                optimized_query = optimized_result.optimized_query

        cost_savings = (
            original_cost - optimized_cost
            if original_cost is not None and optimized_cost is not None
            else None
        )
        execution_time_ms = None

        # Serialize suggestions and optimized query
        suggestions_json = json.dumps(
            [
                {
                    "title": s.title,
                    "description": s.description,
                    "impact": s.impact,
                    "sql_snippet": s.sql_snippet,
                }
                for s in result.suggestions
            ]
        )

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO query_history (
                    query, dialect, original_cost, optimized_cost, cost_savings,
                    execution_time_ms, explanation, suggestions, optimized_query
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    result.original_query,
                    dialect,
                    original_cost,
                    optimized_cost,
                    cost_savings,
                    execution_time_ms,
                    result.explanation,
                    suggestions_json,
                    optimized_query,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_history(self, limit: int = 50) -> List[Dict]:
        """
        Get query history entries

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of history entries as dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, query, dialect, original_cost, optimized_cost, cost_savings,
                   execution_time_ms, timestamp, explanation, suggestions, optimized_query
            FROM query_history
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append(
                {
                    "id": row[0],
                    "query": row[1],
                    "dialect": row[2],
                    "original_cost": row[3],
                    "optimized_cost": row[4],
                    "cost_savings": row[5],
                    "execution_time_ms": row[6],
                    "timestamp": row[7],
                    "explanation": row[8],
                    "suggestions": json.loads(row[9]) if row[9] else [],
                    "optimized_query": row[10],
                }
            )

        return history

    def delete_history(self):
        """Clear all history entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_history")
        conn.commit()
        conn.close()


# Opened on first history read or write. Importing this module does not create
# the database file, so a disabled history route never touches SQLite.
_history_storage: Optional[HistoryStorage] = None


def get_history_storage() -> HistoryStorage:
    global _history_storage
    if _history_storage is None:
        _history_storage = HistoryStorage()
    return _history_storage
