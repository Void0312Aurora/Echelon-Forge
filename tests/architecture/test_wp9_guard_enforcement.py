from __future__ import annotations

import ast
import subprocess
import tempfile
import textwrap
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_EVIDENCE_DOC_CANDIDATES = (
    REPO_ROOT
    / "docs"
    / "task"
    / "simulation_architecture"
    / "wp9_contract_infrastructure_closure"
    / "wp9_guard_allowlist_evidence_20260520.md",
    REPO_ROOT
    / "docs"
    / "task"
    / "simulation_architecture"
    / "archive"
    / "wp9_contract_infrastructure_closure"
    / "wp9_guard_allowlist_evidence_20260520.md",
)

# The allowlist stays explicit and label-driven so the guard can distinguish
# compatibility-only bridges, diagnostics-only evidence, and test-only fixtures.
SIM_DIRECT_ACCESS_ALLOWLIST = {
    "compatibility_only": {
        "files": {
            "python/rl/control/wrappers.py",
            "python/rl/runtime/cooperative_world_batch_vec_env.py",
            "python/rl/runtime/leader_world_batch_runtime.py",
            "python/rl/runtime/single_world_batch_runtime.py",
            "python/rl/runtime/world_batch/cooperative_director.py",
            "python/rl/runtime/world_batch/runtime_access.py",
            "python/rl/runtime/world_batch_vec_env.py",
            "python/rl/tasking/bridge.py",
            "python/rl/tasking/leader_tasking.py",
            "python/scenario/runtime/kernel_apply.py",
            "game/backend/app.py",
        },
        "prefixes": {
            "gym_envs/",
            "game/backend/",
        },
    },
    "diagnostics_only": {
        "prefixes": {
            "python/testing/contracts/",
            "examples/viz/runtime/",
            "tools/diagnostics/",
            "tools/eval/",
        },
        "files": {
            "world_model_train.py",
        },
    },
    "test_only": {
        "prefixes": {
            "tests/",
        },
    },
}

LEGACY_COMMAND_DIRECT_INCLUDE_ALLOWLIST = {
    "src/components/command/air/control_input_resolution.h",
    "src/components/command/command_link.h",
    "src/components/command/default_factory_legacy_spawn_compat.h",
    "src/components/physics/action.h",
    "src/systems/core/operation_system.h",
}

AIR_CONTROL_BRIDGE_HEADER = (
    REPO_ROOT / "src" / "components" / "command" / "air" / "control_input_resolution.h"
)
COMMAND_README_EN = REPO_ROOT / "src" / "components" / "command" / "README.md"
COMMAND_README_ZH = REPO_ROOT / "src" / "components" / "command" / "README.zh.md"
MISSION_COMMAND_HEADER = REPO_ROOT / "src" / "components" / "command" / "mission_command.h"
LEGACY_COMMAND_HEADER = REPO_ROOT / "src" / "components" / "command" / "legacy_command.h"
COMMAND_LINK_HEADER = REPO_ROOT / "src" / "components" / "command" / "command_link.h"
LEGACY_COMMAND_BRIDGE_HEADER = (
    REPO_ROOT / "src" / "components" / "command" / "legacy_command_bridge.h"
)
OPERATION_SYSTEM_HEADER = REPO_ROOT / "src" / "systems" / "core" / "operation_system.h"
SIMULATION_KERNEL_COMMAND_API = (
    REPO_ROOT / "src" / "core" / "engine" / "simulation_kernel_command_api.cpp"
)
DEFAULT_UNIT_FACTORY_HEADER = (
    REPO_ROOT / "src" / "models" / "core" / "default_unit_factory.h"
)
DEFAULT_FACTORY_LEGACY_SEED_HELPER_HEADER = (
    REPO_ROOT / "src" / "components" / "command" / "default_factory_legacy_spawn_compat.h"
)
WP22_COMMAND_RETIREMENT_DOC_EN = (
    REPO_ROOT
    / "docs"
    / "task"
    / "simulation_architecture"
    / "wp22_legacy_compatibility_retirement"
    / "wp22_command_dto_legacy_surface_retirement_cluster_20260522.md"
)
WP22_COMMAND_RETIREMENT_DOC_ZH = (
    REPO_ROOT
    / "docs"
    / "task"
    / "simulation_architecture"
    / "wp22_legacy_compatibility_retirement"
    / "wp22_command_dto_legacy_surface_retirement_cluster_20260522.zh.md"
)


def _iter_python_files() -> list[Path]:
    excluded_prefixes = (".git", ".venv", "__pycache__", "build", "dist", "node_modules", "archive", "temp")
    return [
        path
        for path in sorted(REPO_ROOT.rglob("*.py"))
        if not any(part.startswith(excluded_prefixes) for part in path.parts)
    ]


def _attribute_chain(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Attribute):
        return _attribute_chain(node.value) + [node.attr]
    if isinstance(node, ast.Call):
        return _attribute_chain(node.func)
    if isinstance(node, ast.Name):
        return [node.id]
    return []


def _sim_access_lines(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            chain = _attribute_chain(node)
            if len(chain) > 1 and "sim" in chain:
                lines.append(int(getattr(node, "lineno", 0) or 0))
    return sorted(set(line for line in lines if line > 0))


def _label_for_path(relative_path: str) -> str | None:
    for label, spec in SIM_DIRECT_ACCESS_ALLOWLIST.items():
        if relative_path in spec.get("files", set()):
            return label
    for label, spec in SIM_DIRECT_ACCESS_ALLOWLIST.items():
        for prefix in spec.get("prefixes", set()):
            if relative_path.startswith(prefix):
                return label
    return None


def _iter_cpp_headers() -> list[Path]:
    excluded_prefixes = (".git", ".venv", "__pycache__", "build", "dist", "node_modules", "archive", "temp")
    return [
        path
        for path in sorted(REPO_ROOT.joinpath("src").rglob("*.h"))
        if not any(part.startswith(excluded_prefixes) for part in path.parts)
    ]


def _allowlist_evidence_doc() -> Path:
    for candidate in ALLOWLIST_EVIDENCE_DOC_CANDIDATES:
        if candidate.is_file():
            return candidate
    return ALLOWLIST_EVIDENCE_DOC_CANDIDATES[0]


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    binary = (
        Path(tempfile.gettempdir())
        / f"wp22_legacy_command_guard_bin_{uuid.uuid4().hex}"
    )
    include_args = [
        "-I",
        str(REPO_ROOT / "src"),
    ]
    for flecs_candidate in (
        REPO_ROOT / "build-workshop" / "_deps" / "flecs-src" / "include",
        REPO_ROOT / "build" / "_deps" / "flecs-src" / "include",
        REPO_ROOT / "build-workshop" / "_deps" / "flecs-src",
        REPO_ROOT / "build" / "_deps" / "flecs-src",
        ):
        if (flecs_candidate / "flecs.h").is_file():
            include_args.extend(["-I", str(flecs_candidate)])
            break
    link_args: list[str] = []
    for flecs_lib_dir in (
        REPO_ROOT / "build-workshop" / "_deps" / "flecs-build",
        REPO_ROOT / "build" / "_deps" / "flecs-build",
    ):
        if (flecs_lib_dir / "libflecs_static.a").is_file():
            link_args.extend([str(flecs_lib_dir / "libflecs_static.a")])
            break
        if (flecs_lib_dir / "libflecs.so").is_file():
            link_args.extend([
                "-L",
                str(flecs_lib_dir),
                "-lflecs",
                f"-Wl,-rpath,{flecs_lib_dir}",
            ])
            break
    compile_result = subprocess.run(
        [
            "g++",
            "-std=c++20",
            *include_args,
            "-x",
            "c++",
            "-",
            "-x",
            "none",
            "-o",
            str(binary),
            *link_args,
        ],
        input=source,
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    return subprocess.run(
        [str(binary)],
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_direct_sim_access_is_limited_to_explicitly_labeled_allowlists() -> None:
    hits: dict[str, tuple[str, list[int]]] = {}

    for path in _iter_python_files():
        lines = _sim_access_lines(path)
        if not lines:
            continue

        relative_path = str(path.relative_to(REPO_ROOT))
        label = _label_for_path(relative_path)
        if label is None:
            hits[relative_path] = ("unlabeled", lines)
            continue

        hits[relative_path] = (label, lines)

    violations = {
        path: lines
        for path, (label, lines) in hits.items()
        if label == "unlabeled"
    }
    assert not violations, f"direct sim access without allowlist labels: {violations}"

    used_labels = {label for label, _ in hits.values() if label != "unlabeled"}
    assert used_labels == set(SIM_DIRECT_ACCESS_ALLOWLIST), (
        "allowlist labels should be exercised by live direct sim access files; "
        f"got {sorted(used_labels)}"
    )

    for label, spec in SIM_DIRECT_ACCESS_ALLOWLIST.items():
        assert spec.get("files", set()) or spec.get("prefixes", set()), f"empty allowlist for {label}"


def test_wp9_guard_allowlist_evidence_doc_matches_the_explicit_labels() -> None:
    doc_path = _allowlist_evidence_doc()
    assert doc_path.is_file(), "wp9 guard allowlist evidence doc is missing from both active and archived locations"
    text = doc_path.read_text(encoding="utf-8")

    for label in ("compatibility_only", "diagnostics_only", "test_only"):
        assert label in text

    for path in (
        "python/rl/runtime/world_batch/runtime_access.py",
        "python/testing/contracts/",
        "tests/",
    ):
        assert path in text

    assert "python/rl/tasking/bridge.py" in SIM_DIRECT_ACCESS_ALLOWLIST["compatibility_only"]["files"]


def test_wp22_legacy_command_direct_include_allowlist_stays_explicit() -> None:
    actual = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in _iter_cpp_headers()
        if '#include "components/command/legacy_command.h"' in path.read_text(encoding="utf-8")
    }
    assert actual == LEGACY_COMMAND_DIRECT_INCLUDE_ALLOWLIST, (
        "legacy_command.h direct includes drifted outside the explicit compatibility/bridge "
        f"allowlist: {sorted(actual)}"
    )


def test_wp22_legacy_command_allowlist_entries_remain_named_owner_bound_blockers() -> None:
    command_link_text = COMMAND_LINK_HEADER.read_text(encoding="utf-8")
    operation_text = OPERATION_SYSTEM_HEADER.read_text(encoding="utf-8")
    default_factory_text = DEFAULT_UNIT_FACTORY_HEADER.read_text(encoding="utf-8")
    default_factory_helper_text = DEFAULT_FACTORY_LEGACY_SEED_HELPER_HEADER.read_text(encoding="utf-8")
    command_link_system_text = (
        REPO_ROOT / "src" / "systems" / "systems" / "command_link_system.h"
    ).read_text(encoding="utf-8")

    assert '#include "components/command/legacy_command.h"' in command_link_text
    assert "PendingMovementCommand" in command_link_text
    assert "PendingMissionControlCommand" in command_link_text
    assert "PendingActionCommand" in command_link_text
    assert "PendingMissionCommand" in command_link_text
    assert "Diagnostics transport shell only; maintained delivery must consume typed_command." in command_link_text
    assert "refresh_pending_movement_command_diagnostics_shell(" in command_link_text
    assert "typed_air_control_bridge" in command_link_text
    assert "Bridge-owned typed overlay snapshot only." in command_link_text
    assert "refresh_pending_action_command_typed_air_control_bridge(" in command_link_text
    assert "Quarantined legacy action transport shell: no lossless typed replacement yet." in command_link_text

    assert '#include "components/command/legacy_command.h"' in operation_text
    assert "Compatibility bridge seam" in operation_text
    assert "register_action_mapping_system" in operation_text
    assert "register_command_lag_system" in operation_text
    assert "MovementCommand remains a compatibility mirror here" in operation_text
    assert "LaggedCommand remains a compatibility mirror here" in operation_text
    assert '.term_at(1).optional()' in operation_text
    assert "make_compatibility_control_state_seed(" in operation_text
    assert "refresh_optional_compatibility_autopilot_movement_command_from_control_state(" in operation_text
    assert "refresh_optional_compatibility_lagged_command_mirror_from_control_state(" in operation_text
    for forbidden in (
        "operation_seed_movement_command(",
        "operation_seed_lagged_command(",
        "refresh_compatibility_movement_command_from_control_state(",
        "refresh_compatibility_lagged_command_from_control_state(",
    ):
        assert forbidden not in operation_text, (
            "operation_system must consume bridge-owned compatibility mirror seed/refresh "
            "helpers instead of reintroducing local legacy mirror logic"
        )

    assert '#include "components/command/legacy_command.h"' in default_factory_helper_text
    for token in (
        "struct SpawnCompatibilityControlStateSeed",
        "using SpawnCompatibilityLegacyCommandSeed = SpawnCompatibilityControlStateSeed;",
        "struct SpawnCompatibilityActionCommandSeed",
        "project_spawn_compatibility_movement_command_mirror(",
        "project_spawn_compatibility_lagged_command_mirror(",
        "make_spawn_compatibility_control_state_seed(",
        "apply_spawn_compatibility_control_state_seed(",
        "apply_spawn_compatibility_action_command_seed(",
        "make_spawn_compatibility_legacy_command_seed(",
        "apply_spawn_compatibility_legacy_command_seed(",
        "Compatibility-only spawn seam for default unit factory legacy command bootstrap.",
        "MissionCommandControlState is the maintained spawn-default owner here;",
        "compatibility consumers. It is not a retired seam.",
    ):
        assert token in default_factory_helper_text
    assert "MovementCommand movement_command" not in default_factory_helper_text
    assert "LaggedCommand lagged_command" not in default_factory_helper_text

    assert '#include "components/command/default_factory_legacy_spawn_compat.h"' in default_factory_text
    assert '#include "components/command/legacy_command.h"' not in default_factory_text
    assert "default_unit_factory_detail::apply_spawn_compatibility_action_command_seed(e);" in default_factory_text
    assert "default_unit_factory_detail::apply_spawn_compatibility_control_state_seed(" in default_factory_text
    assert "default_unit_factory_detail::make_spawn_compatibility_control_state_seed(" in default_factory_text

    command_api_text = SIMULATION_KERNEL_COMMAND_API.read_text(encoding="utf-8")
    bridge_text = LEGACY_COMMAND_BRIDGE_HEADER.read_text(encoding="utf-8")

    assert '#include "components/command/legacy_command_bridge.h"' in command_api_text
    assert "set_compatibility_autopilot_control_target(" in command_api_text
    assert "ensure_mission_command_control_state(e);" in command_api_text

    set_unit_command_anchor = command_api_text.index("void SimulationKernel::set_unit_command(")
    set_unit_stick_anchor = command_api_text.index("void SimulationKernel::set_unit_stick_command(")
    set_unit_command_block = command_api_text[set_unit_command_anchor:set_unit_stick_anchor]

    assert "set_compatibility_autopilot_control_target(" in set_unit_command_block
    assert "ensure_mission_command_control_state(e);" in set_unit_command_block
    for token in (
        "e.set<MovementCommand>(make_legacy_autopilot_movement_command(",
        "e.set<LaggedCommand>(make_lagged_command(",
        "ensure_compatibility_control_mirrors(e);",
    ):
        assert token not in set_unit_command_block, (
            "command ingress must stay on the named compatibility bridge so typed state is "
            "touched without forcing legacy movement mirrors back into the maintained delayed path"
        )

    for token in (
        "Compatibility-only bridge seam for quarantined legacy command DTO consumers",
        "ensure_mission_command_control_state(",
        "set_compatibility_autopilot_control_target(",
        "refresh_compatibility_typed_air_control_from_action_command(",
        "refresh_optional_compatibility_typed_air_control_from_action_command(",
        "refresh_compatibility_typed_air_control_from_pending_action_bridge(",
        "refresh_optional_pending_action_typed_air_control_bridge(",
        "refresh_compatibility_control_mirrors_from_state(",
        "refresh_optional_compatibility_autopilot_movement_command_from_control_state(",
        "refresh_optional_compatibility_lagged_command_mirror_from_control_state(",
    ):
        assert token in bridge_text

    assert "deliver_pending_movement_command(" in command_link_system_text
    assert "deliver_pending_action_command(" in command_link_system_text
    assert "pending.typed_command.control_state" in command_link_system_text
    assert "refresh_optional_pending_action_typed_air_control_bridge(" in command_link_system_text
    assert "refresh_pending_movement_command_diagnostics_shell(pending);" in command_link_system_text
    assert '.term_at(1).optional()' in command_link_system_text
    assert '.term_at(2).optional()' in command_link_system_text
    assert "MovementCommand* cmd" in command_link_system_text
    assert "LaggedCommand* lagged" in command_link_system_text
    assert "PendingActionCommand remains a quarantined legacy transport shell in this slice." in command_api_text
    for forbidden in (
        "pending[i].command.target_heading",
        "pending[i].command.target_speed",
        "pending[i].command.target_altitude",
        "deliver_pending_command(cmd[i], pending[i], current_time);",
        "queue_or_refresh_pending_command<PendingActionCommand>(",
    ):
        assert forbidden not in command_link_system_text, (
            "maintained command_link movement delivery must read typed pending control payload "
            "instead of replaying the legacy MovementCommand shell"
        )
    assert "queue_or_refresh_pending_action_command(" in command_api_text
    assert "refresh_compatibility_typed_air_control_from_action_command(" in command_api_text
    assert "refresh_pending_action_command_typed_air_control_bridge(*pending);" in command_api_text
    assert "refresh_pending_movement_command_diagnostics_shell(*pending);" in command_api_text


def test_wp22_air_control_maintained_consumers_use_single_bridge_owned_resolution_surface() -> None:
    bridge_header = AIR_CONTROL_BRIDGE_HEADER.read_text(encoding="utf-8")

    for required in (
        "Bridge-owned compatibility seam for maintained air-control consumers.",
        "struct ResolvedAirCommandInputSources",
        "struct ResolvedAirControlInput",
        "active_typed_air_control_state(",
        "MissionCommandTypedAirControlState",
        "resolve_air_command_input_sources(",
        "resolve_air_control_input(",
        "active_legacy_action_command(",
        "resolved_air_command_throttle(",
        "resolved_pilot_or_legacy_ground_control(",
    ):
        assert required in bridge_header

    maintained_consumers = {
        "src/systems/physics/force_system.h": (
            "resolve_air_control_input(",
            "control_input.has_primary_flight_control_input",
            "it.entity(i).get<MissionCommandControlState>()",
        ),
        "src/systems/physics/propulsion_system.h": (
            "resolve_air_control_input(",
            "control_input.throttle_command",
            "entity.get<MissionCommandControlState>()",
        ),
        "src/systems/physics/instrument_system.h": (
            "resolve_air_control_input(",
            "control_input.instrument_control",
            "it.entity(i).get<MissionCommandControlState>()",
        ),
        "src/systems/physics/ground_contact_system.h": (
            "resolve_air_control_input(",
            "control_input.ground_control",
            "control_input.nose_wheel_steering",
            "it.entity(i).get<MissionCommandControlState>()",
        ),
    }

    forbidden_tokens = (
        "active_legacy_movement_command(",
        "active_legacy_action_command(",
        "inputs.pilot",
        "inputs.legacy_movement",
        ".get<MovementCommand>()",
        ".get<ActionCommand>()",
    )

    for relative_path, required_tokens in maintained_consumers.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert '#include "components/command/air/control_input_resolution.h"' in text
        assert '#include "components/command/legacy_command.h"' not in text
        for token in required_tokens:
            assert token in text, f"{relative_path} drifted off the bridge-owned resolution seam"
        for token in forbidden_tokens:
            assert token not in text, (
                f"{relative_path} reintroduced ad-hoc legacy fallback probing via {token!r}"
            )


def test_wp22_embarked_air_write_path_stays_bridge_state_first() -> None:
    embarked_air_text = (
        REPO_ROOT / "src" / "systems" / "naval" / "embarked_air_ops_system.h"
    ).read_text(encoding="utf-8")
    bridge_text = LEGACY_COMMAND_BRIDGE_HEADER.read_text(encoding="utf-8")

    assert '#include "components/command/legacy_command_bridge.h"' in embarked_air_text
    assert "set_compatibility_autopilot_movement_command(" in embarked_air_text
    assert "deactivate_compatibility_movement_command(helo);" in embarked_air_text
    assert "compatibility_mutable_legacy_movement_command(" not in embarked_air_text
    assert "if (helo_move)" not in embarked_air_text
    assert "ensure_compatibility_control_mirrors(entity);" in bridge_text
    assert "refresh_compatibility_control_mirrors_from_state(entity);" in bridge_text


def test_wp22_command_docs_and_headers_mark_legacy_resolution_as_compatibility_only() -> None:
    readme_en = COMMAND_README_EN.read_text(encoding="utf-8")
    readme_zh = COMMAND_README_ZH.read_text(encoding="utf-8")
    mission_header = MISSION_COMMAND_HEADER.read_text(encoding="utf-8")
    legacy_header = LEGACY_COMMAND_HEADER.read_text(encoding="utf-8")

    assert "only as compatibility DTOs owned by explicit bridge seams" in readme_en
    assert "Ad-hoc `MovementCommand`/`ActionCommand`" in readme_en
    assert "probing inside maintained systems is not an allowed pattern." in readme_en
    assert "仅作为由显式 bridge seam 持有的 compatibility DTO" in readme_zh
    assert "maintained system 内部继续手写" in readme_zh
    assert "`MovementCommand`/`ActionCommand` 探测逻辑" in readme_zh
    assert "compatibility umbrella" in readme_en
    assert "Compatibility-only DTO surface retained for bridge-owned legacy command seams." in legacy_header
    assert "struct MissionCommand : MissionCommandCore, MissionCommandAir, MissionCommandNaval {};" in mission_header


def test_wp22_command_retirement_docs_keep_allowlist_and_default_factory_blockers_explicit() -> None:
    text_en = WP22_COMMAND_RETIREMENT_DOC_EN.read_text(encoding="utf-8")
    text_zh = WP22_COMMAND_RETIREMENT_DOC_ZH.read_text(encoding="utf-8")

    for required in (
        "Noether pass",
        "`control_input_resolution.h`, `command_link.h`, and `operation_system.h` remain named compatibility-owner seams",
        "`default_factory_legacy_spawn_compat.h` owns the remaining spawn-time legacy-command seed and still blocks closure until typed control-state replacement lands",
        "allowlist is not closure evidence",
        "replacement, owner, and failing guard",
    ):
        assert required in text_en

    for required in (
        "Noether pass",
        "`control_input_resolution.h`、`command_link.h` 与 `operation_system.h` 仍是命名的 compatibility-owner seam",
        "`default_factory_legacy_spawn_compat.h` 持有剩余 spawn-time legacy-command seed，直到 typed control-state replacement 落地前仍阻塞 closure",
        "allowlist 不是 closure evidence",
        "replacement、owner 与 failing guard",
    ):
        assert required in text_zh


def test_wp22_air_control_resolution_contract_prefers_pilot_then_legacy_then_action() -> None:
    source = textwrap.dedent(
        r"""
        #include <cmath>
        #include <iostream>
        #include "components/command/air/control_input_resolution.h"

        namespace {
        bool nearly_equal(double a, double b) {
            return std::abs(a - b) < 1.0e-9;
        }
        }

        int main() {
            PilotAction pilot{};
            pilot.throttle = 0.75;
            pilot.brake = 0.25;
            pilot.brake_left = false;
            pilot.brake_right = false;
            pilot.active = true;

            MovementCommand movement = make_legacy_stick_movement_command(
                0.1,
                -0.2,
                0.4,
                true,
                true
            );

            ActionCommand action = make_action_command(
                0.0,
                -0.4,
                0.0,
                0.0,
                false,
                false,
                false,
                false,
                0,
                0,
                0,
                true
            );

            const auto pilot_first = resolve_air_command_input_sources(&pilot, &movement, &action);
            if (!pilot_first.pilot || !pilot_first.legacy_movement || !pilot_first.legacy_action) {
                std::cerr << "expected all three sources to stay visible through the bridge\n";
                return 1;
            }
            if (!nearly_equal(resolved_air_command_throttle(pilot_first), 0.75)) {
                std::cerr << "pilot throttle should win when active\n";
                return 1;
            }

            pilot.active = false;
            const auto legacy_second = resolve_air_command_input_sources(&pilot, &movement, &action);
            if (!nearly_equal(resolved_air_command_throttle(legacy_second), 0.4)) {
                std::cerr << "legacy movement throttle should win when pilot is inactive\n";
                return 1;
            }
            const auto ground = resolved_pilot_or_legacy_ground_control(legacy_second);
            if (ground.throttle_idle || !nearly_equal(ground.brake_amount, 0.0)) {
                std::cerr << "active legacy movement with throttle should not imply braking\n";
                return 1;
            }

            movement.active = false;
            const auto action_third = resolve_air_command_input_sources(&pilot, &movement, &action);
            if (!nearly_equal(resolved_air_command_throttle(action_third), 0.3)) {
                std::cerr << "legacy action accel should map into fallback throttle\n";
                return 1;
            }

            action.active = false;
            const auto none = resolve_air_command_input_sources(&pilot, &movement, &action);
            if (!nearly_equal(resolved_air_command_throttle(none, 0.2), 0.2)) {
                std::cerr << "explicit fallback throttle should be preserved when no source is active\n";
                return 1;
            }
            if (has_resolved_primary_flight_control_input(none)) {
                std::cerr << "inactive pilot and movement should not count as primary control input\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp22_operation_and_command_link_allow_typed_control_state_without_legacy_mirrors() -> None:
    source = textwrap.dedent(
        r"""
        #include <cmath>
        #include <iostream>
        #include <flecs.h>
        #include "components/basic/common.h"
        #include "components/command/command_link.h"
        #include "components/command/common/mission_command_control_state.h"
        #include "components/command/legacy_command.h"
        #include "systems/core/operation_system.h"
        #include "systems/systems/command_link_system.h"

        namespace {
        bool nearly_equal(double a, double b) {
            return std::abs(a - b) < 1.0e-6;
        }
        }

        int main() {
            flecs::world ecs;

            ecs.component<MissionCommandControlState>();
            ecs.component<MovementCommand>();
            ecs.component<ActionCommand>();
            ecs.component<ActionSpaceConfig>();
            ecs.component<Transform>();
            ecs.component<Velocity>();
            ecs.component<CommandLag>();
            ecs.component<LaggedCommand>();
            ecs.component<PendingMovementCommand>();
            ecs.component<CommandLink>();

            register_action_mapping_system(ecs);
            register_command_lag_system(ecs);
            register_command_link_system(ecs);

            const flecs::entity entity = ecs.entity()
                .set<MissionCommandControlState>(
                    make_mission_command_control_state(10.0, 150.0, 1200.0, false)
                )
                .set<ActionCommand>(
                    make_action_command(0.5, 0.4, -0.25, 0.0, false, false, false, false, 0, 0, 0, true)
                )
                .set<ActionSpaceConfig>({30.0, 20.0, 40.0, 120.0, 260.0, 500.0, 4000.0})
                .set<Transform>({0.0, 0.0, 1100.0, 45.0, 0.0, 0.0})
                .set<Velocity>({180.0, 0.0, 0.0})
                .set<CommandLag>({0.5, 0.5, 0.5})
                .set<PendingMovementCommand>(
                    make_pending_movement_command(
                        make_pending_mission_control_command(123.0, 205.0, 1800.0, true),
                        0.0,
                        true
                    )
                )
                .set<CommandLink>({0.0, 0.0});

            ecs.progress(0.1f);

            const MissionCommandControlState* state =
                entity.get<MissionCommandControlState>();
            if (!state) {
                std::cerr << "expected typed mission command control state to remain present\n";
                return 1;
            }
            if (!state->active || !state->lagged_active) {
                std::cerr << "typed state should be active after action mapping and lag delivery\n";
                return 1;
            }
            if (!nearly_equal(state->target_heading_deg, 123.0) ||
                !nearly_equal(state->target_speed_mps, 205.0) ||
                !nearly_equal(state->target_altitude_m, 1800.0)) {
                std::cerr << "command-link delivery should land in typed control state\n";
                return 1;
            }
            if (!state->typed_air_control.action_semantics_active) {
                std::cerr << "action mapping should still update typed air-control semantics\n";
                return 1;
            }

            const PendingMovementCommand* pending = entity.get<PendingMovementCommand>();
            if (!pending || pending->active) {
                std::cerr << "pending movement command should be cleared after delivery\n";
                return 1;
            }
            if (entity.has<MovementCommand>() || entity.has<LaggedCommand>()) {
                std::cerr << "optional mirror refresh must not force-create legacy mirrors\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp22_pending_movement_delivery_ignores_corrupted_legacy_transport_shell() -> None:
    source = textwrap.dedent(
        r"""
        #include <cmath>
        #include <iostream>
        #include <flecs.h>
        #include "components/basic/common.h"
        #include "components/command/command_link.h"
        #include "components/command/common/mission_command_control_state.h"
        #include "components/command/legacy_command.h"
        #include "systems/systems/command_link_system.h"

        namespace {
        bool nearly_equal(double a, double b) {
            return std::abs(a - b) < 1.0e-6;
        }
        }

        int main() {
            flecs::world ecs;

            ecs.component<MissionCommandControlState>();
            ecs.component<MovementCommand>();
            ecs.component<LaggedCommand>();
            ecs.component<PendingMovementCommand>();
            ecs.component<CommandLink>();

            register_command_link_system(ecs);

            PendingMovementCommand pending = make_pending_movement_command(
                make_pending_mission_control_command(123.0, 205.0, 1800.0, true),
                0.0,
                true
            );
            pending.command.target_heading = 301.0;
            pending.command.target_speed = 88.0;
            pending.command.target_altitude = 4444.0;
            pending.command.active = true;

            const flecs::entity entity = ecs.entity()
                .set<MissionCommandControlState>(
                    make_mission_command_control_state(10.0, 150.0, 1200.0, false)
                )
                .set<PendingMovementCommand>(pending)
                .set<CommandLink>({0.0, 0.0});

            ecs.progress(0.1f);

            const MissionCommandControlState* state =
                entity.get<MissionCommandControlState>();
            const PendingMovementCommand* delivered_pending =
                entity.get<PendingMovementCommand>();
            if (!state || !delivered_pending) {
                std::cerr << "expected typed state and pending transport to remain addressable\n";
                return 1;
            }
            if (!nearly_equal(state->target_heading_deg, 123.0) ||
                !nearly_equal(state->target_speed_mps, 205.0) ||
                !nearly_equal(state->target_altitude_m, 1800.0)) {
                std::cerr << "movement delivery must use pending typed control state, not the legacy shell\n";
                return 1;
            }
            if (!nearly_equal(delivered_pending->command.target_heading, 123.0) ||
                !nearly_equal(delivered_pending->command.target_speed, 205.0) ||
                !nearly_equal(delivered_pending->command.target_altitude, 1800.0)) {
                std::cerr << "movement diagnostics shell should be reprojected from typed pending state\n";
                return 1;
            }
            if (delivered_pending->active) {
                std::cerr << "pending movement transport should clear after delivery\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp22_pending_action_delivery_refreshes_typed_overlay_without_claiming_full_replacement() -> None:
    source = textwrap.dedent(
        r"""
        #include <cmath>
        #include <iostream>
        #include <flecs.h>
        #include "components/command/command_link.h"
        #include "components/command/common/mission_command_control_state.h"
        #include "components/command/legacy_command.h"
        #include "systems/systems/command_link_system.h"

        namespace {
        bool nearly_equal(double a, double b) {
            return std::abs(a - b) < 1.0e-6;
        }
        }

        int main() {
            flecs::world ecs;

            ecs.component<MissionCommandControlState>();
            ecs.component<ActionCommand>();
            ecs.component<PendingActionCommand>();
            ecs.component<CommandLink>();

            register_command_link_system(ecs);

            MissionCommandControlState initial_state =
                make_mission_command_control_state(15.0, 180.0, 1400.0, true);
            MissionCommandTypedAirControlState existing_overlay{};
            existing_overlay.instrument_active = true;
            existing_overlay.flaps_pos = 0.35f;
            existing_overlay.speedbrake_pos = 0.15f;
            existing_overlay.master_arm = true;
            existing_overlay.weapon_selected = 4;
            set_mission_command_typed_air_control_state(initial_state, existing_overlay);

            ActionCommand queued = make_action_command(
                -0.7,
                0.8,
                -0.6,
                0.3,
                true,
                false,
                true,
                false,
                0,
                0,
                0,
                true
            );

            PendingActionCommand pending =
                make_pending_action_command(queued, 0.0, true);
            pending.command.accel_cmd = -1.0;
            pending.command.active = true;

            const flecs::entity entity = ecs.entity()
                .set<MissionCommandControlState>(initial_state)
                .set<ActionCommand>(make_action_command())
                .set<PendingActionCommand>(pending)
                .set<CommandLink>({0.0, 0.0});

            ecs.progress(0.1f);

            const MissionCommandControlState* state =
                entity.get<MissionCommandControlState>();
            const ActionCommand* delivered_action = entity.get<ActionCommand>();
            const PendingActionCommand* delivered_pending =
                entity.get<PendingActionCommand>();
            if (!state || !delivered_action || !delivered_pending) {
                std::cerr << "expected action command, typed state, and pending transport\n";
                return 1;
            }
            if (!nearly_equal(delivered_action->accel_cmd, -1.0)) {
                std::cerr << "legacy action shell should still deliver as the quarantined transport payload\n";
                return 1;
            }
            if (!state->typed_air_control.action_semantics_active) {
                std::cerr << "delivery should refresh the typed air-control action overlay\n";
                return 1;
            }
            if (!nearly_equal(state->typed_air_control.throttle_command, 0.9)) {
                std::cerr << "typed overlay should come from the queued bridge snapshot, not the later shell mutation\n";
                return 1;
            }
            if (!state->typed_air_control.instrument_active ||
                !nearly_equal(state->typed_air_control.flaps_pos, 0.35f) ||
                !state->typed_air_control.master_arm ||
                state->typed_air_control.weapon_selected != 4) {
                std::cerr << "pending action overlay must not wipe unrelated maintained typed fields\n";
                return 1;
            }
            if (delivered_pending->active) {
                std::cerr << "pending action transport should clear after delivery\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp22_typed_air_control_overlay_becomes_the_maintained_owner_before_legacy_fallback() -> None:
    source = textwrap.dedent(
        r"""
        #include <cmath>
        #include <iostream>
        #include "components/command/air/control_input_resolution.h"
        #include "components/command/common/mission_command_control_state.h"

        namespace {
        bool nearly_equal(double a, double b) {
            return std::abs(a - b) < 1.0e-9;
        }
        }

        int main() {
            MissionCommandControlState control_state = make_mission_command_control_state(
                90.0,
                220.0,
                1500.0,
                true
            );
            MissionCommandTypedAirControlState typed_air_control{};
            typed_air_control.throttle_command = 0.62;
            typed_air_control.throttle_active = true;
            typed_air_control.throttle_idle = false;
            typed_air_control.brake_amount = 0.4;
            typed_air_control.ground_active = true;
            typed_air_control.flaps_pos = 0.3f;
            typed_air_control.speedbrake_pos = 0.2f;
            typed_air_control.instrument_active = true;
            typed_air_control.master_arm = true;
            typed_air_control.weapon_selected = 7;
            typed_air_control.nose_wheel_yaw_command = -0.25;
            typed_air_control.nose_wheel_steering_active = true;
            set_mission_command_typed_air_control_state(control_state, typed_air_control);

            MovementCommand movement = make_legacy_stick_movement_command(
                0.1,
                -0.2,
                0.1,
                true,
                true
            );
            ActionCommand action = make_action_command(
                0.0,
                1.0,
                0.0,
                0.0,
                false,
                false,
                false,
                false,
                0,
                0,
                0,
                true
            );

            const auto resolved = resolve_air_control_input(
                nullptr,
                &control_state,
                &movement,
                &action,
                0.0
            );
            if (!resolved.has_command_control_state) {
                std::cerr << "typed control-state owner should be visible to maintained consumers\n";
                return 1;
            }
            if (!nearly_equal(resolved.throttle_command, 0.62)) {
                std::cerr << "typed control throttle should win before legacy fallback\n";
                return 1;
            }
            if (!resolved.nose_wheel_steering.available ||
                !nearly_equal(resolved.nose_wheel_steering.yaw_command, -0.25)) {
                std::cerr << "typed nose-wheel steering should be preserved\n";
                return 1;
            }
            if (!nearly_equal(resolved.ground_control.brake_amount, 0.4)) {
                std::cerr << "typed ground brake should be preserved\n";
                return 1;
            }
            if (!resolved.instrument_control.master_arm || resolved.instrument_control.weapon_selected != 7) {
                std::cerr << "typed instrument semantics should be preserved\n";
                return 1;
            }

            reset_mission_command_typed_air_control_state(control_state);
            const auto legacy_fallback = resolve_air_control_input(
                nullptr,
                &control_state,
                &movement,
                &action,
                0.0
            );
            if (!nearly_equal(legacy_fallback.throttle_command, 0.1)) {
                std::cerr << "legacy movement should resume once typed overlay is cleared\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp22_typed_air_control_overlay_stays_visible_without_active_command_target() -> None:
    source = textwrap.dedent(
        r"""
        #include <cmath>
        #include <iostream>
        #include "components/command/air/control_input_resolution.h"
        #include "components/command/common/mission_command_control_state.h"

        namespace {
        bool nearly_equal(double a, double b) {
            return std::abs(a - b) < 1.0e-9;
        }
        }

        int main() {
            MissionCommandControlState control_state =
                make_mission_command_control_state(0.0, 0.0, 0.0, false);
            MissionCommandTypedAirControlState typed_air_control{};
            typed_air_control.throttle_command = 0.2;
            typed_air_control.throttle_active = true;
            typed_air_control.throttle_idle = false;
            typed_air_control.brake_amount = 0.0;
            typed_air_control.ground_active = true;
            typed_air_control.manual_input_active = true;
            set_mission_command_typed_air_control_state(control_state, typed_air_control);

            const auto resolved = resolve_air_control_input(
                nullptr,
                &control_state,
                nullptr,
                nullptr,
                0.0
            );
            if (!resolved.has_command_control_state) {
                std::cerr << "typed air-control overlay should remain visible without an active command target\n";
                return 1;
            }
            if (!nearly_equal(resolved.throttle_command, 0.2)) {
                std::cerr << "typed overlay throttle should remain authoritative when the command target is inactive\n";
                return 1;
            }
            if (resolved.ground_control.throttle_idle) {
                std::cerr << "typed overlay ground semantics should remain visible when active\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp22_exact_stage_inventory_demotes_command_contracts_to_guarded_ledger() -> None:
    exact_stage_text = (
        REPO_ROOT / "src" / "core" / "engine" / "exact_stage_inventory.cpp"
    ).read_text(encoding="utf-8")

    for required in (
        "Guarded contract ledger for exact-stage migration evidence.",
        "They are not maintained implementation truth by themselves.",
        "PendingMovementCommand.command (diagnostics shell)",
        "MovementCommand (optional compatibility projection)",
        "LaggedCommand (optional compatibility projection)",
        "PendingActionCommand.typed_air_control_bridge (overlay projection)",
        "PendingActionCommand remains a quarantined legacy transport shell in this slice.",
        "MissionCommandControlState is the maintained typed owner here.",
        "Lagged command truth lives in MissionCommandControlState.lagged_* for maintained callers.",
        "must not be read as if MovementCommand or ActionCommand were maintained force-stage inputs.",
        "Instrument consumers now read MissionCommand plus typed air-control overlays",
        "Propulsion runtime state is the maintained fuel-burn input here.",
    ):
        assert required in exact_stage_text

    for forbidden in (
        "Deliver queued movement commands whose latency window has expired.",
        "Deliver queued action commands into the live normalized action surface.",
        "Map normalized RL actions onto legacy heading/speed/altitude targets.",
        "Apply first-order lag to heading, speed, and altitude targets.",
        "Consumes the global frame clock. It is the first exact stage that mutates movement-command intent.",
        "Throttle source priority across PilotAction, MovementCommand, and ActionCommand must remain exact because later fuel and instrument stages depend on the chosen propulsion state.",
        "optional compatibility mirror",
        "maintained command owner",
    ):
        assert forbidden not in exact_stage_text, (
            "exact-stage inventory should no longer present compatibility mirrors or quarantined "
            "legacy transport shells as maintained implementation truth"
        )
