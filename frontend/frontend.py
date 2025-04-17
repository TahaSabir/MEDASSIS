import streamlit as st
import requests
from audio_recorder_streamlit import audio_recorder
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
API_URL = "http://127.0.0.1:8000"  # Replace with your deployed backend URL

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
    
    input_text = st.text_area(
        "Enter text to translate",
        height=150,
        key="translation_input"
    )
    
    if st.button("Translate", key="translate_button"):
        with st.spinner("Translating..."):
            if input_text.strip():
                try:
                    response = requests.post(
                        f"{API_URL}/translate",
                        json={
                            "text": input_text,
                            "source_language": source_lang,
                            "target_language": target_lang
                        }
                    )
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
    
    # Input Language Selection
    input_lang = st.selectbox(
        "Input Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="stt_input_lang"
    )
    
    # Output Language Selection
    output_lang = st.selectbox(
        "Output Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="stt_output_lang"
    )
    
    st.markdown("### Record Audio")
    audio_data = audio_recorder()

    st.markdown("### Or Upload Audio File")
    uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "ogg"])

    if audio_data or uploaded_file:
        if audio_data:
            st.audio(audio_data, format="audio/wav")
            audio_to_process = audio_data
        elif uploaded_file:
            st.audio(uploaded_file, format=uploaded_file.type)
            audio_to_process = uploaded_file.read()

        if st.button("Process Audio", key="process_audio_button"):
            with st.spinner("Processing audio..."):
                try:
                    # Send audio data to the backend
                    files = {"audio_file": ("audio.wav", audio_to_process, "audio/wav")}
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
                        if "transcribed_text" in result:
                            st.subheader("Transcribed Text:")
                            st.write(result["transcribed_text"])
                        else:
                            st.error("Error: 'transcribed_text' not found in the response.")
                    else:
                        st.error(f"Error: {response.json().get('error', 'Failed to process audio')}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

def show_tts_mode():
    st.header("Text-to-Speech")
    
    input_text = st.text_area(
        "Enter text",
        height=100,
        key="tts_input"
    )
    
    target_lang = st.selectbox(
        "Select Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="tts_target"
    )
    
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
                    
                    # Display the transcribed text
                    if "transcribed_text" in result:
                        st.subheader("Transcribed Text:")
                        st.write(result["transcribed_text"])
                    else:
                        st.warning("Transcribed text not found in the response.")
                    
                    # Play the generated audio
                    if "audio_file" in result:
                        audio_bytes = base64.b64decode(result["audio_file"])
                        st.audio(audio_bytes, format="audio/wav")
                    else:
                        st.error("Audio file not found in the response.")
                else:
                    st.error("Failed to generate speech")
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
