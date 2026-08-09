"""
News IQ - FastAPI Service
Powers embedding generation, video composition, and platform posting
Called by n8n via HTTP Request nodes
"""

import os
import json
import base64
import tempfile
import subprocess
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import numpy as np
from sentence_transformers import SentenceTransformer

load_dotenv()

app = FastAPI(title="News IQ Service", version="1.0.0")

# Global model (loaded once at startup)
embedding_model = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return embedding_model

# ============================================================================
# EMBEDDING ENDPOINTS
# ============================================================================

class EmbedRequest(BaseModel):
    texts: List[str]

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    count: int
    model: str

@app.post("/embed-batch", response_model=EmbedResponse)
async def embed_batch(request: EmbedRequest):
    """Generate embeddings for a batch of texts."""
    try:
        model = get_embedding_model()
        embeddings = model.encode(request.texts, convert_to_numpy=True)
        embeddings_list = embeddings.tolist()

        return EmbedResponse(
            embeddings=embeddings_list,
            count=len(embeddings_list),
            model="all-MiniLM-L6-v2"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed")
async def embed_single(text: str):
    """Generate embedding for a single text."""
    try:
        model = get_embedding_model()
        embedding = model.encode([text], convert_to_numpy=True)[0]
        return {"embedding": embedding.tolist(), "model": "all-MiniLM-L6-v2"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# VIDEO COMPOSITION ENDPOINTS
# ============================================================================

class VideoComposeRequest(BaseModel):
    audio_base64: str
    script_type: str = "daily_short"  # daily_short or weekly
    title: str = "News Short"
    expected_duration: int = 60

class VideoComposeResponse(BaseModel):
    video_path: str
    file_size_bytes: int
    duration_seconds: int
    format: str
    video_codec: str
    audio_codec: str
    success: bool

@app.post("/compose-video", response_model=VideoComposeResponse)
async def compose_video(request: VideoComposeRequest):
    """
    Compose a video from audio + background image using FFmpeg.
    Returns video metadata. Video file is saved to temp directory.
    """
    temp_dir = tempfile.mkdtemp(prefix="news_iq_video_")

    try:
        # Decode audio
        audio_path = os.path.join(temp_dir, "voiceover.mp3")
        with open(audio_path, "wb") as f:
            f.write(base64.b64decode(request.audio_base64))

        # Determine format
        is_daily = request.script_type == "daily_short"
        resolution = "1080x1920" if is_daily else "1920x1080"  # 9:16 vs 16:9
        format_str = "9:16" if is_daily else "16:9"

        # Create background image (solid color with text overlay capability)
        bg_path = os.path.join(temp_dir, "background.png")
        bg_color = "0x1a1a2e" if is_daily else "0x0f0f23"

        # Generate background using FFmpeg
        bg_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={bg_color}:s={resolution}:d=1",
            "-frames:v", "1",
            bg_path
        ]
        subprocess.run(bg_cmd, check=True, capture_output=True)

        # Compose final video
        video_path = os.path.join(temp_dir, "output.mp4")

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", bg_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-s", resolution,
            "-movflags", "+faststart",
            video_path
        ]

        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

        # Get video metadata
        file_size = os.path.getsize(video_path)

        # Get duration
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0

        return VideoComposeResponse(
            video_path=video_path,
            file_size_bytes=file_size,
            duration_seconds=int(duration),
            format=format_str,
            video_codec="h264",
            audio_codec="aac",
            success=True
        )

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "news-iq",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")))