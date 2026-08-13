"""Tests for WorldBatchCore stage contracts and execution mode plugin registry."""

from __future__ import annotations

import ast
import dis
import inspect
import re
from pathlib import Path
from unittest import mock

import pytest

from python.rl.runtime.world_batch.core import (
    BATCH_STEP_STAGE_NAMES,
    BATCH_STEP_STAGES,
    CooperativePlugin,
    ExecutionModePlugin,
    LeaderPlugin,
    StageContract,
    StandardExecutionPlugin,
    SubStage,
    register_execution_mode,
    registered_execution_modes,
    resolve_execution_mode,
    validate_stage_extension_points,
)

_CORE_PATH = (
    Path(__file__).resolve().parents[2]
    / "python" / "rl" / "runtime" / "world_batch" / "core.py"
)

# Authoritative P0-P10 vocabulary from
# docs/architecture/standards/simulation_system_architecture_design.md §6.
_AUTHORITATIVE_SEMANTIC_STAGES = {
    "P0 ContentCompile",
    "P1 WorldSetup",
    "P2 TaskingIntent",
    "P3 CommandDelivery",
    "P4 PlatformControl",
    "P5 PhysicsStep",
    "P6 SenseTrackLink",
    "P7 FireControlLaunch",
    "P8 MunitionLifecycle",
    "P9 EffectsDamage",
    "P10 ObservationExport",
}

# G4 six-layer vocabulary from the same document (§ information-state layers).
_AUTHORITATIVE_INFORMATION_LAYERS = {
    "World Truth",
    "Sensed State",
    "Track State",
    "Shared Tactical Picture",
    "Agent Observation",
    "Decision Belief",
}

# Full pin of every declared stage: semantic stages, read/write sets,
# information layers, and extension points.  Deliberately duplicates the
# declaration so that any drift in core.py fails here explicitly.
_EXPECTED_STAGE_PINS = {
    "action_prepare": {
        "semantic_stages": ("P4 PlatformControl",),
        "read_set": frozenset({
            "policy_action",
            "world_instrument_state",
            "action_gate_state",
            "truth_cache",
        }),
        "write_set": frozenset({
            "pilot_action_assignments",
            "action_gate_state",
            "last_action_state",
        }),
        "information_layer_consumed": ("Agent Observation",),
        "information_layer_produced": (),
        "extension_points": (),
    },
    "physics_step": {
        "semantic_stages": ("P5 PhysicsStep",),
        "read_set": frozenset({
            "pilot_action_assignments",
            "kernel_command_state",
        }),
        "write_set": frozenset({
            "world_truth_state",
            "world_instrument_state",
        }),
        "information_layer_consumed": (),
        "information_layer_produced": ("World Truth",),
        "extension_points": (),
    },
    "state_read": {
        "semantic_stages": ("P10 ObservationExport",),
        "read_set": frozenset({
            "world_truth_state",
            "world_instrument_state",
        }),
        "write_set": frozenset({
            "truth_cache",
            "instrument_cache",
        }),
        "information_layer_consumed": ("World Truth",),
        "information_layer_produced": ("Agent Observation",),
        "extension_points": (),
    },
    "behavior_update": {
        "semantic_stages": ("P2 TaskingIntent",),
        "read_set": frozenset({
            "truth_cache",
            "instrument_cache",
            "step_counters",
        }),
        "write_set": frozenset({
            "loader_behavior_state",
            "command_chain_state",
            "step_counters",
            "action_gate_state",
        }),
        "information_layer_consumed": ("Agent Observation",),
        "information_layer_produced": (),
        "extension_points": (
            "execution_mode_plugin.finalize_post_step_truth",
            "execution_mode_plugin.update_post_step_behavior",
        ),
    },
    "command_sync": {
        "semantic_stages": ("P2 TaskingIntent", "P3 CommandDelivery"),
        "read_set": frozenset({
            "command_chain_state",
            "command_snapshot_cache",
            "truth_cache",
        }),
        "write_set": frozenset({
            "kernel_command_state",
            "command_snapshot_cache",
        }),
        "information_layer_consumed": ("Agent Observation",),
        "information_layer_produced": (),
        "extension_points": (
            "execution_mode_plugin.skip_post_behavior_command_sync",
        ),
    },
    "observation_build": {
        "semantic_stages": ("P10 ObservationExport",),
        "read_set": frozenset({
            "truth_cache",
            "instrument_cache",
            "visual_cache",
            "world_visual_state",
            "loader_behavior_state",
        }),
        "write_set": frozenset({
            "observation_batch",
            "loader_eval_cache",
            "visual_cache",
            "device_view_cache",
        }),
        "information_layer_consumed": ("Agent Observation",),
        "information_layer_produced": ("Agent Observation",),
        "extension_points": (),
    },
    "flight_shaping": {
        "semantic_stages": ("P10 ObservationExport",),
        "read_set": frozenset({"loader_eval_cache"}),
        "write_set": frozenset({"loader_eval_cache"}),
        "information_layer_consumed": (),
        "information_layer_produced": (),
        "extension_points": (),
    },
    "reward_episode": {
        "semantic_stages": ("P10 ObservationExport", "P1 WorldSetup"),
        "read_set": frozenset({
            "observation_batch",
            "truth_cache",
            "instrument_cache",
            "loader_eval_cache",
            "loader_behavior_state",
            "step_counters",
            "episode_accounting",
        }),
        "write_set": frozenset({
            "reward_buffer",
            "done_buffer",
            "info_buffer",
            "episode_accounting",
            "loader_behavior_state",
            "world_setup_state",
            "truth_cache",
            "instrument_cache",
            "observation_batch",
        }),
        "information_layer_consumed": ("Agent Observation",),
        "information_layer_produced": (),
        "extension_points": (),
    },
}


class TestStageContracts:
    """Structural pins on the §6.1 stage contract declarations."""

    def test_stage_names_match_frozen_set(self):
        assert BATCH_STEP_STAGE_NAMES == frozenset(
            stage.name for stage in BATCH_STEP_STAGES
        )

    def test_expected_stage_sequence(self):
        assert [stage.name for stage in BATCH_STEP_STAGES] == [
            "action_prepare",
            "physics_step",
            "state_read",
            "behavior_update",
            "command_sync",
            "observation_build",
            "flight_shaping",
            "reward_episode",
        ]

    def test_declared_pin_covers_every_stage(self):
        assert set(_EXPECTED_STAGE_PINS) == {
            stage.name for stage in BATCH_STEP_STAGES
        }

    @pytest.mark.parametrize(
        "stage", BATCH_STEP_STAGES, ids=[s.name for s in BATCH_STEP_STAGES]
    )
    def test_stage_full_pin(self, stage: StageContract):
        pin = _EXPECTED_STAGE_PINS[stage.name]
        assert stage.semantic_stages == pin["semantic_stages"]
        assert stage.read_set == pin["read_set"]
        assert stage.write_set == pin["write_set"]
        assert stage.information_layer_consumed == pin["information_layer_consumed"]
        assert stage.information_layer_produced == pin["information_layer_produced"]
        assert stage.extension_points == pin["extension_points"]

    @pytest.mark.parametrize(
        "stage", BATCH_STEP_STAGES, ids=[s.name for s in BATCH_STEP_STAGES]
    )
    def test_semantic_stages_use_authoritative_vocabulary(self, stage: StageContract):
        assert stage.semantic_stages, f"stage {stage.name} declares no semantic stage"
        for semantic_stage in stage.semantic_stages:
            assert semantic_stage in _AUTHORITATIVE_SEMANTIC_STAGES, (
                f"stage {stage.name} uses non-authoritative semantic stage "
                f"{semantic_stage!r}"
            )
        for sub_stage in stage.sub_graph:
            for semantic_stage in sub_stage.semantic_stages:
                assert semantic_stage in _AUTHORITATIVE_SEMANTIC_STAGES, (
                    f"sub-stage {sub_stage.name} uses non-authoritative "
                    f"semantic stage {semantic_stage!r}"
                )

    @pytest.mark.parametrize(
        "stage", BATCH_STEP_STAGES, ids=[s.name for s in BATCH_STEP_STAGES]
    )
    def test_information_layers_use_authoritative_vocabulary(self, stage: StageContract):
        for layer in (
            *stage.information_layer_consumed,
            *stage.information_layer_produced,
        ):
            assert layer in _AUTHORITATIVE_INFORMATION_LAYERS, (
                f"stage {stage.name} uses non-authoritative information layer "
                f"{layer!r}"
            )

    @pytest.mark.parametrize(
        "stage", BATCH_STEP_STAGES, ids=[s.name for s in BATCH_STEP_STAGES]
    )
    def test_every_stage_declares_clock_domain(self, stage: StageContract):
        assert stage.clock_domain.strip(), f"stage {stage.name} has no clock_domain"
        for sub_stage in stage.sub_graph:
            assert sub_stage.clock_domain.strip(), (
                f"sub-stage {sub_stage.name} has no clock_domain"
            )

    def test_stage_contracts_are_frozen(self):
        for stage in BATCH_STEP_STAGES:
            with pytest.raises(AttributeError):
                stage.name = "mutated"  # type: ignore[misc]

    def test_reward_episode_declares_autoreset_sub_stage(self):
        reward = next(s for s in BATCH_STEP_STAGES if s.name == "reward_episode")
        sub_names = [sub.name for sub in reward.sub_graph]
        assert sub_names == ["post_launch_assessment", "episode_autoreset"]
        autoreset = reward.sub_graph[1]
        assert "P1 WorldSetup" in autoreset.semantic_stages
        assert "world_setup_state" in autoreset.write_set

    def test_observation_build_declares_visual_refresh_sub_stage(self):
        obs_stage = next(
            s for s in BATCH_STEP_STAGES if s.name == "observation_build"
        )
        assert [sub.name for sub in obs_stage.sub_graph] == ["visual_refresh"]
        assert isinstance(obs_stage.sub_graph[0], SubStage)

    def test_data_flow_action_prepare_to_physics(self):
        action_prepare = next(
            s for s in BATCH_STEP_STAGES if s.name == "action_prepare"
        )
        physics = next(s for s in BATCH_STEP_STAGES if s.name == "physics_step")
        assert action_prepare.write_set & physics.read_set


class TestStageAnchorsInStepWait:
    """The declared stages must be anchored in WorldBatchVecEnv.step_wait."""

    def _step_wait_anchors(self) -> list[str]:
        from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv

        source = inspect.getsource(WorldBatchVecEnv.step_wait)
        return re.findall(r"#\s*\[stage:([a-z_]+)\]", source)

    def test_anchor_sequence_matches_declared_stage_order(self):
        anchors = self._step_wait_anchors()
        assert anchors == [stage.name for stage in BATCH_STEP_STAGES]

    def test_anchors_are_unique(self):
        anchors = self._step_wait_anchors()
        assert len(anchors) == len(set(anchors))


class TestExtensionPointValidation:
    """Import-time consistency between stage contracts and plugin hooks."""

    def test_module_level_validation_passes(self):
        validate_stage_extension_points(
            BATCH_STEP_STAGES, ExecutionModePlugin.stage_bindings,
        )

    def test_stage_bindings_cover_every_declared_extension_point(self):
        declared = {
            point
            for stage in BATCH_STEP_STAGES
            for point in stage.extension_points
        }
        bound = {
            f"execution_mode_plugin.{hook}"
            for hook in ExecutionModePlugin.stage_bindings
        }
        assert declared == bound

    def test_validation_rejects_unbound_extension_point(self):
        bad_stage = StageContract(
            name="behavior_update",
            semantic_stages=("P2 TaskingIntent",),
            read_set=frozenset({"x"}),
            write_set=frozenset({"y"}),
            clock_domain="outer_step",
            information_layer_consumed=(),
            information_layer_produced=(),
            extension_points=("execution_mode_plugin.not_a_hook",),
        )
        with pytest.raises(ValueError, match="do not match plugin"):
            validate_stage_extension_points(
                (bad_stage,),
                {"update_post_step_behavior": "behavior_update"},
            )

    def test_validation_rejects_binding_to_undeclared_stage(self):
        with pytest.raises(ValueError, match="undeclared stages"):
            validate_stage_extension_points(
                BATCH_STEP_STAGES,
                {"update_post_step_behavior": "no_such_stage"},
            )

    def test_validation_rejects_missing_hook(self):
        stage = StageContract(
            name="behavior_update",
            semantic_stages=("P2 TaskingIntent",),
            read_set=frozenset({"x"}),
            write_set=frozenset({"y"}),
            clock_domain="outer_step",
            information_layer_consumed=(),
            information_layer_produced=(),
            extension_points=("execution_mode_plugin.ghost_hook",),
        )
        with pytest.raises(ValueError, match="missing hooks"):
            validate_stage_extension_points(
                (stage,), {"ghost_hook": "behavior_update"},
            )


class TestExecutionModeRegistry:
    """Registry semantics: registration, resolution, duplicate rejection."""

    def test_all_three_modes_registered(self):
        modes = registered_execution_modes()
        for name in ("cooperative", "execution", "leader"):
            assert name in modes

    def test_resolve_execution_mode(self):
        plugin = resolve_execution_mode("execution")
        assert isinstance(plugin, StandardExecutionPlugin)
        assert plugin.mode_name == "execution"

    def test_resolve_cooperative_plugin(self):
        plugin = resolve_execution_mode("cooperative")
        assert isinstance(plugin, CooperativePlugin)
        assert isinstance(plugin, ExecutionModePlugin)
        assert plugin.mode_name == "cooperative"

    def test_resolve_leader_plugin(self):
        plugin = resolve_execution_mode("leader")
        assert isinstance(plugin, LeaderPlugin)
        assert isinstance(plugin, ExecutionModePlugin)
        assert plugin.mode_name == "leader"

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError, match="unknown execution mode"):
            resolve_execution_mode("nonexistent_mode")

    def test_duplicate_registration_raises(self):
        with pytest.raises(ValueError, match="already registered"):
            register_execution_mode("execution", lambda: StandardExecutionPlugin())

    def test_registered_modes_sorted(self):
        modes = registered_execution_modes()
        assert modes == sorted(modes)


class _FakeLoader:
    def __init__(self, calls):
        self._calls = calls

    def update_behaviors(self, sim_time, *, truth, inst, sync_to_kernel):
        self._calls.append(("update_behaviors", sim_time, truth, inst, sync_to_kernel))

    def update_command_chain_only(self, sim_time, *, truth, inst, sync_to_kernel):
        self._calls.append(
            ("update_command_chain_only", sim_time, truth, inst, sync_to_kernel)
        )


class _FakeHandle:
    def __init__(self, calls, last_truth="truth_after"):
        self.loader = _FakeLoader(calls)
        self.last_truth = last_truth


class TestStandardExecutionPlugin:
    """StandardExecutionPlugin behavior parity with the pre-extraction code."""

    def test_default_skip_post_behavior_sync_is_false(self):
        plugin = StandardExecutionPlugin(
            execution_episode_controller_mainline=False,
        )
        assert plugin.skip_post_behavior_command_sync is False

    def test_mainline_skip_post_behavior_sync_is_true(self):
        plugin = StandardExecutionPlugin(
            execution_episode_controller_mainline=True,
        )
        assert plugin.skip_post_behavior_command_sync is True

    def test_update_post_step_standard_calls_update_behaviors(self):
        calls = []
        plugin = StandardExecutionPlugin(execution_episode_controller_mainline=False)
        plugin.update_post_step_behavior(_FakeHandle(calls), 1.0, "truth", "inst")
        assert [call[0] for call in calls] == ["update_behaviors"]

    def test_update_post_step_mainline_calls_command_chain_only(self):
        calls = []
        plugin = StandardExecutionPlugin(execution_episode_controller_mainline=True)
        plugin.update_post_step_behavior(_FakeHandle(calls), 1.0, "truth", "inst")
        assert [call[0] for call in calls] == ["update_command_chain_only"]

    def test_hybrid_requires_injected_finalizer(self):
        with pytest.raises(ValueError, match="air_combat_event_finalizer"):
            StandardExecutionPlugin(is_air_combat_hybrid=True)

    def test_hybrid_finalizer_called_when_truth_before_is_none(self):
        # Parity pin: the pre-extraction inline code called
        # finalize_air_combat_event_action_info unconditionally for hybrid
        # action modes; the finalizer itself handles truth_before=None.
        finalizer = mock.Mock()
        plugin = StandardExecutionPlugin(
            is_air_combat_hybrid=True,
            air_combat_event_finalizer=finalizer,
        )
        handle = _FakeHandle([], last_truth="truth_after")
        plugin.finalize_post_step_truth(0, handle, None)
        assert finalizer.call_count == 1
        finalizer.assert_called_once_with(
            handle.loader, truth_before=None, truth_after="truth_after",
        )

    def test_hybrid_finalizer_called_with_truth_before(self):
        finalizer = mock.Mock()
        plugin = StandardExecutionPlugin(
            is_air_combat_hybrid=True,
            air_combat_event_finalizer=finalizer,
        )
        handle = _FakeHandle([], last_truth="truth_after")
        plugin.finalize_post_step_truth(3, handle, "truth_before")
        finalizer.assert_called_once_with(
            handle.loader, truth_before="truth_before", truth_after="truth_after",
        )

    def test_non_hybrid_finalizer_not_called(self):
        finalizer = mock.Mock()
        plugin = StandardExecutionPlugin(
            is_air_combat_hybrid=False,
            air_combat_event_finalizer=finalizer,
        )
        plugin.finalize_post_step_truth(0, _FakeHandle([]), "truth_before")
        finalizer.assert_not_called()

    def test_plugin_resolved_via_registry_with_kwargs(self):
        finalizer = mock.Mock()
        plugin = resolve_execution_mode(
            "execution",
            execution_episode_controller_mainline=True,
            is_air_combat_hybrid=True,
            air_combat_event_finalizer=finalizer,
        )
        assert isinstance(plugin, StandardExecutionPlugin)
        assert plugin.skip_post_behavior_command_sync is True
        assert plugin._air_combat_event_finalizer is finalizer


class TestExecutionModePluginBase:
    """Base class default behavior."""

    def test_default_skip_post_behavior_is_false(self):
        plugin = ExecutionModePlugin()
        assert plugin.skip_post_behavior_command_sync is False

    def test_default_update_post_step_calls_update_behaviors(self):
        calls = []
        plugin = ExecutionModePlugin()
        plugin.update_post_step_behavior(_FakeHandle(calls), 1.0, "t", "i")
        assert [call[0] for call in calls] == ["update_behaviors"]

    def test_default_finalize_post_step_truth_is_noop(self):
        plugin = ExecutionModePlugin()
        plugin.finalize_post_step_truth(0, None, None)


class TestCooperativePlugin:
    """CooperativePlugin: wired production consumer in CooperativeWorldBatchVecEnv."""

    def test_mode_name(self):
        plugin = CooperativePlugin()
        assert plugin.mode_name == "cooperative"

    def test_skip_post_behavior_sync_is_false(self):
        plugin = CooperativePlugin()
        assert plugin.skip_post_behavior_command_sync is False

    def test_update_post_step_calls_update_behaviors(self):
        calls = []
        plugin = CooperativePlugin()
        plugin.update_post_step_behavior(_FakeHandle(calls), 1.0, "t", "i")
        assert [call[0] for call in calls] == ["update_behaviors"]

    def test_finalize_post_step_truth_is_noop(self):
        plugin = CooperativePlugin()
        plugin.finalize_post_step_truth(0, None, None)

    def test_resolved_via_registry(self):
        plugin = resolve_execution_mode("cooperative")
        assert isinstance(plugin, CooperativePlugin)
        assert plugin.mode_name == "cooperative"

    def test_cooperative_vec_env_stores_plugin_at_construction(self):
        """Verify CooperativeWorldBatchVecEnv resolves the plugin at construction."""
        from python.rl.runtime.cooperative_world_batch_vec_env import (
            CooperativeWorldBatchVecEnv,
        )
        assert hasattr(CooperativeWorldBatchVecEnv, "__init__")
        import inspect
        source = inspect.getsource(CooperativeWorldBatchVecEnv.__init__)
        assert 'resolve_execution_mode("cooperative")' in source
        assert "_mode_plugin" in source

    def test_cooperative_step_wait_routes_through_plugin(self):
        """Verify the step_wait pipeline uses _mode_plugin.update_post_step_behavior."""
        from python.rl.runtime.cooperative_world_batch_vec_env import (
            CooperativeWorldBatchVecEnv,
        )
        import inspect
        source = inspect.getsource(CooperativeWorldBatchVecEnv.step_wait) + inspect.getsource(
            CooperativeWorldBatchVecEnv._step_wait_refresh_state_and_behavior
        )
        assert "_mode_plugin.update_post_step_behavior(" in source
        assert "_mode_plugin.skip_post_behavior_command_sync" in source


class TestLeaderPlugin:
    """LeaderPlugin: wired production consumer in LeaderWorldBatchExecutionRuntimeGroup."""

    def test_mode_name(self):
        plugin = LeaderPlugin()
        assert plugin.mode_name == "leader"

    def test_skip_post_behavior_sync_is_false(self):
        plugin = LeaderPlugin()
        assert plugin.skip_post_behavior_command_sync is False

    def test_update_post_step_calls_update_behaviors(self):
        calls = []
        plugin = LeaderPlugin()
        plugin.update_post_step_behavior(_FakeHandle(calls), 1.0, "t", "i")
        assert [call[0] for call in calls] == ["update_behaviors"]

    def test_finalize_post_step_truth_is_noop(self):
        plugin = LeaderPlugin()
        plugin.finalize_post_step_truth(0, None, None)

    def test_resolved_via_registry(self):
        plugin = resolve_execution_mode("leader")
        assert isinstance(plugin, LeaderPlugin)
        assert plugin.mode_name == "leader"

    def test_leader_group_stores_plugin_at_construction(self):
        """Verify LeaderWorldBatchExecutionRuntimeGroup resolves the plugin."""
        from python.rl.runtime.leader_world_batch_runtime import (
            LeaderWorldBatchExecutionRuntimeGroup,
        )
        import inspect
        source = inspect.getsource(LeaderWorldBatchExecutionRuntimeGroup.__init__)
        assert 'resolve_execution_mode("leader")' in source
        assert "_mode_plugin" in source

    def test_leader_step_indices_routes_through_plugin(self):
        """Verify step_indices uses _mode_plugin.update_post_step_behavior."""
        from python.rl.runtime.leader_world_batch_runtime import (
            LeaderWorldBatchExecutionRuntimeGroup,
        )
        import inspect
        source = inspect.getsource(LeaderWorldBatchExecutionRuntimeGroup.step_indices)
        assert "_mode_plugin.update_post_step_behavior(" in source
        assert "_mode_plugin.skip_post_behavior_command_sync" in source


class TestCoreLayeringAndHotPath:
    """G2 layering and hot-path guarantees for core.py."""

    def test_core_module_has_no_gym_envs_import_nodes(self):
        tree = ast.parse(_CORE_PATH.read_text(encoding="utf-8"))
        offending: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] == "gym_envs":
                        offending.append(f"import {alias.name} (line {node.lineno})")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.split(".")[0] == "gym_envs":
                    offending.append(f"from {module} import ... (line {node.lineno})")
        assert not offending, (
            "core.py must not import gym_envs (G2 one-way layer rings); "
            f"domain callables are injected at plugin construction: {offending}"
        )

    def test_shared_ops_module_has_no_gym_envs_import_nodes(self):
        shared_ops_path = _CORE_PATH.parent / "_shared_ops.py"
        tree = ast.parse(shared_ops_path.read_text(encoding="utf-8"))
        offending: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] == "gym_envs":
                        offending.append(f"import {alias.name} (line {node.lineno})")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.split(".")[0] == "gym_envs":
                    offending.append(f"from {module} import ... (line {node.lineno})")
        assert not offending, (
            "_shared_ops.py must not import gym_envs (G2 discipline); "
            f"found: {offending}"
        )

    @pytest.mark.parametrize(
        "hook",
        [
            StandardExecutionPlugin.finalize_post_step_truth,
            StandardExecutionPlugin.update_post_step_behavior,
            StandardExecutionPlugin.skip_post_behavior_command_sync.fget,
            ExecutionModePlugin.update_post_step_behavior,
            ExecutionModePlugin.finalize_post_step_truth,
            ExecutionModePlugin.skip_post_behavior_command_sync.fget,
        ],
        ids=[
            "standard.finalize_post_step_truth",
            "standard.update_post_step_behavior",
            "standard.skip_post_behavior_command_sync",
            "base.update_post_step_behavior",
            "base.finalize_post_step_truth",
            "base.skip_post_behavior_command_sync",
        ],
    )
    def test_hot_path_hooks_contain_no_import_opcodes(self, hook):
        opnames = {instruction.opname for instruction in dis.get_instructions(hook)}
        assert "IMPORT_NAME" not in opnames
        assert "IMPORT_FROM" not in opnames

    def test_shared_ops_diff_function_no_import_opcodes(self):
        from python.rl.runtime.world_batch._shared_ops import diff_single_entity_command_chain
        opnames = {instruction.opname for instruction in dis.get_instructions(diff_single_entity_command_chain)}
        assert "IMPORT_NAME" not in opnames
        assert "IMPORT_FROM" not in opnames

    def test_shared_ops_submit_function_no_import_opcodes(self):
        from python.rl.runtime.world_batch._shared_ops import submit_command_chain_assignments
        opnames = {instruction.opname for instruction in dis.get_instructions(submit_command_chain_assignments)}
        assert "IMPORT_NAME" not in opnames
        assert "IMPORT_FROM" not in opnames

    def test_shared_ops_assemble_observation_no_import_opcodes(self):
        from python.rl.runtime.world_batch._shared_ops import assemble_observation_dict
        opnames = {instruction.opname for instruction in dis.get_instructions(assemble_observation_dict)}
        assert "IMPORT_NAME" not in opnames
        assert "IMPORT_FROM" not in opnames

    @pytest.mark.parametrize(
        "plugin_cls",
        [CooperativePlugin, LeaderPlugin],
        ids=["cooperative", "leader"],
    )
    def test_cooperative_and_leader_hooks_inherit_base_class(self, plugin_cls):
        """Cooperative/Leader hooks are base-class inherited (no override);
        dis coverage on ExecutionModePlugin hooks applies transitively."""
        for hook_name in ("update_post_step_behavior", "finalize_post_step_truth"):
            assert getattr(plugin_cls, hook_name) is getattr(
                ExecutionModePlugin, hook_name
            ), f"{plugin_cls.__name__}.{hook_name} must not override base class"
        assert (
            plugin_cls.skip_post_behavior_command_sync.fget
            is ExecutionModePlugin.skip_post_behavior_command_sync.fget
        )


class TestCooperativePluginBehaviorEquivalence:
    """Mock self-proof: cooperative hook is called with correct arguments."""

    def test_update_post_step_behavior_called_per_slot(self):
        """Prove the cooperative step_wait pipeline calls the plugin hook per slot."""
        from python.rl.runtime.cooperative_world_batch_vec_env import (
            CooperativeWorldBatchVecEnv,
        )
        import inspect
        source = inspect.getsource(CooperativeWorldBatchVecEnv._step_wait_refresh_state_and_behavior)
        assert "self._mode_plugin.update_post_step_behavior(" in source
        assert "slot_state, sim_time, slot_state.last_truth, slot_state.last_inst" in source

    def test_cooperative_plugin_hook_semantic_equivalence(self):
        """Prove that the plugin hook reproduces the pre-wiring inline behavior."""
        calls = []
        plugin = CooperativePlugin()

        class _SlotLikeHandle:
            def __init__(self):
                self.loader = _FakeLoader(calls)

        handle = _SlotLikeHandle()
        plugin.update_post_step_behavior(handle, 2.5, "truth_val", "inst_val")
        assert len(calls) == 1
        assert calls[0] == ("update_behaviors", 2.5, "truth_val", "inst_val", False)

    def test_cooperative_plugin_skip_sync_false_gates_command_sync(self):
        """Prove the plugin gate does not suppress the command-chain sync."""
        plugin = CooperativePlugin()
        assert plugin.skip_post_behavior_command_sync is False

    def test_cooperative_plugin_finalize_not_called_in_step(self):
        """Cooperative rejects hybrid; finalize_post_step_truth is not routed."""
        from python.rl.runtime.cooperative_world_batch_vec_env import (
            CooperativeWorldBatchVecEnv,
        )
        import inspect
        source = inspect.getsource(CooperativeWorldBatchVecEnv.step_wait)
        assert "finalize_post_step_truth" not in source


class TestLeaderPluginBehaviorEquivalence:
    """Mock self-proof: leader hook is called with correct arguments."""

    def test_update_post_step_behavior_called_per_env(self):
        """Prove the leader step_indices calls the plugin hook per env."""
        from python.rl.runtime.leader_world_batch_runtime import (
            LeaderWorldBatchExecutionRuntimeGroup,
        )
        import inspect
        source = inspect.getsource(
            LeaderWorldBatchExecutionRuntimeGroup.step_indices
        )
        assert "self._mode_plugin.update_post_step_behavior(" in source
        assert "handle, sim_time, handle.last_truth, handle.last_inst" in source

    def test_leader_plugin_hook_semantic_equivalence(self):
        """Prove that the plugin hook reproduces the pre-wiring inline behavior."""
        calls = []
        plugin = LeaderPlugin()
        handle = _FakeHandle(calls)
        plugin.update_post_step_behavior(handle, 3.0, "t", "i")
        assert len(calls) == 1
        assert calls[0] == ("update_behaviors", 3.0, "t", "i", False)

    def test_leader_plugin_skip_sync_false(self):
        """Leader always syncs command chain after behavior update."""
        plugin = LeaderPlugin()
        assert plugin.skip_post_behavior_command_sync is False
