from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    gemini_api_key: str = ""
    supabase_url: str = ""
    supabase_key: str = ""
    open_food_facts_enabled: bool = True

    # Comma-separated model names tried in order on 503 / overload errors
    gemini_models: str = "gemini-2.5-flash, gemini-2.5-pro, gemini-2.5-flash-lite, gemini-3.1-flash-preview, gemini-3.1-pro-preview"
    # Max retries *per model* before falling back to the next model
    gemini_max_retries: int = 2

    # Groq API key for Llama 3.3 70B reasoning layer
    groq_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
