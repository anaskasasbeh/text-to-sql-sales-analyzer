"""Settings read from environment variables (and a local .env file, if present)."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

load_dotenv(PROJECT_ROOT / ".env")


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    return int(value) if value else default


@dataclass(frozen=True)
class Settings:
    """All runtime settings in one place."""

    groq_api_key: str
    groq_model: str
    reasoning_effort: str
    max_completion_tokens: int
    csv_path: Path
    db_path: Path
    rate_limit_per_minute: int
    max_question_chars: int = 300
    max_rows: int = 200
    query_timeout_seconds: float = 3.0


def load_settings() -> Settings:
    """Build the settings from the environment, with safe defaults."""
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip(),
        reasoning_effort=os.getenv("GROQ_REASONING_EFFORT", "low").strip(),
        max_completion_tokens=_int_env("GROQ_MAX_COMPLETION_TOKENS", 1024),
        csv_path=PROJECT_ROOT / "data" / "sales_data_sample.csv",
        # One file per process, so the server and the evaluation never lock each other.
        db_path=Path(tempfile.gettempdir()) / f"text_to_sql_sales_{os.getpid()}.db",
        rate_limit_per_minute=_int_env("RATE_LIMIT_PER_MINUTE", 15),
    )
