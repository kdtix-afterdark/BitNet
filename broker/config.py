"""Configuration helpers for the local BitNet broker."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .system_prompts import (
    DEFAULT_SYSTEM_PROMPT_FILENAME,
    default_system_prompts_dir,
    resolve_system_prompt_path,
)


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    return float(value)


@dataclass(frozen=True)
class BrokerEnvVar:
    """Documentation metadata for one broker environment variable."""

    name: str
    default: str
    description: str


def broker_env_vars() -> List[BrokerEnvVar]:
    """Return the environment variable surface for the broker runtime."""
    return [
        BrokerEnvVar(
            "BITNET_WORKSPACE_ROOT",
            "current working directory",
            "Workspace root used to resolve default relative paths.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_MODEL",
            "${workspace_root}/models/bitnet-b1.58-2B-4T-bf16/ggml-model-f32-bitnet.gguf",
            "GGUF model path for the broker-managed llama-server.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_HOST",
            "127.0.0.1",
            "Broker bind host.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_PORT",
            "8091",
            "Broker bind port.",
        ),
        BrokerEnvVar(
            "BITNET_LLAMA_HOST",
            "127.0.0.1",
            "llama-server bind host.",
        ),
        BrokerEnvVar(
            "BITNET_LLAMA_PORT",
            "8080",
            "llama-server bind port.",
        ),
        BrokerEnvVar(
            "BITNET_LLAMA_BUILD_DIR",
            "${workspace_root}/build-metal",
            "Build directory that contains the llama-server binary.",
        ),
        BrokerEnvVar(
            "BITNET_LLAMA_SERVER_PATH",
            "${BITNET_LLAMA_BUILD_DIR}/bin/llama-server",
            "Explicit llama-server binary path override.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_GPU_LAYERS",
            "999",
            "Number of model layers to offload to the GPU backend.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_THREADS",
            "10",
            "Generation thread count.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_CTX_SIZE",
            "8192",
            "Context window size used by the broker-managed model runtime.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_N_PREDICT",
            "4096",
            "Default max completion tokens per request.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_N_KEEP",
            "-1",
            "Prompt tokens to keep when context shifting occurs.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_TEMPERATURE",
            "0.5",
            "Default sampling temperature.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_TOP_P",
            "0.9",
            "Default top-p sampling value.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_STARTUP_TIMEOUT",
            "120",
            "Seconds to wait for llama-server to become ready.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_REQUEST_TIMEOUT",
            "180",
            "Seconds to wait for a model completion response.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_LOG_LEVEL",
            "1",
            "Broker console/file log level: 0=errors, 1=info, 2=debug, 3=trace.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_VERBOSE",
            "0",
            "Broker request detail level: 0=quiet, 1=requests, 2=summaries, 3=payload excerpts.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_LOG_DIR",
            "${workspace_root}/broker_logs",
            "Directory for broker and MCP log files.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_STATE_DIR",
            "${workspace_root}/broker_state",
            "Directory for the durable journal, manifest, and snapshots.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_SYSTEM_PROMPTS_DIR",
            "${workspace_root}/broker/system_prompts",
            "Directory that contains reusable markdown system prompt files.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_SYSTEM_PROMPT",
            "${BITNET_BROKER_SYSTEM_PROMPTS_DIR}/default.system.prompt.md",
            "Default chat system prompt file. Accepts either a workspace-local path or a filename inside BITNET_BROKER_SYSTEM_PROMPTS_DIR.",
        ),
        BrokerEnvVar(
            "BITNET_MCP_CONFIG",
            "${workspace_root}/broker/mcp_servers.json",
            "Path to the MCP server configuration file.",
        ),
        BrokerEnvVar(
            "BITNET_MCP_STARTUP_TIMEOUT",
            "30",
            "Seconds to wait for MCP server startup.",
        ),
        BrokerEnvVar(
            "BITNET_MCP_REQUEST_TIMEOUT",
            "60",
            "Seconds to wait for an MCP tool response.",
        ),
        BrokerEnvVar(
            "BITNET_MCP_PROTOCOL_VERSION",
            "2025-03-26",
            "Protocol version passed during MCP initialize handshake.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_SNAPSHOT_TURN_INTERVAL",
            "3",
            "Create a warm-state snapshot after this many completed turns.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_SNAPSHOT_HISTORY_TURNS",
            "8",
            "Turns retained verbatim in warm snapshots; older turns are compacted into a recovered session summary.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_HEARTBEAT_INTERVAL_SECONDS",
            "30",
            "Heartbeat cadence for liveness/audit events; set 0 to disable.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_MEMORY_SYNC_ENABLED",
            "1",
            "Enable async cold-memory sync to the Memory MCP server.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_MEMORY_SYNC_RETRY_SECONDS",
            "15",
            "Retry delay for failed async memory sync items.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_TRACE_TURNS",
            "0",
            "Enable per-turn broker trace capture for prompt assembly, raw model output, repairs, and session persistence.",
        ),
        BrokerEnvVar(
            "BITNET_BROKER_TRACE_DIR",
            "${workspace_root}/broker_traces",
            "Directory for append-only broker turn trace logs and per-correlation trace files.",
        ),
    ]


def broker_env_help_text() -> str:
    """Format the broker environment variable surface for CLI help output."""
    lines = [
        "Environment variables (CLI flags override these values):",
    ]
    width = max(len(item.name) for item in broker_env_vars())
    for item in broker_env_vars():
        lines.append(
            "  {name:<{width}}  default={default}  {description}".format(
                name=item.name,
                width=width,
                default=item.default,
                description=item.description,
            )
        )
    return "\n".join(lines)


@dataclass
class BrokerConfig:
    """Runtime configuration for the broker and managed llama-server."""

    workspace_root: Path
    model_path: Path
    broker_host: str
    broker_port: int
    llama_host: str
    llama_port: int
    llama_build_dir: Path
    llama_server_path: Path
    gpu_layers: int
    threads: int
    ctx_size: int
    n_predict: int
    n_keep: int
    temperature: float
    top_p: float
    startup_timeout: int
    request_timeout: int
    log_level: int
    verbose: int
    log_dir: Path
    state_dir: Path
    system_prompts_dir: Path
    system_prompt_path: Path
    mcp_config_path: Path
    mcp_startup_timeout: int
    mcp_request_timeout: int
    mcp_protocol_version: str
    snapshot_turn_interval: int
    snapshot_history_turns: int
    heartbeat_interval_seconds: int
    memory_sync_enabled: bool
    memory_sync_retry_seconds: int
    trace_turns: bool
    trace_dir: Path

    @classmethod
    def from_env(cls) -> "BrokerConfig":
        workspace_root = Path(
            os.environ.get("BITNET_WORKSPACE_ROOT", Path.cwd())
        ).resolve()

        model_path = Path(
            os.environ.get(
                "BITNET_BROKER_MODEL",
                workspace_root
                / "models"
                / "bitnet-b1.58-2B-4T-bf16"
                / "ggml-model-f32-bitnet.gguf",
            )
        ).resolve()

        llama_build_dir = Path(
            os.environ.get(
                "BITNET_LLAMA_BUILD_DIR",
                workspace_root / "build-metal",
            )
        ).resolve()

        llama_server_path = Path(
            os.environ.get(
                "BITNET_LLAMA_SERVER_PATH",
                llama_build_dir / "bin" / "llama-server",
            )
        ).resolve()

        log_dir = Path(
            os.environ.get("BITNET_BROKER_LOG_DIR", workspace_root / "broker_logs")
        ).resolve()
        state_dir = Path(
            os.environ.get("BITNET_BROKER_STATE_DIR", workspace_root / "broker_state")
        ).resolve()
        system_prompts_dir = Path(
            os.environ.get(
                "BITNET_BROKER_SYSTEM_PROMPTS_DIR",
                default_system_prompts_dir(workspace_root),
            )
        ).resolve()
        trace_dir = Path(
            os.environ.get("BITNET_BROKER_TRACE_DIR", workspace_root / "broker_traces")
        ).resolve()
        system_prompt_path = resolve_system_prompt_path(
            os.environ.get(
                "BITNET_BROKER_SYSTEM_PROMPT",
                DEFAULT_SYSTEM_PROMPT_FILENAME,
            ),
            workspace_root=workspace_root,
            prompts_dir=system_prompts_dir,
        )

        return cls(
            workspace_root=workspace_root,
            model_path=model_path,
            broker_host=os.environ.get("BITNET_BROKER_HOST", "127.0.0.1"),
            broker_port=_env_int("BITNET_BROKER_PORT", 8091),
            llama_host=os.environ.get("BITNET_LLAMA_HOST", "127.0.0.1"),
            llama_port=_env_int("BITNET_LLAMA_PORT", 8080),
            llama_build_dir=llama_build_dir,
            llama_server_path=llama_server_path,
            gpu_layers=_env_int("BITNET_BROKER_GPU_LAYERS", 999),
            threads=_env_int("BITNET_BROKER_THREADS", 10),
            ctx_size=_env_int("BITNET_BROKER_CTX_SIZE", 8192),
            n_predict=_env_int("BITNET_BROKER_N_PREDICT", 4096),
            n_keep=_env_int("BITNET_BROKER_N_KEEP", -1),
            temperature=_env_float("BITNET_BROKER_TEMPERATURE", 0.5),
            top_p=_env_float("BITNET_BROKER_TOP_P", 0.9),
            startup_timeout=_env_int("BITNET_BROKER_STARTUP_TIMEOUT", 120),
            request_timeout=_env_int("BITNET_BROKER_REQUEST_TIMEOUT", 180),
            log_level=_env_int("BITNET_BROKER_LOG_LEVEL", 1),
            verbose=_env_int("BITNET_BROKER_VERBOSE", 0),
            log_dir=log_dir,
            state_dir=state_dir,
            system_prompts_dir=system_prompts_dir,
            system_prompt_path=system_prompt_path,
            mcp_config_path=Path(
                os.environ.get(
                    "BITNET_MCP_CONFIG",
                    workspace_root / "broker" / "mcp_servers.json",
                )
            ).resolve(),
            mcp_startup_timeout=_env_int("BITNET_MCP_STARTUP_TIMEOUT", 30),
            mcp_request_timeout=_env_int("BITNET_MCP_REQUEST_TIMEOUT", 60),
            mcp_protocol_version=os.environ.get(
                "BITNET_MCP_PROTOCOL_VERSION",
                "2025-03-26",
            ),
            snapshot_turn_interval=_env_int("BITNET_BROKER_SNAPSHOT_TURN_INTERVAL", 3),
            snapshot_history_turns=_env_int("BITNET_BROKER_SNAPSHOT_HISTORY_TURNS", 8),
            heartbeat_interval_seconds=_env_int(
                "BITNET_BROKER_HEARTBEAT_INTERVAL_SECONDS", 30
            ),
            memory_sync_enabled=(
                os.environ.get("BITNET_BROKER_MEMORY_SYNC_ENABLED", "1").strip().lower()
                not in {"0", "false", "no", "off"}
            ),
            memory_sync_retry_seconds=_env_int(
                "BITNET_BROKER_MEMORY_SYNC_RETRY_SECONDS", 15
            ),
            trace_turns=(
                os.environ.get("BITNET_BROKER_TRACE_TURNS", "0").strip().lower()
                in {"1", "true", "yes", "on"}
            ),
            trace_dir=trace_dir,
        )
