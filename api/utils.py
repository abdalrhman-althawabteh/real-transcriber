import os
import re

INSTAGRAM_PATTERN = re.compile(
    r"^https?://(www\.)?instagram\.com/(reel|p|tv)/[\w-]+/?(\?.*)?$"
)


def is_valid_instagram_url(url: str) -> bool:
    return bool(INSTAGRAM_PATTERN.match(url.strip()))


def cleanup_files(*paths: str) -> None:
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
