"""Structured logging for the local BitNet broker.

Provides a four-level logging system (error / info / debug / trace) with:

- Automatic log file capture in ``{workspace_root}/logs/{component}/``
- Timestamp-named session files (``broker-20260325-123456.log``) so each
  broker run produces its own archive without overwriting previous runs.
- A ``{component}-latest.log`` file updated on every run for easy UAT
  reference (no need to find the latest timestamped file).
- A ``standard_log_dir(workspace_root, component)`` helper that returns the
  canonical log path used by all broker components.

Log level mapping
-----------------
``verbose`` parameter controls the minimum level written to **both** the
console and the session log file:

+-------+-------+---------+
| value | name  | logging |
+-------+-------+---------+
|   0   | ERROR | 40      |
|   1   | INFO  | 20      |
|   2   | DEBUG | 10      |
|   3   | TRACE | 5       |
+-------+-------+---------+

The ``debug`` parameter is reserved for component-specific deep diagnostics
(request/response body dumps, per-token traces, etc.).  Components check
``logger.debug_level >= N`` to gate expensive instrumentation.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# TRACE level — sits below DEBUG (10) so verbose=3 emits everything.
# ---------------------------------------------------------------------------

TRACE: int = 5
logging.addLevelName(TRACE, "TRACE")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def standard_log_dir(workspace_root: Path, component: str) -> Path:
    """Return the canonical log directory for *component*.

    All broker components write logs to ``{workspace_root}/logs/{component}/``
    so UAT reporters have a single, predictable place to collect evidence.

    Parameters
    ----------
    workspace_root:
        Root of the BitNet workspace (the directory that contains ``broker/``).
    component:
        A short slug identifying the producer, e.g. ``"broker"``,
        ``"llama-server"``, ``"mcp"``, or ``"uat"``.
    """
    return workspace_root / "logs" / component


def _verbose_to_python_level(verbose: int) -> int:
    """Map the 0-3 verbose int to a Python logging level integer."""
    return {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG, 3: TRACE}.get(
        max(0, min(3, verbose)), logging.INFO
    )


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# BrokerLogger
# ---------------------------------------------------------------------------

class BrokerLogger:
    """Thin wrapper around :mod:`logging` that adds TRACE support, automatic
    log file creation, and a ``latest`` reference.

    Parameters
    ----------
    name:
        Logger name (used in the ``[name]`` column of log lines).
    verbose:
        Minimum verbosity level to emit: 0=error, 1=info, 2=debug, 3=trace.
    debug_level:
        Depth of debug instrumentation for expensive operations (0-3).
    log_dir:
        Directory where log files are written.  Created automatically if it
        does not exist.  When ``None`` the logger writes only to stderr.
    """

    def __init__(
        self,
        name: str,
        verbose: int = 1,
        debug: int = 0,
        debug_level: Optional[int] = None,
        log_dir: Optional[Path] = None,
    ) -> None:
        self.verbose = max(0, min(3, verbose))
        # Accept either `debug` or `debug_level` as keyword; `debug_level` wins if both.
        self.debug_level = max(0, min(3, debug_level if debug_level is not None else debug))
        self._name = name
        self._log_dir = log_dir
        self._session_log: Optional[Path] = None
        self._latest_log: Optional[Path] = None

        py_level = _verbose_to_python_level(self.verbose)

        # Use a unique logger name to avoid clashing with the root logger or
        # other broker instances created during tests.
        internal_name = "broker.%s.%s" % (name, id(self))
        self._logger = logging.getLogger(internal_name)
        self._logger.setLevel(py_level)
        self._logger.propagate = False

        formatter = _build_formatter()

        # Console handler — only attach once (avoid duplicate output in tests).
        if not self._logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(py_level)
            ch.setFormatter(formatter)
            self._logger.addHandler(ch)

        # File handler — always create when log_dir is given.
        if log_dir is not None:
            log_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            self._session_log = log_dir / ("%s-%s.log" % (name, ts))
            self._latest_log = log_dir / ("%s-latest.log" % name)
            fh = logging.FileHandler(str(self._session_log), encoding="utf-8")
            fh.setLevel(py_level)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
            # latest.log is opened in write mode (truncate) so it always
            # represents the *current* broker run only.  UAT reporters can
            # attach this file directly without hunting for the timestamped
            # archive.  Previous runs are preserved in the session files.
            lh = logging.FileHandler(str(self._latest_log), mode="w", encoding="utf-8")
            lh.setLevel(py_level)
            lh.setFormatter(formatter)
            self._logger.addHandler(lh)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def for_component(
        cls,
        component: str,
        verbose: int = 1,
        debug: int = 0,
        debug_level: Optional[int] = None,
        log_dir: Optional[Path] = None,
    ) -> "BrokerLogger":
        """Create a :class:`BrokerLogger` for a named component.

        This is the recommended factory for production use.  The *component*
        slug becomes both the logger name and (when *log_dir* is provided) the
        leaf directory name under ``logs/``.
        """
        effective_debug = debug_level if debug_level is not None else debug
        return cls(component, verbose=verbose, debug_level=effective_debug, log_dir=log_dir)

    # ------------------------------------------------------------------
    # Level predicates
    # ------------------------------------------------------------------

    def is_enabled_for_error(self) -> bool:
        return True  # errors are always emitted

    def is_enabled_for_info(self) -> bool:
        return self.verbose >= 1

    def is_enabled_for_debug(self) -> bool:
        return self.verbose >= 2

    def is_enabled_for_trace(self) -> bool:
        return self.verbose >= 3

    # ------------------------------------------------------------------
    # Emit helpers
    # ------------------------------------------------------------------

    def error(self, msg: str, **kwargs: object) -> None:
        self._logger.error(msg, **kwargs)

    def info(self, msg: str, **kwargs: object) -> None:
        if self.is_enabled_for_info():
            self._logger.info(msg, **kwargs)

    def debug(self, msg: str, **kwargs: object) -> None:
        if self.is_enabled_for_debug():
            self._logger.debug(msg, **kwargs)

    def trace(self, msg: str, **kwargs: object) -> None:
        if self.is_enabled_for_trace():
            self._logger.log(TRACE, msg, **kwargs)

    # ------------------------------------------------------------------
    # Log-file paths
    # ------------------------------------------------------------------

    @property
    def session_log_path(self) -> Optional[Path]:
        """Path to this session's timestamped log file, or ``None``."""
        return self._session_log

    @property
    def latest_log_path(self) -> Optional[Path]:
        """Path to the rolling ``{name}-latest.log`` file, or ``None``."""
        return self._latest_log

    def close(self) -> None:
        """Flush and close all file handlers."""
        for handler in list(self._logger.handlers):
            try:
                handler.flush()
                handler.close()
            except Exception:  # noqa: BLE001
                pass
        self._logger.handlers.clear()
