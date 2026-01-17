"""Configuration settings for Noah Reading Agent."""

import os
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "Noah Reading Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str = "dev-secret-key-change-in-production"

    # Database - Individual components
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "noah"
    database_user: str = "noah_user"
    database_password: str = ""

    # Legacy database_url support
    database_url: Optional[str] = None

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # AWS Agent Core
    agent_core_endpoint: str = ""
    agent_core_api_key: str = ""

    # Vector Database
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1-aws"

    # Amazon Product API
    amazon_access_key: str = ""
    amazon_secret_key: str = ""
    amazon_associate_tag: str = ""

    # CORS - Handle as comma-separated string, then split
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def allowed_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def database_connection_url(self) -> str:
        """Construct database URL from components or use provided URL."""
        if self.database_url:
            return self.database_url

        # Construct from individual components
        password = self.database_password or os.getenv('DATABASE_PASSWORD', '')
        return f"postgresql://{self.database_user}:{password}@{self.database_host}:{self.database_port}/{self.database_name}"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
