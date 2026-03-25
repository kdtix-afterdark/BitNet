"""Minimal stdio MCP client and registry for the local broker."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import BrokerConfig


@dataclass
class McpServerConfig:
    """Configuration for one stdio MCP server."""

    name: str
    command: str
    args: List[str]
    enabled: bool = True
    transport: str = "stdio"
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    description: str = ""

    @classmethod
    def from_dict(cls, name: str, payload: Dict[str, Any]) -> "McpServerConfig":
        return cls(
            name=name,
            command=str(payload["command"]),
            args=[str(arg) for arg in payload.get("args", [])],
            enabled=bool(payload.get("enabled", True)),
            transport=str(payload.get("transport", "stdio")),
            cwd=str(payload["cwd"]) if payload.get("cwd") is not None else None,
            env={str(key): str(value) for key, value in payload.get("env", {}).items()},
            description=str(payload.get("description", "")),
        )


class McpStdioSession:
    """One synchronous stdio MCP client session."""

    def __init__(self, config: McpServerConfig, broker_config: BrokerConfig) -> None:
        self.config = config
        self.broker_config = broker_config
        self._process: Optional[subprocess.Popen[str]] = None
        self._next_id = 1
        self._lock = threading.Lock()
        self._initialized = False
        self._log_handle = None

    def start(self) -> None:
        """Launch the MCP server and complete initialize handshake."""
        if self._initialized:
            return
        if self.config.transport != "stdio":
            raise ValueError(
                "Unsupported MCP transport for %s: %s"
                % (self.config.name, self.config.transport)
            )

        self.broker_config.log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.broker_config.log_dir / ("mcp-%s.log" % self.config.name)
        self._log_handle = log_path.open("a", encoding="utf-8")

        env = os.environ.copy()
        env.update(self._expand_env(self.config.env or {}))

        cwd = (
            self._expand_path(self.config.cwd)
            if self.config.cwd
            else self.broker_config.workspace_root
        )
        command = [self.config.command, *self.config.args]
        self._process = subprocess.Popen(
            command,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self._log_handle,
            text=True,
            bufsize=1,
        )

        self._request(
            "initialize",
            {
                "protocolVersion": self.broker_config.mcp_protocol_version,
                "capabilities": {"tools": {}},
                "clientInfo": {
                    "name": "bitnet-local-broker",
                    "version": "0.1.0",
                },
            },
        )
        self._notify("notifications/initialized", {})
        self._initialized = True

    def stop(self) -> None:
        """Terminate the MCP server process if the broker started it."""
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=2)
        self._process = None
        self._initialized = False
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return MCP tool descriptors for the server."""
        self.start()
        result = self._request("tools/list", {})
        tools = result.get("tools", [])
        return tools if isinstance(tools, list) else []

    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call one MCP tool and return the raw result payload."""
        self.start()
        return self._request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments or {},
            },
        )

    def _request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send one JSON-RPC request and block for the matching response."""
        if self._process is None or self._process.stdin is None or self._process.stdout is None:
            raise RuntimeError("MCP server %s is not running" % self.config.name)

        with self._lock:
            request_id = self._next_id
            self._next_id += 1
            payload = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {},
            }
            self._process.stdin.write(json.dumps(payload, ensure_ascii=True) + "\n")
            self._process.stdin.flush()

            deadline = time.time() + self.broker_config.mcp_request_timeout
            while time.time() < deadline:
                line = self._process.stdout.readline()
                if line == "":
                    if self._process.poll() is not None:
                        raise RuntimeError(
                            "MCP server %s exited unexpectedly" % self.config.name
                        )
                    time.sleep(0.05)
                    continue

                message = json.loads(line)
                if "id" not in message:
                    continue
                if message["id"] != request_id:
                    continue
                if "error" in message:
                    raise RuntimeError(
                        "MCP error from %s: %s" % (self.config.name, message["error"])
                    )
                result = message.get("result", {})
                return result if isinstance(result, dict) else {"result": result}

            raise TimeoutError(
                "Timed out waiting for MCP response from %s for method %s"
                % (self.config.name, method)
            )

    def _notify(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Send one JSON-RPC notification."""
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("MCP server %s is not running" % self.config.name)
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }
        self._process.stdin.write(json.dumps(payload, ensure_ascii=True) + "\n")
        self._process.stdin.flush()

    def _expand_env(self, env: Dict[str, str]) -> Dict[str, str]:
        expanded: Dict[str, str] = {}
        for key, value in env.items():
            expanded[key] = value.replace(
                "${workspace_root}",
                str(self.broker_config.workspace_root),
            )
        return expanded

    def _expand_path(self, raw_path: str) -> Path:
        return Path(
            raw_path.replace(
                "${workspace_root}",
                str(self.broker_config.workspace_root),
            )
        ).resolve()


class McpRegistry:
    """Load configured MCP servers and provide lazy stdio sessions."""

    def __init__(self, broker_config: BrokerConfig) -> None:
        self.broker_config = broker_config
        self._server_configs = self._load_server_configs(broker_config.mcp_config_path)
        self._sessions: Dict[str, McpStdioSession] = {}

    def list_servers(self) -> List[Dict[str, Any]]:
        """Return configured MCP server metadata."""
        servers = []
        for name in sorted(self._server_configs.keys()):
            config = self._server_configs[name]
            servers.append(
                {
                    "name": config.name,
                    "enabled": config.enabled,
                    "transport": config.transport,
                    "command": config.command,
                    "args": config.args,
                    "description": config.description,
                    "configured": True,
                    "connected": name in self._sessions and self._sessions[name]._initialized,
                }
            )
        return servers

    def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Return tools exposed by one configured MCP server."""
        return self._get_session(server_name).list_tools()

    def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call one tool on one configured MCP server."""
        return self._get_session(server_name).call_tool(tool_name, arguments)

    def close(self) -> None:
        """Close all launched MCP sessions."""
        for session in self._sessions.values():
            session.stop()
        self._sessions.clear()

    def _get_session(self, server_name: str) -> McpStdioSession:
        if server_name not in self._server_configs:
            raise ValueError(
                "Unknown MCP server '%s'. Configure it in %s"
                % (server_name, self.broker_config.mcp_config_path)
            )
        config = self._server_configs[server_name]
        if not config.enabled:
            raise ValueError(
                "MCP server '%s' is disabled in %s"
                % (server_name, self.broker_config.mcp_config_path)
            )
        if server_name not in self._sessions:
            self._sessions[server_name] = McpStdioSession(config, self.broker_config)
        return self._sessions[server_name]

    def _load_server_configs(self, config_path: Path) -> Dict[str, McpServerConfig]:
        if not config_path.exists():
            example = config_path.parent / (config_path.stem + ".example" + config_path.suffix)
            if example.exists():
                config_path = example
            else:
                return {}

        payload = json.loads(config_path.read_text(encoding="utf-8"))
        raw_servers = payload.get("servers", payload)
        if not isinstance(raw_servers, dict):
            raise ValueError("MCP config at %s must contain a 'servers' object" % config_path)

        server_configs: Dict[str, McpServerConfig] = {}
        for name, server_payload in raw_servers.items():
            if not isinstance(server_payload, dict):
                raise ValueError("MCP server config for %s must be an object" % name)
            server_configs[name] = McpServerConfig.from_dict(name, server_payload)
        return server_configs
