"""Audit logging for security events."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

_AUDIT_LOGGER_NAME = "vibeforge.audit"
_AUDIT_LOG_PATH_ENV = "VIBEFORGE_AUDIT_LOG_PATH"
_AUDIT_LOG_LEVEL_ENV = "VIBEFORGE_AUDIT_LOG_LEVEL"
_AUDIT_LOG_MAX_BYTES_ENV = "VIBEFORGE_AUDIT_LOG_MAX_BYTES"
_AUDIT_LOG_BACKUP_COUNT_ENV = "VIBEFORGE_AUDIT_LOG_BACKUP_COUNT"


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_audit_log_path() -> Path:
    value = os.getenv(_AUDIT_LOG_PATH_ENV, "logs/audit.log")
    path = Path(value)
    if not path.is_absolute():
        module_root = Path(__file__).resolve()
        repo_root = module_root.parents[4] if len(module_root.parents) > 4 else Path.cwd()
        path = repo_root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_audit_logger() -> logging.Logger:
    logger = logging.getLogger(_AUDIT_LOGGER_NAME)
    if logger.handlers:
        return logger

    level_name = os.getenv(_AUDIT_LOG_LEVEL_ENV, "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    log_path = _get_audit_log_path()
    handler = RotatingFileHandler(
        log_path,
        maxBytes=_env_int(_AUDIT_LOG_MAX_BYTES_ENV, 100 * 1024 * 1024),
        backupCount=_env_int(_AUDIT_LOG_BACKUP_COUNT_ENV, 10),
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_audit_event(
    event: str,
    *,
    result: str = "success",
    agent_id: str | None = None,
    ip: str | None = None,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "result": result,
    }
    if agent_id is not None:
        payload["agent_id"] = agent_id
    if ip is not None:
        payload["ip"] = ip
    if session_id is not None:
        payload["session_id"] = session_id
    if metadata:
        payload["metadata"] = metadata

    logger = get_audit_logger()
    logger.info(json.dumps(payload, ensure_ascii=True))
