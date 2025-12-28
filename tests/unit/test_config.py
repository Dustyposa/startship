import os
from src.config import Settings, settings


def test_default_settings():
    """Test default settings are loaded"""
    s = Settings()
    assert s.api_host == "0.0.0.0"
    assert s.api_port == 8000
    assert s.db_type == "sqlite"
    assert s.llm_provider == "openai"
    assert s.llm_model == "gpt-4o-mini"


def test_settings_from_env():
    """Test settings can be loaded from environment"""
    os.environ["API_PORT"] = "9000"
    os.environ["LLM_MODEL"] = "gpt-4o"
    s = Settings()
    assert s.api_port == 9000
    assert s.llm_model == "gpt-4o"
    # Clean up
    del os.environ["API_PORT"]
    del os.environ["LLM_MODEL"]


def test_global_settings_instance():
    """Test global settings instance exists"""
    assert settings is not None
    assert isinstance(settings, Settings)
