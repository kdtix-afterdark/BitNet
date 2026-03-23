"""Deterministic tests for broker/run_profile.py — TASK-LAH-002 TDD coverage.

Covers:
1. SandboxPolicy dataclass: defaults and explicit construction.
2. ToolAccess dataclass: defaults, category flags, allow/deny lists.
3. MemoryPolicy dataclass: defaults, routing_priority values.
4. ModelBudget dataclass: defaults and custom budgets.
5. RunProfile dataclass: composition and field storage.
6. RUN_PROFILE_MATRIX: all five canonical profiles present, correct
   sub-policy values for each.
7. resolve_profile(): known names return the correct profile; unknown
   names fall back to the "default" profile.
8. PROFILE_NAMES: contains exactly the five canonical names.

Run:
    pytest tests/test_run_profile.py -v
"""

import pytest

from broker.run_profile import (
    PROFILE_NAMES,
    RUN_PROFILE_MATRIX,
    MemoryPolicy,
    ModelBudget,
    RunProfile,
    SandboxPolicy,
    ToolAccess,
    resolve_profile,
)


# ---------------------------------------------------------------------------
# SandboxPolicy
# ---------------------------------------------------------------------------


class TestSandboxPolicy:
    """Unit tests for the SandboxPolicy dataclass."""

    def test_defaults(self):
        sp = SandboxPolicy()
        assert sp.allow_read is True
        assert sp.allow_write is False
        assert sp.allow_network is False
        assert sp.allow_exec is False

    def test_explicit_all_true(self):
        sp = SandboxPolicy(
            allow_read=True, allow_write=True,
            allow_network=True, allow_exec=True,
        )
        assert sp.allow_read is True
        assert sp.allow_write is True
        assert sp.allow_network is True
        assert sp.allow_exec is True

    def test_explicit_all_false(self):
        sp = SandboxPolicy(
            allow_read=False, allow_write=False,
            allow_network=False, allow_exec=False,
        )
        assert sp.allow_read is False
        assert sp.allow_write is False
        assert sp.allow_network is False
        assert sp.allow_exec is False

    def test_equality(self):
        a = SandboxPolicy(allow_read=True, allow_write=True)
        b = SandboxPolicy(allow_read=True, allow_write=True)
        assert a == b

    def test_inequality(self):
        a = SandboxPolicy(allow_write=True)
        b = SandboxPolicy(allow_write=False)
        assert a != b

    def test_is_dataclass(self):
        import dataclasses
        assert dataclasses.is_dataclass(SandboxPolicy())


# ---------------------------------------------------------------------------
# ToolAccess
# ---------------------------------------------------------------------------


class TestToolAccess:
    """Unit tests for the ToolAccess dataclass."""

    def test_defaults(self):
        ta = ToolAccess()
        assert ta.filesystem_read is True
        assert ta.filesystem_write is False
        assert ta.mcp_memory is False
        assert ta.mcp_sequential_thinking is False
        assert ta.mcp_context7 is False
        assert ta.mcp_custom is False
        assert ta.allow_tool_names == []
        assert ta.deny_tool_names == []

    def test_allow_deny_lists_not_shared(self):
        ta1 = ToolAccess()
        ta2 = ToolAccess()
        ta1.allow_tool_names.append("read_text_file")
        assert ta2.allow_tool_names == []

    def test_deny_list_not_shared(self):
        ta1 = ToolAccess()
        ta2 = ToolAccess()
        ta1.deny_tool_names.append("exec_command")
        assert ta2.deny_tool_names == []

    def test_all_mcp_enabled(self):
        ta = ToolAccess(
            mcp_memory=True,
            mcp_sequential_thinking=True,
            mcp_context7=True,
            mcp_custom=True,
        )
        assert ta.mcp_memory is True
        assert ta.mcp_sequential_thinking is True
        assert ta.mcp_context7 is True
        assert ta.mcp_custom is True

    def test_allow_tool_names_stored(self):
        ta = ToolAccess(allow_tool_names=["read_text_file", "search_text"])
        assert ta.allow_tool_names == ["read_text_file", "search_text"]

    def test_deny_tool_names_stored(self):
        ta = ToolAccess(deny_tool_names=["write_file"])
        assert ta.deny_tool_names == ["write_file"]

    def test_is_dataclass(self):
        import dataclasses
        assert dataclasses.is_dataclass(ToolAccess())


# ---------------------------------------------------------------------------
# MemoryPolicy
# ---------------------------------------------------------------------------


class TestMemoryPolicy:
    """Unit tests for the MemoryPolicy dataclass."""

    def test_defaults(self):
        mp = MemoryPolicy()
        assert mp.enabled is False
        assert mp.routing_priority == "model_first"
        assert mp.auto_store is False

    def test_memory_first_priority(self):
        mp = MemoryPolicy(enabled=True, routing_priority="memory_first", auto_store=True)
        assert mp.enabled is True
        assert mp.routing_priority == "memory_first"
        assert mp.auto_store is True

    def test_memory_only_priority(self):
        mp = MemoryPolicy(routing_priority="memory_only")
        assert mp.routing_priority == "memory_only"

    def test_equality(self):
        a = MemoryPolicy(enabled=True, routing_priority="memory_first")
        b = MemoryPolicy(enabled=True, routing_priority="memory_first")
        assert a == b

    def test_inequality(self):
        a = MemoryPolicy(routing_priority="model_first")
        b = MemoryPolicy(routing_priority="memory_first")
        assert a != b

    def test_is_dataclass(self):
        import dataclasses
        assert dataclasses.is_dataclass(MemoryPolicy())


# ---------------------------------------------------------------------------
# ModelBudget
# ---------------------------------------------------------------------------


class TestModelBudget:
    """Unit tests for the ModelBudget dataclass."""

    def test_defaults(self):
        mb = ModelBudget()
        assert mb.ctx_size == 2048
        assert mb.max_new_tokens == 512
        assert mb.temperature == pytest.approx(0.2)

    def test_custom_values(self):
        mb = ModelBudget(ctx_size=8192, max_new_tokens=2048, temperature=0.4)
        assert mb.ctx_size == 8192
        assert mb.max_new_tokens == 2048
        assert mb.temperature == pytest.approx(0.4)

    def test_small_budget(self):
        mb = ModelBudget(ctx_size=512, max_new_tokens=64, temperature=0.0)
        assert mb.ctx_size == 512
        assert mb.max_new_tokens == 64
        assert mb.temperature == pytest.approx(0.0)

    def test_equality(self):
        a = ModelBudget(ctx_size=4096)
        b = ModelBudget(ctx_size=4096)
        assert a == b

    def test_inequality(self):
        a = ModelBudget(ctx_size=2048)
        b = ModelBudget(ctx_size=4096)
        assert a != b

    def test_is_dataclass(self):
        import dataclasses
        assert dataclasses.is_dataclass(ModelBudget())


# ---------------------------------------------------------------------------
# RunProfile
# ---------------------------------------------------------------------------


class TestRunProfile:
    """Unit tests for the RunProfile dataclass."""

    def _make_profile(self, **overrides) -> RunProfile:
        defaults = dict(
            name="test",
            description="test profile",
            model_family="balanced",
            tool_access=ToolAccess(),
            memory_policy=MemoryPolicy(),
            sandbox_policy=SandboxPolicy(),
            budget=ModelBudget(),
        )
        defaults.update(overrides)
        return RunProfile(**defaults)

    def test_required_fields_stored(self):
        rp = self._make_profile()
        assert rp.name == "test"
        assert rp.description == "test profile"
        assert rp.model_family == "balanced"

    def test_sub_policy_stored(self):
        ta = ToolAccess(mcp_memory=True)
        mp = MemoryPolicy(enabled=True)
        sp = SandboxPolicy(allow_write=True)
        mb = ModelBudget(ctx_size=4096)
        rp = self._make_profile(
            tool_access=ta, memory_policy=mp,
            sandbox_policy=sp, budget=mb,
        )
        assert rp.tool_access is ta
        assert rp.memory_policy is mp
        assert rp.sandbox_policy is sp
        assert rp.budget is mb

    def test_model_family_values(self):
        for family in ("fast", "balanced", "high-capacity"):
            rp = self._make_profile(model_family=family)
            assert rp.model_family == family

    def test_is_dataclass(self):
        import dataclasses
        assert dataclasses.is_dataclass(self._make_profile())


# ---------------------------------------------------------------------------
# RUN_PROFILE_MATRIX — presence and structure
# ---------------------------------------------------------------------------


class TestRunProfileMatrix:
    """Verify the five canonical profiles exist in RUN_PROFILE_MATRIX."""

    EXPECTED_NAMES = {"default", "read_only", "memory_first", "tool_heavy", "thinking"}

    def test_all_expected_profiles_present(self):
        for name in self.EXPECTED_NAMES:
            assert name in RUN_PROFILE_MATRIX, f"Profile '{name}' missing from matrix"

    def test_no_extra_profiles(self):
        assert set(RUN_PROFILE_MATRIX.keys()) == self.EXPECTED_NAMES

    def test_all_values_are_run_profiles(self):
        for name, profile in RUN_PROFILE_MATRIX.items():
            assert isinstance(profile, RunProfile), f"Matrix['{name}'] is not a RunProfile"

    def test_names_match_keys(self):
        for key, profile in RUN_PROFILE_MATRIX.items():
            assert profile.name == key, (
                f"Profile key '{key}' does not match profile.name '{profile.name}'"
            )

    # --- default profile ---
    def test_default_no_memory(self):
        p = RUN_PROFILE_MATRIX["default"]
        assert p.memory_policy.enabled is False

    def test_default_no_write(self):
        p = RUN_PROFILE_MATRIX["default"]
        assert p.sandbox_policy.allow_write is False

    def test_default_no_mcp(self):
        p = RUN_PROFILE_MATRIX["default"]
        ta = p.tool_access
        assert ta.mcp_memory is False
        assert ta.mcp_sequential_thinking is False
        assert ta.mcp_context7 is False

    def test_default_model_family_balanced(self):
        assert RUN_PROFILE_MATRIX["default"].model_family == "balanced"

    def test_default_model_first_routing(self):
        assert RUN_PROFILE_MATRIX["default"].memory_policy.routing_priority == "model_first"

    # --- read_only profile ---
    def test_read_only_no_memory(self):
        p = RUN_PROFILE_MATRIX["read_only"]
        assert p.memory_policy.enabled is False

    def test_read_only_no_write(self):
        p = RUN_PROFILE_MATRIX["read_only"]
        assert p.sandbox_policy.allow_write is False

    def test_read_only_no_exec(self):
        p = RUN_PROFILE_MATRIX["read_only"]
        assert p.sandbox_policy.allow_exec is False

    def test_read_only_model_family_fast(self):
        assert RUN_PROFILE_MATRIX["read_only"].model_family == "fast"

    def test_read_only_max_tokens_256(self):
        assert RUN_PROFILE_MATRIX["read_only"].budget.max_new_tokens == 256

    def test_read_only_no_network(self):
        assert RUN_PROFILE_MATRIX["read_only"].sandbox_policy.allow_network is False

    # --- memory_first profile ---
    def test_memory_first_memory_enabled(self):
        p = RUN_PROFILE_MATRIX["memory_first"]
        assert p.memory_policy.enabled is True

    def test_memory_first_routing_priority(self):
        assert RUN_PROFILE_MATRIX["memory_first"].memory_policy.routing_priority == "memory_first"

    def test_memory_first_auto_store(self):
        assert RUN_PROFILE_MATRIX["memory_first"].memory_policy.auto_store is True

    def test_memory_first_mcp_memory_enabled(self):
        assert RUN_PROFILE_MATRIX["memory_first"].tool_access.mcp_memory is True

    def test_memory_first_write_allowed(self):
        assert RUN_PROFILE_MATRIX["memory_first"].sandbox_policy.allow_write is True

    def test_memory_first_ctx_4096(self):
        assert RUN_PROFILE_MATRIX["memory_first"].budget.ctx_size == 4096

    def test_memory_first_no_exec(self):
        assert RUN_PROFILE_MATRIX["memory_first"].sandbox_policy.allow_exec is False

    # --- tool_heavy profile ---
    def test_tool_heavy_all_mcp(self):
        ta = RUN_PROFILE_MATRIX["tool_heavy"].tool_access
        assert ta.mcp_memory is True
        assert ta.mcp_sequential_thinking is True
        assert ta.mcp_context7 is True
        assert ta.mcp_custom is True

    def test_tool_heavy_write_allowed(self):
        assert RUN_PROFILE_MATRIX["tool_heavy"].sandbox_policy.allow_write is True

    def test_tool_heavy_network_allowed(self):
        assert RUN_PROFILE_MATRIX["tool_heavy"].sandbox_policy.allow_network is True

    def test_tool_heavy_no_exec(self):
        assert RUN_PROFILE_MATRIX["tool_heavy"].sandbox_policy.allow_exec is False

    def test_tool_heavy_model_family_high_capacity(self):
        assert RUN_PROFILE_MATRIX["tool_heavy"].model_family == "high-capacity"

    def test_tool_heavy_ctx_8192(self):
        assert RUN_PROFILE_MATRIX["tool_heavy"].budget.ctx_size == 8192

    def test_tool_heavy_max_tokens_1024(self):
        assert RUN_PROFILE_MATRIX["tool_heavy"].budget.max_new_tokens == 1024

    # --- thinking profile ---
    def test_thinking_sequential_thinking_enabled(self):
        assert RUN_PROFILE_MATRIX["thinking"].tool_access.mcp_sequential_thinking is True

    def test_thinking_no_memory(self):
        assert RUN_PROFILE_MATRIX["thinking"].memory_policy.enabled is False

    def test_thinking_no_write(self):
        assert RUN_PROFILE_MATRIX["thinking"].sandbox_policy.allow_write is False

    def test_thinking_model_family_high_capacity(self):
        assert RUN_PROFILE_MATRIX["thinking"].model_family == "high-capacity"

    def test_thinking_ctx_8192(self):
        assert RUN_PROFILE_MATRIX["thinking"].budget.ctx_size == 8192

    def test_thinking_max_tokens_2048(self):
        assert RUN_PROFILE_MATRIX["thinking"].budget.max_new_tokens == 2048

    def test_thinking_temperature(self):
        assert RUN_PROFILE_MATRIX["thinking"].budget.temperature == pytest.approx(0.4)

    def test_thinking_no_mcp_memory(self):
        assert RUN_PROFILE_MATRIX["thinking"].tool_access.mcp_memory is False


# ---------------------------------------------------------------------------
# resolve_profile
# ---------------------------------------------------------------------------


class TestResolveProfile:
    """Unit tests for the resolve_profile() helper."""

    def test_known_name_returns_correct_profile(self):
        for name in ("default", "read_only", "memory_first", "tool_heavy", "thinking"):
            profile = resolve_profile(name)
            assert profile.name == name

    def test_unknown_name_returns_default(self):
        profile = resolve_profile("nonexistent_profile_xyz")
        assert profile.name == "default"

    def test_empty_string_returns_default(self):
        profile = resolve_profile("")
        assert profile.name == "default"

    def test_returns_run_profile_instance(self):
        for name in ("default", "read_only", "memory_first", "tool_heavy", "thinking"):
            assert isinstance(resolve_profile(name), RunProfile)

    def test_unknown_returns_run_profile_instance(self):
        assert isinstance(resolve_profile("no_such_profile"), RunProfile)

    def test_default_fallback_has_no_memory(self):
        fallback = resolve_profile("unknown_name")
        assert fallback.memory_policy.enabled is False

    def test_memory_first_routing_enabled(self):
        profile = resolve_profile("memory_first")
        assert profile.memory_policy.enabled is True
        assert profile.memory_policy.routing_priority == "memory_first"

    def test_all_profiles_resolvable(self):
        for name in PROFILE_NAMES:
            profile = resolve_profile(name)
            assert profile is not None
            assert profile.name == name


# ---------------------------------------------------------------------------
# PROFILE_NAMES
# ---------------------------------------------------------------------------


class TestProfileNames:
    """Verify the PROFILE_NAMES list matches the matrix keys."""

    CANONICAL = ["default", "read_only", "memory_first", "tool_heavy", "thinking"]

    def test_all_canonical_names_present(self):
        for name in self.CANONICAL:
            assert name in PROFILE_NAMES, f"'{name}' not in PROFILE_NAMES"

    def test_no_extra_names(self):
        assert set(PROFILE_NAMES) == set(self.CANONICAL)

    def test_is_list(self):
        assert isinstance(PROFILE_NAMES, list)

    def test_length(self):
        assert len(PROFILE_NAMES) == 5
