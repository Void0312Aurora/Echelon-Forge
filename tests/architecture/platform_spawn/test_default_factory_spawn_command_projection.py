from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_UNIT_FACTORY_HEADER = REPO_ROOT / "src" / "models" / "core" / "default_unit_factory.h"
DEFAULT_FACTORY_SPAWN_COMMAND_PROJECTION = (
  REPO_ROOT / "src" / "components" / "command" / "default_factory_spawn_command_projection.h"
)


def _header_text() -> str:
  return DEFAULT_UNIT_FACTORY_HEADER.read_text(encoding="utf-8")


def _helper_text() -> str:
  return DEFAULT_FACTORY_SPAWN_COMMAND_PROJECTION.read_text(encoding="utf-8")


def test_wp22_default_factory_spawn_command_projection_is_named_owner_seam() -> None:
  text = _helper_text()

  for token in (
    "struct SpawnCommandProjectionControlStateSeed",
    "struct SpawnCommandProjectionActionSeed",
    "project_spawn_command_projection_movement_mirror(",
    "project_spawn_command_projection_lagged_mirror(",
    "make_spawn_command_projection_control_state_seed(",
    "apply_spawn_command_projection_control_state_seed(",
    "apply_spawn_command_projection_action_seed(",
    "entity.template set<MissionCommandControlState>(seed.control_state);",
    "project_spawn_command_projection_movement_mirror(seed.control_state)",
    "project_spawn_command_projection_lagged_mirror(seed.control_state)",
    "Default-factory spawn command projection seam.",
    "MissionCommandControlState is the maintained spawn-default owner here;",
    "consumers until their readers move to typed control state.",
  ):
    assert token in text

  assert "SpawnCompatibilityLegacyCommandSeed" not in text
  assert "make_spawn_compatibility_legacy_command_seed" not in text
  assert "apply_spawn_compatibility_legacy_command_seed" not in text
  assert "MovementCommand movement_command" not in text
  assert "LaggedCommand lagged_command" not in text
  assert "legacy command bootstrap" not in text


def test_wp22_default_factory_uses_explicit_spawn_command_projection_helper() -> None:
  text = _header_text()

  assert '#include "components/command/default_factory_spawn_command_projection.h"' in text
  assert '#include "components/command/legacy_command.h"' not in text
  assert "SpawnCompatibilityLegacyCommandSeed" not in text
  assert "default_unit_factory_detail::apply_spawn_command_projection_action_seed(e);" in text
  assert "default_unit_factory_detail::apply_spawn_command_projection_control_state_seed(" in text
  assert "default_unit_factory_detail::make_spawn_command_projection_control_state_seed(" in text


def test_wp22_default_factory_spawn_body_routes_command_projection_through_named_seam() -> None:
  text = _header_text()

  spawn_anchor = text.index("flecs::entity spawn(")
  spawn_body = text[spawn_anchor:]

  seam_call = "default_unit_factory_detail::apply_spawn_command_projection_control_state_seed("
  assert seam_call in spawn_body

  forbidden_direct_seeds = (
    "e.set<ActionCommand>(make_action_command());",
    "e.set<MovementCommand>(make_legacy_autopilot_movement_command(",
    "e.set<LaggedCommand>(make_lagged_command(",
  )
  for token in forbidden_direct_seeds:
    assert token not in spawn_body, (
      "default spawn reintroduced unlabeled command mirror seeding instead of the "
      "named spawn command projection seam"
    )
