import React, { useState } from "react";
import axios from "axios";

function App() {
  const [inputText, setInputText] = useState("");
  const [targetLanguage, setTargetLanguage] = useState("Spanish");
  const [translatedText, setTranslatedText] = useState("");
  const [transcript, setTranscript] = useState("");
  const [ttsAudioUrl, setTtsAudioUrl] = useState("");

  const handleTranslate = async () => {
    try {
      const formData = new FormData();
      formData.append("text", inputText);
      formData.append("target_language", targetLanguage);
      const response = await axios.post("http://localhost:8000/translate", formData);
      setTranslatedText(response.data.translated_text);
    } catch (error) {
      console.error("Error during translation", error);
    }
  };

  const handleSTT = async (e) => {
    e.preventDefault();
    const file = e.target.elements.audio.files[0];
    const formData = new FormData();
    formData.append("audio_file", file);
    try {
      const response = await axios.post("http://localhost:8000/stt", formData);
      setTranscript(response.data.transcript);
    } catch (error) {
      console.error("Error during STT", error);
    }
  };

  const handleTTS = async () => {
    try {
      const formData = new FormData();
      formData.append("text", translatedText);
      const response = await axios.post("http://localhost:8000/tts", formData, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      setTtsAudioUrl(url);
    } catch (error) {
      console.error("Error during TTS", error);
    }
  };

  return (
    <div className="App">
      <h1>Healthcare Translation Web App</h1>

      {/* STT Section */}
      <div className="section">
        <h2>Speech-to-Text (STT)</h2>
        <form onSubmit={handleSTT}>
          <input type="file" name="audio" accept="audio/*" />
          <button type="submit">Transcribe</button>
        </form>
        {transcript && (
          <>
            <h3>Transcript</h3>
            <p>{transcript}</p>
          </>
        )}
      </div>

      {/* Translation Section */}
      <div className="section">
        <h2>Translation</h2>
        <textarea
          rows="4"
          placeholder="Enter text (or use STT transcript)..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        ></textarea>
        <br />
        <label>
          Select Target Language:{" "}
          <select value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)}>
            <option value="Spanish">Spanish</option>
            <option value="French">French</option>
            <option value="Italian">Italian</option>
          </select>
        </label>
        <br />
        <button onClick={handleTranslate}>Translate</button>
        {translatedText && (
          <>
            <h3>Translated Text</h3>
            <p>{translatedText}</p>
            <button onClick={handleTTS}>Speak</button>
          </>
        )}
      </div>

      {/* Audio Playback */}
      {ttsAudioUrl && (
        <div className="section">
          <h2>Audio Playback</h2>
          <audio controls src={ttsAudioUrl}></audio>
        </div>
      )}
    </div>
  );
}

export default App;
