---
title: AISPY
emoji: 🕵️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# AISPY on Hugging Face Spaces (Docker)

This repository can be deployed as a **Docker Space** on Hugging Face.

## 1) Create the Space

1. Go to Hugging Face → **New Space**.
2. Choose:
   - **SDK**: `Docker`
   - **Visibility**: your choice (public/private)
3. Create the Space and push this repository code.

## 2) Required Space Secrets

Open your Space settings → **Variables and secrets** and add:

- `GROQ_API_KEY` (required)
- `TAVILY_API_KEY` (required for web search)
- `LANGCHAIN_API_KEY` (optional, if LangSmith tracing is enabled)
- `LANGCHAIN_TRACING_V2` (optional, usually `true`)
- `LANGCHAIN_PROJECT` (optional)

If your app uses additional providers, add those keys too.

## 3) Build & Run Behavior

- `Dockerfile` installs system packages (`ffmpeg`, `tesseract-ocr`, `libgl1`) needed by media/CV stack.
- Python dependencies are installed from `requirements-cpu.txt`.
- CPU-only PyTorch wheels are installed from the official CPU index.
- App runs with:
  - `gunicorn app:app --bind 0.0.0.0:${PORT}`
- Hugging Face provides `PORT` (default `7860`), matching Space config.

## 4) Local Test (Optional)

```bash
docker build -t aispy:local .
docker run --rm -it -p 7860:7860 \
  -e GROQ_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  aispy:local
```

Then open: `http://localhost:7860`

## 5) Notes

- First build can take time due to ML dependencies.
- If you hit memory limits on free CPU Spaces, reduce model size or move to upgraded hardware.
- Keep secrets only in Space settings (not in committed `.env` files).
