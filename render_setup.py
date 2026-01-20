"""
Adapter for Render.com deployment
"""
import os
from pathlib import Path

def configure_for_render():
    """Configure paths and settings for Render"""
    
    # Check if we're on Render
    ON_RENDER = os.getenv('RENDER', '').lower() == 'true'
    
    if ON_RENDER:
        print("🌐 Running on Render.com")
        
        # Render-specific paths
        base_path = Path("/opt/render/project/src")
        
        # Override environment variables
        os.environ['CHROMA_PERSIST_DIRECTORY'] = str(base_path / "data" / "chroma_db")
        os.environ['LOG_FILE_PATH'] = str(base_path / "data" / "translation_logs.jsonl")
        os.environ['DICTIONARY_DB_PATH'] = str(base_path / "data" / "dictionary_db")
        
        print(f"📁 Using Render paths:")
        print(f"  Chroma: {os.environ['CHROMA_PERSIST_DIRECTORY']}")
        print(f"  Logs: {os.environ['LOG_FILE_PATH']}")
        print(f"  Dictionary: {os.environ['DICTIONARY_DB_PATH']}")
    
    return ON_RENDER

# Import this in your main.py