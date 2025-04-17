# backend/stt.py
from faster_whisper import WhisperModel
import tempfile
import os
from typing import Dict, Any
import logging
from googletrans import Translator
import soundfile as sf
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up custom temp directory
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
tempfile.tempdir = TEMP_DIR

# Initialize the Whisper model
model = WhisperModel("base", device="cpu", compute_type="int8")

def transcribe_audio(audio_bytes: bytes, input_language: str = "en", output_language: str = "en") -> Dict[str, Any]:
    """
    Transcribe audio using Faster-Whisper model.
    """
    tmp_path = None  # Initialize tmp_path to ensure it exists in the finally block
    try:
        # Save the raw audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name  # Assign the temporary file path

        # Transcribe the audio file
        segments, info = model.transcribe(tmp_path, language=input_language)
        segments = list(segments)

        # Combine all segments into a single text
        original_text = " ".join([segment.text for segment in segments])

        # Translate the text if needed
        translated_text = original_text
        if input_language != output_language:
            translator = Translator()
            translated = translator.translate(original_text, src=input_language, dest=output_language)
            translated_text = translated.text

        return {
            "original_text": original_text.strip(),
            "translated_text": translated_text.strip(),
            "confidence": sum([segment.avg_logprob for segment in segments]) / max(len(segments), 1),
            "language": output_language,
            "segments": [{"text": s.text, "start": s.start, "end": s.end} for s in segments]
        }
    finally:
        # Ensure the temporary file is deleted if it was created
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)