import os
import logging
from gtts import gTTS
from googletrans import Translator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Map ISO 639-1 language codes to their corresponding codes for gTTS
LANGUAGE_VOICE_MAP = {
    "en": "en",  # English
    "es": "es",  # Spanish
    "fr": "fr",  # French
    "de": "de",  # German
    "it": "it",  # Italian
    "pt": "pt",  # Portuguese
    "ru": "ru",  # Russian
    "zh": "zh-CN",  # Chinese
    "ja": "ja",  # Japanese
    "ar": "ar"  # Arabic
}

def text_to_speech(text: str, output_path: str, target_language: str) -> tuple:
    """
    Convert text to speech using gTTS (Google Text-to-Speech).
    Takes already translated text and generates speech.
    Returns both the audio file path and the transcript.
    """
    try:
        logger.info(f"Starting TTS conversion for text: {text}")
        logger.info(f"Target language: {target_language}")

        # Ensure the output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Get the language code for the target language
        target_voice = LANGUAGE_VOICE_MAP.get(target_language)
        if not target_voice:
            raise ValueError(
                f"Unsupported language '{target_language}'. Supported languages: {', '.join(LANGUAGE_VOICE_MAP.keys())}"
            )

        # Generate speech using gTTS with the text (already translated)
        tts = gTTS(text=text, lang=target_voice)
        tts.save(output_path)

        logger.info(f"Speech saved to: {output_path}")

        # Return the audio file path and transcript
        return output_path, text
    except Exception as e:
        logger.error(f"TTS conversion failed: {str(e)}")
        raise RuntimeError("An error occurred while generating speech. Please try again.")


if __name__ == "__main__":
    # CLI for testing the TTS functionality
    text = input("Enter the text to convert to speech: ").strip()
    if not text:
        print("Error: Text cannot be empty.")
        exit(1)

    target_language = input("Enter the target language (e.g., 'en' for English) [default: 'en']: ").strip() or "en"

    try:
        output_file, transcript = text_to_speech(
            text=text,
            output_path="output/cli_test_output.wav",
            target_language=target_language
        )
        print(f"Speech saved to: {output_file}")
        print(f"Transcript: {transcript}")
    except Exception as e:
        print(f"Error: {str(e)}")
