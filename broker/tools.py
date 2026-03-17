"""Deterministic local evidence tools for the broker MVP."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List

from .mcp import McpRegistry


class ToolRegistry:
    """Safe deterministic tools exposed by the broker MVP."""

    def __init__(self, workspace_root: Path, mcp_registry: McpRegistry | None = None) -> None:
        self.workspace_root = workspace_root.resolve()
        self.mcp_registry = mcp_registry
        self._tools: Dict[str, Callable[..., Any]] = {
            "list_directory": self.list_directory,
            "read_text_file": self.read_text_file,
            "search_text": self.search_text,
            "mcp_list_servers": self.mcp_list_servers,
            "mcp_list_server_tools": self.mcp_list_server_tools,
            "mcp_call_tool": self.mcp_call_tool,
            "mcp_memory_call": self.mcp_memory_call,
            "mcp_sequential_thinking": self.mcp_sequential_thinking,
            "mcp_context7_call": self.mcp_context7_call,
        }

    def list_tools(self) -> List[str]:
        """Return the supported tool names."""
        return sorted(self._tools.keys())

    def run_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one registered tool call."""
        tool_name = tool_call.get("tool")
        if tool_name not in self._tools:
            raise ValueError("Unsupported tool: %s" % tool_name)

        args = tool_call.get("args", {})
        result = self._tools[tool_name](**args)
        return {
            "tool": tool_name,
            "args": args,
            "result": result,
        }

    def _resolve_path(self, raw_path: str) -> Path:
        candidate = (self.workspace_root / raw_path).resolve()
        if self.workspace_root not in candidate.parents and candidate != self.workspace_root:
            raise ValueError("Path escapes workspace root: %s" % raw_path)
        return candidate

    def list_directory(self, path: str = ".", max_entries: int = 200) -> Dict[str, Any]:
        """List files under a workspace-relative directory."""
        target = self._resolve_path(path)
        if not target.is_dir():
            raise ValueError("Not a directory: %s" % path)

        entries = []
        for child in sorted(target.iterdir(), key=lambda item: item.name)[:max_entries]:
            entries.append(
                {
                    "name": child.name,
                    "path": str(child.relative_to(self.workspace_root)),
                    "is_dir": child.is_dir(),
                }
            )

        return {
            "path": str(target.relative_to(self.workspace_root)),
            "entries": entries,
        }

    def read_text_file(self, path: str, max_chars: int = 4000) -> Dict[str, Any]:
        """Read a UTF-8 text file from the workspace."""
        target = self._resolve_path(path)
        if not target.is_file():
            raise ValueError("Not a file: %s" % path)

        content = target.read_text(encoding="utf-8", errors="replace")
        return {
            "path": str(target.relative_to(self.workspace_root)),
            "content": content[:max_chars],
            "truncated": len(content) > max_chars,
        }

    def search_text(
        self,
        pattern: str,
        path: str = ".",
        glob: str = "",
        max_matches: int = 50,
    ) -> Dict[str, Any]:
        """Search text within the workspace using ripgrep if available."""
        target = self._resolve_path(path)
        if not target.exists():
            raise ValueError("Search path does not exist: %s" % path)

        if shutil.which("rg"):
            command = ["rg", "-n", "--hidden", "--no-heading"]
            if glob:
                command.extend(["--glob", glob])
            command.extend([pattern, str(target)])
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                cwd=str(self.workspace_root),
            )
            if result.returncode not in (0, 1):
                raise RuntimeError(result.stderr.strip() or "ripgrep failed")

            lines = [line for line in result.stdout.splitlines() if line.strip()]
            matches = []
            for line in lines[:max_matches]:
                parts = line.split(":", 2)
                if len(parts) != 3:
                    continue
                match_path = Path(parts[0]).resolve()
                rel_path = match_path.relative_to(self.workspace_root)
                matches.append(
                    {
                        "path": str(rel_path),
                        "line": int(parts[1]),
                        "text": parts[2],
                    }
                )

            return {
                "pattern": pattern,
                "path": str(target.relative_to(self.workspace_root)),
                "matches": matches,
                "truncated": len(lines) > max_matches,
            }

        raise RuntimeError("ripgrep is required for search_text in this MVP")

    def mcp_list_servers(self) -> Dict[str, Any]:
        """List configured MCP servers known to the broker."""
        if self.mcp_registry is None:
            return {"servers": []}
        return {"servers": self.mcp_registry.list_servers()}

    def mcp_list_server_tools(self, server: str) -> Dict[str, Any]:
        """List tools exposed by one configured MCP server."""
        if self.mcp_registry is None:
            raise ValueError("MCP registry is not configured")
        return {
            "server": server,
            "tools": self.mcp_registry.list_tools(server),
        }

    def mcp_call_tool(
        self,
        server: str,
        tool: str,
        arguments: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Call one tool on one configured MCP server."""
        if self.mcp_registry is None:
            raise ValueError("MCP registry is not configured")
        return {
            "server": server,
            "tool": tool,
            "result": self.mcp_registry.call_tool(server, tool, arguments),
        }

    def mcp_memory_call(
        self,
        tool: str,
        arguments: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Convenience wrapper for the configured Memory MCP server."""
        return self.mcp_call_tool("memory", tool, arguments)

    def mcp_sequential_thinking(
        self,
        arguments: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Convenience wrapper for the Sequential Thinking MCP tool."""
        return self.mcp_call_tool("sequential-thinking", "sequentialthinking", arguments)

    def mcp_context7_call(
        self,
        tool: str,
        arguments: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Convenience wrapper for the configured Context7 MCP server."""
        return self.mcp_call_tool("context7", tool, arguments)

    def close(self) -> None:
        """Close any launched MCP sessions."""
        if self.mcp_registry is not None:
            self.mcp_registry.close()


def tool_result_to_evidence(tool_result: Dict[str, Any]) -> Dict[str, str]:
    """Convert one tool result into a prompt-ready evidence item."""
    return {
        "source": "tool:%s" % tool_result["tool"],
        "kind": "tool-result",
        "content": json.dumps(tool_result["result"], indent=2, ensure_ascii=True),
    }
