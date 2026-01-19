# core/validator.py
import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    sanitized_text: str
    warnings: List[str]
    errors: List[str]
    metadata: Dict

class TranslationValidator:
    """Input validation for translation agent"""
    
    def __init__(self):
        self.config = {
            "max_length": 5000,
            "min_length": 1,
            "supported_languages": {"zu", "en", "af", "xh", "nso", "st", "ts", "ss", "ve", "tn", "nr"},
            "html_strip": True,
            "injection_check": True,
            "profanity_filter": False,
        }
    
    def validate_input(self, text: str, target_lang: str) -> ValidationResult:
        """Main validation pipeline"""
        result = ValidationResult(
            is_valid=True,
            sanitized_text=text,
            warnings=[],
            errors=[],
            metadata={
                "original_length": len(text),
                "target_lang": target_lang,
            }
        )
        
        # Run validations
        self._validate_not_empty(text, result)
        if result.is_valid:
            self._validate_language(target_lang, result)
        if result.is_valid:
            self._validate_length(text, result)
        if result.is_valid:
            self._sanitize_text(result)
        if result.is_valid and self.config["injection_check"]:
            self._check_injection(result)
        if result.is_valid:
            self._check_suspicious_patterns(result)
        if result.is_valid:
            self._check_gibberish(result)
        
        return result
    
    def _validate_not_empty(self, text: str, result: ValidationResult):
        if not text or not text.strip():
            result.is_valid = False
            result.errors.append("Text cannot be empty or whitespace only")
    
    def _validate_language(self, target_lang: str, result: ValidationResult):
        if target_lang not in self.config["supported_languages"]:
            result.is_valid = False
            result.errors.append(
                f"Unsupported language: '{target_lang}'. "
                f"Supported: {', '.join(sorted(self.config['supported_languages']))}"
            )
    
    def _validate_length(self, text: str, result: ValidationResult):
        length = len(text)
        if length < self.config["min_length"]:
            result.is_valid = False
            result.errors.append(
                f"Text too short ({length} chars). Minimum: {self.config['min_length']}"
            )
        
        if length > self.config["max_length"]:
            result.sanitized_text = text[:self.config["max_length"]]
            result.warnings.append(
                f"Text truncated from {length} to {self.config['max_length']} characters"
            )
            result.metadata["truncated"] = True
            result.metadata["truncated_from"] = length
    
    def _sanitize_text(self, result: ValidationResult):
        text = result.sanitized_text
        
        if self.config["html_strip"]:
            text = re.sub(r'<[^>]+>', '', text)
        
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        try:
            text = text.encode('utf-8', 'ignore').decode('utf-8')
        except:
            pass
        
        if text != result.sanitized_text:
            result.metadata["was_sanitized"] = True
        result.sanitized_text = text
    
    def _check_injection(self, result: ValidationResult):
        banned_patterns = [
            r"<script.*?>.*?</script>",
            r"eval\(.*\)",
            r"javascript:",
            r"onload\s*=",
            r"onerror\s*=",
        ]
        
        for pattern in banned_patterns:
            if re.search(pattern, result.sanitized_text, re.IGNORECASE):
                result.is_valid = False
                result.errors.append("Potentially dangerous content detected")
                break
    
    def _check_suspicious_patterns(self, result: ValidationResult):
        text = result.sanitized_text
        
        # Check for repeated characters
        if re.search(r'(.)\1{4,}', text):
            result.warnings.append("Repeated characters detected - may be gibberish")
        
        # Check for URL-like patterns
        if re.search(r'https?://|www\.', text):
            result.warnings.append("Text contains URLs")
        
        # Check for excessive punctuation
        if text.count('!') > 5 or text.count('?') > 5:
            result.warnings.append("Excessive punctuation")
    
    def _check_gibberish(self, result: ValidationResult):
        """Detect gibberish/meaningless text"""
        text = result.sanitized_text.lower()
        words = text.split()
        
        if not words:
            return
        
        # Check 1: Words with no vowels (likely gibberish)
        vowel_count = 0
        for word in words[:5]:  # Check first 5 words
            if re.search(r'[aeiouy]', word):
                vowel_count += 1
        
        vowel_ratio = vowel_count / min(len(words), 5)
        if vowel_ratio < 0.3:
            result.warnings.append("Text may be gibberish (few vowels detected)")
        
        # Check 2: Repeated character patterns
        if re.search(r'(.)\1{3,}', text):  # Same character 4+ times
            result.warnings.append("Repeated character patterns detected")
        
        # Check 3: Random letter sequences
        random_patterns = [
            r'[b-df-hj-np-tv-z]{5,}',  # 5+ consonants in a row
            r'[aeiou]{4,}',  # 4+ vowels in a row
        ]
        
        for pattern in random_patterns:
            if re.search(pattern, text):
                result.warnings.append("Unusual letter sequence detected")
                break
        
        # Check 4: Mixed case weirdness (like "cMe" instead of "cme" or "CME")
        if not text.islower() and not text.isupper() and not text.istitle():
            # Count mixed case words
            mixed_words = [w for w in words if not w.islower() and not w.isupper() and len(w) > 2]
            if len(mixed_words) / len(words) > 0.5:
                result.warnings.append("Unusual capitalization patterns")

    def validate_output(self, source_text: str, translated_text: str, source_type: str) -> Dict:
        """Validate translation output quality"""
        if not translated_text:
            return {"quality": "error", "warnings": ["No translation produced"]}
        
        quality = "medium"
        warnings = []
        score = 0.8
        
        # Check if API returned same text (bad response)
        if source_type == "api" and translated_text.lower() == source_text.lower():
            quality = "low"
            warnings.append("API returned same text - possibly gibberish input")
            score = 0.2
            return {"quality": quality, "score": score, "warnings": warnings, "source_type": source_type}
        
        # Length ratio check
        if len(source_text) > 0:
            ratio = len(translated_text) / len(source_text)
            if ratio < 0.3:
                quality = "low"
                warnings.append(f"Translation too short (ratio: {ratio:.2f})")
                score = 0.3
            elif ratio > 3.0:
                quality = "low"
                warnings.append(f"Translation too long (ratio: {ratio:.2f})")
                score = 0.4
        
        # Dictionary sources get higher score
        if source_type == "dictionary":
            quality = "high"
            score = 0.95
        
        # Check for placeholder indicators
        placeholders = ["[UNK]", "[MASK]", "???", "<...>", "##"]
        if any(ph in translated_text for ph in placeholders):
            quality = "low"
            warnings.append("Contains untranslated markers")
            score = 0.5
        
        return {
            "quality": quality,
            "score": score,
            "warnings": warnings,
            "source_type": source_type,
            "length_ratio": len(translated_text) / len(source_text) if len(source_text) > 0 else 0,
        }