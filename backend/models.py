from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class AnalyzeRequest(BaseModel):
    query: str
    schema_context: Optional[str] = None

class PlanNode(BaseModel):
    node_type: str
    cost: float
    rows: int
    relation_name: Optional[str] = None
    children: List["PlanNode"] = []

class Suggestion(BaseModel):
    title: str
    description: str
    impact: str  # "High", "Medium", "Low"
    sql_snippet: Optional[str] = None

class AnalysisResult(BaseModel):
    original_query: str
    execution_plan: PlanNode
    suggestions: List[Suggestion]
    optimized_query: Optional[str] = None
    explanation: str

class TextToSqlRequest(BaseModel):
    schema_def: str
    question: str

class TextToSqlResponse(BaseModel):
    query: str
    explanation: str
