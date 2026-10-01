from __future__ import annotations

from tests.architecture.structural_boundaries.helpers import *


def test_wp22_bindings_core_keeps_explicit_diagnostics_and_legacy_allowlists() -> None:
  names = _simulation_kernel_binding_names()
  binding_set = set(names)
  text = bindings_core_text()

  assert "Maintained SimulationKernel API surface" in text
  assert "Diagnostics-only introspection surface." in text
  assert "Legacy compatibility debug surface." in text
  assert "Diagnostics override surface." in text
  assert "bind_simulation_kernel_maintained_surface(simulation_kernel);" in text
  assert "bind_simulation_kernel_diagnostics_introspection_surface(simulation_kernel);" in text
  assert "bind_simulation_kernel_legacy_compatibility_debug_surface(simulation_kernel);" in text
  assert "bind_simulation_kernel_diagnostics_override_surface(simulation_kernel);" in text

  assert BINDINGS_DIAGNOSTICS_ALLOWLIST.issubset(binding_set)
  assert BINDINGS_LEGACY_ALLOWLIST.issubset(binding_set)

  for name in binding_set:
    if name.startswith("debug_"):
      assert name in BINDINGS_DIAGNOSTICS_ALLOWLIST | BINDINGS_LEGACY_ALLOWLIST, (
        "new debug binding requires an explicit WP22-E allowlist entry: "
        f"{name}"
      )

  assert "set_contact_list" in BINDINGS_DIAGNOSTICS_ALLOWLIST
  assert "debug_set_legacy_movement_command" in BINDINGS_LEGACY_ALLOWLIST


def test_wp22_ground_native_probe_surface_is_exactly_its_allowlist_and_never_maintained() -> None:
  """Native-probe Ground tooling stays quarantined and enumerable.

  The surface serves `native_probe_only` tooling, so its names must be exactly the
  allowlist (no silent growth), each registered once (a second `.def` on an earlier
  surface would silently shadow it through nanobind overload order), and no Ground
  or Arnis name may appear on the maintained surface, where it would read as
  supported API.
  """
  text = bindings_core_text()
  assert "bind_simulation_kernel_diagnostics_ground_native_probe_surface(simulation_kernel);" in text
  ground_block = _extract_function_block(
    text,
    "void bind_simulation_kernel_diagnostics_ground_native_probe_surface(",
  )
  ground_names = set(re.findall(r'\.def\s*\(\s*"([^"]+)"', ground_block))
  assert ground_names == BINDINGS_GROUND_NATIVE_PROBE_ALLOWLIST

  class_start = text.index('nb::class_<SimulationKernel> simulation_kernel(m, "SimulationKernel");')
  every_registration = re.findall(r'\.def\s*\(\s*"([^"]+)"', text[class_start:])
  duplicated = sorted(
    name
    for name in BINDINGS_GROUND_NATIVE_PROBE_ALLOWLIST
    if every_registration.count(name) != 1
  )
  assert duplicated == [], f"native-probe Ground bindings registered more than once: {duplicated}"

  maintained_block = _extract_function_block(
    text,
    "void bind_simulation_kernel_maintained_surface(",
  )
  maintained_names = set(re.findall(r'\.def\s*\(\s*"([^"]+)"', maintained_block))
  leaked = sorted(name for name in maintained_names if re.search(r"ground|arnis", name))
  assert leaked == [], (
    "Ground/Arnis bindings belong on the native-probe surface until a reviewed Ground "
    f"owner package promotes a facade/contract replacement; found on maintained: {leaked}"
  )

def test_wp22_bindings_core_direct_world_entity_drilling_stays_quarantined() -> None:
  text = bindings_core_text()
  maintained_block = _extract_function_block(
    text,
    "void bind_simulation_kernel_maintained_surface("
  )
  diagnostics_block = _diagnostics_introspection_text(text)
  legacy_block = _extract_function_block(
    text,
    "void bind_simulation_kernel_legacy_compatibility_debug_surface("
  )
  override_block = _extract_function_block(
    text,
    "void bind_simulation_kernel_diagnostics_override_surface("
  )
  quarantine_helper = _extract_function_block(
    text,
    "diagnostics_legacy_binding_entity_quarantine_lookup(SimulationKernel &self"
  )

  assert "self.acquire_world_lease()" not in maintained_block
  assert "lookup_entity(" not in maintained_block
  assert "self.acquire_world_lease()" not in override_block
  assert "WP22-R3 quarantine marker" in quarantine_helper
  assert "self.acquire_world_lease()" in quarantine_helper
  assert "world_lease.world().entity(" in quarantine_helper
  assert "diagnostics_legacy_binding_entity_quarantine_lookup(" in diagnostics_block
  assert "diagnostics_legacy_binding_entity_quarantine_lookup(" in legacy_block
  assert "self.acquire_world_lease()" not in diagnostics_block
  assert "self.acquire_world_lease()" not in legacy_block
  assert "lookup_entity(" not in text

def test_wp22_legacy_debug_setter_routes_through_bridge_helpers_not_direct_component_writes() -> None:
  text = bindings_core_text()
  legacy_block = _extract_function_block(
    text,
    "void bind_simulation_kernel_legacy_compatibility_debug_surface("
  )
  setter_block = _extract_binding_lambda_block(
    legacy_block,
    "debug_set_legacy_movement_command",
  )

  assert "diagnostics_quarantined_legacy_movement_bridge_write(" in setter_block
  assert "diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id)" in setter_block
  assert "e.set<MovementCommand>" not in setter_block
  assert "make_legacy_autopilot_movement_command(" not in setter_block
  assert "set_compatibility_autopilot_movement_command(" not in setter_block
  assert "deactivate_compatibility_movement_command(e)" not in setter_block
  bridge_helper_block = _extract_function_block(
    text,
    "void diagnostics_quarantined_legacy_movement_bridge_write("
  )
  assert "Diagnostics quarantine" in bridge_helper_block
  assert "set_compatibility_autopilot_movement_command(" in bridge_helper_block
  assert "deactivate_compatibility_movement_command(e)" in bridge_helper_block

def test_wp22_debug_movement_mirror_and_pending_shells_carry_quarantine_snapshot_markers() -> None:
  text = bindings_core_text()
  diagnostics_block = _diagnostics_introspection_text(text)
  legacy_block = _extract_function_block(
    text,
    "void bind_simulation_kernel_legacy_compatibility_debug_surface("
  )

  for binding_name in (
    "debug_get_pending_movement_command",
    "debug_get_pending_action_command",
  ):
    binding_block = _extract_binding_lambda_block(
      diagnostics_block,
      binding_name,
    )
    assert "diagnostics_mark_read_only_snapshot(" in binding_block
    assert '"diagnostics_pending_transport_shell"' in binding_block
    assert 'out["diagnostics_transport_shell"] = true;' in binding_block
    assert 'out["read_only_snapshot"] = true;' not in binding_block
    assert 'out["maintained_truth"] = false;' not in binding_block
    assert 'out["state_access_mode"] = "read_only_transport_shell";' in binding_block
    assert 'out["transport_shell_truth_owner"] =' in binding_block
    assert "read-only transport shell snapshot" in binding_block

  legacy_getter_block = _extract_binding_lambda_block(
    legacy_block,
    "debug_get_legacy_movement_command",
  )
  assert "diagnostics_mark_read_only_snapshot(" in legacy_getter_block
  assert '"diagnostics_legacy_mirror"' in legacy_getter_block
  assert 'out["diagnostics_legacy_mirror"] = true;' in legacy_getter_block
  assert 'out["state_access_mode"] = "read_only_legacy_mirror";' in legacy_getter_block
  assert 'out["mirror_truth_owner"] = "typed_control_state_bridge_projection";' in legacy_getter_block
  assert "read-only legacy movement shell mirror" in legacy_getter_block

  marker_helper = _extract_function_block(
    text,
    "void diagnostics_mark_read_only_snapshot("
  )
  assert 'out["diagnostics_only"] = true;' in marker_helper
  assert 'out["quarantined_surface"] = true;' in marker_helper
  assert 'out["read_only_snapshot"] = true;' in marker_helper
  assert 'out["maintained_truth"] = false;' in marker_helper
  assert (
    'out["diagnostics_quarantine_marker"] = "read_only_diagnostics_quarantine";'
    in marker_helper
  )

def test_wp22_bindings_core_still_exposes_broad_surface_as_quarantined_fact() -> None:
  names = _simulation_kernel_binding_names()
  # 85 at the WP22-E first wave; the viz unified-scene-rendering merge later
  # added set_sun_direction/get_sun_direction (non-debug maintained surface),
  # which this count guard silently missed until 2026-08-13.
  # 87 -> 86 on 2026-08-13: the dead-binding sweep removed get_egi_state
  # (zero python consumers; the EGI component itself stays alive in C++).
  # 86 -> 87: PR #35 (merge cfb9924e, 2026-09-17) landed
  # debug_set_contact_list_preserve_timestamps (diagnostics override). Its commit
  # 5dca2af6 was rebased onto the 86-pin commit e08db6af, so the pin never saw it;
  # it is now on the diagnostics allowlist.
  # 87 -> 89: Geodetic Frame P3-B added the maintained
  # set_geodetic_anchor/get_geodetic_anchor pair (scenario anchor of the local
  # frame, consumed by the scenario kernel-apply path). The base still carries
  # one unallowlisted diagnostics binding (debug_get_countermeasure_state, from
  # 2b1d936e), an inherited red that this package does not absorb into the pin.
  # The Ground native-probe surface is counted separately, by name, so the
  # broad count stays the pre-Ground baseline instead of absorbing it.
  ground_native_probe = [name for name in names if name in BINDINGS_GROUND_NATIVE_PROBE_ALLOWLIST]
  assert len(ground_native_probe) == len(BINDINGS_GROUND_NATIVE_PROBE_ALLOWLIST)
  assert len(names) - len(ground_native_probe) == 89, (
    "WP22-E expects the broad SimulationKernel binding count to stay explicit; "
    "update this guard only with a deliberate allowlist reshaping change"
  )

def test_wp22_typed_air_control_state_seam_stays_small_and_owner_named() -> None:
  control_state_text = _text(MISSION_COMMAND_CONTROL_STATE)
  resolution_text = _text(AIR_CONTROL_RESOLUTION)
  line_count = _line_count(MISSION_COMMAND_CONTROL_STATE)

  assert "struct MissionCommandTypedAirControlState {" in control_state_text
  assert "Minimal typed ownership seam for air-control semantics" in control_state_text
  assert "MissionCommandTypedAirControlState typed_air_control{};" in control_state_text
  assert "mission_command_typed_air_control_active(" in control_state_text
  assert "reset_mission_command_typed_air_control_state(" in control_state_text
  assert "set_mission_command_typed_air_control_state(" in control_state_text
  assert "active_typed_air_control_state(" in resolution_text
  assert "MissionCommandTypedAirControlState" in resolution_text
  assert line_count < 160, (
    "typed air-control owner seam should remain a compact bridge-owned header, "
    "not a new god file"
  )

def test_wp22_exact_stage_inventory_stays_contract_ledger_not_runtime_truth_register() -> None:
  exact_stage_inventory = (
    REPO_ROOT / "src" / "core" / "engine" / "exact_stage_inventory.cpp"
  )
  text = _text(exact_stage_inventory)
  line_count = _line_count(exact_stage_inventory)

  for required in (
    "Guarded contract ledger for exact-stage migration evidence.",
    "They are not maintained implementation truth by themselves.",
    "maintained delayed-delivery truth lands in MissionCommandControlState",
    "PendingActionCommand remains a quarantined legacy transport shell in this slice.",
    "PendingActionCommand.typed_air_control_bridge (overlay projection)",
    "MissionCommandControlState is the maintained typed owner here.",
    "Propulsion runtime state is the maintained fuel-burn input here.",
  ):
    assert required in text

  for forbidden in (
    "Map normalized RL actions onto legacy heading/speed/altitude targets.",
    "Apply first-order lag to heading, speed, and altitude targets.",
    "Consumes the global frame clock. It is the first exact stage that mutates movement-command intent.",
    "optional compatibility mirror",
    "maintained command owner",
  ):
    assert forbidden not in text

  assert line_count < 500, (
    "exact-stage inventory should remain a compact contract ledger and guard surface, "
    "not expand into another structural god file"
  )

def test_wp22_command_link_pending_transport_headers_keep_typed_owner_markers_explicit() -> None:
  command_link = _text(REPO_ROOT / "src" / "components" / "command" / "command_link.h")
  bridge = _text(REPO_ROOT / "src" / "components" / "command" / "legacy_command_bridge.h")
  command_api = _text(REPO_ROOT / "src" / "core" / "engine" / "simulation_kernel_command_api.cpp")
  command_link_system = _text(REPO_ROOT / "src" / "systems" / "systems" / "command_link_system.h")

  for required in (
    "Diagnostics transport shell only; maintained delivery must consume typed_command.",
    "refresh_pending_movement_command_diagnostics_shell(",
    "typed_air_control_bridge",
    "Bridge-owned typed overlay snapshot only. This is not a full typed",
    "action replacement; it merely preserves the maintained air-control",
  ):
    assert required in command_link

  for required in (
    "refresh_compatibility_typed_air_control_from_pending_action_bridge(",
    "refresh_optional_pending_action_typed_air_control_bridge(",
  ):
    assert required in bridge

  for required in (
    "refresh_pending_action_command_typed_air_control_bridge(*pending);",
    "refresh_pending_movement_command_diagnostics_shell(*pending);",
  ):
    assert required in command_api

  for required in (
    "refresh_optional_pending_action_typed_air_control_bridge(",
    "refresh_pending_movement_command_diagnostics_shell(pending);",
  ):
    assert required in command_link_system
