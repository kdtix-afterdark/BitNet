"""Helpers for live broker trace and UAT state monitoring."""

from __future__ import annotations

from typing import Any, Dict


def _excerpt(value: Any, limit: int = 120) -> str:
    text = str(value).replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def summarize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    results = list(state.get("results", []))
    scripted = sum(1 for item in results if str(item.get("kind", "")).strip().lower() == "scripted")
    inserted = sum(1 for item in results if str(item.get("kind", "")).strip().lower() == "inserted")
    skipped = sum(1 for item in results if str(item.get("kind", "")).strip().lower() == "skipped")
    latest = results[-1] if results else {}
    return {
        "session_id": state.get("session_id"),
        "next_turn_index": state.get("next_turn_index"),
        "completed": state.get("completed", False),
        "scripted_turns": scripted,
        "inserted_turns": inserted,
        "skipped_turns": skipped,
        "broker_turn_count": state.get("broker_turn_count", 0),
        "external_turns_detected": state.get("external_turns_detected", 0),
        "latest_kind": latest.get("kind"),
        "latest_prompt_excerpt": _excerpt(latest.get("prompt", "")),
        "latest_response_excerpt": _excerpt(latest.get("response", "")),
    }


def format_trace_event(event: Dict[str, Any]) -> str:
    phase = str(event.get("phase", "unknown"))
    correlation_id = str(event.get("correlation_id", ""))[:8]
    payload = event.get("payload", {})
    prefix = f"[trace] corr={correlation_id} phase={phase}"

    if not isinstance(payload, dict):
        return f"{prefix} payload={_excerpt(payload)}"

    if phase == "turn_started":
        return f"{prefix} prompt={_excerpt(payload.get('prompt', ''))}"
    if phase == "prompt_built":
        return (
            f"{prefix} history={payload.get('conversation_history_count', 0)} "
            f"summary_turns={payload.get('summarized_turn_count', 0)} "
            f"messages={len(payload.get('messages', []))}"
        )
    if phase == "llama_request_built":
        return (
            f"{prefix} messages={len(payload.get('messages', []))} "
            f"max_tokens={payload.get('max_tokens')} temp={payload.get('temperature')} "
            f"top_p={payload.get('top_p')}"
        )
    if phase == "llama_response_received":
        return f"{prefix} raw={_excerpt(payload.get('raw_content', ''))}"
    if phase == "repair_completed":
        return (
            f"{prefix} repair_applied={payload.get('repair_applied')} "
            f"reason={payload.get('repair_reason')} "
            f"post={_excerpt(payload.get('post_repair_content', ''))}"
        )
    if phase == "session_persisted":
        return (
            f"{prefix} message_count={payload.get('message_count')} "
            f"turn_count={payload.get('turn_count')} "
            f"summarized_turn_count={payload.get('summarized_turn_count')}"
        )
    if phase == "turn_completed":
        return f"{prefix} final={_excerpt(payload.get('final_response', ''))}"
    if phase == "turn_failed":
        return f"{prefix} error={_excerpt(payload.get('error', ''))}"
    if phase == "route_handled":
        return (
            f"{prefix} route_reason={payload.get('route_reason')} "
            f"response={_excerpt(payload.get('response', ''))}"
        )
    return f"{prefix} keys={','.join(sorted(payload.keys())[:6])}"
