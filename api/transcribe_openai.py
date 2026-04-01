from openai import AsyncOpenAI
from config import settings


async def transcribe_with_openai(
    audio_path: str,
    language: str = "auto",
    prompt: str = "",
) -> dict:
    """
    Sends audio file to OpenAI Whisper API.
    Returns dict with transcript, language_detected, duration_seconds.
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    kwargs: dict = {
        "model": "whisper-1",
        "response_format": "verbose_json",
    }
    if language != "auto":
        kwargs["language"] = language
    if prompt:
        kwargs["prompt"] = prompt

    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(file=f, **kwargs)

    return {
        "transcript": response.text,
        "language_detected": getattr(response, "language", None),
        "duration_seconds": getattr(response, "duration", None),
    }
