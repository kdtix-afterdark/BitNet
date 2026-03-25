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
    n_keep: int
    temperature: float
    top_p: float
    gpu_layers: int
    batch_size: int
    ubatch_size: int
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

        # Auto-detect: prefer build-metal/ (GPU) over build/ (CPU) when the
        # env var is not set explicitly.
        if "BITNET_LLAMA_SERVER_PATH" in os.environ:
            llama_server_path = Path(os.environ["BITNET_LLAMA_SERVER_PATH"]).resolve()
        else:
            metal_path = workspace_root / "build-metal" / "bin" / "llama-server"
            cpu_path = workspace_root / "build" / "bin" / "llama-server"
            llama_server_path = metal_path if metal_path.exists() else cpu_path

        log_dir = Path(
            os.environ.get("BITNET_BROKER_LOG_DIR", workspace_root / "broker_logs")
        ).resolve()

        # i2_s safeguard: the BLAS backend only claims MUL_MAT ops when the
        # physical batch dimension reaches its min_batch=32 threshold, and
        # GGML_TYPE_I2_S requires external scale handling that the generic BLAS
        # dequantize-to-float path does not support.  With BLAS enabled this
        # causes a reproducible segfault at n_ubatch >= 32.  Default both batch
        # dimensions to 31 for i2_s models so the managed runtime is safe
        # out-of-the-box.  Users can raise these values once they either disable
        # BLAS (`-DGGML_BLAS=OFF`) or apply an explicit I2_S guard in
        # `3rdparty/llama.cpp/ggml/src/ggml-blas.cpp` to decline MUL_MAT for
        # GGML_TYPE_I2_S (see PR #37 comment thread for details).
        model_path_lower = str(model_path).lower()
        is_i2s_model = "i2_s" in model_path_lower or "-i2s" in model_path_lower
        _safe_batch = 31 if is_i2s_model else 512
        batch_size = _env_int("BITNET_BROKER_BATCH_SIZE", _safe_batch)
        ubatch_size = _env_int("BITNET_BROKER_UBATCH_SIZE", _safe_batch)

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
            n_keep=_env_int("BITNET_BROKER_N_KEEP", -1),
            temperature=_env_float("BITNET_BROKER_TEMPERATURE", 0.2),
            top_p=_env_float("BITNET_BROKER_TOP_P", 0.9),
            gpu_layers=_env_int("BITNET_BROKER_GPU_LAYERS", 0),
            batch_size=batch_size,
            ubatch_size=ubatch_size,
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
