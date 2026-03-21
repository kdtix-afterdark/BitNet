"""In-memory session tracking for the local BitNet broker."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from broker.durable_state import SessionLedger, record_session_opened


@dataclass
class Session:
    """Broker session metadata stored in memory for the MVP."""

    session_id: str
    created_at: str
    system_prompt: str
    metadata: Dict[str, str] = field(default_factory=dict)


class SessionStore:
    """Simple in-memory session store.

    In addition to ``Session`` metadata, each session is paired with an
    append-only ``SessionLedger`` that records all activity events for the
    duration of the session.  The ledger is accessible via ``get_ledger()``.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}
        self._ledgers: Dict[str, SessionLedger] = {}

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

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def get_ledger(self, session_id: str) -> Optional[SessionLedger]:
        """Return the ``SessionLedger`` for *session_id*, or ``None`` if not found."""
        return self._ledgers.get(session_id)

