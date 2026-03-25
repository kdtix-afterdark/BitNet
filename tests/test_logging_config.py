"""Regression tests for broker/logging_config.py.

Covers:
- TRACE custom level (below DEBUG) exists and is named "TRACE".
- BrokerLogger initialization, log-level filtering, and file capture.
- Log directory creation and latest.log symlink/copy.
- Verbose and debug config fields in BrokerConfig.
- CLI --verbose / --debug args wired through apply_cli_overrides.
- BrokerLogger.for_component() factory produces named loggers.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import List

import pytest


# ---------------------------------------------------------------------------
# TRACE level
# ---------------------------------------------------------------------------

class TestTraceLevelExists:
    def test_trace_level_is_below_debug(self):
        from broker.logging_config import TRACE
        assert TRACE < logging.DEBUG

    def test_trace_level_name_is_trace(self):
        from broker.logging_config import TRACE
        assert logging.getLevelName(TRACE) == "TRACE"

    def test_trace_numeric_value_is_5(self):
        from broker.logging_config import TRACE
        assert TRACE == 5


# ---------------------------------------------------------------------------
# BrokerLogger: basic construction
# ---------------------------------------------------------------------------

class TestBrokerLoggerInit:
    def test_creates_without_error(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            BrokerLogger("test-init", verbose=1, debug=0, log_dir=Path(tmpdir))

    def test_for_component_factory(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = BrokerLogger.for_component(
                "broker", verbose=1, debug=0, log_dir=Path(tmpdir)
            )
            assert logger is not None

    def test_default_verbose_is_one(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = BrokerLogger("test-defaults", log_dir=Path(tmpdir))
            assert logger.verbose == 1

    def test_default_debug_is_zero(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = BrokerLogger("test-defaults", log_dir=Path(tmpdir))
            assert logger.debug_level == 0


# ---------------------------------------------------------------------------
# Level filtering
# ---------------------------------------------------------------------------

class TestBrokerLoggerLevelFiltering:
    """Messages below the configured level must NOT be written."""

    def _capture_log(self, verbose: int, debug: int = 0) -> "BrokerLogger":
        from broker.logging_config import BrokerLogger
        tmpdir = tempfile.mkdtemp()
        return BrokerLogger("filter-test", verbose=verbose, debug=debug,
                            log_dir=Path(tmpdir)), Path(tmpdir)

    def test_verbose_0_suppresses_info(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = BrokerLogger("t", verbose=0, log_dir=Path(tmpdir))
            assert not logger.is_enabled_for_info()

    def test_verbose_1_allows_info(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = BrokerLogger("t", verbose=1, log_dir=Path(tmpdir))
            assert logger.is_enabled_for_info()

    def test_verbose_1_suppresses_debug(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = BrokerLogger("t", verbose=1, log_dir=Path(tmpdir))
            assert not logger.is_enabled_for_debug()

    def test_verbose_2_allows_debug(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = BrokerLogger("t", verbose=2, log_dir=Path(tmpdir))
            assert logger.is_enabled_for_debug()

    def test_verbose_2_suppresses_trace(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = BrokerLogger("t", verbose=2, log_dir=Path(tmpdir))
            assert not logger.is_enabled_for_trace()

    def test_verbose_3_allows_trace(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = BrokerLogger("t", verbose=3, log_dir=Path(tmpdir))
            assert logger.is_enabled_for_trace()

    def test_verbose_0_always_allows_error(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = BrokerLogger("t", verbose=0, log_dir=Path(tmpdir))
            assert logger.is_enabled_for_error()


# ---------------------------------------------------------------------------
# Log file creation
# ---------------------------------------------------------------------------

class TestLogFileCreation:
    def test_log_file_created_in_log_dir(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            BrokerLogger("broker", verbose=1, log_dir=log_dir)
            log_files = list(log_dir.glob("broker*.log"))
            assert len(log_files) >= 1, "at least one broker log file should exist"

    def test_log_dir_created_if_absent(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "deep" / "nested" / "logs"
            assert not log_dir.exists()
            BrokerLogger("broker", verbose=1, log_dir=log_dir)
            assert log_dir.exists()

    def test_latest_log_reference_exists(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            BrokerLogger("broker", verbose=1, log_dir=log_dir)
            assert (log_dir / "broker-latest.log").exists()

    def test_written_messages_appear_in_log_file(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = BrokerLogger("broker", verbose=2, log_dir=log_dir)
            logger.info("UAT test message sentinel-abc123")
            latest = log_dir / "broker-latest.log"
            content = latest.read_text(encoding="utf-8")
            assert "sentinel-abc123" in content

    def test_debug_messages_appear_when_verbose_2(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = BrokerLogger("broker", verbose=2, log_dir=log_dir)
            logger.debug("debug-sentinel-xyz789")
            latest = log_dir / "broker-latest.log"
            content = latest.read_text(encoding="utf-8")
            assert "debug-sentinel-xyz789" in content

    def test_debug_messages_suppressed_when_verbose_1(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = BrokerLogger("broker", verbose=1, log_dir=log_dir)
            logger.debug("should-not-appear-debug-aaa")
            latest = log_dir / "broker-latest.log"
            content = latest.read_text(encoding="utf-8")
            assert "should-not-appear-debug-aaa" not in content

    def test_trace_messages_appear_when_verbose_3(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = BrokerLogger("broker", verbose=3, log_dir=log_dir)
            logger.trace("trace-sentinel-qqq999")
            latest = log_dir / "broker-latest.log"
            content = latest.read_text(encoding="utf-8")
            assert "trace-sentinel-qqq999" in content

    def test_error_always_written_regardless_of_verbose(self):
        from broker.logging_config import BrokerLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = BrokerLogger("broker", verbose=0, log_dir=log_dir)
            logger.error("error-sentinel-err000")
            latest = log_dir / "broker-latest.log"
            content = latest.read_text(encoding="utf-8")
            assert "error-sentinel-err000" in content


# ---------------------------------------------------------------------------
# BrokerConfig verbose/debug fields
# ---------------------------------------------------------------------------

class TestBrokerConfigVerboseDebug:
    def test_verbose_default_is_one(self):
        from broker.config import BrokerConfig
        cfg = BrokerConfig.from_env()
        assert cfg.verbose == 1

    def test_debug_level_default_is_zero(self):
        from broker.config import BrokerConfig
        cfg = BrokerConfig.from_env()
        assert cfg.debug_level == 0

    def test_verbose_read_from_env(self, monkeypatch):
        monkeypatch.setenv("BITNET_BROKER_VERBOSE", "2")
        from broker import config as cfg_module
        import importlib
        importlib.reload(cfg_module)
        cfg = cfg_module.BrokerConfig.from_env()
        assert cfg.verbose == 2

    def test_debug_level_read_from_env(self, monkeypatch):
        monkeypatch.setenv("BITNET_BROKER_DEBUG", "3")
        from broker import config as cfg_module
        import importlib
        importlib.reload(cfg_module)
        cfg = cfg_module.BrokerConfig.from_env()
        assert cfg.debug_level == 3

    def test_verbose_clamped_to_range(self, monkeypatch):
        monkeypatch.setenv("BITNET_BROKER_VERBOSE", "99")
        from broker import config as cfg_module
        import importlib
        importlib.reload(cfg_module)
        cfg = cfg_module.BrokerConfig.from_env()
        assert cfg.verbose <= 3


# ---------------------------------------------------------------------------
# apply_cli_overrides: --verbose and --debug
# ---------------------------------------------------------------------------

class TestCliVerboseDebugOverrides:
    def test_verbose_arg_overrides_config(self):
        from broker.config import BrokerConfig
        cfg = BrokerConfig.from_env()
        original_verbose = cfg.verbose
        cfg.apply_cli_overrides(verbose=3)
        assert cfg.verbose == 3

    def test_debug_arg_overrides_config(self):
        from broker.config import BrokerConfig
        cfg = BrokerConfig.from_env()
        cfg.apply_cli_overrides(debug_level=2)
        assert cfg.debug_level == 2

    def test_none_verbose_leaves_config_unchanged(self):
        from broker.config import BrokerConfig
        cfg = BrokerConfig.from_env()
        original = cfg.verbose
        cfg.apply_cli_overrides(verbose=None)
        assert cfg.verbose == original

    def test_none_debug_leaves_config_unchanged(self):
        from broker.config import BrokerConfig
        cfg = BrokerConfig.from_env()
        original = cfg.debug_level
        cfg.apply_cli_overrides(debug_level=None)
        assert cfg.debug_level == original


# ---------------------------------------------------------------------------
# Log directory convention: workspace_root/logs/<component>/
# ---------------------------------------------------------------------------

class TestStandardLogDirectory:
    def test_standard_log_dir_for_broker_component(self):
        from broker.logging_config import standard_log_dir
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            d = standard_log_dir(ws, "broker")
            assert d == ws / "logs" / "broker"

    def test_standard_log_dir_for_llama_server(self):
        from broker.logging_config import standard_log_dir
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            d = standard_log_dir(ws, "llama-server")
            assert d == ws / "logs" / "llama-server"

    def test_uat_log_dir(self):
        from broker.logging_config import standard_log_dir
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            d = standard_log_dir(ws, "uat")
            assert d == ws / "logs" / "uat"
