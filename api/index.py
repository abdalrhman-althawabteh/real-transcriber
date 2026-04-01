import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models import TranscribeRequest, TranscribeResponse
from downloader import download_video
from audio import extract_audio
from transcribe_openai import transcribe_with_openai
from transcribe_gemini import transcribe_with_gemini
from utils import is_valid_instagram_url, cleanup_files

import yt_dlp.utils as yt_utils


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.tmp_dir, exist_ok=True)
    yield


app = FastAPI(title="Instagram Reel Transcriber", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(req: TranscribeRequest):

    if not is_valid_instagram_url(req.url):
        raise HTTPException(
            status_code=422,
            detail="Invalid Instagram URL. Must be a public reel, post, or IGTV link.",
        )

    if req.provider == "openai" and not settings.openai_api_key:
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY is not configured.",
        )
    if req.provider == "gemini" and not settings.gemini_api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY is not configured.",
        )

    video_path = None
    audio_path = None
    was_trimmed = False

    try:
        loop = asyncio.get_event_loop()

        video_path = await loop.run_in_executor(
            None, download_video, req.url, settings.tmp_dir
        )

        if req.provider == "openai":
            audio_path, was_trimmed = await loop.run_in_executor(
                None, extract_audio, video_path, settings.max_file_size_mb
            )
            result = await transcribe_with_openai(audio_path, req.language, req.prompt)

        else:
            result = await loop.run_in_executor(
                None, transcribe_with_gemini, video_path, req.language
            )

        return TranscribeResponse(
            transcript=result["transcript"],
            provider=req.provider,
            duration_seconds=result.get("duration_seconds"),
            language_detected=result.get("language_detected"),
            warning="Audio was re-encoded at lower bitrate to fit 25MB limit." if was_trimmed else None,
        )

    except yt_utils.DownloadError as e:
        msg = str(e)
        hint = ""
        if "login" in msg.lower() or "private" in msg.lower() or "404" in msg:
            hint = " This may be a private reel. Try setting COOKIES_FROM_BROWSER=chrome in your .env file."
        raise HTTPException(status_code=422, detail=f"Could not download reel: {msg}{hint}")

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cleanup_files(video_path, audio_path)
