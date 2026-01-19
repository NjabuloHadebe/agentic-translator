# core/agent.py - FIXED VERSION
import uuid
import time
from typing import Dict, Optional, List
from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from core.memory import TranslationMemory
from core.logger import TranslationLogger

class AgenticTranslator:
    def __init__(self, session_id: str = None):
        print("🚀 Initializing Translator...")
        
        # Local LLM (free) - use llama2 since you have it
        self.llm = Ollama(model="llama2", temperature=0.1)
        print("✅ LLM loaded (llama2)")
        
        # Memory
        self.memory = TranslationMemory()
        
        # Logger
        self.logger = TranslationLogger()
        
        # Session
        self.session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        
        # Create a simple translation chain (NO AGENT TOOLS)
        self.translation_prompt = PromptTemplate(
            input_variables=["text", "target_lang"],
            template="""Translate this to {target_lang}. Return ONLY the translation, no explanations.
            
            Text: "{text}"
            
            Translation: """
        )
        
        self.translation_chain = LLMChain(
            llm=self.llm,
            prompt=self.translation_prompt
        )
        
        print(f"✅ Translator ready (Session: {self.session_id})")
    
    def get_accurate_translation(self, text: str, target_lang: str) -> str:
        """Get accurate translation with better prompting"""
        
        # Common translations for accuracy
        common_translations = {
            ('hello', 'zu'): 'Sawubona',
            ('thank you', 'zu'): 'Ngiyabonga',
            ('thanks', 'zu'): 'Ngiyabonga',
            ('how are you', 'zu'): 'Unjani?',
            ('good morning', 'zu'): 'Sawubona',
            ('yes', 'zu'): 'Yebo',
            ('no', 'zu'): 'Cha',
            ('please', 'zu'): 'Ngiyacela',
            ('sorry', 'zu'): 'Ngiyaxolisa',
            ('water', 'zu'): 'Amanzi',
        }
        
        # Check common translations first
        text_lower = text.lower().strip()
        for (key, lang), translation in common_translations.items():
            if lang == target_lang and key in text_lower:
                return translation
        
        # Use LLM for other translations
        try:
            result = self.translation_chain.run(
                text=text,
                target_lang=target_lang
            )
            
            # Clean the result
            result = result.strip()
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1]
            
            return result
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            return f"Error: {str(e)[:50]}"
    
    def translate(self, 
                 text: str, 
                 target_lang: str,
                 source_lang: str = "en",
                 use_memory: bool = True) -> Dict:
        """Main translation method - SIMPLIFIED"""
        
        print(f"\n{'='*50}")
        print(f"📋 Translating: '{text}' → {target_lang}")
        
        # Check memory for similar translations
        similar_translations = []
        if use_memory:
            similar_translations = self.memory.find_similar(
                query_text=text,
                target_lang=target_lang,
                session_id=self.session_id,
                limit=2
            )
            
            if similar_translations:
                print(f"🔍 Found {len(similar_translations)} similar translations")
                # Use the most similar one
                best_match = max(similar_translations, key=lambda x: x.get('similarity', 0))
                if best_match.get('similarity', 0) > 0.8:
                    print(f"🎯 Using similar: {best_match['output'][:50]}...")
                    translation = best_match['output']
                else:
                    translation = self.get_accurate_translation(text, target_lang)
            else:
                translation = self.get_accurate_translation(text, target_lang)
        else:
            translation = self.get_accurate_translation(text, target_lang)
        
        print(f"✅ Translation: {translation}")
        
        # Store in memory (with FIXED metadata)
        memory_id = ""
        if use_memory and translation and not translation.startswith("Error"):
            try:
                # FIX: Convert list to string for ChromaDB
                tools_used_str = "llama2_chain"
                
                memory_id = self.memory.store_translation(
                    input_text=text,
                    output_text=translation,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    session_id=self.session_id,
                    metadata={
                        "tools_used": tools_used_str,  # STRING, not list
                        "confidence": "0.9",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                )
            except Exception as e:
                print(f"⚠️  Memory error: {e}")
        
        # Log the translation (logger can handle lists)
        try:
            self.logger.log(
                input_text=text,
                output_text=translation,
                source_lang=source_lang,
                target_lang=target_lang,
                session_id=self.session_id,
                tools_used=["llama2_chain"],  # Logger accepts lists
                confidence=0.9,
                memory_id=memory_id,
                similar_found=len(similar_translations)
            )
        except Exception as e:
            print(f"⚠️  Logging error: {e}")
        
        return {
            "translation": translation,
            "session_id": self.session_id,
            "similar_found": len(similar_translations),
            "memory_used": use_memory,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "memory_id": memory_id
        }

# Factory function
def create_translator(session_id: str = None):
    return AgenticTranslator(session_id=session_id)