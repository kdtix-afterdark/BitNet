"""HTTP entrypoint for the local BitNet broker MVP."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from .config import BrokerConfig
from .llama_runtime import LlamaServerRuntime
from .logging_config import BrokerLogger, standard_log_dir
from .mcp import McpRegistry
from .memory_routing import (
    collect_memory_evidence_for_profile,
    maybe_answer_from_memory_evidence,
    maybe_collect_memory_evidence,
    maybe_route_memory_prompt,
)
from .postprocess import (
    postprocess_markdown,
    repair_chat_response,
    repair_required_sections,
)
from .prompting import build_messages
from .session_store import SessionStore, load_persisted_session, persist_messages
from .tools import ToolRegistry, tool_result_to_evidence


DEFAULT_CHAT_PROMPT = "You are a helpful local assistant."
DEFAULT_ARTIFACT_PROMPT = "You are a precise technical writer producing grounded local artifacts."


class BrokerApp:
    """Own the broker runtime state shared across HTTP requests."""

    def __init__(self, config: BrokerConfig) -> None:
        self.config = config
        self._state_dir = config.workspace_root / "broker_state"
        self.sessions = SessionStore()
        self.runtime = LlamaServerRuntime(config)
        self.mcp_registry = McpRegistry(config)
        self.tools = ToolRegistry(config.workspace_root, self.mcp_registry)
        self.logger = BrokerLogger.for_component(
            "broker",
            verbose=config.verbose,
            debug_level=config.debug_level,
            log_dir=standard_log_dir(config.workspace_root, "broker"),
        )


    def build_health(self) -> Dict[str, Any]:
        """Return a combined broker + model health view."""
        self.logger.debug("Health check requested")
        try:
            model_health = self.runtime.health()
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Health check: llama-server unavailable: %s" % exc)
            model_health = {
                "status": "unavailable",
                "error": str(exc),
            }

        health = {
            "status": "ok",
            "broker": {
                "host": self.config.broker_host,
                "port": self.config.broker_port,
                "workspace_root": str(self.config.workspace_root),
                "model_path": str(self.config.model_path),
                "tools": self.tools.list_tools(),
                "mcp_servers": self.mcp_registry.list_servers(),
                "log_dir": str(
                    standard_log_dir(self.config.workspace_root, "broker")
                ),
            },
            "llama_server": model_health,
        }
        self.logger.debug(
            "Health: llama_server.status=%s" % model_health.get("status", "unknown")
        )
        return health

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
        self.logger.debug("run_tools: %d tool(s) executed" % len(results))
        return {"results": results}

    def chat(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a grounded chat request."""
        prompt = body.get("prompt", "").strip()
        if not prompt:
            raise ValueError("chat requests require a non-empty prompt")
        session_id = self._normalize_session_id(body.get("session_id"))
        profile = body.get("profile")
        include_tool_manifest = bool(body.get("include_tool_manifest", True))
        broker_controls_tools = bool(body.get("broker_controls_tools", False))
        memory_query = body.get("memory_query")

        self.logger.info(
            "Chat request: session=%s profile=%s prompt_len=%d"
            % (session_id or "anon", profile or "default", len(prompt))
        )
        self.logger.trace("Chat prompt: %s" % prompt)

        # Restore session from disk if the broker was restarted or session is unknown.
        if session_id and self.sessions.get(session_id) is None:
            persisted = load_persisted_session(self._state_dir, session_id)
            if persisted is not None:
                loaded_messages, loaded_system_prompt = persisted
                self.sessions.restore(
                    session_id=session_id,
                    messages=loaded_messages,
                    system_prompt=loaded_system_prompt or DEFAULT_CHAT_PROMPT,
                )
                self.logger.info(
                    "Session %s restored from disk (%d prior turns)"
                    % (session_id, sum(1 for m in loaded_messages if m.get("role") == "assistant"))
                )
            else:
                # No persisted state found — seed a fresh in-memory entry so
                # turns accumulate and are persisted on the first response.
                # We reuse `restore()` here because it accepts an explicit
                # session_id, whereas `create()` generates a random UUID.
                self.sessions.restore(
                    session_id=session_id,
                    messages=[],
                    system_prompt=self._resolve_system_prompt(body, DEFAULT_CHAT_PROMPT),
                )
                self.logger.debug("Session %s: new session initialised" % session_id)

        memory_route = maybe_route_memory_prompt(prompt, self.mcp_registry)
        if memory_route is not None and memory_route.handled:
            self.logger.info(
                "Memory route handled: reason=%s ops=%d"
                % (memory_route.route_reason, len(memory_route.operations or []))
            )
            self._append_session_turn(session_id, prompt, memory_route.response or "")
            return {
                "response": memory_route.response,
                "original_response": None,
                "repair_applied": False,
                "repair_reason": None,
                "route_applied": True,
                "route_reason": memory_route.route_reason,
                "route_operations": memory_route.operations or [],
                "model_invoked": False,
                "memory_evidence_applied": bool(memory_route.evidence),
                "memory_evidence_reason": memory_route.route_reason,
                "evidence": memory_route.evidence or [],
                "raw": None,
            }

        system_prompt = self._resolve_system_prompt(body, DEFAULT_CHAT_PROMPT)
        evidence = self.collect_evidence(body)
        memory_evidence_result = maybe_collect_memory_evidence(
            prompt,
            self.mcp_registry,
            explicit_query=memory_query if isinstance(memory_query, str) else None,
        )
        # If no memory evidence from the standard path and the profile requests
        # memory-first behaviour, try again using the prompt as the query.
        if memory_evidence_result is None:
            memory_evidence_result = collect_memory_evidence_for_profile(
                prompt=prompt,
                profile=profile if isinstance(profile, str) else None,
                mcp_registry=self.mcp_registry,
                explicit_query=memory_query if isinstance(memory_query, str) else None,
            )
        memory_evidence = (
            list(memory_evidence_result.evidence or [])
            if memory_evidence_result is not None
            else []
        )
        route_operations = (
            list(memory_evidence_result.operations or [])
            if memory_evidence_result is not None
            else []
        )
        if memory_evidence:
            evidence = memory_evidence + evidence

        if broker_controls_tools and route_operations:
            broker_control_result = maybe_answer_from_memory_evidence(
                prompt,
                route_operations,
            )
            if broker_control_result is not None and broker_control_result.handled:
                return {
                    "response": broker_control_result.response,
                    "original_response": None,
                    "repair_applied": False,
                    "repair_reason": None,
                    "route_applied": True,
                    "route_reason": broker_control_result.route_reason,
                    "route_operations": broker_control_result.operations or route_operations,
                    "model_invoked": False,
                    "memory_evidence_applied": bool(memory_evidence),
                    "memory_evidence_reason": (
                        memory_evidence_result.route_reason
                        if memory_evidence_result is not None and memory_evidence
                        else None
                    ),
                    "include_tool_manifest": include_tool_manifest,
                    "broker_controls_tools": broker_controls_tools,
                    "evidence": broker_control_result.evidence or memory_evidence,
                    "raw": None,
                }

        conversation_history: List[Dict[str, str]] = []
        if session_id:
            session = self.sessions.get(session_id)
            if session is not None:
                conversation_history = list(session.messages)

        self.logger.debug(
            "Building messages: history_turns=%d evidence=%d"
            % (len(conversation_history) // 2, len(evidence))
        )
        if self.logger.is_enabled_for_trace():
            self.logger.trace("Conversation history: %s" % json.dumps(conversation_history))

        messages = build_messages(
            system_prompt=system_prompt,
            user_prompt=prompt,
            evidence_items=evidence,
            conversation_history=conversation_history,
            tool_manifest=self.tools.tool_manifest() if include_tool_manifest else [],
            broker_controls_tools=broker_controls_tools,
            grounded_user_prompt=bool(evidence),
        )
        self.logger.debug("Invoking llama-server: messages=%d" % len(messages))
        response = self.runtime.chat(
            messages=messages,
            max_tokens=body.get("max_tokens"),
            temperature=body.get("temperature"),
        )
        content = response["choices"][0]["message"]["content"]
        repaired_content, repair_applied, repair_reason = repair_chat_response(
            prompt=prompt,
            text=content,
            evidence_items=evidence,
        )
        self.logger.info(
            "Chat complete: session=%s repair=%s response_len=%d"
            % (session_id or "anon", repair_applied, len(repaired_content))
        )
        self.logger.trace("Chat response: %s" % repaired_content[:500])
        self._append_session_turn(session_id, prompt, repaired_content)
        return {
            "response": repaired_content,
            "original_response": content,
            "repair_applied": repair_applied,
            "repair_reason": repair_reason,
            "route_applied": False,
            "route_reason": None,
            "route_operations": route_operations,
            "model_invoked": True,
            "memory_evidence_applied": bool(memory_evidence),
            "memory_evidence_reason": (
                memory_evidence_result.route_reason
                if memory_evidence_result is not None and memory_evidence
                else None
            ),
            "include_tool_manifest": include_tool_manifest,
            "broker_controls_tools": broker_controls_tools,
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
            tool_manifest=[],
            broker_controls_tools=False,
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

    def _normalize_session_id(self, session_id: Any) -> Optional[str]:
        """Return a clean session_id string or None if not provided."""
        if not isinstance(session_id, str) or not session_id.strip():
            return None
        return session_id.strip()

    def _append_session_turn(
        self,
        session_id: Optional[str],
        user_prompt: str,
        assistant_response: str,
    ) -> None:
        """Append user and assistant turns to the session message history and persist to disk."""
        if not session_id:
            return
        if not assistant_response.strip():
            return
        try:
            self.sessions.append_message(session_id, "user", user_prompt)
            self.sessions.append_message(session_id, "assistant", assistant_response)
        except ValueError:
            pass
        # Persist to disk so turns survive a broker restart.
        session = self.sessions.get(session_id)
        if session is not None:
            try:
                persist_messages(
                    self._state_dir,
                    session_id,
                    list(session.messages),
                    system_prompt=session.system_prompt,
                )
            except OSError:
                pass

    def close(self) -> None:
        """Release broker-managed resources."""
        self.tools.close()


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
            self.app.logger.error("Bad request [%s]: %s" % (parsed.path, exc))
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self.app.logger.error("Internal error [%s]: %s" % (parsed.path, exc))
            self._send_json(500, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        """Route HTTP access log through BrokerLogger instead of stderr."""
        self.app.logger.debug("HTTP %s" % (format % args))

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
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
    parser.add_argument("--n-keep", type=int, default=None, help="Tokens to keep on context shift (-1 = all)")
    parser.add_argument("--temperature", type=float, default=None, help="Default temperature")
    parser.add_argument("--top-p", type=float, default=None, help="Top-p nucleus sampling threshold")
    parser.add_argument("--gpu-layers", type=int, default=None, help="GPU layers to offload (0 = CPU-only, 999 = all)")
    parser.add_argument("--batch-size", type=int, default=None, help="Logical batch size for llama-server (-b). Defaults to 31 for i2_s models (BLAS crash safeguard).")
    parser.add_argument("--ubatch-size", type=int, default=None, help="Physical micro-batch size for llama-server (-ub). Defaults to 31 for i2_s models (BLAS crash safeguard).")
    parser.add_argument(
        "--verbose", type=int, default=None, choices=[0, 1, 2, 3],
        metavar="LEVEL",
        help="Console and log verbosity: 0=error, 1=info (default), 2=debug, 3=trace. "
             "Also settable via BITNET_BROKER_VERBOSE.",
    )
    parser.add_argument(
        "--debug", type=int, default=None, choices=[0, 1, 2, 3],
        metavar="LEVEL",
        dest="debug_level",
        help="Debug instrumentation depth: 0=off (default) … 3=deep trace. "
             "Also settable via BITNET_BROKER_DEBUG.",
    )
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
    if args.n_keep is not None:
        config.n_keep = args.n_keep
    if args.temperature is not None:
        config.temperature = args.temperature
    if args.top_p is not None:
        config.top_p = args.top_p
    if args.gpu_layers is not None:
        config.gpu_layers = args.gpu_layers
    if args.batch_size is not None:
        config.batch_size = args.batch_size
    if args.ubatch_size is not None:
        config.ubatch_size = args.ubatch_size
    if getattr(args, "verbose", None) is not None:
        config.verbose = max(0, min(3, args.verbose))
    if getattr(args, "debug_level", None) is not None:
        config.debug_level = max(0, min(3, args.debug_level))
    return config


def main() -> None:
    """Run the broker HTTP server."""
    parser = build_arg_parser()
    args = parser.parse_args()
    config = apply_cli_overrides(BrokerConfig.from_env(), args)
    app = BrokerApp(config)

    log_dir = standard_log_dir(config.workspace_root, "broker")
    latest_log = log_dir / "broker-latest.log"
    app.logger.info(
        "Broker starting: verbose=%d debug=%d log=%s"
        % (config.verbose, config.debug_level, latest_log)
    )
    app.logger.info(
        "Listening on http://%s:%d" % (config.broker_host, config.broker_port)
    )
    app.logger.info(
        "llama-server target: http://%s:%d" % (config.llama_host, config.llama_port)
    )
    app.logger.debug("model_path=%s" % config.model_path)
    app.logger.debug("state_dir=%s" % app._state_dir)

    print(
        "Starting BitNet broker on http://%s:%d" % (config.broker_host, config.broker_port)
    )
    print("Logs: %s" % latest_log)

    server = BrokerHTTPServer((config.broker_host, config.broker_port), app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        app.logger.info("Broker shutting down")

    finally:
        app.close()
        app.runtime.stop()
        server.server_close()


if __name__ == "__main__":
    main()
