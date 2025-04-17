# Healthcare Translation Web App

A medical translation application built with FastAPI and Streamlit that supports:
- Text Translation
- Speech-to-Text
- Text-to-Speech

## Features
- Medical text translation
- Speech recognition and translation
- Text-to-speech conversion
- Mobile-responsive interface
- Support for multiple languages

## Setup
1. Clone the repository
```bash
git clone <repository-url>
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the backend
```bash
cd backend
uvicorn app:app --reload
```

4. Run the frontend
```bash
cd frontend
streamlit run frontend.py
```

## Project Structure
- `/backend` - FastAPI backend
- `/frontend` - Streamlit frontend
- `/models` - ML models