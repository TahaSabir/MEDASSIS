import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import secrets
import bleach
from pathlib import Path
from gtts import gTTS
from fastapi.responses import JSONResponse, FileResponse
from backend.translation import translate_text, SUPPORTED_LANGUAGES
from backend.stt import transcribe_audio  # Correct import
from pydantic import BaseModel, validator
import logging
from pydub import AudioSegment
import base64
from typing import Literal
from googletrans import Translator

# Security configurations
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))

# Configure rate limiter
limiter = Limiter(key_func=get_remote_address)

# Configure secure file handling
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

def secure_filename(filename: str) -> str:
    ext = Path(filename).suffix
    return f"{secrets.token_urlsafe(16)}{ext}"

# Add near the top of the file, after imports
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Map ISO 639-1 language codes to supported languages in gTTS
LANGUAGE_VOICE_MAP = {
    "en": "en",  # English
    "es": "es",  # Spanish
    "fr": "fr",  # French
    "de": "de",  # German
    "it": "it",  # Italian
    "pt": "pt",  # Portuguese
    "ru": "ru",  # Russian
    "zh-CN": "zh-CN",  # Chinese (Simplified)
    "zh-TW": "zh-TW",  # Chinese (Traditional)
    "ja": "ja",  # Japanese
    "ar": "ar",  # Arabic
    "hi": "hi",  # Hindi
    "ko": "ko",  # Korean
    "nl": "nl",  # Dutch
    "sv": "sv",  # Swedish
    "no": "no",  # Norwegian
    "da": "da",  # Danish
    "fi": "fi",  # Finnish
    "pl": "pl",  # Polish
    "cs": "cs",  # Czech
    "el": "el",  # Greek
    "ro": "ro",  # Romanian
    "hu": "hu",  # Hungarian
    "id": "id",  # Indonesian
    "vi": "vi",  # Vietnamese
    "th": "th",  # Thai
    "tr": "tr",  # Turkish
    "uk": "uk",  # Ukrainian
    "bn": "bn",  # Bengali
    "ta": "ta",  # Tamil
    "te": "te",  # Telugu
    "ml": "ml",  # Malayalam
    "kn": "kn",  # Kannada
    "mr": "mr",  # Marathi
    "gu": "gu",  # Gujarati
    "pa": "pa",  # Punjabi
    "ur": "ur",  # Urdu
    "si": "si",  # Sinhala
    "my": "my",  # Burmese
    "jw": "jw",  # Javanese
    "su": "su",  # Sundanese
    "la": "la",  # Latin
    "cy": "cy",  # Welsh
    "af": "af",  # Afrikaans
    "zu": "zu",  # Zulu
}

def text_to_speech(text: str, output_path: str = "output/output.wav", source_language: str = "es", target_language: str = "en"):
    """
    Convert text to speech using gTTS (Google Text-to-Speech).
    Supports multiple languages and works in open-source environments.
    """
    try:
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Get the language for the target language
        target_voice = LANGUAGE_VOICE_MAP.get(target_language)
        if not target_voice:
            raise ValueError(
                f"Unsupported language '{target_language}'. Supported languages: {', '.join(LANGUAGE_VOICE_MAP.keys())}"
            )

        # Generate speech using gTTS
        tts = gTTS(text=text, lang=target_voice)
        tts.save(output_path)
        return output_path, text
    except Exception as e:
        raise RuntimeError(f"TTS conversion failed: {str(e)}")
# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Healthcare Translation Web App")

# Add security middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

class TranslateRequest(BaseModel):
    text: str
    source_language: str
    target_language: str

class TTSRequest(BaseModel):
    text: str
    target_language: str

    @validator('text')
    def sanitize_text(cls, v):
        return bleach.clean(v)

    @validator('target_language')
    def validate_language(cls, v):
        if v not in LANGUAGE_VOICE_MAP:
            raise ValueError(f"Unsupported language '{v}'. Supported languages: {', '.join(LANGUAGE_VOICE_MAP.keys())}")
        return v

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Healthcare Translation Web App!"}

@app.post("/translate")
async def translate_endpoint(request: TranslateRequest):
    """
    Endpoint for text translation.
    Accepts text, source language, and target language as input.
    Returns the translated text.
    """
    try:
        result = translate_text(
            text=request.text,
            source_lang=request.source_language,
            target_lang=request.target_language
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/stt")
@limiter.limit("10/minute")
async def stt_endpoint(
    request: Request,
    audio_file: UploadFile = File(...),
    input_language: str = Form("en"),
    output_language: str = Form("en")
):
    try:
        # Read the file content
        content = await audio_file.read()
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 10MB."
            )

        # Process the audio using the transcribe_audio function
        transcription_result = transcribe_audio(
            audio_bytes=content,
            input_language=input_language,
            output_language=output_language
        )

        return JSONResponse({
            "success": True,
            **transcription_result
        })

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(
            {
                "success": False,
                "error": "Failed to process audio",
                "details": str(e)
            },
            status_code=500
        )

@app.post("/tts")
async def tts_endpoint(request: TTSRequest):
    try:
        # First translate the text
        translator = Translator()
        translated_text = translator.translate(request.text, dest=request.target_language).text
        
        # Generate the speech with translated text
        output_path, _ = text_to_speech(
            text=translated_text,  # Use the translated text
            output_path="output/output.wav",
            target_language=request.target_language
        )

        # Read the audio file and encode it in Base64
        with open(output_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Return the Base64-encoded audio and translated transcript
        return JSONResponse({
            "audio_file": audio_base64,
            "transcript": translated_text  # Return the translated text as transcript
        })
    except Exception as e:
        logger.error(f"TTS endpoint error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
