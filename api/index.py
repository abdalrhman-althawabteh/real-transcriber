import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

from config import settings
from models import TranscribeRequest, TranscribeResponse
from utils import is_valid_instagram_url, cleanup_files


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


@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))

@app.get("/style.css")
async def serve_css():
    return FileResponse(os.path.join(PUBLIC_DIR, "style.css"), media_type="text/css")

@app.get("/app.js")
async def serve_js():
    return FileResponse(os.path.join(PUBLIC_DIR, "app.js"), media_type="application/javascript")

@app.get("/api/health")
async def health():
    return {"status": "ok", "public_dir": PUBLIC_DIR, "public_exists": os.path.exists(PUBLIC_DIR)}


@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(req: TranscribeRequest):
    # Lazy imports — keeps startup fast and avoids cold-start import crashes
    from downloader import download_video
    from audio import extract_audio

    if not is_valid_instagram_url(req.url):
        raise HTTPException(
            status_code=422,
            detail="Invalid Instagram URL. Must be a public reel, post, or IGTV link.",
        )

    if req.provider == "openai" and not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured.")
    if req.provider == "gemini" and not settings.gemini_api_key:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY is not configured.")

    video_path = None
    audio_path = None
    was_trimmed = False

    try:
        loop = asyncio.get_running_loop()  # correct for Python 3.10+

        video_path = await loop.run_in_executor(
            None, download_video, req.url, settings.tmp_dir
        )

        if req.provider == "openai":
            from transcribe_openai import transcribe_with_openai
            audio_path, was_trimmed = await loop.run_in_executor(
                None, extract_audio, video_path, settings.max_file_size_mb
            )
            result = await transcribe_with_openai(audio_path, req.language, req.prompt)

        else:
            from transcribe_gemini import transcribe_with_gemini
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

    except Exception as e:
        import yt_dlp.utils as yt_utils
        if isinstance(e, yt_utils.DownloadError):
            msg = str(e)
            hint = " (private reel? try adding cookies)" if any(w in msg.lower() for w in ["login", "private", "404"]) else ""
            raise HTTPException(status_code=422, detail=f"Could not download reel: {msg}{hint}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cleanup_files(video_path, audio_path)
