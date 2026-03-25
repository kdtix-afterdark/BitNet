"""Focused tests for the broker durable state layer."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from broker.config import BrokerConfig
from broker.durable_state import BrokerStateManager


def _build_config(root: Path, *, snapshot_turn_interval: int = 3) -> BrokerConfig:
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
        system_prompts_dir=root / "broker" / "system_prompts",
        system_prompt_path=root / "broker" / "system_prompts" / "default.system.prompt.md",
        mcp_config_path=root / "broker" / "mcp_servers.json",
        mcp_startup_timeout=5,
        mcp_request_timeout=5,
        mcp_protocol_version="2025-03-26",
        snapshot_turn_interval=snapshot_turn_interval,
        snapshot_history_turns=2,
        heartbeat_interval_seconds=0,
        memory_sync_enabled=True,
        memory_sync_retry_seconds=5,
        trace_turns=False,
        trace_dir=root / "broker_traces",
    )


class BrokerStateManagerTests(unittest.TestCase):
    def test_clean_shutdown_persists_manifest_and_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = _build_config(Path(temp_dir))
            manager = BrokerStateManager(config)
            manager.startup()
            manager.record_session_open(
                session_id="session-1",
                system_prompt="You are helpful.",
                metadata={"project": "demo"},
                created_at="2026-03-19T01:00:00+00:00",
            )
            manager.record_turn_started(
                session_id="session-1",
                correlation_id="corr-1",
                prompt="Hello there",
                payload={"source": "test"},
            )
            manager.record_turn_completed(
                session_id="session-1",
                correlation_id="corr-1",
                user_prompt="Hello there",
                assistant_response="Hello back.",
                payload={"model_invoked": True},
            )
            manager.queue_memory_sync(
                session_id="session-1",
                correlation_id="corr-1",
                kind="session_turn",
                payload={
                    "entity_name": "BrokerSession::session-1",
                    "entity_type": "broker-session",
                    "observation": "User: Hello there\nAssistant: Hello back.",
                },
            )
            manager.shutdown_clean()

            manifest = json.loads((config.state_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["clean_shutdown"])
            self.assertGreaterEqual(manifest["last_seq"], 1)
            self.assertEqual(manifest["pending_sync_count"], 1)
            self.assertIsNotNone(manifest["last_snapshot_path"])

    def test_dirty_recovery_replays_session_and_pending_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = _build_config(Path(temp_dir), snapshot_turn_interval=10)
            manager = BrokerStateManager(config)
            manager.startup()
            manager.record_session_open(
                session_id="session-2",
                system_prompt="Recovered prompt",
                metadata={"project": "recovery"},
                created_at="2026-03-19T01:05:00+00:00",
            )
            manager.record_turn_completed(
                session_id="session-2",
                correlation_id="corr-2",
                user_prompt="First question",
                assistant_response="First answer",
                payload={"model_invoked": True},
            )
            manager.queue_memory_sync(
                session_id="session-2",
                correlation_id="corr-2",
                kind="session_turn",
                payload={
                    "entity_name": "BrokerSession::session-2",
                    "entity_type": "broker-session",
                    "observation": "Recovered observation",
                },
            )

            manifest_path = config.state_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["active_pid"] = 999999
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            recovered = BrokerStateManager(config).startup()
            self.assertTrue(recovered.report["dirty_recovery"])
            self.assertEqual(recovered.report["pending_sync_count"], 1)
            self.assertEqual(len(recovered.sessions), 1)
            restored_session = recovered.sessions[0]
            self.assertEqual(restored_session.session_id, "session-2")
            self.assertEqual(len(restored_session.messages), 2)
            self.assertEqual(restored_session.messages[-1]["content"], "First answer")

    def test_snapshot_recovery_uses_compact_history_plus_journal_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = _build_config(Path(temp_dir), snapshot_turn_interval=2)
            manager = BrokerStateManager(config)
            manager.startup()
            manager.record_session_open(
                session_id="session-3",
                system_prompt="Snapshot prompt",
                metadata={},
                created_at="2026-03-19T01:10:00+00:00",
            )
            manager.record_turn_completed(
                session_id="session-3",
                correlation_id="corr-1",
                user_prompt="Turn one question",
                assistant_response="Turn one answer",
                payload={"model_invoked": True},
            )
            manager.record_turn_completed(
                session_id="session-3",
                correlation_id="corr-2",
                user_prompt="Turn two question",
                assistant_response="Turn two answer",
                payload={"model_invoked": True},
            )
            manager.record_turn_completed(
                session_id="session-3",
                correlation_id="corr-3",
                user_prompt="Turn three question",
                assistant_response="Turn three answer",
                payload={"model_invoked": True},
            )

            report = BrokerStateManager(config).inspect_last_session()
            self.assertEqual(report["replay_mode"], "partial")
            self.assertEqual(report["active_session"]["session_id"], "session-3")

            recovered = BrokerStateManager(config).startup()
            restored = recovered.sessions[0]
            self.assertLessEqual(len(restored.messages), 4)
            self.assertEqual(restored.messages[-1]["content"], "Turn three answer")
            self.assertIn("Turn one question", restored.summary)
            self.assertIn("Turn one answer", restored.summary)
            self.assertGreaterEqual(restored.summarized_turn_count, 1)

    def test_running_recovery_report_preserves_dirty_startup_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = _build_config(Path(temp_dir), snapshot_turn_interval=10)
            manager = BrokerStateManager(config)
            manager.startup()
            manager.record_session_open(
                session_id="session-4",
                system_prompt="Dirty prompt",
                metadata={"project": "dirty"},
                created_at="2026-03-19T01:20:00+00:00",
            )
            manager.record_turn_completed(
                session_id="session-4",
                correlation_id="corr-4",
                user_prompt="Dirty question",
                assistant_response="Dirty answer",
                payload={"model_invoked": False},
            )

            manifest_path = config.state_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["active_pid"] = 999999
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            restarted = BrokerStateManager(config)
            recovery = restarted.startup()
            self.assertTrue(recovery.report["dirty_recovery"])

            live_report = restarted.get_last_recovery_report()
            self.assertTrue(live_report["dirty_recovery"])
            self.assertEqual(live_report["active_session"]["session_id"], "session-4")


if __name__ == "__main__":
    unittest.main()
