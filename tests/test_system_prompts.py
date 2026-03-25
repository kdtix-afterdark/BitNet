"""Regression tests for file-backed system prompt selection."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from broker.config import BrokerConfig
from broker.server import BrokerApp
from broker.session_store import SessionStore
from broker.system_prompts import SystemPromptLoader


class _FakeState:
    def __init__(self) -> None:
        self.session_open_calls: list[dict[str, object]] = []

    def record_session_open(
        self,
        *,
        session_id: str,
        system_prompt: str,
        metadata: dict[str, str],
        created_at: str,
    ) -> None:
        self.session_open_calls.append(
            {
                "session_id": session_id,
                "system_prompt": system_prompt,
                "metadata": metadata,
                "created_at": created_at,
            }
        )


def _build_config(root: Path) -> BrokerConfig:
    prompt_dir = root / "broker" / "system_prompts"
    return BrokerConfig(
        workspace_root=root,
        model_path=root / "models" / "dummy.gguf",
        broker_host="127.0.0.1",
        broker_port=8091,
        llama_host="127.0.0.1",
        llama_port=8080,
        llama_build_dir=root / "build-metal",
        llama_server_path=root / "build-metal" / "bin" / "llama-server",
        gpu_layers=999,
        threads=10,
        ctx_size=8192,
        n_predict=4096,
        n_keep=-1,
        temperature=0.5,
        top_p=0.9,
        startup_timeout=5,
        request_timeout=5,
        log_level=0,
        verbose=0,
        log_dir=root / "broker_logs",
        state_dir=root / "broker_state",
        mcp_config_path=root / "broker" / "mcp_servers.json",
        mcp_startup_timeout=5,
        mcp_request_timeout=5,
        mcp_protocol_version="2025-03-26",
        snapshot_turn_interval=3,
        snapshot_history_turns=2,
        heartbeat_interval_seconds=0,
        memory_sync_enabled=True,
        memory_sync_retry_seconds=5,
        trace_turns=False,
        trace_dir=root / "broker_traces",
        system_prompts_dir=prompt_dir,
        system_prompt_path=prompt_dir / "default.system.prompt.md",
    )


def _build_app(config: BrokerConfig) -> BrokerApp:
    app = object.__new__(BrokerApp)
    app.config = config
    app.sessions = SessionStore()
    app.state = _FakeState()
    app.system_prompts = SystemPromptLoader(
        workspace_root=config.workspace_root,
        prompts_dir=config.system_prompts_dir,
        default_prompt_path=config.system_prompt_path,
    )
    return app


class SessionSystemPromptTests(unittest.TestCase):
    def test_stateless_chat_uses_default_prompt_from_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt_dir = root / "broker" / "system_prompts"
            prompt_dir.mkdir(parents=True)
            (prompt_dir / "default.system.prompt.md").write_text(
                "Default prompt from markdown.",
                encoding="utf-8",
            )

            app = _build_app(_build_config(root))

            resolved = app._resolve_system_prompt({})

            self.assertEqual(resolved, "Default prompt from markdown.")

    def test_create_session_loads_default_prompt_from_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt_dir = root / "broker" / "system_prompts"
            prompt_dir.mkdir(parents=True)
            (prompt_dir / "default.system.prompt.md").write_text(
                "Default prompt from markdown.",
                encoding="utf-8",
            )

            app = _build_app(_build_config(root))

            payload = app.create_session({"metadata": {"uat": "default"}})

            self.assertEqual(payload["system_prompt"], "Default prompt from markdown.")

    def test_create_session_loads_named_prompt_from_prompts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt_dir = root / "broker" / "system_prompts"
            prompt_dir.mkdir(parents=True)
            (prompt_dir / "default.system.prompt.md").write_text(
                "Default prompt from markdown.",
                encoding="utf-8",
            )
            (prompt_dir / "kdtix.system.prompt.md").write_text(
                "KDTIX prompt from markdown.",
                encoding="utf-8",
            )

            app = _build_app(_build_config(root))

            payload = app.create_session(
                {
                    "system_prompt_path": "kdtix.system.prompt.md",
                    "metadata": {"uat": "named"},
                }
            )

            self.assertEqual(payload["system_prompt"], "KDTIX prompt from markdown.")

    def test_inline_system_prompt_overrides_markdown_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt_dir = root / "broker" / "system_prompts"
            prompt_dir.mkdir(parents=True)
            (prompt_dir / "default.system.prompt.md").write_text(
                "Default prompt from markdown.",
                encoding="utf-8",
            )
            (prompt_dir / "kdtix.system.prompt.md").write_text(
                "KDTIX prompt from markdown.",
                encoding="utf-8",
            )

            app = _build_app(_build_config(root))

            payload = app.create_session(
                {
                    "system_prompt": "Inline prompt wins.",
                    "system_prompt_path": "kdtix.system.prompt.md",
                }
            )

            self.assertEqual(payload["system_prompt"], "Inline prompt wins.")

    def test_create_session_rejects_prompt_paths_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt_dir = root / "broker" / "system_prompts"
            prompt_dir.mkdir(parents=True)
            (prompt_dir / "default.system.prompt.md").write_text(
                "Default prompt from markdown.",
                encoding="utf-8",
            )
            outside_prompt = root.parent / "outside.system.prompt.md"
            outside_prompt.write_text("Outside workspace prompt.", encoding="utf-8")
            self.addCleanup(outside_prompt.unlink)

            app = _build_app(_build_config(root))

            with self.assertRaises(ValueError):
                app.create_session({"system_prompt_path": str(outside_prompt)})


if __name__ == "__main__":
    unittest.main()
