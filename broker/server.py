"""HTTP entrypoint for the local BitNet broker MVP."""

from __future__ import annotations

import argparse
import json
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse
from uuid import uuid4

from .config import BrokerConfig, broker_env_help_text
from .durable_state import BrokerStateManager, PendingSyncItem
from .llama_runtime import LlamaServerRuntime
from .mcp import McpRegistry
from .memory_routing import (
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
from .runtime_log import BrokerLogger
from .session_store import SessionStore
from .system_prompts import SystemPromptLoader
from .tools import ToolRegistry, tool_result_to_evidence
from .turn_trace import TurnTraceRecorder


DEFAULT_ARTIFACT_PROMPT = "You are a precise technical writer producing grounded local artifacts."


class BrokerApp:
    """Own the broker runtime state shared across HTTP requests."""

    def __init__(self, config: BrokerConfig) -> None:
        self.config = config
        self.logger = BrokerLogger(config.log_dir, config.log_level, config.verbose)
        self.logger.start()
        self.state = BrokerStateManager(config)
        recovery = self.state.startup()
        self.sessions = SessionStore()
        self.system_prompts = SystemPromptLoader(
            workspace_root=config.workspace_root,
            prompts_dir=config.system_prompts_dir,
            default_prompt_path=config.system_prompt_path,
        )
        self.turn_traces = TurnTraceRecorder(config.trace_dir, config.trace_turns)
        for session in recovery.sessions:
            self.sessions.restore(session)
        self.runtime = LlamaServerRuntime(config)
        self.mcp_registry = McpRegistry(config)
        self.tools = ToolRegistry(config.workspace_root, self.mcp_registry)
        self._recovery_report = recovery.report
        self._memory_sync_stop = threading.Event()
        self._memory_sync_thread: threading.Thread | None = None
        self.state.start_heartbeat()
        self._start_memory_sync_worker()
        self.logger.info(
            "Broker initialized",
            broker_host=self.config.broker_host,
            broker_port=self.config.broker_port,
            llama_port=self.config.llama_port,
            recovered_sessions=len(recovery.sessions),
            dirty_recovery=recovery.report.get("dirty_recovery", False),
        )

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
                "llama_build_dir": str(self.config.llama_build_dir),
                "llama_server_path": str(self.config.llama_server_path),
                "system_prompts_dir": str(self.config.system_prompts_dir),
                "system_prompt_path": str(self.config.system_prompt_path),
                "gpu_layers": self.config.gpu_layers,
                "threads": self.config.threads,
                "ctx_size": self.config.ctx_size,
                "n_predict": self.config.n_predict,
                "n_keep": self.config.n_keep,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "tools": self.tools.list_tools(),
                "mcp_servers": self.mcp_registry.list_servers(),
                "durable_state": self.state.build_health(),
                "trace_turns": self.config.trace_turns,
                "trace_dir": str(self.config.trace_dir),
            },
            "llama_server": model_health,
        }

    def collect_evidence(self, body: Dict[str, Any]) -> List[Dict[str, str]]:
        """Merge explicit evidence with deterministic tool results."""
        session_id = self._normalize_session_id(body.get("session_id"))
        correlation_id = body.get("_correlation_id")
        evidence = list(body.get("evidence", []))
        for tool_call in body.get("tool_calls", []):
            tool_result = self._execute_tool_call(
                tool_call,
                session_id=session_id,
                correlation_id=correlation_id if isinstance(correlation_id, str) else None,
            )
            evidence.append(tool_result_to_evidence(tool_result))
        return evidence

    def _resolve_prompt_override(self, body: Dict[str, Any]) -> str | None:
        inline_prompt = body.get("system_prompt")
        prompt_path = body.get("system_prompt_path")
        if isinstance(inline_prompt, str) and inline_prompt.strip():
            return self.system_prompts.resolve(inline_prompt=inline_prompt).content
        if isinstance(prompt_path, str) and prompt_path.strip():
            return self.system_prompts.resolve(prompt_path=prompt_path).content
        return None

    def _resolve_system_prompt(self, body: Dict[str, Any], default: str | None = None) -> str:
        override = self._resolve_prompt_override(body)
        if override is not None:
            return override
        session_id = body.get("session_id")
        if session_id:
            session = self.sessions.get(session_id)
            if session is not None:
                return session.system_prompt
        if default is not None:
            return default
        return self.system_prompts.resolve().content

    def _resolve_session_prompt(self, body: Dict[str, Any]) -> str:
        override = self._resolve_prompt_override(body)
        if override is not None:
            return override
        return self.system_prompts.resolve().content

    def create_session(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create one broker session."""
        session = self.sessions.create(
            system_prompt=self._resolve_session_prompt(body),
            metadata=body.get("metadata", {}),
        )
        self.state.record_session_open(
            session_id=session.session_id,
            system_prompt=session.system_prompt,
            metadata=session.metadata,
            created_at=session.created_at,
        )
        return {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "system_prompt": session.system_prompt,
            "metadata": session.metadata,
            "message_count": len(session.messages),
        }

    def _trace_turn(
        self,
        *,
        correlation_id: str,
        session_id: str | None,
        phase: str,
        payload: Dict[str, Any],
    ) -> None:
        self.turn_traces.record(
            correlation_id=correlation_id,
            session_id=session_id,
            phase=phase,
            payload=payload,
        )

    def run_tools(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deterministic tool calls without involving the model."""
        session_id = self._normalize_session_id(body.get("session_id"))
        correlation_id = str(uuid4())
        results = [
            self._execute_tool_call(call, session_id=session_id, correlation_id=correlation_id)
            for call in body.get("tool_calls", [])
        ]
        self.logger.debug(
            "Tool run completed",
            correlation_id=correlation_id,
            session_id=session_id,
            tool_count=len(results),
        )
        return {"results": results, "correlation_id": correlation_id}

    def chat(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a grounded chat request."""
        prompt = body.get("prompt", "").strip()
        if not prompt:
            raise ValueError("chat requests require a non-empty prompt")
        session_id = self._normalize_session_id(body.get("session_id"))
        correlation_id = str(uuid4())
        include_tool_manifest = bool(body.get("include_tool_manifest", True))
        broker_controls_tools = bool(body.get("broker_controls_tools", False))
        memory_query = body.get("memory_query")
        body["_correlation_id"] = correlation_id
        self.state.record_turn_started(
            session_id=session_id,
            correlation_id=correlation_id,
            prompt=prompt,
            payload={
                "include_tool_manifest": include_tool_manifest,
                "broker_controls_tools": broker_controls_tools,
                "memory_query": memory_query,
            },
        )
        self.logger.debug(
            "Chat turn started",
            correlation_id=correlation_id,
            session_id=session_id,
            prompt=prompt if self.config.verbose >= 3 else prompt[:120],
        )
        self._trace_turn(
            correlation_id=correlation_id,
            session_id=session_id,
            phase="turn_started",
            payload={
                "prompt": prompt,
                "include_tool_manifest": include_tool_manifest,
                "broker_controls_tools": broker_controls_tools,
                "memory_query": memory_query,
            },
        )

        try:
            memory_route = maybe_route_memory_prompt(prompt, self.mcp_registry)
            if memory_route is not None and memory_route.handled:
                persisted = self._append_session_turn(
                    session_id,
                    prompt,
                    memory_route.response,
                )
                self._trace_turn(
                    correlation_id=correlation_id,
                    session_id=session_id,
                    phase="route_handled",
                    payload={
                        "route_reason": memory_route.route_reason,
                        "response": memory_route.response,
                        "operations": memory_route.operations or [],
                        "evidence": memory_route.evidence or [],
                        "model_invoked": False,
                    },
                )
                if persisted is not None:
                    self._trace_turn(
                        correlation_id=correlation_id,
                        session_id=session_id,
                        phase="session_persisted",
                        payload=persisted,
                    )
                self.state.record_turn_completed(
                    session_id=session_id,
                    correlation_id=correlation_id,
                    user_prompt=prompt,
                    assistant_response=memory_route.response or "",
                    payload={
                        "model_invoked": False,
                        "route_applied": True,
                        "route_reason": memory_route.route_reason,
                        "route_operation_count": len(memory_route.operations or []),
                    },
                )
                self.logger.info(
                    "Chat turn completed",
                    correlation_id=correlation_id,
                    session_id=session_id,
                    model_invoked=False,
                    route_reason=memory_route.route_reason,
                )
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
                    "correlation_id": correlation_id,
                }

            system_prompt = self._resolve_system_prompt(body)
            evidence = self.collect_evidence(body)
            memory_evidence_result = maybe_collect_memory_evidence(
                prompt,
                self.mcp_registry,
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
                    persisted = self._append_session_turn(
                        session_id,
                        prompt,
                        broker_control_result.response,
                    )
                    self._trace_turn(
                        correlation_id=correlation_id,
                        session_id=session_id,
                        phase="route_handled",
                        payload={
                            "route_reason": broker_control_result.route_reason,
                            "response": broker_control_result.response,
                            "operations": broker_control_result.operations or route_operations,
                            "evidence": broker_control_result.evidence or memory_evidence,
                            "model_invoked": False,
                        },
                    )
                    if persisted is not None:
                        self._trace_turn(
                            correlation_id=correlation_id,
                            session_id=session_id,
                            phase="session_persisted",
                            payload=persisted,
                        )
                    self.state.record_turn_completed(
                        session_id=session_id,
                        correlation_id=correlation_id,
                        user_prompt=prompt,
                        assistant_response=broker_control_result.response or "",
                        payload={
                            "model_invoked": False,
                            "route_applied": True,
                            "route_reason": broker_control_result.route_reason,
                            "route_operation_count": len(
                                broker_control_result.operations or route_operations
                            ),
                            "memory_evidence_reason": (
                                memory_evidence_result.route_reason
                                if memory_evidence_result is not None and memory_evidence
                                else None
                            ),
                        },
                    )
                    self.logger.info(
                        "Chat turn completed",
                        correlation_id=correlation_id,
                        session_id=session_id,
                        model_invoked=False,
                        route_reason=broker_control_result.route_reason,
                    )
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
                        "correlation_id": correlation_id,
                    }

            session = None
            conversation_history = []
            conversation_summary = ""
            summarized_turn_count = 0
            if session_id:
                session = self.sessions.get(session_id)
                if session is None:
                    raise ValueError("unknown session_id: %s" % session_id)
                conversation_history = list(session.messages)
                conversation_summary = session.summary
                summarized_turn_count = session.summarized_turn_count

            messages = build_messages(
                system_prompt=system_prompt,
                user_prompt=prompt,
                evidence_items=evidence,
                conversation_history=conversation_history,
                conversation_summary=conversation_summary,
                summarized_turn_count=summarized_turn_count,
                tool_manifest=self.tools.tool_manifest() if include_tool_manifest else [],
                broker_controls_tools=broker_controls_tools,
                grounded_user_prompt=bool(evidence),
            )
            self._trace_turn(
                correlation_id=correlation_id,
                session_id=session_id,
                phase="prompt_built",
                payload={
                    "system_prompt": system_prompt,
                    "evidence_items": evidence,
                    "conversation_history_count": len(conversation_history),
                    "conversation_history": conversation_history,
                    "conversation_summary": conversation_summary,
                    "summarized_turn_count": summarized_turn_count,
                    "messages": messages,
                },
            )
            request_payload = self.runtime.build_chat_payload(
                messages=messages,
                max_tokens=body.get("max_tokens"),
                temperature=body.get("temperature"),
                top_p=body.get("top_p"),
            )
            self._trace_turn(
                correlation_id=correlation_id,
                session_id=session_id,
                phase="llama_request_built",
                payload=request_payload,
            )
            response = self.runtime.chat_payload(request_payload)
            content = response["choices"][0]["message"]["content"]
            self._trace_turn(
                correlation_id=correlation_id,
                session_id=session_id,
                phase="llama_response_received",
                payload={
                    "raw_response": response,
                    "raw_content": content,
                },
            )
            repaired_content, repair_applied, repair_reason = repair_chat_response(
                prompt=prompt,
                text=content,
                evidence_items=evidence,
                conversation_history=conversation_history,
            )
            self._trace_turn(
                correlation_id=correlation_id,
                session_id=session_id,
                phase="repair_completed",
                payload={
                    "repair_applied": repair_applied,
                    "repair_reason": repair_reason,
                    "pre_repair_content": content,
                    "post_repair_content": repaired_content,
                },
            )
            persisted = self._append_session_turn(session_id, prompt, repaired_content)
            if persisted is not None:
                self._trace_turn(
                    correlation_id=correlation_id,
                    session_id=session_id,
                    phase="session_persisted",
                    payload=persisted,
                )
            self.state.record_turn_completed(
                session_id=session_id,
                correlation_id=correlation_id,
                user_prompt=prompt,
                assistant_response=repaired_content,
                payload={
                    "model_invoked": True,
                    "repair_applied": repair_applied,
                    "repair_reason": repair_reason,
                    "route_operation_count": len(route_operations),
                    "memory_evidence_reason": (
                        memory_evidence_result.route_reason
                        if memory_evidence_result is not None and memory_evidence
                        else None
                    ),
                },
            )
            self.logger.info(
                "Chat turn completed",
                correlation_id=correlation_id,
                session_id=session_id,
                model_invoked=True,
                repair_applied=repair_applied,
            )
            self._trace_turn(
                correlation_id=correlation_id,
                session_id=session_id,
                phase="turn_completed",
                payload={
                    "final_response": repaired_content,
                    "repair_applied": repair_applied,
                    "repair_reason": repair_reason,
                    "model_invoked": True,
                },
            )
            self._queue_turn_memory_sync(
                session_id=session_id,
                correlation_id=correlation_id,
                user_prompt=prompt,
                assistant_response=repaired_content,
                model_invoked=True,
                route_reason=None,
            )
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
                "correlation_id": correlation_id,
            }
        except Exception as exc:  # noqa: BLE001
            self.state.record_turn_failed(
                session_id=session_id,
                correlation_id=correlation_id,
                prompt=prompt,
                error=str(exc),
            )
            self._trace_turn(
                correlation_id=correlation_id,
                session_id=session_id,
                phase="turn_failed",
                payload={
                    "error": str(exc),
                },
            )
            self.logger.error(
                "Chat turn failed",
                correlation_id=correlation_id,
                session_id=session_id,
                error=str(exc),
            )
            raise

    def draft_artifact(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Draft one artifact using evidence gathered by deterministic tools."""
        artifact_id = body.get("artifact_id", "").strip()
        task = body.get("task", "").strip()
        if not artifact_id:
            raise ValueError("artifact drafts require artifact_id")
        if not task:
            raise ValueError("artifact drafts require task")
        correlation_id = str(uuid4())
        self.state.record_turn_started(
            session_id=None,
            correlation_id=correlation_id,
            prompt="Artifact: %s\n\n%s" % (artifact_id, task),
            payload={"artifact_id": artifact_id, "artifact_draft": True},
        )
        self.logger.debug(
            "Artifact draft started",
            artifact_id=artifact_id,
            correlation_id=correlation_id,
        )

        try:
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
                top_p=body.get("top_p"),
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
            self.state.record_turn_completed(
                session_id=None,
                correlation_id=correlation_id,
                user_prompt="Artifact: %s\n\n%s" % (artifact_id, task),
                assistant_response=repaired,
                payload={
                    "artifact_id": artifact_id,
                    "artifact_draft": True,
                    "repair_applied": repair_applied,
                    "missing_sections_before_repair": missing_before_repair,
                    "missing_sections_after_repair": remaining_missing,
                    "model_invoked": True,
                },
            )
            self.logger.info(
                "Artifact draft completed",
                artifact_id=artifact_id,
                correlation_id=correlation_id,
                repair_applied=repair_applied,
            )
            self._queue_artifact_memory_sync(
                artifact_id=artifact_id,
                task=task,
                draft=repaired,
                correlation_id=correlation_id,
            )
            return {
                "artifact_id": artifact_id,
                "draft": repaired,
                "original_draft": cleaned,
                "repair_applied": repair_applied,
                "missing_sections": remaining_missing,
                "missing_sections_before_repair": missing_before_repair,
                "evidence": evidence,
                "raw": response,
                "correlation_id": correlation_id,
            }
        except Exception as exc:  # noqa: BLE001
            self.state.record_turn_failed(
                session_id=None,
                correlation_id=correlation_id,
                prompt="Artifact: %s\n\n%s" % (artifact_id, task),
                error=str(exc),
            )
            self.logger.error(
                "Artifact draft failed",
                artifact_id=artifact_id,
                correlation_id=correlation_id,
                error=str(exc),
            )
            raise

    def close(self) -> None:
        """Release broker-managed resources."""
        self._stop_memory_sync_worker()
        self.state.stop_heartbeat()
        self._flush_memory_sync(timeout_seconds=10)
        self.state.shutdown_clean()
        self.logger.info("Broker shutdown clean")
        self.tools.close()
        self.mcp_registry.close()
        self.logger.close()

    def _append_session_turn(
        self,
        session_id: Any,
        user_prompt: str,
        assistant_response: Any,
    ) -> Dict[str, Any] | None:
        session_id_str = self._normalize_session_id(session_id)
        if not session_id_str:
            return None
        if not isinstance(assistant_response, str) or not assistant_response.strip():
            return None
        self.sessions.append_message(session_id_str, "user", user_prompt)
        self.sessions.append_message(session_id_str, "assistant", assistant_response)
        session = self.sessions.get(session_id_str)
        if session is None:
            return None
        return {
            "message_count": len(session.messages),
            "turn_count": session.turn_count,
            "updated_at": session.updated_at,
            "summary": session.summary,
            "summarized_turn_count": session.summarized_turn_count,
            "last_messages": session.messages[-4:],
        }

    def get_recovery_report(self) -> Dict[str, Any]:
        """Return the current persisted recovery summary."""
        return self.state.get_last_recovery_report()

    def _normalize_session_id(self, session_id: Any) -> str | None:
        if not isinstance(session_id, str) or not session_id.strip():
            return None
        return session_id.strip()

    def _execute_tool_call(
        self,
        tool_call: Dict[str, Any],
        session_id: str | None,
        correlation_id: str | None,
    ) -> Dict[str, Any]:
        result = self.tools.run_tool_call(tool_call)
        self.state.record_tool_called(
            tool_name=result.get("tool", ""),
            arguments=result.get("args", {}),
            result=result.get("result", {}),
            session_id=session_id,
            correlation_id=correlation_id,
        )
        self.logger.debug(
            "Tool called",
            tool_name=result.get("tool", ""),
            session_id=session_id,
            correlation_id=correlation_id,
        )
        return result

    def _start_memory_sync_worker(self) -> None:
        if not self.config.memory_sync_enabled or not self.mcp_registry.has_server("memory"):
            return
        self._memory_sync_stop.clear()
        self._memory_sync_thread = threading.Thread(
            target=self._memory_sync_loop,
            name="broker-memory-sync",
            daemon=True,
        )
        self._memory_sync_thread.start()
        self.logger.debug("Memory sync worker started")

    def _stop_memory_sync_worker(self) -> None:
        self._memory_sync_stop.set()
        if self._memory_sync_thread is not None:
            self._memory_sync_thread.join(timeout=2)
            self._memory_sync_thread = None
        self.logger.debug("Memory sync worker stopped")

    def _memory_sync_loop(self) -> None:
        while not self._memory_sync_stop.is_set():
            item = self.state.get_ready_sync_item()
            if item is None:
                self._memory_sync_stop.wait(1)
                continue
            claimed = self.state.record_memory_sync_attempt(item.item_id)
            if claimed is None:
                continue
            try:
                detail = self._sync_item_to_memory(claimed)
                self.state.record_memory_sync_completed(claimed.item_id, detail=detail)
                self.logger.debug(
                    "Memory sync completed",
                    item_id=claimed.item_id,
                    session_id=claimed.session_id,
                )
            except Exception as exc:  # noqa: BLE001
                self.state.record_memory_sync_failed(claimed.item_id, str(exc))
                self.logger.error(
                    "Memory sync failed",
                    item_id=claimed.item_id,
                    session_id=claimed.session_id,
                    error=str(exc),
                )

    def _flush_memory_sync(self, timeout_seconds: int) -> None:
        if not self.config.memory_sync_enabled or not self.mcp_registry.has_server("memory"):
            return
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            item = self.state.get_ready_sync_item()
            if item is None:
                return
            claimed = self.state.record_memory_sync_attempt(item.item_id)
            if claimed is None:
                continue
            try:
                detail = self._sync_item_to_memory(claimed)
                self.state.record_memory_sync_completed(claimed.item_id, detail=detail)
                self.logger.debug(
                    "Memory sync flushed",
                    item_id=claimed.item_id,
                    session_id=claimed.session_id,
                )
            except Exception as exc:  # noqa: BLE001
                self.state.record_memory_sync_failed(claimed.item_id, str(exc))
                self.logger.error(
                    "Memory sync flush failed",
                    item_id=claimed.item_id,
                    session_id=claimed.session_id,
                    error=str(exc),
                )
                return

    def _sync_item_to_memory(self, item: PendingSyncItem) -> Dict[str, Any]:
        entity_name = str(item.payload["entity_name"])
        entity_type = str(item.payload.get("entity_type", item.kind))
        observation = str(item.payload["observation"])
        existing = self.mcp_registry.call_tool("memory", "open_nodes", {"names": [entity_name]})
        entities = existing.get("entities", []) if isinstance(existing, dict) else []
        if entities:
            result = self.mcp_registry.call_tool(
                "memory",
                "add_observations",
                {
                    "observations": [
                        {
                            "entityName": entity_name,
                            "contents": [observation],
                        }
                    ]
                },
            )
            operation = "add_observations"
        else:
            result = self.mcp_registry.call_tool(
                "memory",
                "create_entities",
                {
                    "entities": [
                        {
                            "name": entity_name,
                            "entityType": entity_type,
                            "observations": [observation],
                        }
                    ]
                },
            )
            operation = "create_entities"
        return {
            "entity_name": entity_name,
            "operation": operation,
            "result_excerpt": json.dumps(result, ensure_ascii=True)[:1200],
        }

    def _queue_turn_memory_sync(
        self,
        session_id: str | None,
        correlation_id: str,
        user_prompt: str,
        assistant_response: str,
        model_invoked: bool,
        route_reason: str | None,
    ) -> None:
        if not session_id or not model_invoked:
            return
        if not self.config.memory_sync_enabled or not self.mcp_registry.has_server("memory"):
            return
        session = self.sessions.get(session_id)
        if session is None:
            return
        turn_number = len(session.messages) // 2
        observation = (
            "[%s] turn=%d correlation=%s\nUser: %s\nAssistant: %s"
            % (
                session.updated_at,
                turn_number,
                correlation_id,
                user_prompt.strip()[:500],
                assistant_response.strip()[:700],
            )
        )
        self.state.queue_memory_sync(
            session_id=session_id,
            correlation_id=correlation_id,
            kind="session_turn",
            payload={
                "entity_name": "BrokerSession::%s" % session_id,
                "entity_type": "broker-session",
                "observation": observation,
                "turn_number": turn_number,
                "route_reason": route_reason,
            },
        )
        self.logger.debug(
            "Memory sync queued",
            session_id=session_id,
            correlation_id=correlation_id,
            kind="session_turn",
        )

    def _queue_artifact_memory_sync(
        self,
        artifact_id: str,
        task: str,
        draft: str,
        correlation_id: str,
    ) -> None:
        if not self.config.memory_sync_enabled or not self.mcp_registry.has_server("memory"):
            return
        observation = (
            "[%s] artifact=%s correlation=%s\nTask: %s\nDraft excerpt: %s"
            % (
                datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
                artifact_id,
                correlation_id,
                task.strip()[:500],
                draft.strip()[:700],
            )
        )
        self.state.queue_memory_sync(
            session_id="artifact::%s" % artifact_id,
            correlation_id=correlation_id,
            kind="artifact_draft",
            payload={
                "entity_name": "Artifact::%s" % artifact_id,
                "entity_type": "artifact-draft",
                "observation": observation,
            },
        )
        self.logger.debug(
            "Memory sync queued",
            session_id="artifact::%s" % artifact_id,
            correlation_id=correlation_id,
            kind="artifact_draft",
        )


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
        if parsed.path == "/recovery/last":
            self._send_json(200, self.app.get_recovery_report())
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
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        summary = None
        if self.app.config.verbose >= 2:
            summary = self._response_summary(payload)
        detail = payload if self.app.config.verbose >= 3 else None
        self.app.logger.request(
            self.command,
            self.path,
            status_code,
            summary=summary,
            detail=detail,
        )

    def _response_summary(self, payload: Dict[str, Any]) -> str:
        if "session_id" in payload:
            return "session_id=%s" % payload.get("session_id")
        if "correlation_id" in payload:
            return "correlation_id=%s" % payload.get("correlation_id")
        if "error" in payload:
            return "error=%s" % payload.get("error")
        return "keys=%s" % ",".join(sorted(payload.keys())[:6])


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI arguments for the broker server."""
    parser = argparse.ArgumentParser(
        description="Run the BitNet local broker",
        epilog=broker_env_help_text(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--model", type=str, help="Path to the GGUF model")
    parser.add_argument("--broker-host", type=str, default=None, help="Host for the broker")
    parser.add_argument("--broker-port", type=int, default=None, help="Port for the broker")
    parser.add_argument("--llama-host", type=str, default=None, help="Host for llama-server")
    parser.add_argument("--llama-port", type=int, default=None, help="Port for llama-server")
    parser.add_argument("--llama-build-dir", type=str, default=None, help="Build directory containing llama-server")
    parser.add_argument("--gpu-layers", type=int, default=None, help="Number of layers to offload to the GPU backend")
    parser.add_argument("--threads", type=int, default=None, help="Generation threads")
    parser.add_argument("--ctx-size", type=int, default=None, help="Model context size")
    parser.add_argument("--n-predict", type=int, default=None, help="Default max tokens")
    parser.add_argument("--keep", type=int, default=None, help="Number of prompt tokens to keep on context shift")
    parser.add_argument("--temperature", type=float, default=None, help="Default temperature")
    parser.add_argument("--top-p", type=float, default=None, help="Default top-p sampling value")
    parser.add_argument(
        "--log-level",
        type=int,
        choices=[0, 1, 2, 3],
        default=None,
        help="Broker log level: 0=errors, 1=info, 2=debug, 3=trace",
    )
    parser.add_argument(
        "--verbose",
        type=int,
        choices=[0, 1, 2, 3],
        default=None,
        help="Broker request detail level: 0=quiet, 1=requests, 2=summaries, 3=payload excerpts",
    )
    parser.add_argument(
        "--recover-last-session",
        action="store_true",
        help="Print the broker recovery report and exit",
    )
    parser.add_argument(
        "--trace-turns",
        action="store_true",
        default=None,
        help="Enable per-turn broker trace capture for root-cause debugging",
    )
    parser.add_argument(
        "--trace-dir",
        type=str,
        default=None,
        help="Directory for broker turn trace logs and per-correlation trace files",
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
    if args.llama_build_dir:
        config.llama_build_dir = config.workspace_root.joinpath(args.llama_build_dir).resolve()
        config.llama_server_path = (config.llama_build_dir / "bin" / "llama-server").resolve()
    if args.gpu_layers is not None:
        config.gpu_layers = args.gpu_layers
    if args.threads is not None:
        config.threads = args.threads
    if args.ctx_size is not None:
        config.ctx_size = args.ctx_size
    if args.n_predict is not None:
        config.n_predict = args.n_predict
    if args.keep is not None:
        config.n_keep = args.keep
    if args.temperature is not None:
        config.temperature = args.temperature
    if args.top_p is not None:
        config.top_p = args.top_p
    if args.log_level is not None:
        config.log_level = args.log_level
    if args.verbose is not None:
        config.verbose = args.verbose
    if args.trace_turns is not None:
        config.trace_turns = bool(args.trace_turns)
    if args.trace_dir:
        config.trace_dir = config.workspace_root.joinpath(args.trace_dir).resolve()
    return config


def main() -> None:
    """Run the broker HTTP server."""
    parser = build_arg_parser()
    args = parser.parse_args()
    config = apply_cli_overrides(BrokerConfig.from_env(), args)
    if args.recover_last_session:
        print(json.dumps(BrokerStateManager(config).inspect_last_session(), indent=2))
        return
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
        app.close()
        app.runtime.stop()
        server.server_close()


if __name__ == "__main__":
    main()
