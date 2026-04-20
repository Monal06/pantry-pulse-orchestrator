from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Gemini API Keys (primary provider)
    gemini_api_key: str = ""  # Single key (backward compatible)
    gemini_api_keys: str = ""  # Multiple keys for rotation: key1,key2,key3,key4,key5

    groq_api_key: str = ""  # Groq API Key (secondary provider)

    # Database
    supabase_url: str = ""
    supabase_key: str = ""
    open_food_facts_enabled: bool = True

    # Deployment
    environment: str = "development"  # development or production
    cors_origins: str = "*"  # Comma-separated URLs in production

    # Comma-separated model names tried in order on 503 / overload errors

    gemini_models: str = "gemini-2.0-flash,gemini-2.5-flash,gemini-flash-latest"
    # Max retries *per model* before falling back to the next model
    gemini_max_retries: int = 1

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def get_all_gemini_keys(self) -> list[str]:
        """Get all Gemini API keys for rotation."""
        keys = []

        # First, try comma-separated keys
        if self.gemini_api_keys:
            keys.extend([k.strip() for k in self.gemini_api_keys.split(",") if k.strip()])

        # Add single key if not already in list
        if self.gemini_api_key and self.gemini_api_key not in keys:
            keys.append(self.gemini_api_key)

        return keys


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
