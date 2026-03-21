"""Run profile and capability matrix for the broker harness.

A *run profile* is a stable, provider-neutral descriptor that expresses the
combination of model family, tool access, memory routing, sandbox permissions,
and token budget for a class of task.  Adapters and workflow stories consume
profiles by name so that provider-specific knobs never need to appear in
planning artifacts.

Profiles are created by composing four sub-policy dataclasses:

    SandboxPolicy – execution permissions (read / write / network / exec)
    ToolAccess    – which broker and MCP tool categories are enabled
    MemoryPolicy  – memory-routing behaviour (enabled, priority, auto-store)
    ModelBudget   – token and temperature budget

The canonical matrix is the module-level dict ``RUN_PROFILE_MATRIX``.
Use ``resolve_profile(name)`` to look up a profile by name.

Reference: docs/plans/local_llm_agent_harness_modern_stacks.md §11
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Sub-policy dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SandboxPolicy:
    """Defines what execution permissions are granted within a profile.

    Attributes:
        allow_read: Permit read access to filesystem tools (``read_text_file``,
            ``list_directory``, ``search_text``).
        allow_write: Permit write access, including memory-store operations
            and any tool that persists state.
        allow_network: Permit outbound MCP calls that cross a network boundary
            (remote MCP servers, context-lookup APIs).
        allow_exec: Permit execution of arbitrary shell commands or code.
            Defaults to ``False``; should remain ``False`` for all standard
            profiles.
    """

    allow_read: bool = True
    allow_write: bool = False
    allow_network: bool = False
    allow_exec: bool = False


@dataclass
class ToolAccess:
    """Defines which broker and MCP tool categories are available.

    Broker built-in categories
    --------------------------
    filesystem_read: Enable ``list_directory``, ``read_text_file``,
        ``search_text``.
    filesystem_write: Enable any broker tool that persists to disk.

    MCP tool categories
    -------------------
    mcp_memory: Enable ``mcp_memory_call`` (Knowledge Graph memory server).
    mcp_sequential_thinking: Enable ``mcp_sequential_thinking`` (step-by-step
        reasoning server).
    mcp_context7: Enable ``mcp_context7_call`` (external docs lookup).
    mcp_custom: Enable any custom MCP server registered in
        ``mcp_servers.json`` beyond the three standard ones.

    Explicit allow / deny lists
    ---------------------------
    allow_tool_names: When non-empty, restricts execution to exactly these
        tool names regardless of the category flags above.
    deny_tool_names: When non-empty, blocks these specific tool names even if
        their category flag is enabled.
    """

    filesystem_read: bool = True
    filesystem_write: bool = False
    mcp_memory: bool = False
    mcp_sequential_thinking: bool = False
    mcp_context7: bool = False
    mcp_custom: bool = False
    allow_tool_names: List[str] = field(default_factory=list)
    deny_tool_names: List[str] = field(default_factory=list)


@dataclass
class MemoryPolicy:
    """Defines memory-routing behaviour for the profile.

    Attributes:
        enabled: Whether the memory subsystem is active for this profile.
        routing_priority: Governs the order in which the broker considers
            routing options.  Canonical values:

            ``"model_first"``
                The language model is invoked first; memory is consulted only
                for context injection, never as a short-circuit.
            ``"memory_first"``
                Deterministic memory routes are tried before the model;
                matched routes short-circuit model invocation.
            ``"memory_only"``
                Only deterministic memory routes are used; the model is never
                invoked.  Suited for retrieval-only query patterns.
        auto_store: When ``True`` the broker automatically writes notable
            context (assistant responses, tool results) into the memory store
            after each turn.
    """

    enabled: bool = False
    routing_priority: str = "model_first"
    auto_store: bool = False


@dataclass
class ModelBudget:
    """Token and compute budget for a single turn.

    These values map directly to llama-server launch parameters and per-request
    overrides.  Adapters MAY tighten but MUST NOT exceed the declared budget.

    Attributes:
        ctx_size: Total context window in tokens (prompt + output).
        max_new_tokens: Maximum tokens to generate in a single response.
        temperature: Sampling temperature.  Lower values produce more
            deterministic output; higher values increase diversity.
    """

    ctx_size: int = 2048
    max_new_tokens: int = 512
    temperature: float = 0.2


# ---------------------------------------------------------------------------
# RunProfile – composite profile descriptor
# ---------------------------------------------------------------------------


@dataclass
class RunProfile:
    """A stable, provider-neutral run profile for the broker harness.

    A ``RunProfile`` binds together the four sub-policies and a *model family*
    hint so that adapters can select an appropriate model without embedding
    provider-specific names in planning artifacts.

    Attributes:
        name: Unique profile identifier.  Used as the key in
            ``RUN_PROFILE_MATRIX`` and as the value passed to
            ``resolve_profile()``.
        description: Human-readable summary of the intended use case.
        model_family: Coarse capability tier, independent of provider.
            Canonical values: ``"fast"``, ``"balanced"``, ``"high-capacity"``.
            Adapters map these to concrete model identifiers in their own
            configuration.
        tool_access: Which broker and MCP tools are available.
        memory_policy: Memory-routing behaviour.
        sandbox_policy: Execution permissions.
        budget: Token and temperature budget.
    """

    name: str
    description: str
    model_family: str
    tool_access: ToolAccess
    memory_policy: MemoryPolicy
    sandbox_policy: SandboxPolicy
    budget: ModelBudget


# ---------------------------------------------------------------------------
# Canonical run profile matrix
# ---------------------------------------------------------------------------

#: Maps profile name → ``RunProfile``.  Downstream adapters and workflow
#: stories refer to profiles by name only; never by provider-specific flags.
RUN_PROFILE_MATRIX: Dict[str, RunProfile] = {
    # ------------------------------------------------------------------
    # default
    # Conservative, read-only profile suitable for question-answering
    # and summarisation tasks that do not require state mutation.
    # ------------------------------------------------------------------
    "default": RunProfile(
        name="default",
        description=(
            "Balanced read-only profile for general question-answering and "
            "summarisation.  No memory routing or write access."
        ),
        model_family="balanced",
        tool_access=ToolAccess(
            filesystem_read=True,
            filesystem_write=False,
            mcp_memory=False,
            mcp_sequential_thinking=False,
            mcp_context7=False,
            mcp_custom=False,
        ),
        memory_policy=MemoryPolicy(
            enabled=False,
            routing_priority="model_first",
            auto_store=False,
        ),
        sandbox_policy=SandboxPolicy(
            allow_read=True,
            allow_write=False,
            allow_network=False,
            allow_exec=False,
        ),
        budget=ModelBudget(ctx_size=2048, max_new_tokens=512, temperature=0.2),
    ),
    # ------------------------------------------------------------------
    # read_only
    # Most restrictive profile; suitable for untrusted or sandboxed
    # evaluation contexts where no state mutation is permitted.
    # ------------------------------------------------------------------
    "read_only": RunProfile(
        name="read_only",
        description=(
            "Strictest sandbox profile.  Read-only filesystem access, no MCP, "
            "no memory writes, no network egress.  Use for untrusted or "
            "audited evaluation contexts."
        ),
        model_family="fast",
        tool_access=ToolAccess(
            filesystem_read=True,
            filesystem_write=False,
            mcp_memory=False,
            mcp_sequential_thinking=False,
            mcp_context7=False,
            mcp_custom=False,
        ),
        memory_policy=MemoryPolicy(
            enabled=False,
            routing_priority="model_first",
            auto_store=False,
        ),
        sandbox_policy=SandboxPolicy(
            allow_read=True,
            allow_write=False,
            allow_network=False,
            allow_exec=False,
        ),
        budget=ModelBudget(ctx_size=2048, max_new_tokens=256, temperature=0.1),
    ),
    # ------------------------------------------------------------------
    # memory_first
    # Activates the memory routing subsystem so that the Knowledge Graph
    # is consulted before (and instead of) the model when a deterministic
    # route matches.  Suitable for recall-heavy assistant sessions.
    # ------------------------------------------------------------------
    "memory_first": RunProfile(
        name="memory_first",
        description=(
            "Memory-first routing profile.  The Knowledge Graph memory server "
            "is consulted before the model; matched routes short-circuit model "
            "invocation.  Auto-store is enabled so responses are persisted."
        ),
        model_family="balanced",
        tool_access=ToolAccess(
            filesystem_read=True,
            filesystem_write=False,
            mcp_memory=True,
            mcp_sequential_thinking=False,
            mcp_context7=False,
            mcp_custom=False,
        ),
        memory_policy=MemoryPolicy(
            enabled=True,
            routing_priority="memory_first",
            auto_store=True,
        ),
        sandbox_policy=SandboxPolicy(
            allow_read=True,
            allow_write=True,
            allow_network=False,
            allow_exec=False,
        ),
        budget=ModelBudget(ctx_size=4096, max_new_tokens=512, temperature=0.2),
    ),
    # ------------------------------------------------------------------
    # tool_heavy
    # Full tool access including MCP servers and filesystem writes.
    # Suitable for agentic tasks that must read, reason, write, and
    # call external services.
    # ------------------------------------------------------------------
    "tool_heavy": RunProfile(
        name="tool_heavy",
        description=(
            "Full tool-access profile for agentic tasks.  All broker tools, "
            "memory, sequential-thinking, and context-lookup MCP servers are "
            "enabled.  Write access and network egress are permitted."
        ),
        model_family="high-capacity",
        tool_access=ToolAccess(
            filesystem_read=True,
            filesystem_write=True,
            mcp_memory=True,
            mcp_sequential_thinking=True,
            mcp_context7=True,
            mcp_custom=True,
        ),
        memory_policy=MemoryPolicy(
            enabled=True,
            routing_priority="memory_first",
            auto_store=True,
        ),
        sandbox_policy=SandboxPolicy(
            allow_read=True,
            allow_write=True,
            allow_network=True,
            allow_exec=False,
        ),
        budget=ModelBudget(ctx_size=8192, max_new_tokens=1024, temperature=0.3),
    ),
    # ------------------------------------------------------------------
    # thinking
    # Activates sequential-thinking MCP for step-by-step reasoning tasks
    # that benefit from explicit chain-of-thought scaffolding.  No
    # filesystem writes or memory persistence.
    # ------------------------------------------------------------------
    "thinking": RunProfile(
        name="thinking",
        description=(
            "Sequential-thinking profile.  The sequential-thinking MCP server "
            "is enabled to scaffold explicit chain-of-thought reasoning.  "
            "Read-only; no memory persistence."
        ),
        model_family="high-capacity",
        tool_access=ToolAccess(
            filesystem_read=True,
            filesystem_write=False,
            mcp_memory=False,
            mcp_sequential_thinking=True,
            mcp_context7=False,
            mcp_custom=False,
        ),
        memory_policy=MemoryPolicy(
            enabled=False,
            routing_priority="model_first",
            auto_store=False,
        ),
        sandbox_policy=SandboxPolicy(
            allow_read=True,
            allow_write=False,
            allow_network=False,
            allow_exec=False,
        ),
        budget=ModelBudget(ctx_size=8192, max_new_tokens=2048, temperature=0.4),
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def resolve_profile(name: str) -> RunProfile:
    """Return the ``RunProfile`` for *name*, falling back to ``"default"``.

    Args:
        name: Profile identifier.  Must be a key in ``RUN_PROFILE_MATRIX``.

    Returns:
        The matching ``RunProfile`` when *name* is found, or the ``"default"``
        profile when *name* is not registered.

    Example::

        profile = resolve_profile("memory_first")
        if profile.memory_policy.enabled:
            # activate memory routing …
    """
    return RUN_PROFILE_MATRIX.get(name, RUN_PROFILE_MATRIX["default"])


#: Ordered list of canonical profile names, suitable for documentation and
#: validation loops.
PROFILE_NAMES: List[str] = list(RUN_PROFILE_MATRIX.keys())
