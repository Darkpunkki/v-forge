"""Standalone agent bridge service for VibeForge."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import ssl
from datetime import datetime, timezone
from typing import Any, Optional

import websockets

try:
    from .cli_wrapper import ClaudeInvocationError, invoke_claude
except ImportError:  # pragma: no cover - allows running as a script
    from cli_wrapper import ClaudeInvocationError, invoke_claude


class RegistrationError(RuntimeError):
    """Raised when registration handshake fails."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_register_message(
    agent_id: str,
    auth_token: str,
    workdir: Optional[str],
    capabilities: list[str],
) -> dict[str, Any]:
    return {
        "type": "register",
        "agent_id": agent_id,
        "auth_token": auth_token,
        "capabilities": capabilities,
        "workdir": workdir,
        "metadata": {
            "pid": os.getpid(),
            "platform": sys.platform,
        },
    }


def _build_heartbeat_message(agent_id: str) -> dict[str, Any]:
    return {
        "type": "heartbeat",
        "agent_id": agent_id,
        "timestamp": _now_iso(),
    }


def _build_progress_message(
    agent_id: str,
    message_id: str,
    status: str,
    progress_text: str = "",
) -> dict[str, Any]:
    return {
        "type": "progress",
        "message_id": message_id,
        "agent_id": agent_id,
        "status": status,
        "progress_text": progress_text,
        "metadata": {
            "timestamp": _now_iso(),
        },
    }


def _build_response_message(
    agent_id: str,
    message_id: str,
    content: str = "",
    usage: Optional[dict[str, Any]] = None,
    error: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "type": "response",
        "message_id": message_id,
        "agent_id": agent_id,
        "content": content,
        "usage": usage or {},
        "error": error,
    }


class BridgeClient:
    """WebSocket client that bridges VibeForge dispatches to Claude Code CLI."""

    def __init__(
        self,
        *,
        url: str,
        agent_id: str,
        auth_token: str,
        workdir: Optional[str],
        capabilities: list[str],
        heartbeat_interval: float = 30.0,
        register_timeout: float = 10.0,
        max_backoff: float = 60.0,
        ssl_context: Optional[ssl.SSLContext] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._url = url
        self._agent_id = agent_id
        self._auth_token = auth_token
        self._workdir = workdir
        self._capabilities = capabilities
        self._heartbeat_interval = heartbeat_interval
        self._register_timeout = register_timeout
        self._max_backoff = max_backoff
        self._ssl_context = ssl_context
        self._logger = logger or logging.getLogger("agent_bridge")
        self._send_lock = asyncio.Lock()
        self._busy = False
        self._session_id: Optional[str] = None

    async def run(self, stop_event: asyncio.Event) -> None:
        backoff = 1.0
        while not stop_event.is_set():
            try:
                await self._connect_once(stop_event)
                backoff = 1.0
            except RegistrationError as exc:
                self._logger.error("Registration failed: %s", exc)
                break
            except Exception as exc:
                if stop_event.is_set():
                    break
                self._logger.warning("Connection error: %s", exc)

            if stop_event.is_set():
                break

            await self._sleep_with_backoff(backoff, stop_event)
            backoff = min(backoff * 2.0, self._max_backoff)

    async def _sleep_with_backoff(self, seconds: float, stop_event: asyncio.Event) -> None:
        self._logger.info("Reconnecting in %.1f seconds", seconds)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            return

    async def _connect_once(self, stop_event: asyncio.Event) -> None:
        self._logger.info("Connecting to %s", self._url)
        async with websockets.connect(
            self._url,
            ping_interval=None,
            ssl=self._ssl_context,
        ) as websocket:
            await self._register(websocket)
            self._logger.info("Registered as %s (session %s)", self._agent_id, self._session_id)

            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(websocket, stop_event)
            )
            receiver_task = asyncio.create_task(
                self._receive_loop(websocket, stop_event)
            )
            stop_task = asyncio.create_task(stop_event.wait())

            done, pending = await asyncio.wait(
                [receiver_task, stop_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if stop_event.is_set():
                self._logger.info("Shutdown requested; closing connection")
                await websocket.close()

            for task in pending:
                task.cancel()

            heartbeat_task.cancel()
            await asyncio.gather(heartbeat_task, return_exceptions=True)

            if receiver_task in done and not receiver_task.cancelled():
                exc = receiver_task.exception()
                if exc:
                    raise exc

    async def _register(self, websocket: Any) -> None:
        register_msg = _build_register_message(
            self._agent_id,
            self._auth_token,
            self._workdir,
            self._capabilities,
        )
        await self._send_json(websocket, register_msg)

        try:
            raw = await asyncio.wait_for(websocket.recv(), timeout=self._register_timeout)
        except asyncio.TimeoutError as exc:
            raise RegistrationError("Timed out waiting for registered message") from exc
        except Exception as exc:
            raise RegistrationError("Registration handshake failed") from exc

        data = self._parse_json(raw)
        if not data or data.get("type") != "registered":
            raise RegistrationError("Did not receive registered acknowledgment")

        self._session_id = data.get("session_id")

    async def _heartbeat_loop(self, websocket: Any, stop_event: asyncio.Event) -> None:
        try:
            while not stop_event.is_set():
                await asyncio.sleep(self._heartbeat_interval)
                if stop_event.is_set():
                    break
                heartbeat = _build_heartbeat_message(self._agent_id)
                await self._send_json(websocket, heartbeat)
        except Exception:
            # Connection likely closed; heartbeat loop will exit
            return

    async def _receive_loop(self, websocket: Any, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            try:
                raw = await websocket.recv()
            except Exception:
                break

            data = self._parse_json(raw)
            if not data:
                continue

            msg_type = data.get("type")
            if msg_type == "dispatch":
                await self._handle_dispatch(websocket, data)
            elif msg_type == "heartbeat":
                # Server heartbeat; no action required.
                continue
            elif msg_type == "registered":
                # Duplicate registered message; ignore.
                continue
            else:
                self._logger.debug("Ignoring message type: %s", msg_type)

    async def _handle_dispatch(self, websocket: Any, data: dict[str, Any]) -> None:
        message_id = data.get("message_id")
        content = data.get("content")

        if not message_id or not content:
            self._logger.warning("Invalid dispatch message received")
            return

        if self._busy:
            error_msg = _build_response_message(
                self._agent_id,
                message_id,
                error="agent busy",
            )
            await self._send_json(websocket, error_msg)
            return

        self._busy = True
        try:
            progress = _build_progress_message(
                self._agent_id,
                message_id,
                status="running",
                progress_text="Task execution started",
            )
            await self._send_json(websocket, progress)

            result = await asyncio.to_thread(
                invoke_claude,
                content,
                self._workdir,
            )

            response = _build_response_message(
                self._agent_id,
                message_id,
                content=result.content,
                usage=result.usage,
            )
            await self._send_json(websocket, response)
        except ClaudeInvocationError as exc:
            response = _build_response_message(
                self._agent_id,
                message_id,
                error=str(exc),
            )
            await self._send_json(websocket, response)
        except Exception as exc:
            response = _build_response_message(
                self._agent_id,
                message_id,
                error=f"Bridge error: {exc}",
            )
            await self._send_json(websocket, response)
        finally:
            self._busy = False

    async def _send_json(self, websocket: Any, payload: dict[str, Any]) -> None:
        async with self._send_lock:
            await websocket.send(json.dumps(payload))

    def _parse_json(self, raw: Any) -> Optional[dict[str, Any]]:
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        if not isinstance(raw, str):
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self._logger.warning("Received invalid JSON")
            return None


def _setup_signal_handlers(stop_event: asyncio.Event, logger: logging.Logger) -> None:
    def _handler(signum: int, _frame: Any) -> None:
        logger.info("Received signal %s; shutting down", signum)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handler)
        except Exception:
            continue


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VibeForge Agent Bridge")
    parser.add_argument("--url", required=True, help="WebSocket URL for VibeForge")
    parser.add_argument("--agent-id", required=True, help="Agent identifier")
    parser.add_argument("--token", required=True, help="Authentication token")
    parser.add_argument("--workdir", required=True, help="Working directory for Claude CLI")
    parser.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Capability label (repeatable)",
    )
    parser.add_argument(
        "--heartbeat",
        type=float,
        default=30.0,
        help="Heartbeat interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--register-timeout",
        type=float,
        default=10.0,
        help="Registration timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification (self-signed certs)",
    )
    return parser.parse_args()


async def _run_bridge(args: argparse.Namespace) -> None:
    logger = logging.getLogger("agent_bridge")
    stop_event = asyncio.Event()
    _setup_signal_handlers(stop_event, logger)

    ssl_context = None
    if args.url.startswith("wss://"):
        if args.insecure:
            ssl_context = ssl._create_unverified_context()
            logger.warning("TLS verification disabled (insecure mode)")
        else:
            ssl_context = ssl.create_default_context()

    client = BridgeClient(
        url=args.url,
        agent_id=args.agent_id,
        auth_token=args.token,
        workdir=args.workdir,
        capabilities=args.capability,
        heartbeat_interval=args.heartbeat,
        register_timeout=args.register_timeout,
        ssl_context=ssl_context,
        logger=logger,
    )

    await client.run(stop_event)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s",
    )

    args = _parse_args()

    try:
        asyncio.run(_run_bridge(args))
    except RegistrationError:
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
