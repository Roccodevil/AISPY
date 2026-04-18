FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System packages needed for media processing / CV dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (CPU-friendly)
COPY requirements-cpu.txt /app/requirements-cpu.txt
RUN pip install --upgrade pip && \
    pip install -r requirements-cpu.txt && \
    pip install gunicorn && \
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy project files
COPY . /app

# Hugging Face Spaces exposes port 7860 by default
ENV PORT=7860
EXPOSE 7860

# Run Flask app in production mode
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 180"]
