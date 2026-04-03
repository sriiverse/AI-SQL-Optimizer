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
        # Extract costs from execution plans
        original_cost = result.execution_plan.execution_cost or 0.0
        optimized_cost = (
            optimized_result.execution_plan.execution_cost if optimized_result else 0.0
        )
        cost_savings = original_cost - optimized_cost

        # Extract execution time
        execution_time_ms = result.execution_plan.execution_time_ms or 0.0

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

        optimized_query = (
            optimized_result.optimized_query
            if optimized_result and optimized_result.optimized_query
            else None
        )

        conn = sqlite3.connect(self.db_path)
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


# Global instance
history_storage = HistoryStorage()
