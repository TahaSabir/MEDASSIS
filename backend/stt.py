# backend/stt.py
from faster_whisper import WhisperModel
import tempfile
import os
from typing import Dict, Any
import logging
from googletrans import Translator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transcribe_audio(audio_bytes: bytes, input_language: str = "en", output_language: str = "en") -> Dict[str, Any]:
    """
    Transcribe audio using Faster-Whisper large-v3 model optimized for medical vocabulary.
    Optionally translates the transcription into the desired output language.
    Returns a dictionary with transcription text and metadata.
    """
    try:
        # Initialize the Whisper model
        model = WhisperModel(
            model_size_or_path="large-v3",
            device="cpu",
            compute_type="int8",
            num_workers=4
        )

        # Create a temporary file and close it before passing to the model
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name  # Save the file path
        try:
            # Transcribe the audio file
            segments_generator, info = model.transcribe(
                tmp_path,
                beam_size=5,
                word_timestamps=True,
                vad_filter=True,
                language=input_language  # Use the specified input language
            )
            
            # Convert the generator to a list
            segments = list(segments_generator)
            
            # Combine all segments into a single text
            text = " ".join([segment.text for segment in segments])

            # Translate the text if the input and output languages are different
            if input_language != output_language:
                translator = Translator()
                translated = translator.translate(text, src=input_language, dest=output_language)
                text = translated.text

            # Prepare the response
            return {
                "text": text.strip(),
                "confidence": sum([segment.avg_logprob for segment in segments]) / max(len(segments), 1),
                "language": output_language,
                "segments": [{"text": s.text, "start": s.start, "end": s.end} for s in segments]
            }
        finally:
            # Ensure the temporary file is deleted
            os.remove(tmp_path)
            
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise RuntimeError(f"Transcription failed: {str(e)}")