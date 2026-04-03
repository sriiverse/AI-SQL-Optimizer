from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models import AnalyzeRequest, AnalysisResult, TextToSqlRequest, TextToSqlResponse
from analyze import analyze_query_demo, analyze_query_with_gemini, analyze_pipeline_demo
from generator import generate_sql_demo, generate_sql_with_gemini, generate_mongodb_demo
from socket_manager import manager
from history_storage import history_storage
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from datetime import datetime

load_dotenv()

# --- Module-level singleton: model is initialized ONCE at startup ---
_gemini_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, clean up on shutdown."""
    global _gemini_model
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            _gemini_model = genai.GenerativeModel('gemini-flash-latest')
            print("--- Gemini model initialized successfully at startup ---")
        except Exception as e:
            print(f"Startup Error initializing Gemini model: {e}")
    else:
        print("--- No GEMINI_API_KEY found, running in demo mode ---")
    yield  # App runs here
    # Shutdown: nothing to clean up for the Gemini client

app = FastAPI(title="AI SQL Optimizer", lifespan=lifespan)

def get_model():
    """Returns the shared, pre-initialized Gemini model instance."""
    return _gemini_model

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "SQL Optimizer API is running"}

@app.get("/health")
async def health():
    """Lightweight keep-alive endpoint for ping checks."""
    return {"status": "ok"}

@app.get("/ping")
async def ping():
    """Endpoint to keep the server awake - can be called by external services"""
    return {"status": "awake", "timestamp": datetime.now().isoformat()}

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_query_endpoint(request: AnalyzeRequest):
    try:
        model = get_model()
        if model:
            result = await analyze_query_with_gemini(request.query, request.dialect, model)
        else:
            # Demo/fallback mode: route to MongoDB or SQL analyser
            if request.dialect == "mongodb":
                result = analyze_pipeline_demo(request.query)
            else:
                result = analyze_query_demo(request.query)
        
        # Store in history (in a real app, we would have the optimized result too)
        # For now, we store the analysis result as-is
        history_storage.add_entry(result, dialect=request.dialect)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-sql", response_model=TextToSqlResponse)
async def generate_sql_endpoint(request: TextToSqlRequest):
    try:
        model = get_model()
        if model:
            return await generate_sql_with_gemini(request.schema_def, request.question, request.dialect, model)
        else:
            # Demo/fallback mode: route to MongoDB or SQL generator
            if request.dialect == "mongodb":
                return generate_mongodb_demo(request.schema_def, request.question)
            return generate_sql_demo(request.schema_def, request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- WebSockets & CLI Agent Logic ---

class ExecuteRequest(BaseModel):
    client_id: str
    query: str

class ExecutionResult(BaseModel):
    status: str
    execution_time_ms: float
    note: Optional[str] = None

@app.websocket("/ws/agent/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Endpoint for the local Node.js CLI Agent to connect securely.
    """
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Wait for responses from the CLI (e.g., the JSON EXPLAIN plan)
            data = await websocket.receive_text()
            print(f"Received from Agent [{client_id}]: {data}")
            
            # Parse the execution result from CLI
            try:
                result_data = json.loads(data)
                if result_data.get("type") == "EXECUTION_RESULT":
                    # Store execution result in history
                    # In a real implementation, we would associate this with the original query
                    # For now, we'll create a mock analysis result for storage
                    execution_time_ms = result_data.get("execution_time_ms", 0)
                    from cost_calculator import calculate_execution_cost
                    # Assume PostgreSQL dialect for cost calculation (would be passed from frontend in reality)
                    execution_cost = calculate_execution_cost(execution_time_ms, "postgresql")
                    
                    # Create a mock AnalysisResult for storage purposes
                    # In a real implementation, we would store the actual query and results
                    from models import AnalysisResult, PlanNode, Suggestion
                    mock_plan = PlanNode(
                        node_type="EXECUTED",
                        cost=0.0,
                        rows=0,
                        relation_name="executed_query",
                        execution_time_ms=execution_time_ms,
                        execution_cost=execution_cost
                    )
                    mock_result = AnalysisResult(
                        original_query="[Query executed via CLI agent]",
                        execution_plan=mock_plan,
                        suggestions=[],
                        explanation="Query executed via local CLI agent"
                    )
                    
                    # Store in history (this would be improved with actual query tracking)
                    history_storage.add_entry(mock_result, dialect="postgresql")
                    print(f"Stored execution result in history: {execution_time_ms}ms, cost: ")
                    
            except json.JSONDecodeError:
                print(f"Failed to parse execution result from client {client_id}")
            except Exception as e:
                print(f"Error processing execution result: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)

@app.post("/agent/execute")
async def execute_via_agent(request: ExecuteRequest):
    """
    React frontend calls this to trigger execution on the user's laptop.
    """
    success = await manager.send_execute_command(request.client_id, request.query)
    if success:
        return {"status": "success", "message": f"Command sent to local agent {request.client_id}"}
    else:
        raise HTTPException(status_code=404, detail="CLI Agent is not connected. Please run queryforge connect in your terminal.")

@app.post("/agent/execution-result")
async def receive_execution_result(client_id: str, result: ExecutionResult):
    """
    Receive execution results from the CLI agent and store in history.
    This endpoint would be called by the CLI agent after executing a query.
    """
    # In a real implementation, we would associate this with a specific query
    # For now, we'll just acknowledge receipt
    # The frontend would need to store the query separately and associate it with this result
    print(f"Received execution result from client {client_id}: {result}")
    return {"status": "success", "message": "Execution result received"}

@app.get("/history")
async def get_history(limit: int = 50):
    """
    Get query history entries
    """
    history = history_storage.get_history(limit=limit)
    return {"history": history}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
