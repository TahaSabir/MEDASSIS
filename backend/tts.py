import pyttsx3
import os
from googletrans import Translator

# Map ISO 639-1 language codes to system voice names
LANGUAGE_VOICE_MAP = {
    "en": "microsoft david desktop - english (united states)",  # English
    "es": "microsoft helena desktop - spanish (spain)",         # Spanish
    "fr": "microsoft hortense desktop - french (france)",       # French
    # Add more mappings as needed
}

def text_to_speech(text: str, output_path: str = "output/output.wav", source_language: str = "es", target_language: str = "en"):
    """
    Translate text (if needed) and convert it to speech using pyttsx3.
    Supports multiple voices and works in low-resource environments.
    """
    try:
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:  # Check if the directory part of the path is not empty
            os.makedirs(output_dir, exist_ok=True)

        # Initialize the translator
        translator = Translator()

        # Translate the text if the source and target languages are different
        if source_language != target_language:
            translated = translator.translate(text, src=source_language, dest=target_language)
            text = translated.text

        # Initialize pyttsx3 TTS engine
        engine = pyttsx3.init()

        # Get the voice for the target language
        target_voice = LANGUAGE_VOICE_MAP.get(target_language)
        if not target_voice:
            raise ValueError(
                f"Unsupported language '{target_language}'. Supported languages: {', '.join(LANGUAGE_VOICE_MAP.keys())}"
            )

        # Set the voice based on the target language
        voices = engine.getProperty("voices")
        for voice in voices:
            if target_voice.lower() in voice.name.lower():
                engine.setProperty("voice", voice.id)
                break
        else:
            raise ValueError(
                f"Voice for language '{target_language}' not found. Ensure the correct voice is installed on your system."
            )

        # Set speech rate (optional, adjust as needed)
        engine.setProperty("rate", 150)

        # Save the speech to a file
        engine.save_to_file(text, output_path)
        engine.runAndWait()

        return output_path
    except Exception as e:
        raise RuntimeError(f"TTS conversion failed: {str(e)}")


if __name__ == "__main__":
    # Take input dynamically
    text = input("Enter the text to convert to speech: ")
    source_language = input("Enter the source language (e.g., 'es' for Spanish): ")
    target_language = input("Enter the target language (e.g., 'en' for English): ")

    try:
        output_file = text_to_speech(
            text=text,
            output_path="output/medical_terms.wav",
            source_language=source_language,
            target_language=target_language
        )
        print(f"Speech saved to: {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")
