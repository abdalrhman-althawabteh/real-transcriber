import yt_dlp
import os
import uuid
from config import settings


def download_video(url: str, output_dir: str) -> str:
    """
    Downloads an Instagram reel/post to output_dir.
    Returns the full path to the downloaded file.
    Raises yt_dlp.utils.DownloadError on failure.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_id = str(uuid.uuid4())
    output_template = os.path.join(output_dir, f"{output_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": False,
        "socket_timeout": 30,
        "merge_output_format": "mp4",
    }

    if settings.cookies_file:
        ydl_opts["cookiefile"] = settings.cookies_file
    elif settings.cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (settings.cookies_from_browser,)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = info.get("ext", "mp4")
        path = os.path.join(output_dir, f"{output_id}.{ext}")
        if not os.path.exists(path):
            for fname in os.listdir(output_dir):
                if fname.startswith(output_id):
                    path = os.path.join(output_dir, fname)
                    break
        return path
