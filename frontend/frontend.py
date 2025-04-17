import streamlit as st
import requests
import json
from audio_recorder_streamlit import audio_recorder
import io
import soundfile as sf
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="MedAssist - Healthcare Translation",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    h1 {
        color: #2563eb;
    }
    .success-message {
        padding: 1rem;
        border-radius: 8px;
        background-color: #dcfce7;
        color: #166534;
    }
    .error-message {
        padding: 1rem;
        border-radius: 8px;
        background-color: #fee2e2;
        color: #991b1b;
    }
</style>
""", unsafe_allow_html=True)

# Backend API URL
API_URL = "http://localhost:8000"

# Supported languages
LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French"
}

def main():
    # Sidebar
    with st.sidebar:
        st.title("🏥 MedAssist")
        st.markdown("---")
        selected_mode = st.radio(
            "Select Mode",
            ["Translation", "Speech-to-Text", "Text-to-Speech"]
        )

    # Main content
    if selected_mode == "Translation":
        show_translation_mode()
    elif selected_mode == "Speech-to-Text":
        show_stt_mode()
    else:
        show_tts_mode()

def show_translation_mode():
    st.header("Medical Text Translation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source_lang = st.selectbox(
            "Source Language",
            options=LANGUAGES.keys(),
            format_func=lambda x: LANGUAGES[x],
            key="trans_source"
        )
        source_text = st.text_area(
            "Enter text to translate",
            height=200,
            key="trans_input"
        )
        
    with col2:
        target_lang = st.selectbox(
            "Target Language",
            options=LANGUAGES.keys(),
            format_func=lambda x: LANGUAGES[x],
            key="trans_target"
        )
        
    if st.button("Translate"):
        if source_text:
            try:
                response = requests.post(
                    f"{API_URL}/translate",
                    json={
                        "text": source_text,
                        "source_language": source_lang,
                        "target_language": target_lang
                    }
                )
                if response.status_code == 200:
                    translated_text = response.json()["translated_text"]
                    with col2:
                        st.text_area(
                            "Translation",
                            value=translated_text,
                            height=200,
                            key="trans_output"
                        )
                else:
                    st.error("Translation failed. Please try again.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter text to translate.")

def show_stt_mode():
    st.header("Speech-to-Text Conversion")
    
    input_lang = st.selectbox(
        "Select Input Language",
        options=LANGUAGES.keys(),
        format_func=lambda x: LANGUAGES[x],
        key="stt_input_lang"
    )
    
    output_lang = st.selectbox(
        "Select Output Language",
        options=LANGUAGES.keys(),
        format_func=lambda x: LANGUAGES[x],
        key="stt_output_lang"
    )
    
    # Audio input options
    audio_input = st.radio(
        "Choose audio input method",
        ["Upload Audio File", "Record Audio"]
    )
    
    if audio_input == "Upload Audio File":
        audio_file = st.file_uploader(
            "Upload an audio file",
            type=["wav", "mp3", "ogg"]
        )
        if audio_file:
            if st.button("Transcribe"):
                try:
                    files = {"audio_file": audio_file}
                    response = requests.post(
                        f"{API_URL}/stt",
                        files=files,
                        data={
                            "input_language": input_lang,
                            "output_language": output_lang
                        }
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.markdown("### Transcription")
                        st.write(result["text"])
                        st.markdown("### Confidence Score")
                        
                        # Normalize confidence score to be between 0 and 1
                        confidence = max(0.0, min(1.0, float(result["confidence"])))
                        st.progress(confidence)
                        st.text(f"Confidence: {confidence:.2%}")
                    else:
                        st.error("Transcription failed. Please try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        audio_bytes = audio_recorder()
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            if st.button("Transcribe"):
                try:
                    # Convert audio bytes to wav file
                    audio_data, _ = sf.read(io.BytesIO(audio_bytes))
                    with io.BytesIO() as wav_io:
                        sf.write(wav_io, audio_data, 44100, format='WAV')
                        wav_bytes = wav_io.getvalue()
                    
                    files = {"audio_file": ("recording.wav", wav_bytes)}
                    response = requests.post(
                        f"{API_URL}/stt",
                        files=files,
                        data={
                            "input_language": input_lang,
                            "output_language": output_lang
                        }
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.markdown("### Transcription")
                        st.write(result["text"])
                        st.markdown("### Confidence Score")
                        st.progress(float(result["confidence"]))
                    else:
                        st.error("Transcription failed. Please try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def show_tts_mode():
    st.header("Text-to-Speech Conversion")
    
    input_text = st.text_area(
        "Enter text to convert to speech",
        height=150
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        source_lang = st.selectbox(
            "Source Language",
            options=LANGUAGES.keys(),
            format_func=lambda x: LANGUAGES[x],
            key="tts_source"
        )
    
    with col2:
        target_lang = st.selectbox(
            "Target Language",
            options=LANGUAGES.keys(),
            format_func=lambda x: LANGUAGES[x],
            key="tts_target"
        )
    
    if st.button("Generate Speech"):
        if input_text:
            try:
                response = requests.post(
                    f"{API_URL}/tts",
                    data={
                        "text": input_text,
                        "source_language": source_lang,
                        "target_language": target_lang
                    }
                )
                if response.status_code == 200:
                    st.audio(response.content, format="audio/wav")
                else:
                    st.error("Speech generation failed. Please try again.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter text to convert to speech.")

if __name__ == "__main__":
    main()