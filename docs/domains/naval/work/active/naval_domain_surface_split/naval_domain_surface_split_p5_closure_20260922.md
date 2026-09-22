# Naval Domain Surface Split — `P5-A` Closure Decision

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/naval_domain_surface_split/naval_domain_surface_split_p5_closure_20260922.md`
Owner: `domains/naval`
Last verified: `2026-09-23`

Parent: [Naval Domain Surface Split](README.md)

Status: `2026-09-23` closure decision **accepted for the bounded N4 package**. The
previous hold on acceptance item 2 was discharged by a native executable projection
test in the split branch. N5/N6 remain explicitly out of scope, so the package stays
under `work/active/` as a maintained boundary rather than an authority claim.

## What This Record Decides

`P5-A` is "close or hold the subproject with acceptance and parent progress updates".
This record carries the original per-item gate verdicts measured on `2026-09-22`
at `f692a7cc`, plus the split-branch follow-up that discharged the held projection
item on `2026-09-23`.

The original decision was **held** on one named item rather than on the package as a
whole. The split branch now discharges that item with
`src/tests/test_simulation_kernel_smoke.cpp::naval_mission_command_projection_is_executed_for_ships_only`;
the action command surface, bounded observation adapter, config alias, and eval gates
remain measured below.

## Gate Verdicts

| Gate item | Verdict | Deciding evidence |
| --- | --- | --- |
| 1 Action/intent ownership | **met** | the maintained command surface is `_naval_station3_command_surface` (`gym_envs/universal_env_parts/naval_actions.py`), the remaining `PilotAction` carrier is value-degenerate (a neutral ship `PilotAction` carrying fixed constants, with the policy 3-vector only in `policy_action` for diagnostics), it declares itself compatibility-only, and `tests/runtime/naval/test_naval_station_policy_surface.py` pins both halves — that the carrier's action equals the constants independently of the policy action, and that the command surface is not compatibility-only. Air action modes are refused for naval profiles. |
| 2 Command ownership | **met in the split branch** | `NavalCommandIntent` and its projection exist and are called (`src/components/domains/naval/command/mission_command_naval.h`, write seam in `src/components/command/mission_command.h`). The native test `naval_mission_command_projection_is_executed_for_ships_only` constructs a command, invokes the kernel setter, reads the projected component, checks activation and field values, and confirms an aircraft does not receive the naval component. |
| 3 Observation ownership | **met, with two named nuances** | the 23-field naval mode carries no `takeoff_*`, `runway_*`, `gear*`, or `ils*` field, the adapter reads the three role/slot entries from the cooperative roster (the same source as the air role vector minus the air-only formation-role field), `air_takeoff_formation_fallback` is recorded false per step, and the policy instruments filter drops the gear/flap/ILS indices. Nuances: `role_code` and `relative_slot_code` are shared-core fields rather than air ones, so "no formation semantics" holds by field ownership while the maintained cooperative path still *writes* the air owner-slice `task_order.formation_role_id` on naval entries (`python/rl/runtime/world_batch/cooperative_director.py`) — written, never read as naval policy semantics; and the negation assertions check the adapter's own `field_names`, which is generated from the same table the vector is built from. |
| 4 Config ownership | **met** | the maintained config name is the domain-neutral `shaping_backend`, resolved with canonical `flight_shaping_backend` precedence in `python/env_config.py`; all three naval active configs use the alias; `tests/runtime/core/test_env_config.py` 24 passed, including the canonical-over-alias precedence guard. |
| 5 Regression safety | **met after repair, red before it** | on this tree at `391e77bd` and identically on `cfb9924e`, `test_reward_surface_does_not_emit_airfield_penalty` failed: `'naval_screen_separation_penalty' not found in {...}`. That is not a contracts question but it is a naval surface test, so the item was **not** met when this record was drafted. Repaired in `f692a7cc` (see below). Now: `tests/runtime/naval` 69 passed; the wider naval surface 142 passed, 2 skipped, 59 subtests passed; the maintained smoke suite 843 passed, 1 skipped, 45 subtests passed, exit 0. |
| 6 Capability boundary | **met** | `naval_limited_engagement_v1` exists only as blocked documentation — there is no implementation to open — and `tools/eval/naval_station_policy_eval.py` refuses a run whose reward terms contain `weapon_release`, `fire_weapon`, `fire_gun`, `damage`, `kill`, `hit`, `intercept`, or `roll_stability` (`passed` requires `not forbidden_present`). |

## The Red Test Repaired Here

`tests/runtime/naval/test_naval_station_policy_surface.py::test_reward_surface_does_not_emit_airfield_penalty`
was failing on `main` before this work, and the maintained smoke suite never saw it
because the file is not in `ci_smoke_suite.json`.

The failing assertion was not the airfield question it is named for; it asserted that
a naval term was present. `_add_term` in
`gym_envs/scenario_loader/reward_runtime/naval.py` stores a term only when its value is
non-zero, so a declared term vanished exactly when the ship sat on station — zero
station error, exactly zero separation error. Its neighbour
`naval_station_error_penalty` survived only through floating-point residue
(`-3.6e-17`), which is why two adjacent assertions disagreed.

The repair is in the implementation, not the test, because the surface is observed as
a **key set**: the same eval gate fails on `required_reward_terms_missing`. The
always-computed terms are now recorded unconditionally on both sides of the
term/breakdown boundary, terms gated on an event are untouched so an absent gated term
still means the event did not happen, and
`test_declared_naval_reward_terms_survive_an_exactly_zero_value` keeps the property
and pins the module's declared set against the eval gate's required set.

## Evidence

Run from the package worktree at `f692a7cc`, Windows MSVC host:

```bash
cmo_python -m pytest -q tests/runtime/naval
cmo_python -m pytest -q tests/runtime/naval/test_naval_station_policy_surface.py
cmo_python -m pytest -q tests/runtime/naval tests/training/test_naval_training_entry_contracts.py \
  tests/eval/test_evaluation_cli_contracts.py tests/runtime/mission/test_mission_obs_taxonomy.py \
  tests/architecture/command_tasking tests/runtime/core/test_env_config.py
cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```

| Command | Outcome |
| --- | --- |
| `tests/runtime/naval` | `69 passed, 4 subtests passed` |
| `tests/runtime/naval/test_naval_station_policy_surface.py` | `20 passed` |
| the wider naval surface set | `142 passed, 2 skipped, 59 subtests passed` |
| `tests/runtime/core/test_env_config.py` | `24 passed` |
| the maintained smoke suite | `843 passed, 1 skipped, 45 subtests passed`, exit 0 |

The original independent verification pass over gate items 1-3 reproduced the item-1
tests and item-3 adapter trace, and reported the red test with the same root cause
before the repair. The split-branch native test above discharges its former item-2
finding.

## Residual Map

Immediate:

- The projection is now exercised natively. Direct Python binding of
  `NavalCommandIntent` remains intentionally absent; the C++ test is the owner-level
  executable evidence.
- **`carrier_required` is still true.** A neutral `PilotAction` enters the shared
  PilotAction/ActionCommand path every naval step. It carries no policy semantics, but
  it is a live air-shaped carrier on a naval path.
- **`WorldPilotActionAssignment` has no naval-owned replacement packet**, as the `P2-B`
  closure already recorded.

Follow-on:

- `MissionCommand` transport-shape cleanup: the flat shell still carries air owner
  slices and target-altitude naming.

Deferred:

- N5 weapon release and N6 damage authority. `naval_limited_engagement_v1` stays
  blocked; the `P2-B` and N4 records already forbid opening it here.
- Formal naval policy training, after transport, observation, reward, and eval gates.

## Forbidden Claims

This closure does not establish, and no reader may take from it:

- weapon release, launch/reject, hit, intercept, damage, kill, health-delta, or
  engagement-reward authority;
- fleet C2 or complete naval maneuver/station-keeping control;
- learned-policy acceptance or formal training results;
- that the command projection opens N5 authority — the executable test verifies only
  transport projection and domain isolation;
- that the remaining `PilotAction` and `MissionCommand` carriers are removed. They are
  bounded and compatibility-only, and they stay.

## Indexes Synchronized

- [Naval Domain Surface Split](README.md) — phase `P5` and status line.
- [Acceptance Gate](naval_domain_surface_split_acceptance_20260601.md) — decision line.
- [Naval owner README](../../../README.md) — active-work entry.
- The package stays under `work/active/` because N5/N6 and the remaining carrier
  cleanup are still separate work, not because the projection gate is open.
