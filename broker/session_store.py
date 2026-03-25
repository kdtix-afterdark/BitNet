"""In-memory session tracking with optional disk persistence for the local BitNet broker."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from broker.durable_state import SessionLedger, record_session_opened


@dataclass
class Session:
    """Broker session metadata stored in memory for the MVP."""

    session_id: str
    created_at: str
    system_prompt: str
    metadata: Dict[str, str] = field(default_factory=dict)
    messages: List[Dict[str, str]] = field(default_factory=list)
    updated_at: str = ""
    turn_count: int = 0
    summary: str = ""
    summarized_turn_count: int = 0


class SessionStore:
    """Simple in-memory session store.

    In addition to ``Session`` metadata, each session is paired with an
    append-only ``SessionLedger`` that records all activity events for the
    duration of the session.  The ledger is accessible via ``get_ledger()``.

    Each session also maintains an ordered ``messages`` list of
    ``{"role": ..., "content": ...}`` dicts that represent the model-facing
    conversation history accumulated across turns.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}
        self._ledgers: Dict[str, SessionLedger] = {}

    def create(
        self, system_prompt: str, metadata: Optional[Dict[str, str]] = None
    ) -> Session:
        now = datetime.now(timezone.utc).isoformat()
        session = Session(
            session_id=str(uuid4()),
            created_at=now,
            updated_at=now,
            system_prompt=system_prompt.strip(),
            metadata=metadata or {},
        )
        self._sessions[session.session_id] = session
        ledger = SessionLedger(session.session_id)
        ledger.record(
            record_session_opened(
                session.session_id,
                ledger.next_sequence,
                system_prompt=session.system_prompt,
            )
        )
        self._ledgers[session.session_id] = ledger
        return session

    def restore(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
    ) -> Session:
        """Restore a session by ID with pre-existing message history.

        Used to revive an in-memory session from persisted disk state after a
        broker restart.  A minimal ``SessionLedger`` is created for the restored
        session so subsequent operations work without errors.
        """
        now = datetime.now(timezone.utc).isoformat()
        session = Session(
            session_id=session_id,
            created_at=now,
            updated_at=now,
            system_prompt=(system_prompt or "").strip(),
            messages=list(messages),
            turn_count=sum(1 for m in messages if m.get("role") == "assistant"),
        )
        self._sessions[session_id] = session
        ledger = SessionLedger(session_id)
        ledger.record(
            record_session_opened(
                session_id,
                ledger.next_sequence,
                system_prompt=session.system_prompt,
            )
        )
        self._ledgers[session_id] = ledger
        return session

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def get_ledger(self, session_id: str) -> Optional[SessionLedger]:
        """Return the ``SessionLedger`` for *session_id*, or ``None`` if not found."""
        return self._ledgers.get(session_id)

    def append_message(self, session_id: str, role: str, content: str) -> None:
        """Append one ``{"role", "content"}`` turn to the session's message history.

        ``turn_count`` is incremented only when *role* is ``"assistant"`` so it
        represents the number of completed assistant responses, not the total
        message count.
        """
        session = self.get(session_id)
        if session is None:
            raise ValueError("unknown session_id: %s" % session_id)
        session.messages.append(
            {
                "role": role.strip(),
                "content": content.strip(),
            }
        )
        if role.strip() == "assistant":
            session.turn_count += 1
        session.updated_at = datetime.now(timezone.utc).isoformat()



# ---------------------------------------------------------------------------
# Disk persistence helpers (restart-safe session history)
# ---------------------------------------------------------------------------

def _session_file(state_dir: Path, session_id: str) -> Path:
    """Return the path for the persisted session JSON file."""
    return state_dir / "sessions" / ("%s.json" % session_id)


def persist_messages(
    state_dir: Path,
    session_id: str,
    messages: List[Dict[str, str]],
    system_prompt: str = "",
) -> None:
    """Save *messages* (and optional *system_prompt*) for *session_id* to disk.

    The file is written atomically-ish by writing to a ``.tmp`` file and then
    renaming, so a crash mid-write doesn't corrupt the previous data.
    """
    dest = _session_file(state_dir, session_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "session_id": session_id,
        "system_prompt": system_prompt,
        "messages": messages,
    }
    tmp = dest.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(dest)


def load_persisted_session(
    state_dir: Path,
    session_id: str,
) -> Optional[Tuple[List[Dict[str, str]], str]]:
    """Load messages and system_prompt for *session_id* from disk.

    Returns ``(messages, system_prompt)`` or ``None`` if no persisted state
    exists for *session_id*.
    """
    dest = _session_file(state_dir, session_id)
    if not dest.exists():
        return None
    try:
        payload = json.loads(dest.read_text(encoding="utf-8"))
        messages = payload.get("messages", [])
        system_prompt = payload.get("system_prompt", "")
        return messages, system_prompt
    except (json.JSONDecodeError, OSError):
        return None
