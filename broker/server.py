"""HTTP entrypoint for the local BitNet broker MVP."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse

from .config import BrokerConfig
from .llama_runtime import LlamaServerRuntime
from .postprocess import postprocess_markdown, repair_required_sections
from .prompting import build_messages
from .session_store import SessionStore
from .tools import ToolRegistry, tool_result_to_evidence


DEFAULT_CHAT_PROMPT = "You are a helpful local assistant."
DEFAULT_ARTIFACT_PROMPT = "You are a precise technical writer producing grounded local artifacts."


class BrokerApp:
    """Own the broker runtime state shared across HTTP requests."""

    def __init__(self, config: BrokerConfig) -> None:
        self.config = config
        self.sessions = SessionStore()
        self.runtime = LlamaServerRuntime(config)
        self.tools = ToolRegistry(config.workspace_root)

    def build_health(self) -> Dict[str, Any]:
        """Return a combined broker + model health view."""
        try:
            model_health = self.runtime.health()
        except Exception as exc:  # noqa: BLE001
            model_health = {
                "status": "unavailable",
                "error": str(exc),
            }

        return {
            "status": "ok",
            "broker": {
                "host": self.config.broker_host,
                "port": self.config.broker_port,
                "workspace_root": str(self.config.workspace_root),
                "model_path": str(self.config.model_path),
                "tools": self.tools.list_tools(),
            },
            "llama_server": model_health,
        }

    def collect_evidence(self, body: Dict[str, Any]) -> List[Dict[str, str]]:
        """Merge explicit evidence with deterministic tool results."""
        evidence = list(body.get("evidence", []))
        for tool_call in body.get("tool_calls", []):
            tool_result = self.tools.run_tool_call(tool_call)
            evidence.append(tool_result_to_evidence(tool_result))
        return evidence

    def _resolve_system_prompt(self, body: Dict[str, Any], default: str) -> str:
        session_id = body.get("session_id")
        if body.get("system_prompt"):
            return body["system_prompt"]
        if session_id:
            session = self.sessions.get(session_id)
            if session is not None:
                return session.system_prompt
        return default

    def create_session(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create one broker session."""
        session = self.sessions.create(
            system_prompt=body.get("system_prompt", DEFAULT_CHAT_PROMPT),
            metadata=body.get("metadata", {}),
        )
        return {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "system_prompt": session.system_prompt,
            "metadata": session.metadata,
        }

    def run_tools(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deterministic tool calls without involving the model."""
        results = [self.tools.run_tool_call(call) for call in body.get("tool_calls", [])]
        return {"results": results}

    def chat(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a grounded chat request."""
        prompt = body.get("prompt", "").strip()
        if not prompt:
            raise ValueError("chat requests require a non-empty prompt")

        system_prompt = self._resolve_system_prompt(body, DEFAULT_CHAT_PROMPT)
        evidence = self.collect_evidence(body)
        messages = build_messages(
            system_prompt=system_prompt,
            user_prompt=prompt,
            evidence_items=evidence,
        )
        response = self.runtime.chat(
            messages=messages,
            max_tokens=body.get("max_tokens"),
            temperature=body.get("temperature"),
        )
        content = response["choices"][0]["message"]["content"]
        return {
            "response": content,
            "evidence": evidence,
            "raw": response,
        }

    def draft_artifact(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Draft one artifact using evidence gathered by deterministic tools."""
        artifact_id = body.get("artifact_id", "").strip()
        task = body.get("task", "").strip()
        if not artifact_id:
            raise ValueError("artifact drafts require artifact_id")
        if not task:
            raise ValueError("artifact drafts require task")

        system_prompt = self._resolve_system_prompt(body, DEFAULT_ARTIFACT_PROMPT)
        evidence = self.collect_evidence(body)
        required_sections = body.get("required_sections", [])
        prompt = "Artifact: %s\n\n%s" % (artifact_id, task)
        messages = build_messages(
            system_prompt=system_prompt,
            user_prompt=prompt,
            evidence_items=evidence,
            required_sections=required_sections,
        )
        response = self.runtime.chat(
            messages=messages,
            max_tokens=body.get("max_tokens"),
            temperature=body.get("temperature"),
        )
        cleaned, missing_before_repair = postprocess_markdown(
            response["choices"][0]["message"]["content"],
            required_sections,
        )
        repair_applied = bool(required_sections and missing_before_repair)
        repaired = (
            repair_required_sections(cleaned, required_sections, artifact_id)
            if repair_applied
            else cleaned
        )
        remaining_missing = postprocess_markdown(repaired, required_sections)[1]
        return {
            "artifact_id": artifact_id,
            "draft": repaired,
            "original_draft": cleaned,
            "repair_applied": repair_applied,
            "missing_sections": remaining_missing,
            "missing_sections_before_repair": missing_before_repair,
            "evidence": evidence,
            "raw": response,
        }


class BrokerHTTPServer(ThreadingHTTPServer):
    """Threaded HTTP server that carries the shared broker app instance."""

    def __init__(self, address: Iterable[Any], app: BrokerApp) -> None:
        super().__init__(address, BrokerRequestHandler)
        self.app = app


class BrokerRequestHandler(BaseHTTPRequestHandler):
    """Serve the MVP broker contract over localhost HTTP."""

    server_version = "BitNetBroker/0.1"

    @property
    def app(self) -> BrokerApp:
        return self.server.app  # type: ignore[attr-defined]

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(200, self.app.build_health())
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            body = self._read_json()
            if parsed.path == "/sessions":
                payload = self.app.create_session(body)
                self._send_json(201, payload)
                return
            if parsed.path == "/tools/run":
                self._send_json(200, self.app.run_tools(body))
                return
            if parsed.path == "/chat":
                self._send_json(200, self.app.chat(body))
                return
            if parsed.path == "/artifacts/draft":
                self._send_json(200, self.app.draft_artifact(body))
                return
            self._send_json(404, {"error": "not_found"})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        """Keep broker output quiet by default."""
        return

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI arguments for the broker server."""
    parser = argparse.ArgumentParser(description="Run the BitNet local broker")
    parser.add_argument("--model", type=str, help="Path to the GGUF model")
    parser.add_argument("--broker-host", type=str, default=None, help="Host for the broker")
    parser.add_argument("--broker-port", type=int, default=None, help="Port for the broker")
    parser.add_argument("--llama-host", type=str, default=None, help="Host for llama-server")
    parser.add_argument("--llama-port", type=int, default=None, help="Port for llama-server")
    parser.add_argument("--threads", type=int, default=None, help="Generation threads")
    parser.add_argument("--ctx-size", type=int, default=None, help="Model context size")
    parser.add_argument("--n-predict", type=int, default=None, help="Default max tokens")
    parser.add_argument("--temperature", type=float, default=None, help="Default temperature")
    return parser


def apply_cli_overrides(config: BrokerConfig, args: argparse.Namespace) -> BrokerConfig:
    """Overlay CLI args on top of environment-derived config."""
    if args.model:
        config.model_path = config.workspace_root.joinpath(args.model).resolve()
    if args.broker_host:
        config.broker_host = args.broker_host
    if args.broker_port is not None:
        config.broker_port = args.broker_port
    if args.llama_host:
        config.llama_host = args.llama_host
    if args.llama_port is not None:
        config.llama_port = args.llama_port
    if args.threads is not None:
        config.threads = args.threads
    if args.ctx_size is not None:
        config.ctx_size = args.ctx_size
    if args.n_predict is not None:
        config.n_predict = args.n_predict
    if args.temperature is not None:
        config.temperature = args.temperature
    return config


def main() -> None:
    """Run the broker HTTP server."""
    parser = build_arg_parser()
    args = parser.parse_args()
    config = apply_cli_overrides(BrokerConfig.from_env(), args)
    app = BrokerApp(config)

    server = BrokerHTTPServer((config.broker_host, config.broker_port), app)
    try:
        print(
            "Starting BitNet broker on http://%s:%d"
            % (config.broker_host, config.broker_port)
        )
        print(
            "Managed llama-server target is http://%s:%d"
            % (config.llama_host, config.llama_port)
        )
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.runtime.stop()
        server.server_close()


if __name__ == "__main__":
    main()
