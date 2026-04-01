import os
import time
from config import settings


def transcribe_with_gemini(video_path: str, language: str = "auto") -> dict:
    """
    Uploads video to Gemini File API and requests transcription.
    Requires google-generativeai to be installed (uncomment in requirements.txt).
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError(
            "Google Gemini is not available in this deployment. "
            "To enable it, uncomment google-generativeai in requirements.txt and redeploy."
        )

    genai.configure(api_key=settings.gemini_api_key)

    uploaded = genai.upload_file(
        path=video_path,
        mime_type="video/mp4",
        display_name=os.path.basename(video_path),
    )

    while uploaded.state.name == "PROCESSING":
        time.sleep(1)
        uploaded = genai.get_file(uploaded.name)

    if uploaded.state.name != "ACTIVE":
        raise RuntimeError(f"Gemini file processing failed: {uploaded.state.name}")

    lang_hint = f" The audio is in {language}." if language != "auto" else ""
    prompt = (
        f"Transcribe the spoken audio in this video verbatim.{lang_hint}"
        " Output only the transcript text, no timestamps, no speaker labels."
    )

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([uploaded, prompt])

    try:
        genai.delete_file(uploaded.name)
    except Exception:
        pass

    return {
        "transcript": response.text.strip(),
        "language_detected": None,
        "duration_seconds": None,
    }
