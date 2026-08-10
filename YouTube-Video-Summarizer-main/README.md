# YouTube-Video-Summarizer

This project is a simple tool that automatically summarizes YouTube videos by extracting key points and presenting them in an easy-to-read format.

# Features

- Extracts video transcript.
- Generates a concise summary (extractive or Gemini-powered abstractive).
- User accounts (register/login) required to summarize videos.
- React frontend, Flask JSON API backend.

# Technologies Used

- **Backend:** Python, Flask, Flask-Login, Flask-SQLAlchemy (SQLite), Flask-CORS
- **Frontend:** React, React Router, Vite
- **Libraries:**
  - yt_dlp
  - moviepy
  - pydub
  - speech_recognition
  - transformers (`summarizer`)
  - torch
  - google-generativeai
  - python-dotenv
  - jspdf (PDF export)

# Getting Started

## Backend

```bash
cd YouTube-Video-Summarizer-main
python -m venv .venv
.venv\Scripts\activate        # Windows; use `source .venv/bin/activate` on macOS/Linux

# torch's +cpu wheels aren't on PyPI, install them from PyTorch's own index first
pip install torch==2.7.1 torchaudio==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`) with your `GEMINI_API_KEY` if you want abstractive summaries.

```bash
python main.py
```

Runs the API at `http://127.0.0.1:5000`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs the app at `http://localhost:5173` (proxies `/api` requests to the Flask backend).

# Usage
- Register or log in.
- Paste a YouTube video URL.
- Choose extractive or abstractive summarization.
- Read, copy, or download the summary as a PDF.

# Contributing
- Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.



