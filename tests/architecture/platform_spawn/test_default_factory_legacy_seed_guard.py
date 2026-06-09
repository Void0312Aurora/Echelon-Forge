from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_UNIT_FACTORY_HEADER = REPO_ROOT / "src" / "models" / "core" / "default_unit_factory.h"
DEFAULT_FACTORY_LEGACY_SEED_HELPER = (
    REPO_ROOT / "src" / "components" / "command" / "default_factory_legacy_spawn_compat.h"
)


def _header_text() -> str:
    return DEFAULT_UNIT_FACTORY_HEADER.read_text(encoding="utf-8")


def _helper_text() -> str:
    return DEFAULT_FACTORY_LEGACY_SEED_HELPER.read_text(encoding="utf-8")


def test_wp22_default_factory_legacy_seed_is_named_spawn_compatibility_seam() -> None:
    text = _helper_text()

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
        "entity.template set<MissionCommandControlState>(seed.control_state);",
        "project_spawn_compatibility_movement_command_mirror(seed.control_state)",
        "project_spawn_compatibility_lagged_command_mirror(seed.control_state)",
        "Compatibility-only spawn seam for default unit factory legacy command bootstrap.",
        "MissionCommandControlState is the maintained spawn-default owner here;",
        "compatibility consumers. It is not a retired seam.",
    ):
        assert token in text

    assert "MovementCommand movement_command" not in text
    assert "LaggedCommand lagged_command" not in text
    assert "retired seam" in text
    assert "It is not maintained" not in text


def test_wp22_default_factory_uses_explicit_spawn_compatibility_helper() -> None:
    text = _header_text()

    assert '#include "components/command/default_factory_legacy_spawn_compat.h"' in text
    assert '#include "components/command/legacy_command.h"' not in text
    assert "struct SpawnCompatibilityLegacyCommandSeed" not in text
    assert "default_unit_factory_detail::apply_spawn_compatibility_action_command_seed(e);" in text
    assert "default_unit_factory_detail::apply_spawn_compatibility_control_state_seed(" in text
    assert "default_unit_factory_detail::make_spawn_compatibility_control_state_seed(" in text


def test_wp22_default_factory_spawn_body_routes_legacy_seed_through_named_seam() -> None:
    text = _header_text()

    spawn_anchor = text.index("flecs::entity spawn(flecs::world& ecs,")
    spawn_body = text[spawn_anchor:]

    seam_call = "default_unit_factory_detail::apply_spawn_compatibility_control_state_seed("
    assert seam_call in spawn_body

    forbidden_direct_seeds = (
        "e.set<ActionCommand>(make_action_command());",
        "e.set<MovementCommand>(make_legacy_autopilot_movement_command(",
        "e.set<LaggedCommand>(make_lagged_command(",
    )
    for token in forbidden_direct_seeds:
        assert token not in spawn_body, (
            "default spawn reintroduced unlabeled legacy command seeding instead of the "
            "named spawn compatibility seam"
        )
