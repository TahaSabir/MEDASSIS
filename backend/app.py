from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
# Change the relative
from backend.stt import transcribe_audio
from backend.tts import text_to_speech
from backend.translation import translate_text, SUPPORTED_LANGUAGES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Healthcare Translation Web App")

# Enable CORS for all origins (adjust as needed for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranslateRequest(BaseModel):
    text: str
    source_language: str
    target_language: str

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Healthcare Translation Web App!"}

@app.post("/translate")
async def translate_endpoint(request: TranslateRequest):
    try:
        result = translate_text(
            text=request.text,
            source_lang=request.source_language,
            target_lang=request.target_language
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )

@app.post("/stt")
async def stt_endpoint(
    audio_file: UploadFile = File(...),
    input_language: str = Form("en"),
    output_language: str = Form("en")
):
    """
    Endpoint for speech-to-text conversion using Faster-Whisper.
    Accepts WAV, MP3, OGG audio files.
    Returns transcription with confidence scores and timestamps.
    """
    if not audio_file.filename.endswith((".wav", ".mp3", ".ogg")):
        raise HTTPException(
            status_code=400, 
            detail="Supported formats: WAV, MP3, OGG"
        )
    
    try:
        contents = await audio_file.read()
        logger.info(f"Processing audio file: {audio_file.filename}")
        
        result = transcribe_audio(contents, input_language=input_language, output_language=output_language)
        
        return JSONResponse({
            "success": True,
            "text": result["text"],
            "confidence": result.get("confidence", 0.0),
            "language": result.get("language", "en"),
            "segments": result.get("segments", []),
            "file_processed": audio_file.filename
        })
        
    except RuntimeError as e:
        logger.error(f"Transcription failed: {str(e)}")
        return JSONResponse(
            {
                "success": False,
                "error": "Speech recognition failed",
                "details": str(e)
            }, 
            status_code=500
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(
            {
                "success": False,
                "error": "Internal server error",
                "details": str(e)
            }, 
            status_code=500
        )

@app.post("/tts")
async def tts_endpoint(
    text: str = Form(...),
    source_language: str = Form("en"),
    target_language: str = Form("en")
):
    """
    Endpoint for text-to-speech conversion using pyttsx3
    Accepts text, source language, and target language as input
    Returns the generated audio file
    """
    try:
        # Convert text to speech using pyttsx3
        output_file = text_to_speech(
            text=text,
            output_path="output/output.wav",
            source_language=source_language,
            target_language=target_language
        )
        return FileResponse(path=output_file, filename="output.wav", media_type="audio/wav")
    except Exception as e:
        logger.error(f"TTS conversion failed: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
