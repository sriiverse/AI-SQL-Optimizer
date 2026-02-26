from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import AnalyzeRequest, AnalysisResult, TextToSqlRequest, TextToSqlResponse
from analyze import analyze_query_demo, analyze_query_with_gemini
from generator import generate_sql_demo, generate_sql_with_gemini
import os
from dotenv import load_dotenv
import google.generativeai as genai

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

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_query_endpoint(request: AnalyzeRequest):
    try:
        model = get_model()
        if model:
            return await analyze_query_with_gemini(request.query, request.dialect, model)
        else:
            return analyze_query_demo(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-sql", response_model=TextToSqlResponse)
async def generate_sql_endpoint(request: TextToSqlRequest):
    try:
        model = get_model()
        if model:
            return await generate_sql_with_gemini(request.schema_def, request.question, request.dialect, model)
        else:
            return generate_sql_demo(request.schema_def, request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
