# Naval Domain Surface Split — `P2-B` Command Projection Closure

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/naval_domain_surface_split/naval_domain_surface_split_p2b_command_projection_20260921.md`
Owner: `domains/naval`
Last verified: `2026-09-23`

Parent: [Naval Domain Surface Split](README.md)

Status: `P2-B` accepted. Command projection is landed, bounded behind owner-slice
guards and a native executable regression test, and does not open N5 weapon-engagement
or N6 damage authority.

## Cluster Goal

Bound `MissionCommand` compatibility use behind shared-core and naval-owner
projection tests, so the flat shell stays a transport and never becomes naval
runtime truth.

## What Landed

| Artifact | Role |
| --- | --- |
| `components/domains/naval/command/mission_command_naval.h` | Declares `NavalCommandIntent` — the maintained naval runtime command component — plus the projection `mission_command_naval_intent(naval_owner_slice, shared_core)`. |
| `components/command/mission_command.h` | Keeps only the thin compatibility-shell forwarding overloads and the `MissionCommand`-shaped write seam. |
| `components/command/...` write seam | `set_mission_command_naval_projection(entity, command)` splits the flat shell into its owner slices and publishes `NavalCommandIntent`. |
| `core/engine/simulation_kernel_command_api.cpp` | `set_unit_command` (ship path) and `set_mission_command` route through the seam. |
| `systems/systems/command_link_system.h` | Pending-command delivery routes through the seam, so a queued command publishes the intent at delivery time, not at enqueue time. |
| `models/core/default_unit_factory.h` | Spawn seeds and pre-spawned embarked helos route through the seam. |
| `systems/domains/naval/ship_motion_system.h`, `submarine_motion_system.h`, `embarked_air_ops_system.h` | Consume `NavalCommandIntent` instead of the flat shell. |

### Carrier field corrected during the projection

`embarked_air_ops_system.h` previously stored its relay-refresh timestamp in
`MissionCommandAir::takeoff_interval_s` — an air-owned field on the shared
transport shell. The naval runtime now owns
`NavalCommandIntent::last_relay_refresh_time_s`, so a naval system no longer
writes an air-domain field to hold naval bookkeeping.

## Evidence

| Gate | Command | Outcome |
| --- | --- | --- |
| Naval station behaviour | `python -m pytest -q tests/runtime/naval/test_ship_naval_station_command.py` | pass — relative station correction still driven through the projection |
| Command-chain roundtrip | `python -m pytest -q tests/runtime/mission` | pass — 84 passed, 8 subtests passed |
| Ground tasking shell | `python -m pytest -q tests/runtime/ground` | pass |
| Domain shell guard | `python -m pytest -q tests/architecture/command_tasking` | pass — 21 passed |
| Tasking token mapping | `python -m pytest -q tests/architecture/command_tasking/test_naval_tasking_standard_guard.py` | pass — English/Chinese tokens, C++ enum, and Python profile agree |
| Native projection execution | `build-local-win/ef_test.exe --test-case="*naval_mission_command_projection*"` | pass — ship projection is activated and populated; aircraft is not given NavalCommandIntent |
| Composition contract | `python tools/maintenance/simulation_composition_contract.py check` | pass — exit 0, no stale generated artifact |

The `P2-B` acceptance criterion — *naval station/ROE/assigned-target fields
survive via maintained naval slices* — is met for the station/motion and embarked
air-ops consumers by construction and observed behaviour. The compatibility
reader in `systems/domains/naval/naval_mission_weapon_release_system.h` still
reads `MissionCommand`; it remains outside this projection closure while N5 is
blocked and must not be counted as a migrated consumer.

### Guard coverage added

- `test_wp22_maintained_naval_consumers_use_owner_slice_directive_helpers`
  extended to the projected parameter name and to the forbidden direct field
  reads.
- `test_wp22_naval_runtime_consumers_read_the_naval_command_intent_projection`
  — pins that every maintained naval consumer names `NavalCommandIntent` and no
  longer reads `MissionCommand`.
- `test_wp22_naval_command_intent_projection_has_one_authority` — pins the
  projection to a single definition in the naval owner header, so it cannot be
  duplicated field-by-field at a call site and drift.

## Boundary Statement

This closure is a command-transport change only. It does not:

- open N5 weapon release, launch/reject, or engagement authority;
- open N6 damage, kill, or health-delta authority;
- claim fleet C2 maturity;
- claim learned-policy acceptance;
- remove `WorldPilotActionAssignment` or the remaining compatibility shell.

The `MissionCommand` flat shell remains compatibility-active, and
`WorldPilotActionAssignment` remains the world-batch policy action carrier. Both
are recorded as residual work under the parent subproject, not closed here.

## Residuals

- `WorldPilotActionAssignment` still has no naval-owned action assignment
  packet; that is a separate packet and is not required for `P2-B`.
- `MissionCommand` still carries air owner slices and target-altitude naming on
  the transport shell. The maintained naval path no longer depends on them; a
  transport-shape cleanup is a separate scoped change.
- `naval_mission_weapon_release_system.h` is still a compatibility consumer of
  the flat shell. Migrating it requires an N5-scoped decision and executable
  release-boundary evidence; this branch does not make that claim.
- `P5-A` closure remains the last open cluster of this subproject.
