"""
Tests for centralized settings via pydantic-settings.
"""

import os

import pytest

from src.infrastructure.settings import Settings, get_settings


def test_settings_default_values():
    settings = Settings()
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.log_level == "INFO"
    assert settings.cors_origins == ["*"]


def test_settings_port_validation():
    with pytest.raises(ValueError):
        Settings(api_port=0)
    with pytest.raises(ValueError):
        Settings(api_port=70000)


def test_settings_log_level_validation():
    with pytest.raises(ValueError):
        Settings(log_level="VERBOSE")


def test_settings_cors_origins_parsed():
    settings = Settings(cors_allow_origins="https://a.com, https://b.com")
    assert settings.cors_origins == ["https://a.com", "https://b.com"]


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()
    assert "sqlite" in str(settings.database_url)
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 9000
    assert settings.log_level == "DEBUG"


def test_get_settings_cached():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
