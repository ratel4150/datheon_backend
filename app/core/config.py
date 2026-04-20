from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    groq_api_key: str
    database_url: str
    resend_api_key: str = ""
    internal_api_key: str = "cambiar_en_produccion"
    environment: str = "development"
    allowed_origins: str = "http://localhost:3000"

    def get_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"

settings = Settings()