"""Configuration settings for Noah Reading Agent."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "Noah Reading Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str

    # Database
    database_url: str
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "noah_db"
    database_user: str = "noah_user"
    database_password: str

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: str
    aws_secret_access_key: str

    # AWS Agent Core
    agent_core_endpoint: str
    agent_core_api_key: str

    # Vector Database
    pinecone_api_key: str
    pinecone_environment: str = "us-east-1-aws"

    # Amazon Product API
    amazon_access_key: str
    amazon_secret_key: str
    amazon_associate_tag: str

    # CORS - Handle as comma-separated string, then split
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
