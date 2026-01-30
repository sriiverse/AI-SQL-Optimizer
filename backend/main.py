from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import AnalyzeRequest, AnalysisResult, TextToSqlRequest, TextToSqlResponse
from analyze import analyze_query_demo, analyze_query_with_gemini
from generator import generate_sql_demo, generate_sql_with_gemini
import os
from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai

app = FastAPI(title="AI SQL Optimizer")

@app.on_event("startup")
async def startup_event():
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            print("--- DEBUG: CHECKING AVAILABLE MODELS ---")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    print(f"Model: {m.name}")
            print("--- DEBUG: END MODEL CHECK ---")
        except Exception as e:
            print(f"DEBUG Error listing models: {e}")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local network testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "SQL Optimizer API is running"}



@app.post("/analyze", response_model=AnalysisResult)
async def analyze_query_endpoint(request: AnalyzeRequest):
    try:
        if os.environ.get("GEMINI_API_KEY"):
            return analyze_query_with_gemini(request.query)
        else:
            return analyze_query_demo(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-sql", response_model=TextToSqlResponse)
async def generate_sql_endpoint(request: TextToSqlRequest):
    try:
        if os.environ.get("GEMINI_API_KEY"):
            return generate_sql_with_gemini(request.schema_def, request.question)
        else:
            return generate_sql_demo(request.schema_def, request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
