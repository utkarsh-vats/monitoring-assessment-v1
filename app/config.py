import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env.local (higher priority) and .env (fallback)
_BASE_DIR = Path(__file__).resolve().parent.parent
_ = load_dotenv(_BASE_DIR / ".env.local")
_ = load_dotenv(_BASE_DIR / ".env")


class Settings(BaseModel):
    app_name: str = "Observable AI Backend Service"
    version: str = "1.0.0"
    environment: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )

    # Multi-provider LLM API Keys
    gemini_api_key: str | None = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY")
    )
    openrouter_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY")
    )
    openai_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )

    # Default model configuration
    gemini_model_name: str = Field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    )
    openrouter_model_name: str = Field(
        default_factory=lambda: os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    )
    openai_model_name: str = Field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )

    # Force mock mode for deterministic offline testing if requested
    force_mock_mode: bool = Field(
        default_factory=lambda: os.getenv("FORCE_MOCK_MODE", "false").lower()
        in ("1", "true", "yes")
    )


settings = Settings()
