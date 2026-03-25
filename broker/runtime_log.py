"""Simple broker console and file logging."""

from __future__ import annotations

import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate(text: str, limit: int = 300) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


class BrokerLogger:
    """Thread-safe broker logger for terminal and broker log file."""

    def __init__(self, log_dir: Path, log_level: int, verbose: int) -> None:
        self.log_dir = log_dir
        self.log_level = max(0, min(3, int(log_level)))
        self.verbose = max(0, min(3, int(verbose)))
        self._lock = threading.Lock()
        self._handle = None

    def start(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._handle = (self.log_dir / "broker.log").open("a", encoding="utf-8")

    def close(self) -> None:
        with self._lock:
            if self._handle is not None:
                self._handle.close()
                self._handle = None

    def error(self, message: str, **fields: Any) -> None:
        self._emit(0, "ERROR", message, fields or None)

    def info(self, message: str, **fields: Any) -> None:
        self._emit(1, "INFO", message, fields or None)

    def debug(self, message: str, **fields: Any) -> None:
        self._emit(2, "DEBUG", message, fields or None)

    def trace(self, message: str, **fields: Any) -> None:
        self._emit(3, "TRACE", message, fields or None)

    def request(
        self,
        method: str,
        path: str,
        status_code: int,
        *,
        summary: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self.verbose <= 0:
            return
        payload: Dict[str, Any] = {"status": status_code}
        if self.verbose >= 2 and summary:
            payload["summary"] = summary
        if self.verbose >= 3 and detail:
            payload["detail"] = {
                key: _truncate(json.dumps(value, ensure_ascii=True), 240)
                if not isinstance(value, str)
                else _truncate(value, 240)
                for key, value in detail.items()
            }
        self.info("%s %s" % (method, path), **payload)

    def _emit(
        self,
        threshold: int,
        label: str,
        message: str,
        fields: Optional[Dict[str, Any]],
    ) -> None:
        if threshold > self.log_level:
            return
        record = {
            "timestamp": _utc_now(),
            "level": label,
            "message": message,
        }
        if fields:
            record.update(fields)
        line = self._format_record(record)
        stream = sys.stderr if threshold == 0 else sys.stdout
        with self._lock:
            print(line, file=stream, flush=True)
            if self._handle is not None:
                self._handle.write(line + "\n")
                self._handle.flush()

    def _format_record(self, record: Dict[str, Any]) -> str:
        extras = []
        for key, value in record.items():
            if key in {"timestamp", "level", "message"}:
                continue
            extras.append("%s=%s" % (key, value))
        suffix = (" | " + " ".join(extras)) if extras else ""
        return "[%s] %s %s%s" % (
            record["timestamp"],
            record["level"],
            record["message"],
            suffix,
        )
