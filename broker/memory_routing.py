"""Deterministic memory-aware routing for broker chat requests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .mcp import McpRegistry


_REMEMBER_RE = re.compile(
    r"^\s*remember\s+(?P<entity>[^:]+?)\s*:\s*(?P<observation>.+?)\s*$",
    flags=re.IGNORECASE,
)
_RECALL_RE = re.compile(
    r"^\s*(?:what do you remember about|recall|open memory for|search memory for)\s+"
    r"(?P<query>.+?)\s*\??\s*$",
    flags=re.IGNORECASE,
)
_SHOW_GRAPH_RE = re.compile(
    r"^\s*(?:show|read|display)\s+(?:the\s+)?memory graph\s*$",
    flags=re.IGNORECASE,
)
_MEMORY_EVIDENCE_RE = re.compile(
    r"^\s*(?:what do you know about|summarize memory for|use memory for|memory about)\s+"
    r"(?P<query>.+?)\s*\??\s*$",
    flags=re.IGNORECASE,
)


@dataclass
class MemoryRouteResult:
    """Result of broker-managed memory routing."""

    handled: bool
    response: Optional[str] = None
    route_reason: Optional[str] = None
    evidence: Optional[List[Dict[str, str]]] = None
    operations: Optional[List[Dict[str, Any]]] = None


def maybe_route_memory_prompt(
    prompt: str,
    mcp_registry: McpRegistry,
) -> Optional[MemoryRouteResult]:
    """Handle explicit memory prompts without relying on model tool choice."""
    prompt = prompt.strip()
    if not prompt:
        return None

    remember_match = _REMEMBER_RE.match(prompt)
    if remember_match:
        return _handle_remember(remember_match, mcp_registry)

    recall_match = _RECALL_RE.match(prompt)
    if recall_match:
        return _handle_recall(recall_match, mcp_registry)

    if _SHOW_GRAPH_RE.match(prompt):
        return _handle_show_graph(mcp_registry)

    return None


def maybe_collect_memory_evidence(
    prompt: str,
    mcp_registry: McpRegistry,
    explicit_query: Optional[str] = None,
) -> Optional[MemoryRouteResult]:
    """Collect Memory MCP results as evidence for non-routed prompts."""
    query = _normalize_value(explicit_query) if explicit_query else ""
    if not query:
        prompt_match = _MEMORY_EVIDENCE_RE.match(prompt.strip())
        if prompt_match:
            query = _normalize_value(prompt_match.group("query"))

    if not query:
        return None

    operations: List[Dict[str, Any]] = []
    try:
        search_result = mcp_registry.call_tool("memory", "search_nodes", {"query": query})
        operations.append(
            {"server": "memory", "tool": "search_nodes", "result": search_result}
        )
        entities = _extract_entities(search_result)

        if not entities:
            exact_result = mcp_registry.call_tool("memory", "open_nodes", {"names": [query]})
            operations.append(
                {"server": "memory", "tool": "open_nodes", "result": exact_result}
            )

        return MemoryRouteResult(
            handled=False,
            route_reason="memory_evidence_injected",
            evidence=_operations_to_evidence(operations),
            operations=operations,
        )
    except Exception as exc:  # noqa: BLE001
        return MemoryRouteResult(
            handled=False,
            route_reason="memory_evidence_failed",
            evidence=[
                {
                    "source": "mcp:memory:error",
                    "kind": "mcp-tool-error",
                    "content": str(exc),
                }
            ],
            operations=[],
        )


def maybe_answer_from_memory_evidence(
    prompt: str,
    operations: Iterable[Dict[str, Any]],
) -> Optional[MemoryRouteResult]:
    """Return a deterministic broker-controlled answer from Memory evidence."""
    prompt = prompt.strip()
    if not prompt:
        return None

    entities = _extract_entities_from_operations(operations)
    if not entities:
        return None

    lowered_prompt = prompt.lower()

    if "summarize" in lowered_prompt or "summary" in lowered_prompt:
        response = _format_memory_summary_sentence(entities)
        if response:
            return MemoryRouteResult(
                handled=True,
                response=response,
                route_reason="broker_controlled_memory_summary",
                evidence=_operations_to_evidence(operations),
                operations=list(operations),
            )

    if "observation" in lowered_prompt and ("list" in lowered_prompt or "what" in lowered_prompt):
        response = _format_memory_observations(entities)
        if response:
            return MemoryRouteResult(
                handled=True,
                response=response,
                route_reason="broker_controlled_memory_observations",
                evidence=_operations_to_evidence(operations),
                operations=list(operations),
            )

    return None


def _handle_remember(
    match: re.Match[str],
    mcp_registry: McpRegistry,
) -> MemoryRouteResult:
    entity = _normalize_value(match.group("entity"))
    observation = _normalize_value(match.group("observation"))
    operations: List[Dict[str, Any]] = []

    try:
        existing = mcp_registry.call_tool("memory", "open_nodes", {"names": [entity]})
        operations.append({"server": "memory", "tool": "open_nodes", "result": existing})
        existing_entities = _extract_entities(existing)

        if existing_entities:
            mutation = mcp_registry.call_tool(
                "memory",
                "add_observations",
                {
                    "observations": [
                        {
                            "entityName": entity,
                            "contents": [observation],
                        }
                    ]
                },
            )
            operations.append(
                {"server": "memory", "tool": "add_observations", "result": mutation}
            )
            response = "Remembered for %s: %s" % (entity, observation)
            reason = "memory_add_observation"
        else:
            mutation = mcp_registry.call_tool(
                "memory",
                "create_entities",
                {
                    "entities": [
                        {
                            "name": entity,
                            "entityType": "note",
                            "observations": [observation],
                        }
                    ]
                },
            )
            operations.append(
                {"server": "memory", "tool": "create_entities", "result": mutation}
            )
            response = "Remembered new entity %s: %s" % (entity, observation)
            reason = "memory_create_entity"

        return MemoryRouteResult(
            handled=True,
            response=response,
            route_reason=reason,
            evidence=_operations_to_evidence(operations),
            operations=operations,
        )
    except Exception as exc:  # noqa: BLE001
        return _memory_error_result("memory_write_failed", exc)


def _handle_recall(
    match: re.Match[str],
    mcp_registry: McpRegistry,
) -> MemoryRouteResult:
    query = _normalize_value(match.group("query"))
    operations: List[Dict[str, Any]] = []

    try:
        search_result = mcp_registry.call_tool("memory", "search_nodes", {"query": query})
        operations.append(
            {"server": "memory", "tool": "search_nodes", "result": search_result}
        )
        entities = _extract_entities(search_result)

        if not entities:
            exact_result = mcp_registry.call_tool("memory", "open_nodes", {"names": [query]})
            operations.append(
                {"server": "memory", "tool": "open_nodes", "result": exact_result}
            )
            entities = _extract_entities(exact_result)

        if not entities:
            response = "I do not have any stored memory for %s." % query
            reason = "memory_recall_not_found"
        else:
            response = _format_entity_summary(query, entities)
            reason = "memory_recall_found"

        return MemoryRouteResult(
            handled=True,
            response=response,
            route_reason=reason,
            evidence=_operations_to_evidence(operations),
            operations=operations,
        )
    except Exception as exc:  # noqa: BLE001
        return _memory_error_result("memory_recall_failed", exc)


def _handle_show_graph(mcp_registry: McpRegistry) -> MemoryRouteResult:
    operations: List[Dict[str, Any]] = []
    try:
        graph = mcp_registry.call_tool("memory", "read_graph", {})
        operations.append({"server": "memory", "tool": "read_graph", "result": graph})
        structured = _extract_structured_content(graph)
        entities = structured.get("entities", []) if isinstance(structured, dict) else []
        relations = structured.get("relations", []) if isinstance(structured, dict) else []

        entity_names = []
        if isinstance(entities, list):
            for entity in entities[:10]:
                if isinstance(entity, dict) and isinstance(entity.get("name"), str):
                    entity_names.append(entity["name"])

        response = "Memory graph has %d entities and %d relations." % (
            len(entities) if isinstance(entities, list) else 0,
            len(relations) if isinstance(relations, list) else 0,
        )
        if entity_names:
            response += " Entities: %s." % ", ".join(entity_names)

        return MemoryRouteResult(
            handled=True,
            response=response,
            route_reason="memory_read_graph",
            evidence=_operations_to_evidence(operations),
            operations=operations,
        )
    except Exception as exc:  # noqa: BLE001
        return _memory_error_result("memory_read_graph_failed", exc)


def _extract_entities(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    structured = _extract_structured_content(payload)
    entities = structured.get("entities", []) if isinstance(structured, dict) else []
    return [entity for entity in entities if isinstance(entity, dict)] if isinstance(entities, list) else []


def _extract_entities_from_operations(
    operations: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    entities: List[Dict[str, Any]] = []
    for operation in operations:
        result = operation.get("result", {})
        if not isinstance(result, dict):
            continue
        for entity in _extract_entities(result):
            if entity not in entities:
                entities.append(entity)
    return entities


def _extract_structured_content(payload: Dict[str, Any]) -> Dict[str, Any]:
    structured = payload.get("structuredContent", {})
    return structured if isinstance(structured, dict) else {}


def _format_entity_summary(query: str, entities: Iterable[Dict[str, Any]]) -> str:
    summary_lines = ["Memory for %s:" % query]
    for entity in list(entities)[:5]:
        name = entity.get("name", "Unknown")
        entity_type = entity.get("entityType", "entity")
        observations = entity.get("observations", [])
        obs_text = "; ".join(
            observation
            for observation in observations[:3]
            if isinstance(observation, str) and observation.strip()
        )
        if obs_text:
            summary_lines.append("- %s (%s): %s" % (name, entity_type, obs_text))
        else:
            summary_lines.append("- %s (%s)" % (name, entity_type))
    return "\n".join(summary_lines)


def _format_memory_summary_sentence(entities: Iterable[Dict[str, Any]]) -> Optional[str]:
    entity_list = list(entities)
    if not entity_list:
        return None

    first = entity_list[0]
    name = str(first.get("name", "Unknown")).strip()
    entity_type = str(first.get("entityType", "entity")).strip()
    observations = [
        observation.strip()
        for observation in first.get("observations", [])
        if isinstance(observation, str) and observation.strip()
    ]
    if observations:
        observation = observations[0]
        return "%s is a %s: %s." % (name, entity_type, observation.rstrip("."))

    return "%s is a %s stored in memory." % (name, entity_type)


def _format_memory_observations(entities: Iterable[Dict[str, Any]]) -> Optional[str]:
    observations: List[str] = []
    for entity in entities:
        for observation in entity.get("observations", []):
            if isinstance(observation, str) and observation.strip():
                observations.append(observation.strip())

    if not observations:
        return None

    return "\n".join("- %s" % observation for observation in observations[:10])


def _operations_to_evidence(operations: Iterable[Dict[str, Any]]) -> List[Dict[str, str]]:
    evidence = []
    for operation in operations:
        evidence.append(
            {
                "source": "mcp:%s:%s"
                % (operation.get("server", "unknown"), operation.get("tool", "unknown")),
                "kind": "mcp-tool-result",
                "content": json.dumps(operation.get("result", {}), indent=2, ensure_ascii=True),
            }
        )
    return evidence


def _memory_error_result(reason: str, exc: Exception) -> MemoryRouteResult:
    return MemoryRouteResult(
        handled=True,
        response="Memory routing is unavailable: %s" % str(exc),
        route_reason=reason,
        evidence=[],
        operations=[],
    )


def _normalize_value(raw_value: str) -> str:
    return raw_value.strip().rstrip("?").strip()
