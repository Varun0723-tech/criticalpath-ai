from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency helper
    load_dotenv = None


if load_dotenv is not None:
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]
    backend_root = current_file.parents[1]

    for env_path in (project_root / ".env", backend_root / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


def _to_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    openai_api_key: str | None
    openai_model: str
    enable_llm: bool
    openai_timeout_seconds: float
    openai_trust_env: bool
    frontend_origins: tuple[str, ...]


@lru_cache
def get_settings() -> Settings:
    origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    origin_list = tuple(item.strip() for item in origins.split(",") if item.strip())
    return Settings(
        app_name="CriticalPath AI: Emergency Care Intelligence System",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        enable_llm=_to_bool(os.getenv("ENABLE_LLM"), default=True),
        openai_timeout_seconds=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "20")),
        openai_trust_env=_to_bool(os.getenv("OPENAI_TRUST_ENV"), default=False),
        frontend_origins=origin_list or ("http://localhost:5173",),
    )
