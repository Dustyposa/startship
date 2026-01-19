"""
Configuration management using Pydantic Settings.
Load from environment variables or .env file.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "GitHub Star RAG Service"
    api_version: str = "1.0.0"

    # Database Configuration
    db_type: str = "sqlite"  # sqlite or postgresql
    sqlite_path: str = "data/starship.db"

    # PostgreSQL (optional)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "starship"
    postgres_user: str = "starship"
    postgres_password: str = ""

    # LLM Configuration
    llm_provider: str = "openai"  # openai, ollama
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    llm_base_url: Optional[str] = None
    llm_timeout: int = 60

    # GitHub Configuration
    github_token: Optional[str] = None

    # Ollama Configuration (for semantic search)
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "bge-m3"
    ollama_timeout: int = 30

    # Storage
    readme_storage_path: str = "data/readmes"

    # Concurrency
    max_concurrent_llm: int = 5
    max_concurrent_github: int = 10

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # ChromaDB Configuration (for semantic search)
    chromadb_path: str = "data/chromadb"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
