# core/prompts.py
ZULU_TRANSLATION_GUIDE = """
You are an expert isiZulu translator. Follow these rules:

1. COMMON ZULU TRANSLATIONS (use these exactly):
   - Hello → Sawubona
   - Thank you → Ngiyabonga
   - How are you? → Unjani? (singular) / Ninjani? (plural)
   - Good morning → Sawubona (morning greeting)
   - Good afternoon → Sawubona (afternoon greeting)
   - Good evening → Sawubona (evening greeting)
   - Yes → Yebo
   - No → Cha
   - Water → Amanzi
   - Food → Ukudla
   - Please → Ngiyacela
   - Sorry → Ngiyaxolisa

2. Translation rules:
   - Return ONLY the isiZulu translation
   - No explanations, no English text
   - If unsure, use common translations above
   - Keep it simple and accurate

3. For other languages, provide accurate translations.

Text to translate: "{text}"
Target language: {target_lang}

Translation:
"""

def get_translation_prompt(text: str, target_lang: str) -> str:
    """Get the appropriate prompt based on target language"""
    
    if target_lang.lower() in ['zu', 'zulu', 'isizulu']:
        return ZULU_TRANSLATION_GUIDE.format(text=text, target_lang="isiZulu")
    else:
        return f"""Translate this text to {target_lang}. 
Return ONLY the translation, no explanations.

Text: "{text}"

Translation: """