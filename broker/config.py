"""Configuration helpers for the local BitNet broker."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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


@dataclass
class BrokerConfig:
    """Runtime configuration for the broker and managed llama-server."""

    workspace_root: Path
    model_path: Path
    broker_host: str
    broker_port: int
    llama_host: str
    llama_port: int
    llama_server_path: Path
    threads: int
    ctx_size: int
    n_predict: int
    temperature: float
    startup_timeout: int
    request_timeout: int
    log_dir: Path
    mcp_config_path: Path
    mcp_startup_timeout: int
    mcp_request_timeout: int
    mcp_protocol_version: str

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
                / "ggml-model-i2s-bitnet.gguf",
            )
        ).resolve()

        llama_server_path = Path(
            os.environ.get(
                "BITNET_LLAMA_SERVER_PATH",
                workspace_root / "build" / "bin" / "llama-server",
            )
        ).resolve()

        log_dir = Path(
            os.environ.get("BITNET_BROKER_LOG_DIR", workspace_root / "broker_logs")
        ).resolve()

        return cls(
            workspace_root=workspace_root,
            model_path=model_path,
            broker_host=os.environ.get("BITNET_BROKER_HOST", "127.0.0.1"),
            broker_port=_env_int("BITNET_BROKER_PORT", 8091),
            llama_host=os.environ.get("BITNET_LLAMA_HOST", "127.0.0.1"),
            llama_port=_env_int("BITNET_LLAMA_PORT", 8080),
            llama_server_path=llama_server_path,
            threads=_env_int("BITNET_BROKER_THREADS", 2),
            ctx_size=_env_int("BITNET_BROKER_CTX_SIZE", 2048),
            n_predict=_env_int("BITNET_BROKER_N_PREDICT", 512),
            temperature=_env_float("BITNET_BROKER_TEMPERATURE", 0.2),
            startup_timeout=_env_int("BITNET_BROKER_STARTUP_TIMEOUT", 120),
            request_timeout=_env_int("BITNET_BROKER_REQUEST_TIMEOUT", 180),
            log_dir=log_dir,
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
        )
