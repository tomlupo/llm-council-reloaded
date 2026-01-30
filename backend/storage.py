"""Conversation storage with support for all deliberation modes."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


DATA_DIR = Path(__file__).parent / "data" / "conversations"


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def create_conversation() -> str:
    _ensure_dir()
    conv_id = str(uuid.uuid4())
    path = DATA_DIR / f"{conv_id}.json"
    data = {
        "id": conv_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": [],
    }
    path.write_text(json.dumps(data, indent=2))
    return conv_id


def _load(conv_id: str) -> dict:
    path = DATA_DIR / f"{conv_id}.json"
    return json.loads(path.read_text())


def _save(conv_id: str, data: dict) -> None:
    path = DATA_DIR / f"{conv_id}.json"
    path.write_text(json.dumps(data, indent=2))


def add_user_message(conv_id: str, content: str, metadata: Optional[dict] = None) -> None:
    data = _load(conv_id)
    msg: dict[str, Any] = {
        "role": "user",
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if metadata:
        msg["metadata"] = metadata
    data["messages"].append(msg)
    _save(conv_id, data)


def add_assistant_message(
    conv_id: str,
    content: str,
    metadata: Optional[dict] = None,
    # Standard 3-stage fields (backward compat)
    stage1: Optional[list[dict]] = None,
    stage2: Optional[list[dict]] = None,
    stage3: Optional[str] = None,
    # Extended fields for new modes
    rounds: Optional[list[dict]] = None,
    scoring: Optional[dict] = None,
    synthesis: Optional[dict] = None,
    # Full mode-specific payload
    mode_data: Optional[dict] = None,
) -> None:
    data = _load(conv_id)
    msg: dict[str, Any] = {
        "role": "assistant",
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if metadata:
        msg["metadata"] = metadata
    if stage1 is not None:
        msg["stage1"] = stage1
    if stage2 is not None:
        msg["stage2"] = stage2
    if stage3 is not None:
        msg["stage3"] = stage3
    if rounds is not None:
        msg["rounds"] = rounds
    if scoring is not None:
        msg["scoring"] = scoring
    if synthesis is not None:
        msg["synthesis"] = synthesis
    if mode_data is not None:
        msg["mode_data"] = mode_data
    data["messages"].append(msg)
    _save(conv_id, data)


def get_conversation(conv_id: str) -> dict:
    return _load(conv_id)


def list_conversations() -> list[dict]:
    _ensure_dir()
    convs = []
    for p in sorted(DATA_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(p.read_text())
            convs.append({
                "id": data["id"],
                "created_at": data["created_at"],
                "message_count": len(data["messages"]),
                "preview": data["messages"][0]["content"][:100] if data["messages"] else "",
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return convs


def delete_conversation(conv_id: str) -> bool:
    path = DATA_DIR / f"{conv_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
