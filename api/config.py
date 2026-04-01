import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    gemini_api_key: str = ""
    tmp_dir: str = "/tmp"
    max_file_size_mb: int = 25
    cookies_file: str = ""
    cookies_from_browser: str = ""

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_file_encoding = "utf-8"


settings = Settings()
