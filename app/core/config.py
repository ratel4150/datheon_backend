from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    groq_api_key: str
    database_url: str
    resend_api_key: str = ""
    internal_api_key: str = "cambiar_en_produccion"
    environment: str = "development"
    allowed_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()