"""In-memory session tracking for the local BitNet broker."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4


@dataclass
class Session:
    """Broker session metadata stored in memory for the MVP."""

    session_id: str
    created_at: str
    updated_at: str
    system_prompt: str
    metadata: Dict[str, str] = field(default_factory=dict)
    messages: List[Dict[str, str]] = field(default_factory=list)
    summary: str = ""
    summarized_turn_count: int = 0
    turn_count: int = 0


class SessionStore:
    """Simple in-memory session store."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def create(
        self, system_prompt: str, metadata: Optional[Dict[str, str]] = None
    ) -> Session:
        session = Session(
            session_id=str(uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            system_prompt=system_prompt.strip(),
            metadata=metadata or {},
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def append_message(self, session_id: str, role: str, content: str) -> None:
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

    def restore(self, session: Session) -> Session:
        """Load a previously persisted session into the active in-memory store."""
        self._sessions[session.session_id] = session
        return session

    def list_sessions(self) -> List[Session]:
        """Return all known sessions."""
        return list(self._sessions.values())
