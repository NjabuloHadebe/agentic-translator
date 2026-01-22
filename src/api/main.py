
# src/api/main.py
import os
import sys
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import OrderedDict
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure src/ is importable (important on Render)
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parent.parent
PROJECT_ROOT = SRC_DIR.parent
for p in (str(SRC_DIR), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Import core libraries
from src.core.agent import create_translator
from src.core.logger import TranslationLogger
from src.core.memory import TranslationMemory

# Logging & memory instances
logger = TranslationLogger()
memory = TranslationMemory()

# FastAPI app
app = FastAPI(
    title="Agentic Translator API",
    description="Advanced translation API with memory and learning capabilities",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Session Management (simple)
# --------------------------
DEFAULT_SESSION_ID = "default"
MAX_SESSIONS = 3
sessions: "OrderedDict[str, Any]" = OrderedDict()

def get_or_create_session(session_id: str):
    """Simple LRU session controller."""
    if session_id in sessions:
        sessions.move_to_end(session_id)
        return sessions[session_id]

    # Limit sessions
    if len(sessions) >= MAX_SESSIONS:
        for k in list(sessions.keys()):
            if k != DEFAULT_SESSION_ID:
                sessions.pop(k, None)
                break

    translator = create_translator(session_id=session_id)
    sessions[session_id] = translator
    return translator

# --------------------------
# Startup (NO WARMUP)
# --------------------------
@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 70)
    print("🚀 Agentic Translator API Starting...")
    print("=" * 70)
    print("⏭️  Warmup disabled (free tier). Translator loads on first request.")
    print("=" * 70)
    print("🌐 API Docs: /docs")
    print("🔧 Health: /health")
    print("=" * 70)

# --------------------------
# Request Models
# --------------------------
class TranslationRequest(BaseModel):
    text: str
    target_lang: str = "zu"
    source_lang: str = "en"
    use_memory: bool = True

class BatchItem(BaseModel):
    text: str
    target_lang: str = "zu"
    source_lang: str = "en"

class BatchTranslationRequest(BaseModel):
    items: List[BatchItem]
    session_id: Optional[str] = None

# --------------------------
# Routes
# --------------------------
@app.post("/translate")
async def translate(request: TranslationRequest, fast_request: Request):
    session_id = fast_request.headers.get("X-Session-ID", DEFAULT_SESSION_ID)
    start = time.time()

    print(f"\n📨 Translate → {request.text[:60]}")

    agent = get_or_create_session(session_id)

    try:
        result = agent.translate(
            text=request.text,
            target_lang=request.target_lang,
            source_lang=request.source_lang,
            use_memory=request.use_memory,
        )

        logger.log(
            input_text=request.text,
            output_text=result["translation"],
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            session_id=session_id,
            agent_thoughts=f"{result['source']}",
            tools_used=[result["source"]],
            confidence=result.get("confidence", 0.0)
        )

        return {
            "success": True,
            "original_text": request.text,
            "translated_text": result["translation"],
            "source": result["source"],
            "quality": result.get("quality", "unknown"),
            "confidence": result.get("confidence"),
            "session_id": session_id,
            "processing_time": time.time() - start,
        }

    except Exception as e:
        print("❌ ERROR:", e)
        raise HTTPException(500, str(e))

@app.post("/translate/batch")
async def translate_batch(request: BatchTranslationRequest, fast_request: Request):
    session_id = request.session_id or fast_request.headers.get("X-Session-ID", DEFAULT_SESSION_ID)
    agent = get_or_create_session(session_id)

    results = []
    for i, item in enumerate(request.items):
        try:
            out = agent.translate(
                text=item.text,
                target_lang=item.target_lang,
                source_lang=item.source_lang,
            )
            results.append({
                "index": i,
                "translated_text": out["translation"],
                "source": out["source"],
                "success": True
            })
        except Exception as e:
            results.append({"index": i, "error": str(e), "success": False})

    return {
        "session_id": session_id,
        "results": results,
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.head("/health")
async def health_head():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "message": "Agentic Translator API",
        "version": "2.0.0",
        "status": "ready",
        "docs": "/docs"
    }

# --------------------------
# Local debug entrypoint
# --------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
