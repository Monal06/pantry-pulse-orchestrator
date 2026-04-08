from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    gemini_api_key: str = ""
    supabase_url: str = ""
    supabase_key: str = ""
    open_food_facts_enabled: bool = True

    # Comma-separated model names tried in order on 503 / overload errors
    gemini_models: str = "gemini-2.5-flash,gemini-2.0-flash,gemini-1.5-flash"
    # Max retries *per model* before falling back to the next model
    gemini_max_retries: int = 2

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
