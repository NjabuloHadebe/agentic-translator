# api/main.py
from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import uuid
import time
import json
import asyncio
from enum import Enum
from core.agent import AgenticTranslator
from core.logger import logger
from core.memory import memory
import traceback

app = FastAPI(
    title="Agentic Translator API",
    description="Advanced translation API with memory, context, and learning capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
sessions = {}

# Request/Response Models
class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to translate")
    target_lang: str = Field(..., description="Target language code (e.g., 'zu', 'fr', 'es')")
    source_lang: str = Field("en", description="Source language code")
    use_memory: bool = Field(True, description="Use translation memory")
    
    @validator('target_lang')
    def validate_lang(cls, v):
        valid_langs = ['zu', 'fr', 'es', 'de', 'zh', 'ja', 'ko', 'ar', 'hi']
        if v not in valid_langs:
            raise ValueError(f"Target language must be one of: {', '.join(valid_langs)}")
        return v

class BatchItem(BaseModel):
    text: str
    target_lang: str = "zu"
    source_lang: str = "en"

class BatchTranslationRequest(BaseModel):
    items: List[BatchItem] = Field(..., max_items=100)
    batch_id: Optional[str] = None

class DictionaryLookupRequest(BaseModel):
    word: str
    source_lang: str = "en"
    target_lang: str = "zu"

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    active_sessions: int
    total_translations: int = 0

class TranslationResponse(BaseModel):
    success: bool
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    source: str = Field(..., description="dictionary, memory, api, or none")
    quality: str = Field(..., description="Translation quality")
    confidence: Optional[float] = None
    session_id: str
    validation: Optional[Dict[str, Any]] = None
    processing_time: float
    timestamp: datetime

# Track API startup time
app_start_time = time.time()

# Dependency functions
async def get_agent(session_id: str = None, request: Request = None) -> AgenticTranslator:
    """Get or create agent for session"""
    if not session_id:
        session_id = request.headers.get("X-Session-ID", f"session_{uuid.uuid4().hex[:8]}")
    
    if session_id not in sessions:
        sessions[session_id] = {
            "agent": AgenticTranslator(session_id=session_id),
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "translation_count": 0,
            "languages_used": set()
        }
        print(f"📱 New session created: {session_id}")
    
    sessions[session_id]["last_activity"] = datetime.utcnow()
    return sessions[session_id]["agent"]

def update_session_stats(session_id: str, source_lang: str, target_lang: str):
    """Update session statistics"""
    if session_id in sessions:
        sessions[session_id]["translation_count"] += 1
        sessions[session_id]["languages_used"].update([source_lang, target_lang])
        # Convert set to list for JSON serialization
        sessions[session_id]["languages_used"] = list(sessions[session_id]["languages_used"])

# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Session-Id"] = request.headers.get("X-Session-ID", "new")
    return response

# Background cleanup task
async def cleanup_inactive_sessions():
    """Clean up sessions inactive for more than 1 hour"""
    current_time = datetime.utcnow()
    inactive_sessions = []
    
    for session_id, session_data in list(sessions.items()):
        if isinstance(session_data["last_activity"], datetime):
            time_diff = (current_time - session_data["last_activity"]).total_seconds()
            if time_diff > 3600:  # 1 hour
                inactive_sessions.append(session_id)
    
    for session_id in inactive_sessions:
        print(f"🗑️  Cleaning up inactive session: {session_id}")
        del sessions[session_id]

# Event handlers
@app.on_event("startup")
async def startup_event():
    print("🚀 Agentic Translator API starting...")
    print("✅ Using existing agent, dictionary, and memory components")

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Shutting down Agentic Translator API")
    await cleanup_inactive_sessions()

# Routes
@app.post("/translate", response_model=TranslationResponse)
async def translate(
    request: TranslationRequest,
    fast_request: Request,
    background_tasks: BackgroundTasks
):
    """Main translation endpoint - compatible with your agent"""
    
    session_id = fast_request.headers.get("X-Session-ID", f"session_{uuid.uuid4().hex[:8]}")
    start_time = time.time()
    
    try:
        # Get agent
        agent = await get_agent(session_id, fast_request)
        
        print(f"\n📨 Translation Request:")
        print(f"   Session: {session_id}")
        print(f"   Text: '{request.text[:50]}...'")
        print(f"   From: {request.source_lang} → To: {request.target_lang}")
        
        # Call your existing agent's translate method
        result = agent.translate(
            text=request.text,
            target_lang=request.target_lang,
            source_lang=request.source_lang,
            use_memory=request.use_memory
        )
        
        # Update session statistics
        update_session_stats(session_id, request.source_lang, request.target_lang)
        
        processing_time = time.time() - start_time
        
        # Format response to match your agent's output
        response_data = {
            "success": "error" not in result,
            "original_text": request.text,
            "translated_text": result.get("translation", ""),
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "source": result.get("source", "unknown"),
            "quality": result.get("quality", "unknown"),
            "confidence": result.get("confidence"),
            "session_id": session_id,
            "validation": result.get("validation", {}),
            "processing_time": processing_time,
            "timestamp": datetime.utcnow()
        }
        
        print(f"✅ Translation complete:")
        print(f"   Source: {response_data['source']}")
        print(f"   Quality: {response_data['quality']}")
        print(f"   Time: {processing_time:.2f}s")
        
        return TranslationResponse(**response_data)
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Internal error: {e}")
        traceback.print_exc()
        
        # Log error
        error_log = {
            "session_id": session_id,
            "error": str(e),
            "text": request.text[:100],
            "timestamp": datetime.utcnow()
        }
        
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.post("/translate/batch")
async def translate_batch(
    batch_request: BatchTranslationRequest,
    fast_request: Request,
    background_tasks: BackgroundTasks
):
    """Batch translation endpoint"""
    session_id = fast_request.headers.get("X-Session-ID", f"batch_{uuid.uuid4().hex[:8]}")
    batch_id = batch_request.batch_id or f"batch_{uuid.uuid4().hex[:8]}"
    
    print(f"\n📦 Batch Translation Request:")
    print(f"   Batch ID: {batch_id}")
    print(f"   Items: {len(batch_request.items)}")
    
    results = []
    agent = await get_agent(session_id, fast_request)
    
    for i, item in enumerate(batch_request.items):
        try:
            result = agent.translate(
                text=item.text,
                target_lang=item.target_lang,
                source_lang=item.source_lang
            )
            
            results.append({
                "index": i,
                "original_text": item.text,
                "translated_text": result.get("translation", ""),
                "source": result.get("source", "unknown"),
                "quality": result.get("quality", "unknown"),
                "confidence": result.get("confidence"),
                "success": "error" not in result
            })
            
            # Small delay to avoid rate limiting
            if (i + 1) % 5 == 0:
                await asyncio.sleep(0.5)
                
        except Exception as e:
            results.append({
                "index": i,
                "original_text": item.text,
                "error": str(e),
                "success": False
            })
    
    return {
        "batch_id": batch_id,
        "session_id": session_id,
        "total_items": len(batch_request.items),
        "successful": len([r for r in results if r.get("success", False)]),
        "failed": len([r for r in results if not r.get("success", False)]),
        "results": results
    }

@app.get("/session/{session_id}/history")
async def get_history(session_id: str, limit: int = Query(20, le=1000)):
    """Get translation history for a session"""
    try:
        logs = logger.read_logs(limit=limit, session_id=session_id)
        return {
            "session_id": session_id,
            "history": logs,
            "count": len(logs) if logs else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/memory")
async def get_memory(session_id: str, limit: int = Query(10, le=100)):
    """Get semantic memory for a session"""
    try:
        context = memory.get_session_context(session_id, limit=limit)
        return {
            "session_id": session_id,
            "context": context,
            "count": len(context) if context else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get simple statistics"""
    try:
        stats = logger.get_stats()
        
        # Add session stats
        total_translations = sum(s["translation_count"] for s in sessions.values())
        
        return {
            **stats,
            "active_sessions": len(sessions),
            "total_translations": total_translations,
            "uptime": time.time() - app_start_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a session's memory"""
    try:
        memory.clear_session(session_id)
        if session_id in sessions:
            del sessions[session_id]
        return {
            "success": True, 
            "message": f"Session {session_id} cleared and removed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    total_translations = sum(s["translation_count"] for s in sessions.values())
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=time.time() - app_start_time,
        active_sessions=len(sessions),
        total_translations=total_translations
    )

@app.get("/sessions")
async def list_sessions(limit: int = Query(50, le=1000)):
    """List all active sessions"""
    session_list = []
    
    for session_id, data in list(sessions.items()):
        session_list.append({
            "session_id": session_id,
            "created_at": data["created_at"],
            "last_activity": data["last_activity"],
            "translation_count": data["translation_count"],
            "languages_used": list(data.get("languages_used", [])),
            "age_seconds": (datetime.utcnow() - data["last_activity"]).total_seconds()
        })
    
    # Sort by last activity (most recent first)
    session_list.sort(key=lambda x: x["last_activity"], reverse=True)
    
    return {
        "total_sessions": len(session_list),
        "sessions": session_list[:limit]
    }

@app.post("/dictionary/lookup")
async def dictionary_lookup(request: DictionaryLookupRequest):
    """Look up a word in the dictionary database"""
    try:
        # This depends on your dictionary implementation
        # You might need to call your dictionary methods directly
        from core.dictionary_db import DictionaryDatabase
        
        db = DictionaryDatabase()
        result = db.get_exact_match(request.word)
        
        return {
            "word": request.word,
            "translation": result if result else None,
            "found": result is not None,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Real-time translation stream (SSE)
@app.get("/translate/stream")
async def stream_translations(
    text: str = Query(..., description="Text to translate"),
    target_lang: str = Query("zu", description="Target language"),
    source_lang: str = Query("en", description="Source language")
):
    """Stream translation progress (Server-Sent Events)"""
    async def event_generator():
        session_id = f"stream_{uuid.uuid4().hex[:8]}"
        agent = AgenticTranslator(session_id=session_id)
        
        # Send initial event
        yield f"data: {json.dumps({'event': 'start', 'session_id': session_id, 'text': text[:50]})}\n\n"
        
        try:
            # Step 1: Validation
            yield f"data: {json.dumps({'event': 'validating', 'progress': 10})}\n\n"
            await asyncio.sleep(0.5)
            
            # Step 2: Dictionary check
            yield f"data: {json.dumps({'event': 'checking_dictionary', 'progress': 30})}\n\n"
            await asyncio.sleep(0.5)
            
            # Step 3: Memory check
            yield f"data: {json.dumps({'event': 'checking_memory', 'progress': 50})}\n\n"
            await asyncio.sleep(0.5)
            
            # Step 4: Translation
            yield f"data: {json.dumps({'event': 'translating', 'progress': 70})}\n\n"
            
            # Actual translation
            result = agent.translate(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang
            )
            
            # Step 5: Complete
            yield f"data: {json.dumps({
                'event': 'complete',
                'progress': 100,
                'translation': result.get('translation', ''),
                'source': result.get('source', 'unknown'),
                'quality': result.get('quality', 'unknown')
            })}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Agentic Translator API",
        "version": "1.0.0",
        "description": "Advanced translation with memory and learning capabilities",
        "endpoints": {
            "translate": "POST /translate - Translate text",
            "translate_batch": "POST /translate/batch - Batch translation",
            "history": "GET /session/{id}/history - Get translation history",
            "memory": "GET /session/{id}/memory - Get session memory",
            "health": "GET /health - Health check",
            "sessions": "GET /sessions - List active sessions",
            "stream": "GET /translate/stream - Real-time translation stream",
            "docs": "GET /docs - API documentation"
        },
        "session_info": "Use X-Session-ID header for session persistence"
    }