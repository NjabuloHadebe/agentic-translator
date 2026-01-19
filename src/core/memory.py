# core/memory.py - FIXED VERSION
import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"
import chromadb
import pandas as pd
from chromadb.config import Settings
from datetime import datetime
import uuid
import json
from typing import List, Dict, Optional, Any

class TranslationMemory:
    """Simple semantic memory using ChromaDB"""
    
    def __init__(self, persist_path: str = "./data/chroma_db"):
        # Settings with telemetry disabled
        settings = Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            chroma_server_ssl_enabled=False
        )
        
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=settings
        )
        
        # Create collections
        self.translation_collection = self.client.get_or_create_collection(
            name="translations",
            metadata={"description": "Semantic memory of translations"}
        )
        
        # Optional: session context collection
        self.session_collection = self.client.get_or_create_collection(
            name="sessions",
            metadata={"description": "Session-specific context"}
        )
        
        print(f"Memory initialized at: {persist_path}")
    
    def store_translation(self, 
                         input_text: str, 
                         output_text: str,
                         source_lang: str = "en",
                         target_lang: str = "zu",  # Changed to isiZulu
                         session_id: str = "default",
                         metadata: Optional[Dict] = None) -> str:
        """Store a translation with semantic search capability"""
        
        # Generate unique ID
        doc_id = f"trans_{uuid.uuid4().hex[:8]}"
        
        # Prepare metadata
        meta = {
            "input": input_text,
            "output": output_text,  # Added output to metadata
            "source_lang": source_lang,
            "target_lang": target_lang,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        # Store in ChromaDB - use INPUT text for embedding
        self.translation_collection.add(
            documents=[input_text],
            metadatas=[meta],
            ids=[doc_id]
        )
        
        # Also store in session collection for quick context retrieval
        self.session_collection.add(
            documents=[f"{input_text} → {output_text}"],
            metadatas=[{"type": "translation", "session_id": session_id}],
            ids=[f"session_{session_id}_{uuid.uuid4().hex[:4]}"]
        )
        
        print(f"Stored in memory: '{input_text[:30]}...' → '{output_text[:30]}...'")
        return doc_id
    
    def find_similar(self, 
                    query_text: str, 
                    target_lang: Optional[str] = None,
                    session_id: Optional[str] = None,
                    limit: int = 3) -> List[Dict]:
        """Find similar past translations"""
        
        # ChromaDB can only handle ONE condition in where clause
        # So we need to choose which filter to use
        where_filter = None
        
        if target_lang:
            where_filter = {"target_lang": target_lang}
        elif session_id:
            where_filter = {"session_id": session_id}
        # Can't use both at the same time in ChromaDB
        
        try:
            results = self.translation_collection.query(
                query_texts=[query_text],
                where=where_filter,
                n_results=limit,
                include=["metadatas", "distances", "documents"]
            )
            
            # Filter by second condition manually if needed
            filtered_results = []
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i]
                
                # Apply additional filters manually
                if target_lang and metadata.get("target_lang") != target_lang:
                    continue
                if session_id and metadata.get("session_id") != session_id:
                    continue
                
                filtered_results.append({
                    "id": results["ids"][0][i],
                    "input": metadata.get("input", ""),
                    "output": metadata.get("output", ""),  # Get output from metadata
                    "source_lang": metadata.get("source_lang", ""),
                    "target_lang": metadata.get("target_lang", ""),
                    "similarity": 1 - results["distances"][0][i] if results["distances"] and i < len(results["distances"][0]) else 0.5,
                    "timestamp": metadata.get("timestamp", "")
                })
            
            if filtered_results:
                print(f"Found {len(filtered_results)} similar translations for: '{query_text[:30]}...'")
            return filtered_results[:limit]
            
        except Exception as e:
            print(f"⚠️  Memory query error: {e}")
            return []
    
    def get_session_context(self, session_id: str, limit: int = 10) -> List[str]:
        """Get recent translations for a specific session"""
        try:
            results = self.session_collection.query(
                query_texts=[""],  # Empty query gets all
                where={"session_id": session_id},
                n_results=limit
            )
            
            return results["documents"][0] if results["documents"] else []
        except Exception as e:
            print(f"⚠️  Session context error: {e}")
            return []
    
    def clear_session(self, session_id: str):
        """Clear all session data"""
        try:
            self.session_collection.delete(where={"session_id": session_id})
            print(f"🧹 Cleared session: {session_id}")
        except Exception as e:
            print(f"⚠️  Clear session error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            translation_count = self.translation_collection.count()
            session_count = self.session_collection.count()
            
            return {
                "translation_count": translation_count,
                "session_count": session_count,
                "status": "healthy"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    def load_dataset_from_csv(self, csv_path: str = "dataset.csv", max_rows: int = 10000):
        """Load dataset.csv into memory"""
        
        print(f"📊 Loading dataset from {csv_path}...")
        
        # Check if file exists
        if not os.path.exists(csv_path):
            print(f"❌ File not found: {csv_path}")
            print(f"   Current directory: {os.getcwd()}")
            return 0
        
        try:
            # Load CSV
            df = pd.read_csv(csv_path)
            print(f"✅ Loaded {len(df)} rows from dataset")
            
            # Show sample
            print("\n📝 Sample from dataset:")
            for i in range(min(3, len(df))):
                eng = str(df.iloc[i].get('source_text', ''))[:80]
                zu = str(df.iloc[i].get('target_text', ''))[:80]
                print(f"  {i+1}. EN: {eng}...")
                print(f"     ZU: {zu}...")
            
            # Load into memory
            loaded_count = 0
            skipped_count = 0
            
            for i, row in df.iterrows():
                if loaded_count >= max_rows:
                    break
                
                english = str(row.get('source_text', '')).strip()
                isizulu = str(row.get('target_text', '')).strip()
                
                # Skip empty rows
                if not english or not isizulu:
                    skipped_count += 1
                    continue
                
                # Store in memory using your existing method
                self.store_translation(
                    input_text=english,
                    output_text=isizulu,
                    source_lang="en",
                    target_lang="zu",
                    session_id="dataset_load",
                    metadata={
                        "source": "dataset_csv",
                        "row_id": i,
                        "language_pair": row.get('language_pair', 'en-zu'),
                        "source_file": row.get('source_file', '')
                    }
                )
                
                loaded_count += 1
                
                # Progress update
                if loaded_count % 1000 == 0:
                    print(f"  Loaded {loaded_count} sentences...")
            
            print(f"\n✅ Successfully loaded {loaded_count} sentences from dataset")
            print(f"⚠️  Skipped {skipped_count} empty/invalid rows")
            
            # Verify by searching for known phrases
            print("\n🔍 Verifying loaded data:")
            test_phrases = [
                "arabic students",
                "teaching practice laboratory",
                "introduction to this module"
            ]
            
            for phrase in test_phrases:
                results = self.find_similar(phrase, target_lang="zu", limit=1)
                if results:
                    print(f"  Found: '{phrase}' → '{results[0]['output'][:50]}...'")
                else:
                    print(f"  Not found: '{phrase}'")
            
            return loaded_count
            
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            import traceback
            traceback.print_exc()
            return 0


# Test function
def test_memory():
    """Test the memory system"""
    print("Testing Translation Memory...")
    
    memory = TranslationMemory(persist_path="./data/test_memory")
    
    # Store some translations
    translations = [
        ("hello", "sawubona", "en", "zu", "test_session"),
        ("thank you", "ngiyabonga", "en", "zu", "test_session"),
        ("good morning", "sawubona", "en", "zu", "test_session"),
    ]
    
    for input_text, output_text, src, tgt, sess in translations:
        doc_id = memory.store_translation(
            input_text=input_text,
            output_text=output_text,
            source_lang=src,
            target_lang=tgt,
            session_id=sess
        )
        print(f"  Stored: {doc_id}")
    
    # Test similar search
    print("\nTesting similar search:")
    similar = memory.find_similar("hello", target_lang="zu")
    for item in similar:
        print(f"  Similar: '{item['input']}' → '{item['output']}' ({item['similarity']:.2f})")
    
    # Test session context
    print("\nTesting session context:")
    context = memory.get_session_context("test_session")
    for item in context[:3]:
        print(f"  Session item: {item}")
    
    # Get stats
    stats = memory.get_stats()
    print(f"\n📊 Memory stats: {stats}")
    
    print("\n✅ Memory test complete!")


if __name__ == "__main__":
    test_memory()