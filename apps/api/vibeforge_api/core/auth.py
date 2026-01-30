"""Authentication helpers for control and agent bridge endpoints."""
from __future__ import annotations

import hmac
import os
import secrets
from pathlib import Path
from typing import Iterable

from fastapi import HTTPException, Request

from vibeforge_api.core.audit_logger import log_audit_event

AUTH_TOKEN_ENV = "VIBEFORGE_AUTH_TOKEN"
AUTH_TOKENS_ENV = "VIBEFORGE_AUTH_TOKENS"
AUTH_TOKEN_FILE_ENV = "VIBEFORGE_AUTH_TOKEN_FILE"


class AuthConfigError(RuntimeError):
    """Raised when authentication is not configured."""


def generate_auth_token() -> str:
    """Generate a secure random token (64 hex chars)."""
    return secrets.token_hex(32)


def _split_tokens(raw: str) -> list[str]:
    return [token.strip() for token in raw.split(",") if token.strip()]


def _load_tokens_from_file(path_value: str) -> list[str]:
    path = Path(path_value)
    if not path.exists():
        return []
    tokens: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith("#"):
            continue
        tokens.append(candidate)
    return tokens


def get_configured_tokens() -> list[str]:
    tokens: list[str] = []

    env_tokens = os.getenv(AUTH_TOKENS_ENV)
    if env_tokens:
        tokens.extend(_split_tokens(env_tokens))

    single_token = os.getenv(AUTH_TOKEN_ENV)
    if single_token:
        tokens.append(single_token.strip())

    token_file = os.getenv(AUTH_TOKEN_FILE_ENV)
    if token_file:
        tokens.extend(_load_tokens_from_file(token_file))

    # Deduplicate while preserving order
    seen = set()
    unique: list[str] = []
    for token in tokens:
        if token and token not in seen:
            unique.append(token)
            seen.add(token)

    return unique


def _match_token(candidate: str, tokens: Iterable[str]) -> bool:
    return any(hmac.compare_digest(candidate, token) for token in tokens)


def validate_auth_token(token: str | None) -> tuple[bool, str]:
    if not token:
        return False, "missing token"

    tokens = get_configured_tokens()
    if not tokens:
        return False, "authentication not configured"

    if not _match_token(token, tokens):
        return False, "invalid token"

    return True, ""


def _extract_token_from_request(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            candidate = parts[1].strip()
            if candidate:
                return candidate

    header_token = request.headers.get("X-Auth-Token")
    if header_token:
        header_token = header_token.strip()
        if header_token:
            return header_token

    query_token = request.query_params.get("token")
    if query_token:
        query_token = query_token.strip()
        if query_token:
            return query_token

    return None


def require_auth(request: Request) -> None:
    ip = request.client.host if request.client else None
    path = request.url.path
    method = request.method

    token = _extract_token_from_request(request)
    if not token:
        log_audit_event(
            "auth_failure",
            result="missing_token",
            ip=ip,
            metadata={"path": path, "method": method},
        )
        raise HTTPException(status_code=401, detail="Missing authentication token")

    tokens = get_configured_tokens()
    if not tokens:
        log_audit_event(
            "auth_failure",
            result="not_configured",
            ip=ip,
            metadata={"path": path, "method": method},
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Authentication not configured. Set VIBEFORGE_AUTH_TOKEN or "
                "VIBEFORGE_AUTH_TOKENS."
            ),
        )

    if not _match_token(token, tokens):
        log_audit_event(
            "auth_failure",
            result="invalid_token",
            ip=ip,
            metadata={"path": path, "method": method},
        )
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    log_audit_event(
        "auth_success",
        ip=ip,
        metadata={"path": path, "method": method},
    )
