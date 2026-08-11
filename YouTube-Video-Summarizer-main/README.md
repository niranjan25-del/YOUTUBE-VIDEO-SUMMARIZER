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

# torch's CPU-only wheels aren't on PyPI, so they're installed separately
# (this is exactly what build.sh does, in order):
pip install -r requirements-torch.txt --index-url https://download.pytorch.org/whl/cpu
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

# Deployment

The frontend and backend deploy to two separate services — Vercel can't
run the Flask backend (it needs a persistent process, and `torch` +
`moviepy` exceed serverless size/time limits).

## Backend -> Render (or any host that runs a persistent Python process)

- **Root Directory:** `YouTube-Video-Summarizer-main`
- **Build Command:** `bash build.sh`
- **Start Command:** `gunicorn main:app --bind 0.0.0.0:$PORT`
- **Instance size:** needs enough RAM for `torch`/`transformers` — a free
  512MB tier will likely OOM; use at least a small paid instance.
- **Environment variables:**
  - `GEMINI_API_KEY` — your Gemini API key
  - `FLASK_SECRET_KEY` — a random secret (`python -c "import secrets; print(secrets.token_hex(32))"`)
  - `FRONTEND_ORIGIN` — your deployed frontend URL(s), comma-separated if more than one
    (e.g. `https://your-app.vercel.app,http://localhost:5173`)

Render automatically sets `RENDER=true`, which `main.py` uses to switch
the session cookie to `SameSite=None; Secure` (required for the frontend
and backend being on different domains).

## Frontend -> Vercel

- **Root Directory:** `YouTube-Video-Summarizer-main/frontend`
- **Framework Preset:** Vite
- **Environment variables:**
  - `VITE_API_BASE_URL` — your backend's URL + `/api`, e.g.
    `https://your-backend.onrender.com/api`

`frontend/vercel.json` handles the SPA rewrite so client-side routes
(`/login`, `/results`, ...) resolve on a direct load or refresh.

# Contributing
- Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.



