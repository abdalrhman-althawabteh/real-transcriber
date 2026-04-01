from pydantic import BaseModel
from typing import Literal


class TranscribeRequest(BaseModel):
    url: str
    provider: Literal["openai", "gemini"] = "openai"
    language: str = "auto"
    prompt: str = ""


class TranscribeResponse(BaseModel):
    transcript: str
    provider: str
    duration_seconds: float | None = None
    language_detected: str | None = None
    warning: str | None = None
