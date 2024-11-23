"""
Translation service implementation using OpenAI API
"""
from openai import OpenAI
import logging
import os

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self, api_key=None):
        """Initialize translation service with API key"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("No API key provided and OPENAI_API_KEY environment variable not set")
            raise ValueError("OpenAI API key is required. Please provide an API key or set OPENAI_API_KEY environment variable.")
        
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise

    def get_translation_prompt(self, source_lang, target_lang, context=None):
        """Generate translation prompt with optional context"""
        prompt = (
            f"You are a professional translator. Translate the following text from {source_lang} to {target_lang}.\n\n"
        )
        
        if context and context.strip() and context != "Add context to help with translation accuracy...":
            prompt += (
                f"Context for translation:\n"
                f"{context}\n\n"
            )
        
        prompt += (
            f"Guidelines:\n"
            f"1. Provide ONLY the translated text\n"
            f"2. Maintain the original tone and context\n"
            f"3. Use natural {target_lang} expressions\n"
            f"4. Preserve formatting and line breaks\n"
            f"5. NO explanations or additional text\n"
            f"6. Consider the provided context (if any) for more accurate translation"
        )
        return prompt
        
    def translate(self, text, source_lang, target_lang, context=None):
        """Translate text using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": self.get_translation_prompt(source_lang, target_lang, context)
                    },
                    {"role": "user", "content": text}
                ]
            )
            
            translation = response.choices[0].message.content.strip()
            return translation
            
        except Exception as e:
            logger.error(f"Error in translation: {str(e)}")
            raise
