from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Agriculture Analytics API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "FastAPI service for agriculture farm, crop, and market reports"
    
    # Database Configuration
    HOST: str
    PORT: int = 3306
    DB: str
    USER: str
    PASSWORD: str
    
    # CORS
    ALLOWED_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
