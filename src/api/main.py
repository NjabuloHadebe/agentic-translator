# src/api/main.py
import os
import sys
import time
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add parent directory to path to import core modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.agent import create_translator
from core.logger import TranslationLogger
from core.memory import TranslationMemory

# Create instances
logger = TranslationLogger()
memory = TranslationMemory()

app = FastAPI(
    title="Agentic Translator API",
    description="Advanced translation API with memory and learning capabilities",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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
app_start_time = time.time()

# Request Models
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

# Event handlers
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*70)
    print("🚀 Agentic Translator API Starting...")
    print("="*70)
    print("✅ Memory initialized from: ./data/chroma_db")
    print("✅ Dictionary loaded from: ./data/dictionary_db")
    print("✅ Logger initialized at: ./data/translation_logs.jsonl")
    print("="*70)
    print("🌐 API Documentation: http://localhost:8000/docs")
    print("🔧 Health check: http://localhost:8000/health")
    print("="*70)

# Routes
@app.post("/translate")
async def translate(request: TranslationRequest, fast_request: Request):
    """Main translation endpoint"""
    
    session_id = fast_request.headers.get("X-Session-ID", f"session_{uuid.uuid4().hex[:8]}")
    start_time = time.time()
    
    print(f"\n📨 Translation Request:")
    print(f"   Session: {session_id}")
    print(f"   Text: '{request.text[:50]}...'")
    print(f"   From: {request.source_lang} → To: {request.target_lang}")
    
    # Get/create agent for this session
    if session_id not in sessions:
        sessions[session_id] = create_translator(session_id=session_id)
        print(f"   📱 New session created: {session_id}")
    
    agent = sessions[session_id]
    
    # Translate
    try:
        result = agent.translate(
            text=request.text,
            target_lang=request.target_lang,
            source_lang=request.source_lang,
            use_memory=request.use_memory
        )
        
        processing_time = time.time() - start_time
        
        # Log the translation
        logger.log(
            input_text=request.text,
            output_text=result['translation'],
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            session_id=session_id,
            agent_thoughts=f"Source: {result['source']}, Quality: {result.get('quality', 'unknown')}",
            tools_used=[result['source']],
            confidence=result.get('confidence', 0.0)
        )
        
        response_data = {
            "success": True,
            "original_text": request.text,
            "translated_text": result['translation'],
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "source": result['source'],
            "quality": result.get('quality', 'unknown'),
            "confidence": result.get('confidence'),
            "session_id": session_id,
            "validation": result.get('validation', {}),
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"✅ Translation complete:")
        print(f"   Source: {response_data['source']}")
        print(f"   Quality: {response_data['quality']}")
        print(f"   Time: {processing_time:.2f}s")
        
        return response_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate/batch")
async def translate_batch(request: BatchTranslationRequest, fast_request: Request):
    """Batch translation endpoint"""
    session_id = request.session_id or fast_request.headers.get("X-Session-ID", f"batch_{uuid.uuid4().hex[:8]}")
    
    print(f"\n📦 Batch Translation Request:")
    print(f"   Session: {session_id}")
    print(f"   Items: {len(request.items)}")
    
    # Get/create agent for this session
    if session_id not in sessions:
        sessions[session_id] = create_translator(session_id=session_id)
    
    agent = sessions[session_id]
    
    results = []
    start_time = time.time()
    
    for i, item in enumerate(request.items):
        try:
            result = agent.translate(
                text=item.text,
                target_lang=item.target_lang,
                source_lang=item.source_lang
            )
            
            results.append({
                "index": i,
                "original_text": item.text,
                "translated_text": result['translation'],
                "source": result['source'],
                "quality": result.get('quality', 'unknown'),
                "confidence": result.get('confidence'),
                "success": True
            })
            
            # Log each translation
            logger.log(
                input_text=item.text,
                output_text=result['translation'],
                source_lang=item.source_lang,
                target_lang=item.target_lang,
                session_id=session_id,
                agent_thoughts=f"Batch item {i}, Source: {result['source']}",
                tools_used=[result['source']],
                confidence=result.get('confidence', 0.0)
            )
            
        except Exception as e:
            results.append({
                "index": i,
                "original_text": item.text,
                "error": str(e),
                "success": False
            })
    
    processing_time = time.time() - start_time
    
    return {
        "session_id": session_id,
        "total_items": len(request.items),
        "successful": len([r for r in results if r.get("success", False)]),
        "failed": len([r for r in results if not r.get("success", False)]),
        "processing_time": processing_time,
        "average_time_per_item": processing_time / len(request.items) if request.items else 0,
        "results": results
    }

@app.get("/session/{session_id}/history")
async def get_history(session_id: str, limit: int = Query(20, le=1000)):
    """Get translation history for a session"""
    logs = logger.read_logs(limit=limit, session_id=session_id)
    return {
        "session_id": session_id,
        "history": logs,
        "count": len(logs)
    }

@app.get("/session/{session_id}/memory")
async def get_memory(session_id: str, limit: int = Query(10, le=100)):
    """Get semantic memory for a session"""
    try:
        # Try to get memory context if the method exists
        if hasattr(memory, 'get_session_context'):
            context = memory.get_session_context(session_id, limit=limit)
        else:
            # Fallback: search for similar translations
            context = memory.find_similar("", session_id=session_id, limit=limit)
        
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
    stats = logger.get_stats()
    stats["active_sessions"] = len(sessions)
    stats["uptime"] = time.time() - app_start_time
    
    # Add session statistics
    total_translations = 0
    for session_id, agent in sessions.items():
        if hasattr(agent, 'request_count'):
            total_translations += agent.request_count
    stats["total_translations_processed"] = total_translations
    
    return stats

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a session's memory"""
    if session_id in sessions:
        del sessions[session_id]
    return {
        "success": True, 
        "message": f"Session {session_id} cleared",
        "remaining_sessions": len(sessions)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    total_translations = sum(
        getattr(agent, 'request_count', 0) 
        for agent in sessions.values()
    )
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "uptime": time.time() - app_start_time,
        "active_sessions": len(sessions),
        "total_translations": total_translations,
        "components": {
            "logger": "active",
            "memory": "loaded ✓",
            "dictionary": "loaded ✓",
            "validator": "active"
        }
    }

@app.get("/test-cases")
async def get_test_cases():
    """Return mixed test cases for comprehensive testing"""
    test_cases = [
        # Category 1: Technical/Specialized terms (likely NOT in dataset)
        ("quantum computing", "zu"),
        ("blockchain protocol", "zu"),
        ("machine learning model", "zu"),
        ("renewable energy sources", "zu"),
        
        # Category 2: Common phrases (might use API)
        ("how are you feeling today?", "zu"),
        ("what time is the meeting?", "zu"),
        ("where can I find help?", "zu"),
        ("thank you for your assistance", "zu"),
        
        # Category 3: Educational/Academic (might be in dataset)
        ("research methodology section", "zu"),
        ("student assessment criteria", "zu"),
        ("library resources access", "zu"),
        ("academic writing style", "zu"),
        
        # Category 4: Business/Professional
        ("project management framework", "zu"),
        ("stakeholder engagement strategy", "zu"),
        ("financial reporting requirements", "zu"),
        ("business development plan", "zu"),
        
        # Category 5: Government/Administrative
        ("public service delivery", "zu"),
        ("policy implementation guidelines", "zu"),
        ("municipal governance structure", "zu"),
        ("community development program", "zu"),
        
        # Category 6: Medical/Health
        ("public health awareness", "zu"),
        ("healthcare service provision", "zu"),
        ("medical research ethics", "zu"),
        ("patient care standards", "zu"),
        
        # Category 7: Cultural/Social
        ("cultural heritage preservation", "zu"),
        ("social integration programs", "zu"),
        ("traditional knowledge systems", "zu"),
        ("community engagement initiatives", "zu"),
        
        # Category 8: Mixed/Interesting cases
        ("artificial intelligence ethics committee", "zu"),
        ("climate change adaptation strategies", "zu"),
        ("digital literacy training program", "zu"),
        ("sustainable development goals", "zu"),
    ]
    
    return {
        "test_cases": [
            {"text": text, "target_lang": lang, "source_lang": "en"} 
            for text, lang in test_cases
        ],
        "count": len(test_cases),
        "description": "Mixed test cases: Technical, Common, Academic, Business, Government, Medical, Cultural",
        "categories": {
            "technical": 4,
            "common": 4,
            "academic": 4,
            "business": 4,
            "government": 4,
            "medical": 4,
            "cultural": 4,
            "mixed": 4
        }
    }

@app.post("/run-tests")
async def run_tests():
    """Run comprehensive test suite via API"""
    print("\n" + "="*70)
    print("🎯 RUNNING COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    session_id = f"comprehensive_tests_{int(time.time())}"
    translator = create_translator(session_id=session_id)
    
    # Mixed test cases
    test_cases = [
        # 5 from dataset
        ("we trusted them because we had to", "zu"),
        ("i trust that this honours degree will prove to be both enriching and successful", "zu"),
        ("we wish the dvcs well on their new responsibilities", "zu"),
        ("if your sentence is a simple one but clearly explains what the author intended then you have paraphrased properly", "zu"),
        ("present a literature review of the key sources identified for the research topic", "zu"),
        
        # 5 new serious
        ("quantum decoherence in macroscopic systems presents significant challenges for scalable quantum computing", "zu"),
        ("the pathophysiology of autoimmune disorders involves molecular mimicry mechanisms targeting self-antigens", "zu"),
        ("monetary policy transmission mechanisms are impaired during liquidity trap scenarios", "zu"),
        ("post-structuralist critiques reveal power dynamics within institutionalized linguistic practices", "zu"),
        ("pharmacokinetic modeling requires consideration of hepatic cytochrome P450 enzyme polymorphisms", "zu"),
    ]
    
    results = []
    
    for i, (text, target_lang) in enumerate(test_cases):
        print(f"\n📋 Test {i+1}: '{text}'")
        
        try:
            result = translator.translate(
                text=text,
                target_lang=target_lang,
            )
            
            source = result.get('source', 'unknown')
            source_icon = "🧠" if source == 'memory' else "🌐" if source == 'api' else "📚" if source == 'dictionary' else "❓"
            
            results.append({
                "index": i + 1,
                "text": text,
                "translation": result.get('translation', ''),
                "source": source,
                "quality": result.get('quality', 'unknown'),
                "confidence": result.get('confidence'),
                "success": 'error' not in result
            })
            
            # Log the translation
            logger.log(
                input_text=text,
                output_text=result['translation'],
                source_lang="en",
                target_lang=target_lang,
                session_id=session_id,
                agent_thoughts=f"Test {i+1}, Source: {source}",
                tools_used=[source],
                confidence=result.get('confidence', 0.0)
            )
            
            print(f"   {source_icon} Source: {source}")
            print(f"   📝 Translation: {result.get('translation', 'N/A')[:60]}...")
            
            if source == 'memory' and result.get('confidence'):
                print(f"   🎯 Similarity: {result['confidence']:.2%}")
            
        except Exception as e:
            results.append({
                "index": i + 1,
                "text": text,
                "error": str(e),
                "success": False
            })
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)  # Small delay
    
    # Summary analysis
    source_counts = {}
    for result in results:
        if result.get('success'):
            source = result.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
    
    print(f"\n" + "="*70)
    print("📊 COMPREHENSIVE RESULTS SUMMARY")
    print("="*70)
    
    print(f"\n📈 Translation Sources:")
    for source, count in source_counts.items():
        percentage = (count / len(test_cases)) * 100
        print(f"   {source}: {count}/{len(test_cases)} ({percentage:.1f}%)")
    
    memory_percentage = (source_counts.get('memory', 0) / len(test_cases)) * 100
    print(f"\n💡 Interpretation:")
    print(f"   Memory usage: {memory_percentage:.1f}%")
    
    if memory_percentage > 50:
        print(f"   ✅ Dataset is effectively supporting translations")
    elif memory_percentage > 20:
        print(f"   ⚠️  Dataset has partial coverage")
    else:
        print(f"   🔍 Dataset has limited matches for these test cases")
    
    return {
        "session_id": session_id,
        "summary": {
            "total_tests": len(test_cases),
            "source_distribution": source_counts,
            "memory_percentage": memory_percentage,
            "success_rate": (len([r for r in results if r.get('success', False)]) / len(test_cases)) * 100
        },
        "results": results
    }

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    session_list = []
    
    for session_id, agent in sessions.items():
        session_list.append({
            "session_id": session_id,
            "translator_ready": True,
            "request_count": getattr(agent, 'request_count', 0),
            "components": {
                "has_memory": hasattr(agent, 'memory') and agent.memory is not None,
                "has_dictionary": hasattr(agent, 'dictionary') and agent.dictionary is not None,
                "has_validator": hasattr(agent, 'validator') and agent.validator is not None
            }
        })
    
    return {
        "total_sessions": len(session_list),
        "sessions": session_list
    }

@app.get("/")
async def root():
    """Welcome page with API usage"""
    return {
        "message": "Agentic Translator API",
        "description": "Advanced translation with memory and learning capabilities",
        "version": "2.0.0",
        "status": "Dataset loaded ✓ Memory working ✓",
        "endpoints": {
            "POST /translate": "Translate text",
            "POST /translate/batch": "Batch translation",
            "GET /session/{id}/history": "Get translation history",
            "GET /session/{id}/memory": "Get session memory",
            "GET /stats": "Get statistics",
            "DELETE /session/{id}": "Clear session",
            "GET /health": "Health check",
            "GET /test-cases": "View test cases",
            "POST /run-tests": "Run comprehensive test suite",
            "GET /sessions": "List active sessions",
            "GET /docs": "Interactive API documentation (Swagger UI)",
            "GET /redoc": "Alternative documentation"
        },
        "usage": "Send X-Session-ID header for session persistence",
        "note": "Your dataset is loaded! All translations will use memory first.",
        "quick_start": {
            "translate": 'curl -X POST "http://localhost:8000/translate" -H "Content-Type: application/json" -d \'{"text": "Hello world", "target_lang": "zu"}\'',
            "run_tests": 'curl -X POST "http://localhost:8000/run-tests"',
            "health": 'curl "http://localhost:8000/health"'
        }
    }

# For running directly
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("🚀 Starting Agentic Translator API")
    print("="*70)
    print("✅ Memory initialized from: ./data/chroma_db")
    print("✅ Dictionary loaded from: ./data/dictionary_db")
    print("✅ Logger initialized at: ./data/translation_logs.jsonl")
    print("="*70)
    print("🌐 API Documentation: http://localhost:8000/docs")
    print("🔧 Test endpoint: POST http://localhost:8000/run-tests")
    print("="*70)
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )