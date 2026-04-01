import subprocess
import os


def get_ffmpeg_exe() -> str:
    """Returns path to ffmpeg binary — uses imageio-ffmpeg bundled binary (works on Vercel)."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"  # fallback to system ffmpeg for local dev


def extract_audio(video_path: str, max_size_mb: int = 25) -> tuple[str, bool]:
    """
    Extracts audio from video_path as an mp3 file.
    Returns (audio_path, was_trimmed).
    """
    ffmpeg = get_ffmpeg_exe()
    audio_path = video_path.rsplit(".", 1)[0] + ".mp3"

    subprocess.run(
        [
            ffmpeg, "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-ab", "128k",
            "-ar", "44100",
            audio_path,
        ],
        check=True,
        capture_output=True,
    )

    size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    was_trimmed = False

    if size_mb > max_size_mb:
        trimmed_path = audio_path.replace(".mp3", "_32k.mp3")
        subprocess.run(
            [
                ffmpeg, "-y",
                "-i", audio_path,
                "-vn",
                "-acodec", "libmp3lame",
                "-ab", "32k",
                trimmed_path,
            ],
            check=True,
            capture_output=True,
        )
        os.remove(audio_path)
        audio_path = trimmed_path
        was_trimmed = True

    return audio_path, was_trimmed
