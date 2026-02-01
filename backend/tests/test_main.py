from fastapi.testclient import TestClient
from main import app
import os
from unittest.mock import patch, MagicMock

client = TestClient(app)

# Mock Response for Analyze
MOCK_ANALYZE_RESPONSE = {
    "original_query": "SELECT * FROM users",
    "execution_plan": {
        "node_type": "Seq Scan",
        "cost": 10.0,
        "rows": 100
    },
    "suggestions": [
        {
            "title": "Avoid SELECT *",
            "description": "Select only necessary columns.",
            "impact": "High"
        }
    ],
    "explanation": "This is a mock explanation.",
    "optimized_query": "SELECT id, name FROM users"
}

# Mock Response for Generator
MOCK_GENERATOR_RESPONSE = {
    "query": "SELECT * FROM users",
    "explanation": "Mock generated query."
}

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "SQL Optimizer API is running"}

@patch("main.analyze_query_with_gemini")
def test_analyze_endpoint_mock(mock_analyze):
    # Setup mock
    mock_analyze.return_value = MOCK_ANALYZE_RESPONSE
    
    # Mock Config
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        response = client.post("/analyze", json={
            "query": "SELECT * FROM users",
            "dialect": "postgresql"
        })
        
    assert response.status_code == 200
    data = response.json()
    assert data["original_query"] == "SELECT * FROM users"
    assert len(data["suggestions"]) == 1

@patch("main.generate_sql_with_gemini")
def test_generate_endpoint_mock(mock_generate):
    # Setup mock
    mock_generate.return_value = MOCK_GENERATOR_RESPONSE
    
    # Mock Config
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        response = client.post("/generate-sql", json={
            "schema_def": "CREATE TABLE users (id INT)",
            "question": "Get all users",
            "dialect": "mysql"
        })
            
    assert response.status_code == 200
    assert response.json()["query"] == "SELECT * FROM users"
