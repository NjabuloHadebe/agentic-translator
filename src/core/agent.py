# src/core/agent.py - FIXED VERSION
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uuid
import requests
import time
from typing import Dict, Optional

# Now imports from same directory will work
from dictionary_db import DictionaryDatabase
from validator import TranslationValidator
from memory import TranslationMemory


class AgenticTranslator:
    def __init__(self, session_id: str = None):
        print("🚀 Initializing Agentic Translator...")
        
        # Initialize YOUR existing components
        self.validator = TranslationValidator()  # YOUR validator
        self.dictionary = DictionaryDatabase()   # YOUR dictionary
        
        # Initialize memory but handle if methods don't exist
        try:
            self.memory = TranslationMemory()
            print("✅ Memory initialized")
        except Exception as e:
            print(f"⚠️  Memory initialization failed: {e}")
            self.memory = None
        
        self.session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        self.request_count = 0
        
        print(f"✅ Translator ready! Session: {self.session_id}")
    
    def _translate_api(self, text: str, target_lang: str = "zu") -> Optional[str]:
        """Translate using Google Translate API"""
        self.request_count += 1
        
        # Rate limiting
        if self.request_count % 5 == 0:
            time.sleep(1)
        
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'en',
                'tl': target_lang,
                'dt': 't',
                'q': text[:1000]
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0 and len(data[0]) > 0:
                    translation = ''.join([item[0] for item in data[0] if item[0]])
                    return translation.strip()
        except Exception as e:
            print(f"⚠️  API error: {e}")
        
        return None
    
    def translate(self, text: str, target_lang: str = "zu") -> Dict:
        """Main translation method"""
        print(f"\n{'='*50}")
        print(f"📋 Request: '{text[:50]}...' → {target_lang}")
        
        # 1. Validate input using YOUR validator
        validation_result = self.validator.validate_input(text, target_lang)
        if not validation_result.is_valid:
            print(f"❌ Validation failed: {validation_result.errors}")
            return {
                "error": True,
                "message": "Input validation failed",
                "errors": validation_result.errors,
                "session_id": self.session_id
            }
        
        cleaned_text = validation_result.sanitized_text
        
        # 2. Check dictionary first
        dict_translation = self.dictionary.get_exact_match(cleaned_text)
        if dict_translation:
            print(f"✅ Using dictionary")
            
            # Validate output using YOUR validator
            output_validation = self.validator.validate_output(
                cleaned_text, 
                dict_translation, 
                "dictionary"
            )
            
            return {
                "translation": dict_translation,
                "session_id": self.session_id,
                "source": "dictionary",
                "quality": output_validation["quality"],
                "confidence": output_validation["score"],
                "validation": {
                    "input_warnings": validation_result.warnings,
                    "output_quality": output_validation
                }
            }
        
        # 3. Check memory (FIXED: Uses find_similar() method)
        if self.memory:
            try:
                # FIX: Use find_similar() method from memory.py
                memory_results = self.memory.find_similar(
                    cleaned_text, 
                    target_lang=target_lang, 
                    limit=3
                )
                
                if memory_results and len(memory_results) > 0:
                    best_match = memory_results[0]
                    
                    # FIX: Lower threshold for better matching (0.7 instead of 0.8)
                    similarity = best_match.get('similarity', 0)
                    if similarity > 0.7:
                        print(f"✅ Using memory (similarity: {similarity:.2f})")
                        
                        # FIX: Get translation from 'output' field (not 'translation')
                        translation_text = best_match.get('output', '')
                        
                        output_validation = self.validator.validate_output(
                            cleaned_text, 
                            translation_text, 
                            "memory"
                        )
                        
                        return {
                            "translation": translation_text,
                            "session_id": self.session_id,
                            "source": "memory",
                            "quality": output_validation["quality"],
                            "confidence": similarity,
                            "validation": {
                                "input_warnings": validation_result.warnings,
                                "output_quality": output_validation
                            }
                        }
                    else:
                        print(f"⚠️  Memory found but similarity too low: {similarity:.2f}")
                        
            except Exception as e:
                print(f"⚠️  Memory error: {e}")
                import traceback
                traceback.print_exc()
        
        # 4. Try API
        print(f"🔍 No dictionary or memory match, trying API...")
        api_translation = self._translate_api(cleaned_text, target_lang)
        
        if api_translation and api_translation.lower() != cleaned_text.lower():
            print(f"✅ Using API")
            
            # Store in memory if available (FIXED: Uses store_translation method)
            if self.memory and hasattr(self.memory, 'store_translation'):
                try:
                    self.memory.store_translation(
                        input_text=cleaned_text,
                        output_text=api_translation,
                        source_lang='en',
                        target_lang=target_lang,
                        session_id=self.session_id,
                        metadata={"source": "api"}
                    )
                except Exception as e:
                    print(f"⚠️  Failed to store in memory: {e}")
            
            # Validate output
            output_validation = self.validator.validate_output(
                cleaned_text, 
                api_translation, 
                "api"
            )
            
            return {
                "translation": api_translation,
                "session_id": self.session_id,
                "source": "api",
                "quality": output_validation["quality"],
                "confidence": output_validation["score"],
                "validation": {
                    "input_warnings": validation_result.warnings,
                    "output_quality": output_validation
                }
            }
        
        # 5. Fallback
        print(f"⚠️  No translation found, returning original")
        
        output_validation = self.validator.validate_output(
            cleaned_text, 
            cleaned_text, 
            "none"
        )
        
        return {
            "translation": cleaned_text,
            "session_id": self.session_id,
            "source": "none",
            "quality": output_validation["quality"],
            "confidence": output_validation["score"],
            "validation": {
                "input_warnings": validation_result.warnings,
                "output_quality": output_validation
            }
        }

# Factory function (for your test_simple.py)
def create_translator(session_id: str = None):
    return AgenticTranslator(session_id=session_id)

# Test
if __name__ == "__main__":
    print("🧪 Testing Agent...")
    
    translator = create_translator("test_session")
    
    test_cases = [
        "Workshop",
        "vote of thanks & closing remarks",
        "Hello world",
        "registration and tea",
        "Dr. S. Ngcobo",
    ]
    
    for text in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: '{text}'")
        result = translator.translate(text, "zu")
        
        if "error" in result:
            print(f"❌ Error: {result['message']}")
        else:
            print(f"✅ Translation: {result['translation'][:100]}...")
            print(f"   Source: {result['source']}, Quality: {result['quality']}")