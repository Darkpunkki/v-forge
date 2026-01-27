"""Agent Bridge WebSocket protocol message models.

Defines the 6 message types used for communication between VibeForge
and remote Agent Bridge services over WebSocket:

  bridge → vibeforge:  register, progress, response, heartbeat
  vibeforge → bridge:  registered, dispatch, heartbeat
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class RegisterMessage(BaseModel):
    """Sent by bridge on connect to register with VibeForge."""

    type: Literal["register"] = "register"
    agent_id: str = Field(..., min_length=1)
    auth_token: str = Field(..., min_length=1)
    capabilities: list[str] = Field(default_factory=list)
    workdir: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RegisteredMessage(BaseModel):
    """Sent by VibeForge to acknowledge successful registration."""

    type: Literal["registered"] = "registered"
    session_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    message: str = "Registration successful"


class DispatchMessage(BaseModel):
    """Sent by VibeForge to assign a task to a remote agent."""

    type: Literal["dispatch"] = "dispatch"
    message_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None


class ProgressMessage(BaseModel):
    """Sent by bridge to report task progress."""

    type: Literal["progress"] = "progress"
    message_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    progress_text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResponseMessage(BaseModel):
    """Sent by bridge when a task is complete."""

    type: Literal["response"] = "response"
    message_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    content: str = ""
    usage: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class HeartbeatMessage(BaseModel):
    """Bidirectional keepalive message."""

    type: Literal["heartbeat"] = "heartbeat"
    agent_id: str = Field(..., min_length=1)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# Discriminated union of all protocol messages
BridgeMessage = Annotated[
    Union[
        RegisterMessage,
        RegisteredMessage,
        DispatchMessage,
        ProgressMessage,
        ResponseMessage,
        HeartbeatMessage,
    ],
    Field(discriminator="type"),
]


def parse_bridge_message(data: dict[str, Any]) -> BridgeMessage:
    """Parse a raw dict into the correct protocol message model.

    Uses Pydantic's discriminated union to select the right type
    based on the 'type' field.

    Raises:
        pydantic.ValidationError: If data doesn't match any message type
            or fails field validation.
    """
    from pydantic import TypeAdapter

    adapter = TypeAdapter(BridgeMessage)
    return adapter.validate_python(data)
