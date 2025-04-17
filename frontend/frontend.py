import streamlit as st
import requests
import json
from audio_recorder_streamlit import audio_recorder
import io
import soundfile as sf
import numpy as np
import time
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import wave
import os
import sounddevice as sd
import threading
import pyaudio
import base64

# Set page configuration
st.set_page_config(
    page_title="MedAssist - Healthcare Translation",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"  # Collapse sidebar by default on mobile
)

# Custom CSS
st.markdown("""
<style>
    /* Custom styles for responsiveness and UI improvements */
    .main {
        background-color: #f8f9fa;
        padding: 1rem;
    }
    .stButton>button {
        width: 100%;
        margin: 0.5rem 0;
        padding: 0.75rem;
        font-size: 1rem;
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        border: none;
    }
    audio {
        width: 100%;
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Backend API URL
API_URL = "http://127.0.0.1:8000"

# Supported languages
LANGUAGES = {
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

# Global variable to control recording
is_recording = False
audio_frames = []

def start_recording(sample_rate: int = 16000, chunk_size: int = 1024, channels: int = 1):
    """
    Start recording audio using pyaudio and save it as a WAV file.

    Args:
        sample_rate (int): Sampling rate for the recording.
        chunk_size (int): Size of each audio chunk.
        channels (int): Number of audio channels.
    """
    global is_recording, audio_frames
    is_recording = True
    audio_frames = []

    def record():
        global is_recording, audio_frames
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk_size)

        while is_recording:
            data = stream.read(chunk_size)
            audio_frames.append(data)

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save the recorded audio to a file
        os.makedirs("temp", exist_okay=True)
        output_path = "temp/recorded_audio.wav"
        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b"".join(audio_frames))

        # Save the audio to session state
        with open(output_path, "rb") as f:
            st.session_state["audio_bytes"] = f.read()

    # Start recording in a separate thread
    threading.Thread(target=record, daemon=True).start()

def stop_recording():
    """
    Stop the audio recording.
    """
    global is_recording
    is_recording = False
    st.success("Recording stopped. Audio saved to temp/recorded_audio.wav")

def show_loading_state():
    """Show loading animation with custom styling"""
    with st.spinner():
        st.markdown("""
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Processing...</p>
            </div>
        """, unsafe_allow_html=True)

def show_error(message: str, level: str = "error"):
    """Display user-friendly error messages"""
    if level == "error":
        st.error(f"⚠️ {message}")
    elif level == "warning":
        st.warning(f"⚠️ {message}")
    else:
        st.info(f"ℹ️ {message}")

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
    
    # Language selection in a single column on mobile
    source_lang = st.selectbox(
        "Source Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x]
    )
    
    target_lang = st.selectbox(
        "Target Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x]
    )
    
    # Full-width text area
    input_text = st.text_area(
        "Enter text to translate",
        height=150,
        key="translation_input"
    )
    
    if st.button("Translate", key="translate_button"):
        with st.spinner("Translating..."):  # Add loading indicator
            if input_text.strip():
                try:
                    # Send request to the backend
                    response = requests.post(
                        f"{API_URL}/translate",
                        json={
                            "text": input_text,
                            "source_language": source_lang,
                            "target_language": target_lang
                        }
                    )

                    # Handle the response
                    if response.status_code == 200:
                        result = response.json()
                        st.subheader("Translated Text:")
                        st.write(result["translated_text"])
                    else:
                        st.error(f"Error: {response.json().get('error', 'Unknown error occurred')}")

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please enter text to translate.")

def show_stt_mode():
    st.header("Speech-to-Text")
    
    # Language selection in a more compact layout
    col1, col2 = st.columns(2)
    with col1:
        input_lang = st.selectbox(
            "Input Language",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            key="stt_input_lang"
        )
    with col2:
        output_lang = st.selectbox(
            "Output Language",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            key="stt_output_lang"
        )
    
    # Audio input section with better organization
    st.markdown("### Audio Input")
    tab1, tab2 = st.tabs(["🎤 Record", "📁 Upload"])
    
    # Recording tab
    with tab1:
        if "recording" not in st.session_state:
            st.session_state.recording = False
        
        col_rec1, col_rec2 = st.columns([2, 1])
        with col_rec1:
            record_button = st.button(
                "🎤 " + ("Stop Recording" if st.session_state.recording else "Start Recording"),
                key="record_button",
                use_container_width=True
            )
        
        if record_button:
            st.session_state.recording = not st.session_state.recording
            if st.session_state.recording:
                start_recording()
            else:
                stop_recording()
                st.session_state["show_process_button"] = True
        
        # Show process button for recorded audio
        if st.session_state.get("show_process_button", False):
            if st.button("Process Recorded Audio", key="process_recorded_button", use_container_width=True):
                process_audio_file("temp/recorded_audio.wav", input_lang, output_lang)
    
    # Upload tab
    with tab2:
        audio_file = st.file_uploader(
            "Upload Audio File",
            type=["wav", "mp3", "ogg"],
            help="Supported formats: WAV, MP3, OGG"
        )
        
        if audio_file:
            st.audio(audio_file, format="audio/wav")
            if st.button("Process Uploaded Audio", key="process_upload_button", use_container_width=True):
                process_audio_file(audio_file, input_lang, output_lang)

def process_audio_file(audio_file, input_lang, output_lang):
    """Helper function to process audio files"""
    with st.spinner("Processing audio..."):
        try:
            # Prepare the files and data
            if isinstance(audio_file, str):
                # For recorded audio
                with open(audio_file, "rb") as f:
                    audio_bytes = f.read()
                files = {"audio_file": ("recorded_audio.wav", audio_bytes, "audio/wav")}
            else:
                # For uploaded audio
                files = {"audio_file": (audio_file.name, audio_file.getvalue(), "audio/wav")}
            
            data = {
                "input_language": input_lang,
                "output_language": output_lang
            }
            
            # Send request to backend
            response = requests.post(
                f"{API_URL}/stt",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Results section
                st.markdown("### Results")
                
                # Original text
                with st.expander("Original Text", expanded=True):
                    st.text_area(
                        "",
                        value=result.get("original_text", ""),
                        height=100,
                        disabled=True
                    )
                
                # Translated text (if languages differ)
                if input_lang != output_lang:
                    with st.expander("Translated Text", expanded=True):
                        st.text_area(
                            "",
                            value=result.get("translated_text", ""),
                            height=100,
                            disabled=True
                        )
            else:
                st.error(f"Error: {response.json().get('error', 'Failed to process audio')}")
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

def show_tts_mode():
    st.header("Text-to-Speech")
    
    # Input text
    input_text = st.text_area(
        "Enter text",
        height=100,
        key="tts_input",
        help="Type or paste your text here"  # Add helpful tooltip
    )
    
    # Language selection
    target_lang = st.selectbox(
        "Select Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="tts_target"
    )
    
    # Generate button
    if st.button("Generate Speech", key="tts_button"):
        if not input_text.strip():
            st.warning("Please enter some text")
            return
            
        with st.spinner("Generating audio..."):
            try:
                response = requests.post(
                    f"{API_URL}/tts",
                    json={
                        "text": input_text,
                        "target_language": target_lang
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    audio_bytes = base64.b64decode(result["audio_file"])
                    
                    # Display in a container
                    with st.container():
                        st.subheader("Generated Audio")
                        st.audio(audio_bytes, format="audio/wav")
                        
                        st.subheader("Transcript")
                        st.text_area(
                            "",
                            value=result["transcript"],
                            height=100,
                            disabled=True
                        )
                else:
                    st.error("Failed to generate speech")
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()