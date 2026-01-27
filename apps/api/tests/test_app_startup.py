"""Startup/import tests for the FastAPI app and LLM provider."""

from fastapi import FastAPI

from models.base import LlmClient
from vibeforge_api.core.llm_provider import get_llm_client
from vibeforge_api.main import app


def test_app_imports():
    """App can be imported and is a FastAPI instance."""
    assert isinstance(app, FastAPI)


def test_get_llm_client_returns_llm_client(monkeypatch):
    """LLM client factory returns a valid LlmClient implementation."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = get_llm_client()
    assert isinstance(client, LlmClient)


def test_get_llm_client_falls_back_to_stub(monkeypatch):
    """When no API key is set, DeterministicStubClient is used."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("VIBEFORGE_LLM_MODE", raising=False)
    monkeypatch.delenv("VIBEFORGE_NO_SPEND", raising=False)
    client = get_llm_client()
    assert client.get_provider_name() == "stub"
