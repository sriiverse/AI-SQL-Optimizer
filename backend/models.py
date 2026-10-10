from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Literal, Optional

from safety_config import MAX_QUERY_CHARS, MAX_QUESTION_CHARS, MAX_SCHEMA_CHARS

SUPPORTED_DIALECTS = ("postgresql", "mysql", "sqlite", "mongodb")

AnalysisSource = Literal["gemini", "groq", "demo", "error"]
PlanOrigin = Literal["synthetic", "engine", "none"]


def _canonical_dialect(value: str) -> str:
    canonical = value.strip().lower()
    if canonical not in SUPPORTED_DIALECTS:
        raise ValueError("Dialect must be one of: postgresql, mysql, sqlite, mongodb.")
    return canonical


def _bounded_text(value: str, limit: int, label: str) -> str:
    if len(value) > limit:
        raise ValueError(f"{label} exceeds the maximum length of {limit} characters.")
    return value


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    query: str
    schema_context: Optional[str] = None
    dialect: str = "postgresql"

    @field_validator("query")
    @classmethod
    def limit_query(cls, value: str) -> str:
        return _bounded_text(value, MAX_QUERY_CHARS, "Query")

    @field_validator("schema_context")
    @classmethod
    def limit_schema_context(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _bounded_text(value, MAX_SCHEMA_CHARS, "Schema")

    @field_validator("dialect")
    @classmethod
    def limit_dialect(cls, value: str) -> str:
        return _canonical_dialect(value)

class PlanNode(BaseModel):
    node_type: Optional[str] = None
    cost: Optional[float] = None
    rows: Optional[int] = None
    relation_name: Optional[str] = None
    children: List["PlanNode"] = []

class Suggestion(BaseModel):
    title: str
    description: str
    impact: Optional[str] = None  # "High", "Medium", "Low" when the model supplied one
    sql_snippet: Optional[str] = None

class ResultProvenance(BaseModel):
    """Additive facts about how a result was produced.

    Leave analysis_source and plan_origin unset when the path is unknown.
    database_connected and performance_measured default to false because a
    missing value must not be read as a live database measurement.
    """

    analysis_source: Optional[AnalysisSource] = None
    plan_origin: Optional[PlanOrigin] = None
    database_connected: bool = False
    performance_measured: bool = False


def reported_provenance(source: AnalysisSource, plan_origin: PlanOrigin) -> dict:
    """Provenance for a path that did not open a database or measure runtime."""
    return {
        "analysis_source": source,
        "plan_origin": plan_origin,
        "database_connected": False,
        "performance_measured": False,
    }


class AnalysisResult(ResultProvenance):
    original_query: str
    execution_plan: PlanNode
    suggestions: List[Suggestion]
    optimized_query: Optional[str] = None
    explanation: str

class TextToSqlRequest(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    schema_def: str
    question: str
    dialect: str = "postgresql"

    @field_validator("schema_def")
    @classmethod
    def limit_schema_def(cls, value: str) -> str:
        return _bounded_text(value, MAX_SCHEMA_CHARS, "Schema")

    @field_validator("question")
    @classmethod
    def limit_question(cls, value: str) -> str:
        return _bounded_text(value, MAX_QUESTION_CHARS, "Question")

    @field_validator("dialect")
    @classmethod
    def limit_dialect(cls, value: str) -> str:
        return _canonical_dialect(value)

class TextToSqlResponse(ResultProvenance):
    query: str
    explanation: str


PlanNode.model_rebuild()
