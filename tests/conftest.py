import os
import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Ensure tests run against local test database and mock settings."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "ledgerly_test_db")
    monkeypatch.setenv("DB_USER", "ledgerly")
    monkeypatch.setenv("DB_PASSWORD", "ledgerly_local_sec_pass")
    monkeypatch.setenv("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
    monkeypatch.setenv("VLLM_MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct-AWQ")