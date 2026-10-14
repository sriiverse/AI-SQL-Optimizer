from contextlib import asynccontextmanager
import hashlib
import secrets
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect, WebSocketException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from models import AnalyzeRequest, AnalysisResult, TextToSqlRequest, TextToSqlResponse
from analyze import analyze_query_demo, analyze_query_with_gemini, analyze_pipeline_demo
from generator import generate_sql_demo, generate_sql_with_gemini, generate_mongodb_demo
from socket_manager import manager
from history_storage import get_history_storage
from body_limit import BodySizeLimitMiddleware
from rate_limit import RateLimitMiddleware, limiter
from safety_config import MAX_BODY_BYTES
import logging
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from datetime import datetime

logger = logging.getLogger(__name__)

load_dotenv()

# Process environment and the .env file loaded above are the deployment
# source. Tests override history_enabled and agent_enabled directly. They do
# not need to change os.environ after this module has been imported.
_ENABLED_VALUES = {"1", "true", "yes", "on"}


def flag_is_enabled(value: Optional[str]) -> bool:
    """True only for 1, true, yes, or on. Missing and every other value are false."""
    if value is None:
        return False
    return value.strip().lower() in _ENABLED_VALUES


def history_enabled() -> bool:
    # HISTORY_ENABLED defaults to false.
    # Do not enable this on a shared or public deployment. History is one
    # SQLite file with no authentication and no per-user isolation. Setting
    # this flag does not make that store safe for public use.
    return flag_is_enabled(os.environ.get("HISTORY_ENABLED"))


def agent_enabled() -> bool:
    # AGENT_ENABLED defaults to false. It only turns on the existing agent
    # channel. It is not authentication and does not make that channel safe
    # for a public multi-user deployment.
    return flag_is_enabled(os.environ.get("AGENT_ENABLED"))


def read_provider_access_token() -> Optional[str]:
    """Server secret for paid Gemini and Groq calls. Missing or blank stays closed."""
    raw = os.environ.get("PROVIDER_ACCESS_TOKEN")
    if raw is None:
        return None
    token = raw.strip()
    return token or None


def provider_access_token() -> Optional[str]:
    # Read on each request. Tests replace this function. A value in frontend
    # JavaScript is not this control and must not be treated as one.
    return read_provider_access_token()


def paid_provider_access(authorization: Optional[str]) -> str:
    """Return closed, denied, or allowed.

    closed: no server token is configured, so paid providers stay off.
    denied: a token is configured and this request did not present it.
    allowed: the bearer token matches the server secret.
    """
    expected = provider_access_token()
    if not expected:
        return "closed"
    if authorization is None:
        return "denied"
    scheme, _, presented = authorization.partition(" ")
    if scheme.lower() != "bearer" or not presented.strip() or presented != presented.strip():
        return "denied"
    presented_hash = hashlib.sha256(presented.encode("utf-8")).digest()
    expected_hash = hashlib.sha256(expected.encode("utf-8")).digest()
    if not secrets.compare_digest(presented_hash, expected_hash):
        return "denied"
    return "allowed"


def _require_paid_provider_access(authorization: Optional[str]) -> str:
    access = paid_provider_access(authorization)
    if access == "denied":
        raise HTTPException(
            status_code=403,
            detail="Paid provider access is not authorized.",
        )
    return access


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
            _gemini_model = genai.GenerativeModel("gemini-flash-latest")
            print("--- Gemini model initialized successfully at startup ---")
        except Exception as e:
            print(f"Startup Error initializing Gemini model: {e}")
    else:
        print("--- No GEMINI_API_KEY found, running in demo mode ---")
    yield  # App runs here
    # Shutdown: nothing to clean up for the Gemini client


app = FastAPI(title="AI SQL Optimizer", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    # Drop the submitted value. Pydantic otherwise echoes it, including an
    # oversized query or schema, in the 422 body.
    detail = jsonable_encoder(
        [
            {"type": error.get("type"), "loc": error.get("loc"), "msg": error.get("msg")}
            for error in exc.errors()
        ]
    )
    return JSONResponse(status_code=422, content={"detail": detail})


def get_model():
    """Returns the shared, pre-initialized Gemini model instance."""
    return _gemini_model


# Added first so CORS stays outermost. Body size runs before the rate limit,
# and both run before a route can call a provider.
app.add_middleware(RateLimitMiddleware, limiter=limiter)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_BODY_BYTES)

# Browser access for the public UI. This is not authentication.
# Credentials stay off because origins are unrestricted and the app has no cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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


def _coerce_analysis(result) -> AnalysisResult:
    if isinstance(result, AnalysisResult):
        return result
    return AnalysisResult.model_validate(result)


def _demo_analysis(query: str, dialect: str):
    if dialect == "mongodb":
        return analyze_pipeline_demo(query)
    return analyze_query_demo(query)


def _demo_generation(schema_def: str, question: str, dialect: str):
    if dialect == "mongodb":
        return generate_mongodb_demo(schema_def, question)
    return generate_sql_demo(schema_def, question)


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_query_endpoint(
    request: AnalyzeRequest,
    authorization: Optional[str] = Header(default=None),
):
    # Paid providers run only when this process has PROVIDER_ACCESS_TOKEN and
    # the caller presents it. CORS and the client IP are not that check.
    access = _require_paid_provider_access(authorization)
    try:
        model = get_model() if access == "allowed" else None
        if model:
            raw_result = await analyze_query_with_gemini(
                request.query, request.dialect, model
            )
        else:
            raw_result = _demo_analysis(request.query, request.dialect)
        result = _coerce_analysis(raw_result)
    except Exception:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail="Analysis failed")

    if history_enabled():
        try:
            get_history_storage().add_entry(result, dialect=request.dialect)
        except Exception:
            logger.exception(
                "History persistence failed; returning the completed analysis"
            )

    return result


@app.post("/generate-sql", response_model=TextToSqlResponse)
async def generate_sql_endpoint(
    request: TextToSqlRequest,
    authorization: Optional[str] = Header(default=None),
):
    access = _require_paid_provider_access(authorization)
    try:
        model = get_model() if access == "allowed" else None
        if model:
            return await generate_sql_with_gemini(
                request.schema_def, request.question, request.dialect, model
            )
        return _demo_generation(request.schema_def, request.question, request.dialect)
    except Exception:
        logger.exception("SQL generation failed")
        raise HTTPException(status_code=500, detail="SQL generation failed")


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
    Local CLI agent socket. The CLI simulates a timer and does not execute SQL.
    Disabled unless AGENT_ENABLED is true. That flag is not authentication.
    """
    if not agent_enabled():
        # Close during CONNECTING. Do not accept the socket or register it.
        raise WebSocketException(code=1008, reason="Agent is disabled")

    await manager.connect(websocket, client_id)
    try:
        while True:
            # Messages from the simulated CLI. They are not database plans.
            data = await websocket.receive_text()
            print(f"Received from Agent [{client_id}]: {data}")

            # Parse the execution result from CLI
            try:
                result_data = json.loads(data)
                if result_data.get("type") == "EXECUTION_RESULT":
                    # The CLI agent does not run the query against a database.
                    # Do not record its timer as a measured execution time, and
                    # do not label this acknowledgement as a model provider.
                    from models import PlanNode

                    mock_plan = PlanNode()
                    mock_result = AnalysisResult(
                        original_query="[Query received from CLI agent]",
                        execution_plan=mock_plan,
                        suggestions=[],
                        explanation="Query acknowledged via local CLI agent. Performance was not measured.",
                        plan_origin="none",
                        database_connected=False,
                        performance_measured=False,
                    )

                    if history_enabled():
                        get_history_storage().add_entry(mock_result, dialect="postgresql")
                        logger.info(
                            "Stored agent acknowledgement without a measured runtime"
                        )

            except json.JSONDecodeError:
                print(f"Failed to parse execution result from client {client_id}")
            except Exception as e:
                print(f"Error processing execution result: {e}")

    except WebSocketDisconnect:
        manager.disconnect(client_id)


@app.post("/agent/execute")
async def execute_via_agent(request: ExecuteRequest):
    """
    Forward a query to a connected CLI socket when AGENT_ENABLED is true.
    The CLI does not execute the query. This flag is not authentication.
    """
    if not agent_enabled():
        raise HTTPException(status_code=404, detail="Agent is disabled")

    success = await manager.send_execute_command(request.client_id, request.query)
    if success:
        return {
            "status": "success",
            "message": f"Command sent to local agent {request.client_id}",
        }
    else:
        raise HTTPException(
            status_code=404,
            detail="CLI agent is not connected.",
        )


@app.post("/agent/execution-result")
async def receive_execution_result(client_id: str, result: ExecutionResult):
    """
    Acknowledge a CLI payload. This route does not execute SQL and does not
    store a measured runtime. Disabled unless AGENT_ENABLED is true.
    """
    if not agent_enabled():
        raise HTTPException(status_code=404, detail="Agent is disabled")

    # The payload is not checked against a database execution. Receipt only.
    print(f"Received execution result from client {client_id}: {result}")
    return {"status": "success", "message": "Execution result received"}


@app.get("/history")
async def get_history(limit: int = 50):
    """
    Return shared history only when HISTORY_ENABLED is true.
    That flag does not add authentication or per-user isolation.
    """
    if not history_enabled():
        raise HTTPException(status_code=404, detail="History is disabled")

    history = get_history_storage().get_history(limit=limit)
    return {"history": history}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
