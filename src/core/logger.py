# src/core/logger.py
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import threading

class TranslationLogger:
    """Logger for agentic translation system"""
    
    def __init__(self, log_file: str = "./data/translation_logs.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        print(f"Logger initialized: {log_file}")
    
    def log(self, 
           input_text: str, 
           output_text: str,
           source_lang: str = "en",
           target_lang: str = "zu",
           session_id: str = "default",
           agent_thoughts: str = "",
           tools_used: List[str] = None,
           confidence: float = None,
           **extra_fields):
        """Log a translation event"""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "input": input_text,
            "output": output_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "tools_used": tools_used or [],
            "confidence": confidence,
            "agent_thoughts": agent_thoughts,
            **extra_fields
        }
        
        # Thread-safe write
        with self._lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        print(f"Logged: '{input_text[:30]}...' → '{output_text[:30]}...'")
    
    def read_logs(self, limit: int = 100, session_id: Optional[str] = None) -> List[Dict]:
        """Read recent logs"""
        if not self.log_file.exists():
            return []
        
        logs = []
        with self._lock:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:  # Read last N lines
                    if line.strip():
                        try:
                            log_entry = json.loads(line.strip())
                            if session_id is None or log_entry.get("session_id") == session_id:
                                logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
        
        return logs
    
    def get_stats(self) -> Dict[str, Any]:
        """Get simple statistics from logs"""
        logs = self.read_logs(limit=1000)
        if not logs:
            return {}
        
        stats = {
            "total_translations": len(logs),
            "by_language": {},
            "avg_confidence": 0,
            "tool_usage": {},
            "recent_sessions": set(),
            "log_file": str(self.log_file)
        }
        
        confidences = []
        for log in logs:
            # Count by target language
            target = log.get("target_lang", "unknown")
            stats["by_language"][target] = stats["by_language"].get(target, 0) + 1
            
            # Track session IDs
            stats["recent_sessions"].add(log.get("session_id", "unknown"))
            
            # Track confidence
            conf = log.get("confidence")
            if conf is not None:
                confidences.append(conf)
            
            # Track tool usage
            for tool in log.get("tools_used", []):
                stats["tool_usage"][tool] = stats["tool_usage"].get(tool, 0) + 1
        
        if confidences:
            stats["avg_confidence"] = sum(confidences) / len(confidences)
        
        # Convert set to list
        stats["recent_sessions"] = list(stats["recent_sessions"])
        
        return stats
    
    def clear_logs(self):
        """Clear all logs (use with caution)"""
        with self._lock:
            if self.log_file.exists():
                self.log_file.unlink()
                print("🧹 Cleared all logs")
    
    def export_logs(self, output_file: str = "./data/logs_export.json"):
        """Export logs to JSON file"""
        logs = self.read_logs(limit=10000)  # Export up to 10k logs
        export_path = Path(output_file)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(logs)} logs to {output_file}")


# Test function
def test_logger():
    """Test the logger"""
    print("🧪 Testing Translation Logger...")
    
    # Create test logger
    test_logger = TranslationLogger("./data/test_logs.jsonl")
    
    # Log some translations
    test_logger.log(
        input_text="Hello",
        output_text="Sawubona",
        source_lang="en",
        target_lang="zu",
        session_id="test_session_1",
        agent_thoughts="Used dictionary lookup",
        tools_used=["dictionary", "cache"],
        confidence=0.95
    )
    
    test_logger.log(
        input_text="Thank you",
        output_text="Ngiyabonga",
        source_lang="en",
        target_lang="zu",
        session_id="test_session_1",
        agent_thoughts="Direct translation from memory",
        tools_used=["memory"],
        confidence=0.98
    )
    
    # Read logs
    logs = test_logger.read_logs()
    print(f"Logged {len(logs)} entries")
    
    # Get stats
    stats = test_logger.get_stats()
    print(f"Stats: {stats}")
    
    print("Logger test complete!")


if __name__ == "__main__":
    test_logger()

# Optional: Singleton instance
# logger = TranslationLogger()