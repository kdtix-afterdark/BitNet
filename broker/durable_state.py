"""Durable broker state management for journaled sessions and crash recovery."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from .config import BrokerConfig
from .session_store import Session


STATE_VERSION = 1
MANIFEST_NAME = "manifest.json"
JOURNAL_NAME = "broker_events.jsonl"
SNAPSHOT_DIR_NAME = "snapshots"
SUMMARY_CHAR_LIMIT = 6000
SUMMARY_TRUNCATION_MARKER = "\n\n[... summarized context omitted ...]\n\n"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate_text(value: str, limit: int = 600) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


@dataclass
class PendingSyncItem:
    """Durable queue item for cold-memory synchronization."""

    item_id: str
    session_id: str
    correlation_id: str
    queued_at: str
    kind: str
    payload: Dict[str, Any]
    attempts: int = 0
    last_attempt_at: Optional[str] = None
    last_error: Optional[str] = None
    next_attempt_at: Optional[str] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "PendingSyncItem":
        return cls(
            item_id=str(payload["item_id"]),
            session_id=str(payload["session_id"]),
            correlation_id=str(payload["correlation_id"]),
            queued_at=str(payload["queued_at"]),
            kind=str(payload.get("kind", "session_turn")),
            payload=dict(payload.get("payload", {})),
            attempts=int(payload.get("attempts", 0)),
            last_attempt_at=payload.get("last_attempt_at"),
            last_error=payload.get("last_error"),
            next_attempt_at=payload.get("next_attempt_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionRuntimeState:
    """Compact persisted view of one broker session."""

    session_id: str
    created_at: str
    updated_at: str
    system_prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    messages: List[Dict[str, str]] = field(default_factory=list)
    summary: str = ""
    summarized_turn_count: int = 0
    turn_count: int = 0

    @classmethod
    def from_snapshot(cls, payload: Dict[str, Any]) -> "SessionRuntimeState":
        return cls(
            session_id=str(payload["session_id"]),
            created_at=str(payload["created_at"]),
            updated_at=str(payload.get("updated_at", payload["created_at"])),
            system_prompt=str(payload["system_prompt"]),
            metadata=dict(payload.get("metadata", {})),
            messages=[dict(message) for message in payload.get("messages", [])],
            summary=str(payload.get("summary", "")),
            summarized_turn_count=int(payload.get("summarized_turn_count", 0)),
            turn_count=int(payload.get("turn_count", 0)),
        )

    def to_snapshot(self) -> Dict[str, Any]:
        return asdict(self)

    def to_session(self) -> Session:
        return Session(
            session_id=self.session_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            system_prompt=self.system_prompt,
            metadata=dict(self.metadata),
            messages=[dict(message) for message in self.messages],
            summary=self.summary,
            summarized_turn_count=self.summarized_turn_count,
            turn_count=self.turn_count,
        )


@dataclass
class RecoveryState:
    """Recovered hot/warm state loaded from disk on broker startup."""

    sessions: List[Session]
    pending_sync: List[PendingSyncItem]
    report: Dict[str, Any]


class BrokerStateManager:
    """Persist broker lifecycle events, snapshots, and pending cold-memory sync."""

    def __init__(self, config: BrokerConfig) -> None:
        self.config = config
        self.state_dir = config.state_dir
        self.journal_path = self.state_dir / JOURNAL_NAME
        self.manifest_path = self.state_dir / MANIFEST_NAME
        self.snapshots_dir = self.state_dir / SNAPSHOT_DIR_NAME
        self._lock = threading.RLock()
        self._sequence = 0
        self._sessions: Dict[str, SessionRuntimeState] = {}
        self._pending_sync: List[PendingSyncItem] = []
        self._manifest = self._default_manifest()
        self._recovery_report: Dict[str, Any] = {}
        self._last_memory_sync: Dict[str, Any] = {}
        self._turns_since_snapshot = 0
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def model_settings_hash(self) -> str:
        return self._manifest.get("model_settings_hash", "")

    def startup(self) -> RecoveryState:
        """Load journaled state from disk and mark the broker instance active."""
        with self._lock:
            self._ensure_dirs()
            recovery = self._load_runtime_state()
            self._sessions = {
                session_id: SessionRuntimeState(
                    session_id=session.session_id,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    system_prompt=session.system_prompt,
                    metadata=dict(session.metadata),
                    messages=[dict(message) for message in session.messages],
                    summary=session.summary,
                    summarized_turn_count=session.summarized_turn_count,
                    turn_count=session.turn_count,
                )
                for session_id, session in {
                    session.session_id: session for session in recovery.sessions
                }.items()
            }
            self._pending_sync = [
                PendingSyncItem.from_dict(item.to_dict()) for item in recovery.pending_sync
            ]
            self._recovery_report = dict(recovery.report)

            self._manifest["clean_shutdown"] = False
            self._manifest["last_started_at"] = _utc_now()
            self._manifest["active_pid"] = os.getpid()
            self._manifest["model_settings_hash"] = self._compute_model_settings_hash()
            self._manifest["last_recovery"] = dict(self._recovery_report)
            self._refresh_manifest_state()
            self._write_manifest_locked()

            if self._recovery_report.get("dirty_recovery"):
                self._append_event_locked(
                    "dirty_recovery_detected",
                    payload={
                        "replay_mode": self._recovery_report.get("replay_mode"),
                        "replayed_events": self._recovery_report.get("replayed_events", 0),
                        "pending_sync_count": self._recovery_report.get("pending_sync_count", 0),
                    },
                )
            self._append_event_locked(
                "broker_started",
                payload={
                    "dirty_recovery": self._recovery_report.get("dirty_recovery", False),
                    "model_settings_hash": self.model_settings_hash,
                },
            )

            return RecoveryState(
                sessions=[session.to_session() for session in self._sessions.values()],
                pending_sync=[PendingSyncItem.from_dict(item.to_dict()) for item in self._pending_sync],
                report=dict(self._recovery_report),
            )

    def inspect_last_session(self) -> Dict[str, Any]:
        """Load the persisted broker state without mutating it."""
        with self._lock:
            self._ensure_dirs()
            recovery = self._load_runtime_state()
            report = dict(recovery.report)
            report["sessions"] = self._summarize_sessions(recovery.sessions)
            return report

    def get_last_recovery_report(self) -> Dict[str, Any]:
        """Return the last startup recovery result for a running broker instance."""
        with self._lock:
            report = dict(self._recovery_report)
            report["sessions"] = self._summarize_sessions(
                session.to_session() for session in self._sessions.values()
            )
            return report

    def start_heartbeat(self) -> None:
        """Start a lightweight heartbeat that records liveness in the journal."""
        if self.config.heartbeat_interval_seconds <= 0 or self._heartbeat_thread is not None:
            return
        self._stop_event.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="broker-heartbeat",
            daemon=True,
        )
        self._heartbeat_thread.start()

    def stop_heartbeat(self) -> None:
        """Stop the background heartbeat thread."""
        self._stop_event.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join(timeout=2)
            self._heartbeat_thread = None

    def record_session_open(
        self,
        session_id: str,
        system_prompt: str,
        metadata: Dict[str, Any],
        created_at: str,
    ) -> None:
        with self._lock:
            self._append_event_locked(
                "session_open",
                session_id=session_id,
                payload={
                    "created_at": created_at,
                    "system_prompt": system_prompt,
                    "metadata": metadata,
                },
            )

    def record_turn_started(
        self,
        session_id: Optional[str],
        correlation_id: str,
        prompt: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            self._append_event_locked(
                "turn_started",
                session_id=session_id,
                correlation_id=correlation_id,
                payload={
                    "prompt_excerpt": _truncate_text(prompt, limit=240),
                    **(payload or {}),
                },
            )

    def record_turn_failed(
        self,
        session_id: Optional[str],
        correlation_id: str,
        prompt: str,
        error: str,
    ) -> None:
        with self._lock:
            self._append_event_locked(
                "turn_failed",
                session_id=session_id,
                correlation_id=correlation_id,
                payload={
                    "prompt_excerpt": _truncate_text(prompt, limit=240),
                    "error": error,
                },
            )

    def record_tool_called(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        session_id: Optional[str],
        correlation_id: Optional[str],
    ) -> None:
        with self._lock:
            self._append_event_locked(
                "tool_called",
                session_id=session_id,
                correlation_id=correlation_id,
                payload={
                    "tool": tool_name,
                    "arguments": arguments,
                    "result_excerpt": _truncate_text(
                        json.dumps(result, ensure_ascii=True, sort_keys=True),
                        limit=1200,
                    ),
                },
            )

    def record_turn_completed(
        self,
        session_id: Optional[str],
        correlation_id: str,
        user_prompt: str,
        assistant_response: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            self._append_event_locked(
                "turn_completed",
                session_id=session_id,
                correlation_id=correlation_id,
                payload={
                    "user_prompt": user_prompt,
                    "assistant_response": assistant_response,
                    **(payload or {}),
                },
            )
            self._turns_since_snapshot += 1
            if self._turns_since_snapshot >= self.config.snapshot_turn_interval:
                self.create_snapshot("interval")

    def queue_memory_sync(
        self,
        session_id: str,
        correlation_id: str,
        kind: str,
        payload: Dict[str, Any],
    ) -> PendingSyncItem:
        item = PendingSyncItem(
            item_id=str(uuid4()),
            session_id=session_id,
            correlation_id=correlation_id,
            queued_at=_utc_now(),
            kind=kind,
            payload=dict(payload),
            next_attempt_at=_utc_now(),
        )
        with self._lock:
            self._append_event_locked(
                "memory_sync_queued",
                session_id=session_id,
                correlation_id=correlation_id,
                payload=item.to_dict(),
            )
        return item

    def get_ready_sync_item(self) -> Optional[PendingSyncItem]:
        with self._lock:
            now = _utc_now()
            for item in self._pending_sync:
                if item.next_attempt_at is None or item.next_attempt_at <= now:
                    return PendingSyncItem.from_dict(item.to_dict())
        return None

    def record_memory_sync_attempt(self, item_id: str) -> Optional[PendingSyncItem]:
        with self._lock:
            item = self._find_pending_sync(item_id)
            if item is None:
                return None
            item.attempts += 1
            item.last_attempt_at = _utc_now()
            item.last_error = None
            self._append_event_locked(
                "memory_sync_attempted",
                session_id=item.session_id,
                correlation_id=item.correlation_id,
                payload={"item_id": item.item_id, "attempts": item.attempts},
            )
            return PendingSyncItem.from_dict(item.to_dict())

    def record_memory_sync_completed(
        self,
        item_id: str,
        detail: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            item = self._find_pending_sync(item_id)
            if item is None:
                return
            self._append_event_locked(
                "memory_sync_completed",
                session_id=item.session_id,
                correlation_id=item.correlation_id,
                payload={
                    "item_id": item.item_id,
                    "detail": detail or {},
                },
            )

    def record_memory_sync_failed(self, item_id: str, error: str) -> None:
        with self._lock:
            item = self._find_pending_sync(item_id)
            if item is None:
                return
            item.last_error = error
            item.next_attempt_at = datetime.fromtimestamp(
                time.time() + self.config.memory_sync_retry_seconds,
                tz=timezone.utc,
            ).isoformat()
            self._append_event_locked(
                "memory_sync_failed",
                session_id=item.session_id,
                correlation_id=item.correlation_id,
                payload={
                    "item_id": item.item_id,
                    "error": error,
                    "next_attempt_at": item.next_attempt_at,
                },
            )

    def create_snapshot(self, reason: str) -> Path:
        with self._lock:
            snapshot_seq = self._sequence
            snapshot_payload = {
                "version": STATE_VERSION,
                "created_at": _utc_now(),
                "reason": reason,
                "seq": snapshot_seq,
                "model_settings_hash": self.model_settings_hash,
                "sessions": [
                    self._build_compact_session_payload(session)
                    for session in self._sessions.values()
                ],
                "pending_sync_queue": [item.to_dict() for item in self._pending_sync],
                "last_memory_sync": dict(self._last_memory_sync),
            }
            snapshot_name = "snapshot-%06d.json" % snapshot_seq
            snapshot_path = self.snapshots_dir / snapshot_name
            self._atomic_write_json(snapshot_path, snapshot_payload)
            self._manifest["last_snapshot_path"] = str(snapshot_path.relative_to(self.state_dir))
            self._manifest["last_snapshot_seq"] = snapshot_seq
            self._manifest["last_snapshot_at"] = snapshot_payload["created_at"]
            self._turns_since_snapshot = 0
            self._write_manifest_locked()
            self._append_event_locked(
                "snapshot_created",
                payload={
                    "reason": reason,
                    "snapshot_path": self._manifest["last_snapshot_path"],
                    "snapshot_seq": snapshot_seq,
                },
            )
            return snapshot_path

    def shutdown_clean(self) -> None:
        with self._lock:
            self.create_snapshot("shutdown")
            self._append_event_locked(
                "shutdown_clean",
                payload={"pending_sync_count": len(self._pending_sync)},
            )
            self._manifest["clean_shutdown"] = True
            self._manifest["active_pid"] = None
            self._manifest["last_shutdown_at"] = _utc_now()
            self._write_manifest_locked()

    def build_health(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "state_dir": str(self.state_dir),
                "journal_path": str(self.journal_path),
                "clean_shutdown": bool(self._manifest.get("clean_shutdown", True)),
                "last_seq": int(self._manifest.get("last_seq", self._sequence)),
                "last_snapshot_seq": self._manifest.get("last_snapshot_seq"),
                "last_snapshot_at": self._manifest.get("last_snapshot_at"),
                "active_session_count": len(self._sessions),
                "pending_sync_count": len(self._pending_sync),
                "last_memory_sync": dict(self._last_memory_sync),
                "last_recovery": dict(self._recovery_report),
            }

    def active_session_count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def pending_sync_count(self) -> int:
        with self._lock:
            return len(self._pending_sync)

    def _heartbeat_loop(self) -> None:
        while not self._stop_event.wait(self.config.heartbeat_interval_seconds):
            try:
                with self._lock:
                    self._append_event_locked(
                        "heartbeat",
                        payload={
                            "active_session_count": len(self._sessions),
                            "pending_sync_count": len(self._pending_sync),
                        },
                    )
                    self._manifest["last_heartbeat_at"] = _utc_now()
                    self._write_manifest_locked()
            except Exception:
                # Heartbeats are best-effort and should never crash the broker.
                continue

    def _load_runtime_state(self) -> RecoveryState:
        self._sessions = {}
        self._pending_sync = []
        self._last_memory_sync = {}
        manifest = self._read_manifest()
        self._manifest = manifest
        self._sequence = int(manifest.get("last_seq", 0))
        snapshot_seq = 0
        snapshot_path = manifest.get("last_snapshot_path")
        if isinstance(snapshot_path, str) and snapshot_path:
            snapshot_full_path = self.state_dir / snapshot_path
            snapshot_payload = self._read_json(snapshot_full_path)
            if snapshot_payload:
                snapshot_seq = int(snapshot_payload.get("seq", 0))
                self._hydrate_from_snapshot(snapshot_payload)
        replayed_events = self._replay_events(snapshot_seq)
        report = self._build_recovery_report(
            dirty_recovery=(
                not bool(manifest.get("clean_shutdown", True))
                and not self._is_pid_active(manifest.get("active_pid"))
            ),
            replayed_events=replayed_events,
            snapshot_seq=snapshot_seq,
            snapshot_path=str(snapshot_path) if snapshot_path else None,
        )
        return RecoveryState(
            sessions=[session.to_session() for session in self._sessions.values()],
            pending_sync=[PendingSyncItem.from_dict(item.to_dict()) for item in self._pending_sync],
            report=report,
        )

    def _hydrate_from_snapshot(self, snapshot_payload: Dict[str, Any]) -> None:
        self._sessions = {
            raw["session_id"]: SessionRuntimeState.from_snapshot(raw)
            for raw in snapshot_payload.get("sessions", [])
        }
        self._pending_sync = [
            PendingSyncItem.from_dict(item)
            for item in snapshot_payload.get("pending_sync_queue", [])
        ]
        self._last_memory_sync = dict(snapshot_payload.get("last_memory_sync", {}))

    def _replay_events(self, min_seq: int) -> int:
        replayed = 0
        if not self.journal_path.exists():
            return replayed
        for raw_line in self.journal_path.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            seq = int(record.get("seq", 0))
            self._sequence = max(self._sequence, seq)
            if seq <= min_seq:
                continue
            replayed += 1
            self._apply_event(record)
        return replayed

    def _build_recovery_report(
        self,
        dirty_recovery: bool,
        replayed_events: int,
        snapshot_seq: int,
        snapshot_path: Optional[str],
    ) -> Dict[str, Any]:
        active_pid = self._manifest.get("active_pid")
        if replayed_events == 0:
            replay_mode = "none" if snapshot_seq else "complete"
        elif snapshot_seq:
            replay_mode = "partial"
        else:
            replay_mode = "complete"

        last_session = self._latest_session()
        return {
            "dirty_recovery": dirty_recovery,
            "active_run_detected": self._is_pid_active(active_pid),
            "replay_mode": replay_mode,
            "replayed_events": replayed_events,
            "last_clean_checkpoint": {
                "snapshot_seq": snapshot_seq or None,
                "snapshot_path": snapshot_path,
                "last_shutdown_at": self._manifest.get("last_shutdown_at"),
            },
            "pending_sync_count": len(self._pending_sync),
            "pending_unsynced_turns": [
                {
                    "item_id": item.item_id,
                    "session_id": item.session_id,
                    "correlation_id": item.correlation_id,
                    "queued_at": item.queued_at,
                    "attempts": item.attempts,
                    "last_error": item.last_error,
                }
                for item in self._pending_sync[:10]
            ],
            "last_successful_memory_sync": dict(self._last_memory_sync),
            "active_session": (
                {
                    "session_id": last_session.session_id,
                    "created_at": last_session.created_at,
                    "updated_at": last_session.updated_at,
                    "turn_count": last_session.turn_count,
                    "message_count": len(last_session.messages),
                    "summary_char_count": len(last_session.summary),
                    "summarized_turn_count": last_session.summarized_turn_count,
                }
                if last_session is not None
                else None
            ),
        }

    def _default_manifest(self) -> Dict[str, Any]:
        return {
            "version": STATE_VERSION,
            "instance_id": str(uuid4()),
            "clean_shutdown": True,
            "last_seq": 0,
            "last_snapshot_path": None,
            "last_snapshot_seq": None,
            "last_snapshot_at": None,
            "last_started_at": None,
            "last_shutdown_at": None,
            "last_heartbeat_at": None,
            "last_event_at": None,
            "model_settings_hash": self._compute_model_settings_hash(),
            "last_recovery": {},
            "active_session_count": 0,
            "pending_sync_count": 0,
            "last_memory_sync_success_at": None,
            "active_pid": None,
        }

    def _compute_model_settings_hash(self) -> str:
        payload = {
            "model_path": str(self.config.model_path),
            "llama_server_path": str(self.config.llama_server_path),
            "gpu_layers": self.config.gpu_layers,
            "threads": self.config.threads,
            "ctx_size": self.config.ctx_size,
            "n_predict": self.config.n_predict,
            "n_keep": self.config.n_keep,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest()

    def _is_pid_active(self, pid: Any) -> bool:
        if not isinstance(pid, int) or pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    def _append_event_locked(
        self,
        event_type: str,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._sequence += 1
        record = {
            "seq": self._sequence,
            "recorded_at": _utc_now(),
            "event_type": event_type,
            "session_id": session_id,
            "correlation_id": correlation_id,
            "payload": payload or {},
        }
        self._append_journal_line(record)
        self._apply_event(record)
        self._manifest["last_seq"] = self._sequence
        self._manifest["last_event_at"] = record["recorded_at"]
        self._refresh_manifest_state()
        self._write_manifest_locked()
        return record

    def _apply_event(self, record: Dict[str, Any]) -> None:
        event_type = record.get("event_type")
        payload = dict(record.get("payload") or {})
        session_id = record.get("session_id")
        recorded_at = str(record.get("recorded_at", _utc_now()))

        if event_type == "session_open" and session_id:
            session = SessionRuntimeState(
                session_id=str(session_id),
                created_at=str(payload.get("created_at", recorded_at)),
                updated_at=str(payload.get("created_at", recorded_at)),
                system_prompt=str(payload.get("system_prompt", "")).strip(),
                metadata=dict(payload.get("metadata", {})),
            )
            self._sessions[session.session_id] = session
            return

        if event_type == "turn_completed" and session_id:
            session = self._sessions.get(str(session_id))
            if session is None:
                session = SessionRuntimeState(
                    session_id=str(session_id),
                    created_at=recorded_at,
                    updated_at=recorded_at,
                    system_prompt="",
                )
                self._sessions[session.session_id] = session
            user_prompt = str(payload.get("user_prompt", "")).strip()
            assistant_response = str(payload.get("assistant_response", "")).strip()
            if user_prompt:
                session.messages.append({"role": "user", "content": user_prompt})
            if assistant_response:
                session.messages.append({"role": "assistant", "content": assistant_response})
                session.turn_count += 1
            session.updated_at = recorded_at
            self._trim_session_messages(session)
            return

        if event_type == "memory_sync_queued":
            item = PendingSyncItem.from_dict(payload)
            if self._find_pending_sync(item.item_id) is None:
                self._pending_sync.append(item)
            return

        if event_type == "memory_sync_attempted":
            item = self._find_pending_sync(str(payload.get("item_id")))
            if item is not None:
                item.attempts = int(payload.get("attempts", item.attempts))
                item.last_attempt_at = recorded_at
            return

        if event_type == "memory_sync_failed":
            item = self._find_pending_sync(str(payload.get("item_id")))
            if item is not None:
                item.last_error = str(payload.get("error", ""))
                item.next_attempt_at = payload.get("next_attempt_at")
            return

        if event_type == "memory_sync_completed":
            item_id = str(payload.get("item_id", ""))
            self._pending_sync = [item for item in self._pending_sync if item.item_id != item_id]
            self._last_memory_sync = {
                "item_id": item_id,
                "completed_at": recorded_at,
                "detail": dict(payload.get("detail", {})),
            }
            return

    def _find_pending_sync(self, item_id: str) -> Optional[PendingSyncItem]:
        for item in self._pending_sync:
            if item.item_id == item_id:
                return item
        return None

    def _latest_session(self) -> Optional[SessionRuntimeState]:
        if not self._sessions:
            return None
        return max(self._sessions.values(), key=lambda item: item.updated_at)

    def _trim_session_messages(self, session: SessionRuntimeState) -> None:
        max_messages = max(self.config.snapshot_history_turns, 1) * 2
        if len(session.messages) > max_messages:
            dropped_messages = session.messages[:-max_messages]
            session.messages = session.messages[-max_messages:]
            self._append_session_summary(session, dropped_messages)

    def _build_compact_session_payload(self, session: SessionRuntimeState) -> Dict[str, Any]:
        return {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "system_prompt": session.system_prompt,
            "metadata": dict(session.metadata),
            "messages": [dict(message) for message in session.messages],
            "summary": session.summary,
            "summarized_turn_count": session.summarized_turn_count,
            "turn_count": session.turn_count,
        }

    def _summarize_sessions(self, sessions: Iterable[Session]) -> List[Dict[str, Any]]:
        return [
            {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "message_count": len(session.messages),
                "turn_count": session.turn_count,
                "summary_char_count": len(session.summary),
                "summarized_turn_count": session.summarized_turn_count,
            }
            for session in sessions
        ]

    def _append_session_summary(
        self,
        session: SessionRuntimeState,
        messages: List[Dict[str, str]],
    ) -> None:
        summary_chunk, summarized_turns = self._summarize_messages(messages)
        if not summary_chunk:
            return
        if session.summary:
            session.summary = f"{session.summary}\n\n{summary_chunk}"
        else:
            session.summary = summary_chunk
        session.summarized_turn_count += summarized_turns
        session.summary = self._trim_summary_text(session.summary)

    def _summarize_messages(self, messages: List[Dict[str, str]]) -> tuple[str, int]:
        lines: List[str] = []
        pending_user: Optional[str] = None
        summarized_turns = 0

        for message in messages:
            role = str(message.get("role", "")).strip().lower()
            content = " ".join(str(message.get("content", "")).split())
            compact = _truncate_text(content, limit=180)
            if not compact:
                continue
            if role == "user":
                if pending_user is not None:
                    lines.append(f"User: {pending_user}")
                    summarized_turns += 1
                pending_user = compact
                continue
            if role == "assistant":
                if pending_user is not None:
                    lines.append(f"User: {pending_user}")
                    lines.append(f"Assistant: {compact}")
                    pending_user = None
                    summarized_turns += 1
                else:
                    lines.append(f"Assistant: {compact}")
                continue
            lines.append(f"{role.title() or 'Message'}: {compact}")

        if pending_user is not None:
            lines.append(f"User: {pending_user}")
            summarized_turns += 1

        return "\n".join(lines), summarized_turns

    def _trim_summary_text(self, summary: str) -> str:
        compact = summary.strip()
        if len(compact) <= SUMMARY_CHAR_LIMIT:
            return compact
        retained_head = SUMMARY_CHAR_LIMIT // 2
        retained_tail = SUMMARY_CHAR_LIMIT - retained_head - len(SUMMARY_TRUNCATION_MARKER)
        if retained_tail < 0:
            retained_tail = 0
        return (
            compact[:retained_head].rstrip()
            + SUMMARY_TRUNCATION_MARKER
            + compact[-retained_tail:].lstrip()
        )

    def _append_journal_line(self, record: Dict[str, Any]) -> None:
        self._ensure_dirs()
        with self.journal_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _write_manifest_locked(self) -> None:
        self._atomic_write_json(self.manifest_path, self._manifest)

    def _refresh_manifest_state(self) -> None:
        self._manifest["active_session_count"] = len(self._sessions)
        self._manifest["pending_sync_count"] = len(self._pending_sync)
        self._manifest["last_memory_sync_success_at"] = self._last_memory_sync.get("completed_at")

    def _read_manifest(self) -> Dict[str, Any]:
        payload = self._read_json(self.manifest_path)
        if payload is None:
            return self._default_manifest()
        merged = self._default_manifest()
        merged.update(payload)
        return merged

    def _read_json(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _atomic_write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        self._ensure_dirs()
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)

    def _ensure_dirs(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
