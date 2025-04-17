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
You are a specialized medical translation assistant. Translate the following medical text from {source_lang_name} to {target_lang_name}.
Return only the translated text without any additional information or repetition.

Original Text:
{text}

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

            # Post-process the output to remove duplicate sentences
            sentences = translated_text.split(". ")
            seen = set()
            cleaned_sentences = []
            for sentence in sentences:
                if sentence not in seen:
                    cleaned_sentences.append(sentence)
                    seen.add(sentence)
            translated_text = ". ".join(cleaned_sentences).strip()

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

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio to text.
    
    Args:
        audio_path (str): Path to the audio file to transcribe.
    
    Returns:
        str: Transcribed text from the audio file.
    """
    # Placeholder implementation (replace with actual transcription logic)
    return "Transcribed text from audio"

# Make sure to expose the function in __all__
__all__ = ['translate_text', 'SUPPORTED_LANGUAGES', 'transcribe_audio']
