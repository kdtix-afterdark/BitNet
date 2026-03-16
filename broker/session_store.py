"""In-memory session tracking for the local BitNet broker."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4


@dataclass
class Session:
    """Broker session metadata stored in memory for the MVP."""

    session_id: str
    created_at: str
    system_prompt: str
    metadata: Dict[str, str] = field(default_factory=dict)


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
            system_prompt=system_prompt.strip(),
            metadata=metadata or {},
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

