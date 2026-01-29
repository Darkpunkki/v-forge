import pytest

AUTH_TOKEN = "test-token"


@pytest.fixture(autouse=True)
def set_auth_env(monkeypatch):
    monkeypatch.setenv("VIBEFORGE_AUTH_TOKEN", AUTH_TOKEN)
    monkeypatch.delenv("VIBEFORGE_AUTH_TOKENS", raising=False)
    monkeypatch.delenv("VIBEFORGE_AUTH_TOKEN_FILE", raising=False)
    yield


@pytest.fixture()
def auth_headers():
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}
