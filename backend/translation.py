import os
from typing import Dict, Any
from llama_cpp import Llama
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported languages with their full names
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ar": "Arabic"
}

# Model configuration
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.gguf")
DEFAULT_CONTEXT_SIZE = 512
DEFAULT_THREADS = 4

# Enhanced prompt template for medical translation
PREPROMPT_TEMPLATE = """
You are a specialized medical translation assistant. Please translate the following medical text:

Source Language: {source_lang} ({source_lang_name})
Target Language: {target_lang} ({target_lang_name})

Original Text:
{text}

Requirements:
- Maintain medical terminology accuracy
- Preserve formal medical tone
- Keep formatting and punctuation
- Ensure cultural appropriateness

Translation:
"""

class MedicalTranslator:
    def __init__(self, model_path: str = MODEL_PATH):
        """Initialize the medical translator with the specified model."""
        try:
            self.llm = Llama(
                model_path=model_path,
                n_ctx=DEFAULT_CONTEXT_SIZE,
                n_threads=DEFAULT_THREADS
            )
            logger.info(f"Model loaded successfully from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise

    def translate_text(self, text: str, source_lang: str = "en", target_lang: str = "es") -> Dict[str, Any]:
        """
        Translate medical text between supported languages.
        
        Args:
            text (str): The medical text to translate
            source_lang (str): Source language code (e.g., 'en', 'es')
            target_lang (str): Target language code (e.g., 'en', 'es')
            
        Returns:
            Dict[str, Any]: Dictionary containing translation results and metadata
        """
        try:
            # Validate languages
            if source_lang not in SUPPORTED_LANGUAGES:
                raise ValueError(f"Source language '{source_lang}' not supported")
            if target_lang not in SUPPORTED_LANGUAGES:
                raise ValueError(f"Target language '{target_lang}' not supported")

            # Skip translation if languages are the same
            if source_lang == target_lang:
                return {
                    "translated_text": text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "confidence": 1.0
                }

            # Prepare the prompt
            prompt = PREPROMPT_TEMPLATE.format(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                source_lang_name=SUPPORTED_LANGUAGES[source_lang],
                target_lang_name=SUPPORTED_LANGUAGES[target_lang]
            )

            # Generate translation
            response = self.llm(
                prompt=prompt,
                max_tokens=DEFAULT_CONTEXT_SIZE,
                stop=["\n\n"],
                temperature=0.3,  # Lower temperature for more accurate translations
                top_p=0.95
            )

            # Extract and clean the translated text
            translated_text = response["choices"][0]["text"].strip()

            # Remove any unwanted keywords or template artifacts
            unwanted_keywords = ["Translation:", "Source Language:", "Target Language:"]
            for keyword in unwanted_keywords:
                translated_text = translated_text.replace(keyword, "").strip()

            # Handle cases where logprobs is None
            confidence = response["choices"][0].get("logprobs", None)
            if confidence is None:
                confidence = 0.0  # Default confidence value if logprobs is not available

            return {
                "translated_text": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "confidence": float(confidence),
                "model_used": os.path.basename(MODEL_PATH)
            }

        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise

# Initialize the translator
translator = MedicalTranslator()

def translate_text(text: str, source_lang: str = "en", target_lang: str = "es") -> Dict[str, Any]:
    """Wrapper function for the translator to be used by the API."""
    return translator.translate_text(text, source_lang, target_lang)

# Make sure to expose the function in __all__
__all__ = ['translate_text', 'SUPPORTED_LANGUAGES']
