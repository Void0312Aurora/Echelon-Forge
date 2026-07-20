# T6 Residual Ledger (2026-07-20)

Language:
- English canonical: `t6_residual_ledger.md`
- Chinese companion: [t6_residual_ledger.zh.md](t6_residual_ledger.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/t6_residual_ledger.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-20`
Baseline commit: `c2952d61`

Status: T6 (test-infrastructure rationalization) residual index for the
[Unified Architecture Program](README.md). Several accepted iterations
(I28, I31, I33) registered non-blocking residuals in prose inside their
`docs/plan/repository_consolidation/README.md` rows without a dedicated
index; this document is the promised T6 ledger those rows point at. Per the
[SCAL Conformance Census](scal_conformance_census_20260720.md) precedent,
this is a descriptive residual register (`reference`), not an independent
review: it indexes already-adjudicated findings with their originating
iteration and adds this iteration's (I36) direct re-verification evidence,
plus I37's follow-on fix-and-close of section 2's registered xmacro helper
defect. It makes no new adjudications and closes no residual on its own;
closing a row here means the owning iteration fixed it (recorded as such,
per section 2.1) or a future iteration still owns it.

## 1. I28: weapon-guidance-realism xfail/expectedFailure inventory

I28 adjudicated the 45 long-standing `tests/runtime/air_combat/weapon_guidance_realism`
junit failures into 33 unique methods across six drift groups, governed
per-method (no blanket skips): 25 methods carry `pytest.mark.xfail(strict=True)`
with a machine-readable `reason=`; 8 methods use plain `unittest.expectedFailure`
instead (pytest's unittest integration reports these as `XFAIL` with **no**
reason string, because a passing leading subTest would otherwise register as
an `XPASS(strict)` failure under `xfail(strict=True)`). I28's own repair
review flagged that the reason for those 8 lives only in source comments and
asked this ledger to index the four whose subTest mix additionally makes them
the "plain" group's harder-to-audit half (the other four fail every subTest,
so their `expectedFailure` folding is comment-adjacent and easier to find).

Re-verified this iteration (I36):

```
CMO_BUILD_DIR=<worktree>/build-local-win pytest -q tests/runtime/air_combat/weapon_guidance_realism -rx
-> 167 passed, 33 xfailed, 217 subtests passed
```

matching I28's landed count exactly.

### 1.1 Four plain-`expectedFailure` node IDs (mixed-pass subTests)

All four live in one module/class; each is a plain `@unittest.expectedFailure`
with no `xfail` marker stacked (under a strict xfail, pytest 9 would flag
their passing subTests as `XPASS(strict)`), so the governance reason lives
only in the adjacent source comment and no reason string appears in `-rx`
output -- which is exactly the audit gap I28 asked this ledger to close.

| Node ID (module/class shared below) | Group | Reason (from source comment) | As-of source pointer |
| --- | --- | --- | --- |
| `test_phase3_power_and_data_link_dependencies_propagate_to_aircraft_overlay` | primary-response selection drift | E-3 wideband data-link hit now reports `rotodome_radar_array` as the primary component | `component_damage.py:982-989` |
| `test_phase2_named_control_components_derive_axis_specific_authority` | primary-response selection drift | F-16 leading-edge flap hit now reports `flight_control_computer` as primary; the collective case bleeds into `roll_control` | `aircraft_damage.py:435-442` |
| `test_phase2_avionics_and_crew_damage_derives_sensor_performance` | cross-subsystem overspill | Wing flight-control hit now degrades sensor range far below the `>=0.9995` no-degradation contract | `aircraft_damage.py:517-524` |
| `test_phase2_crew_consequences_distinguish_pilot_mission_and_command_roles` | cross-subsystem overspill | E-3 crew-station hits now bleed into `pilot`/`command_navigation` roles the case marks as stable | `aircraft_damage.py:594-601` |

Module: `tests/runtime/air_combat/weapon_guidance_realism/test_warhead_and_component_damage.py`,
class `WarheadAndComponentDamageTests` (the pytest wrapper that mixes in the
`AircraftDamageRuntimeMixin`/`ComponentDamageRuntimeMixin` methods above per
this directory's documented wrapper pattern). Full node ID is
`test_warhead_and_component_damage.py::WarheadAndComponentDamageTests::<method>`.

For contrast, the other four `expectedFailure` methods (all-failing subTests,
which do carry `@pytest.mark.xfail(strict=True, reason=...)` stacked above
their `@unittest.expectedFailure` and therefore surface reasons in `-rx`;
not part of this indexing gap) are
`test_live_missile_hit_against_non_f16_structured_target_produces_component_damage`
(`test_geometry_and_edge_cases.py::GeometryAndEdgeCaseTests`),
`test_phase2_aircraft_damage_overlay_tracks_air_specific_subsystems`,
`test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects` (the "G3
hitboxes" `mil_thrust_n` example I28's entry names), and
`test_phase3_fighter_component_geometry_covers_nose_avionics_and_engine_runtime_identity`
(the latter three in `test_warhead_and_component_damage.py::WarheadAndComponentDamageTests`).

### 1.2 33-method group mapping overview

| Group (I28 terminology) | `xfail(strict)` | `expectedFailure` | Total |
| --- | --- | --- | --- |
| Primary-response selection drift | 1 | 2 | 3 |
| Proximity-projection spread | 2 | 1 | 3 |
| Cross-subsystem overspill | 8 | 4 | 12 |
| Loss-state escalation/saturation | 8 | 1 | 9 |
| Aero/fuze response drift | 3 | 0 | 3 |
| Mechanism-calibration drift | 3 | 0 | 3 |
| **Total** | **25** | **8** | **33** |

Group definitions and worked examples (from the re-verified `-rx` output and
source comments):

- **Primary-response selection drift** -- a hit's reported *primary*
  component/response changes (e.g. the AWACS wideband-datalink and F-16
  leading-edge-flap cases above).
- **Proximity-projection spread** -- `projected_hitbox_count`/`component_hit_count`
  now reports a nonzero spread where the contract expects an isolated hit
  (e.g. `test_dfm_p4_direct_component_hit_populates_primary_component_event_fields`).
- **Cross-subsystem overspill** -- damage bleeds into a subsystem/axis the
  case marks as stable, including the entry's own named example,
  `test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects`, where a
  hitbox hit changes `mil_thrust_n` from a calibrated 76310 to 64510.
- **Loss-state escalation/saturation** -- an overlay/loss-state verdict now
  crosses a calibrated threshold (e.g. flight-control overlay saturating at
  0.0, or a verdict escalating from `combat_capable` to `mobility_kill`).
- **Aero/fuze response drift** -- an aerodynamic or fuze-timing response
  magnitude drifts below/above its calibrated band (e.g. sideslip delta
  collapsing to 0.29 deg against a `>2.0 deg` contract).
- **Mechanism-calibration drift** -- a warhead-mechanism calibration no
  longer reproduces its reference magnitude (e.g. `component_failure_count`
  no longer `> 0` for the calibrated profile).

## 2. I33: xmacro helper newline defect and two latent strict-regex sites (fixed at I37)

**Root cause** (registered by I33; fixed at I37 once I35 landed, per this
iteration's own directive to write-protect the helper and the two latent
sites until then -- see 2.1 for the fix and its full re-verification):
`tests/support/xmacro_text.py::expand_header_field_incs`
uses `_INC_INCLUDE_RE = re.compile(r'#include "([^"]+\.inc)"\n?')`, whose
trailing `\n?` optionally consumes the `#include` line's own newline. The
replacement text (`"\n".join(...)` over the expanded field declarations)
carries no trailing newline of its own, so a fully macro-owned struct's
simulated body ends with its last field glued directly to the following
`};` with no intervening newline.

**Consequence**: any source-text boundary test that locates a struct body
with the strict closing-brace pattern

```python
pattern = rf"\bstruct\s+{re.escape(struct_name)}\b[^{{;]*\{{(?P<body>.*?)\n\}};"
```

skips past the glued `};` (no `\n` immediately precedes it) and greedily
over-matches into a neighbouring struct's body. I33 hit this directly:
macro-izing two facade classes extended `test_runtime_dto_contracts.py`'s
match for `RuntimeCapabilities` from a correct bound to 14,642 characters,
swallowing `DeviceResidentOutputDescriptor` and its forbidden-token guard.

**Already repaired at I33** (relaxed `\n\}};` to `\n?\}};`):
`tests/runtime/engagement/test_engagement_contract_shape.py`,
`tests/architecture/runtime_facade/test_runtime_dto_contracts.py` (review-driven
repair after the blocking regression above).

**Two latent sites, still on the strict `\n\}};` form** (green today only
because none of their scanned structs are yet fully macro-owned via an
`.inc` include; a future field-family migration through this pattern would
reproduce the same silent over-match):

| Site | Pointer | Structs scanned |
| --- | --- | --- |
| `tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py` | `_struct_body`, line 54 | `TypedPlatformSpawnAdmission`, `TypedPlatformSpawnResult`, `BatchWorldSetupResult` |
| `tests/runtime/mission/test_policy_contract_shape.py` | `_struct_body`, line 16 | `ActionHoldPolicy`, `ActionIntentPacket`, `CoordinationIntentPacket`, `AgentRole`, `DecisionBelief`, `AgentRoleAuthorizationResult` |

**Status**: fixed at I37. Section 2.1 below records the fix, the new
helper-level unit tests, the four-site regex unification, the two latent
sites' re-verification, and the full verification-gate evidence.

### 2.1 I37 fix and re-verification

**Fix**: `_INC_INCLUDE_RE` in `tests/support/xmacro_text.py` no longer
consumes the `#include` line's own trailing newline --
`re.compile(r'#include "([^"]+\.inc)"\n?')` becomes
`re.compile(r'#include "([^"]+\.inc)"')`. The newline that terminates the
`#include` line is therefore left untouched as literal text in the
surrounding source, so the replacement (which still carries no trailing
newline of its own) is always followed by exactly that preserved newline --
a fully macro-owned struct's simulated body now keeps a newline before
whatever follows (typically the struct's own `};`), matching the
hand-written convention byte-for-byte. `expand_header_field_incs` and
`expand_binding_field_incs` share this one regex, so the single-line fix
covers both call sides; `expand_binding_field_incs` carried the identical
latent defect (confirmed by a dedicated new unit test below) even though no
cited consumer's assertions happened to depend on its glued form.

**New helper-level unit tests** (`tests/support/test_xmacro_text.py`; the
helper had no dedicated unit tests before I37): four tests exercise the fix
directly, independent of any production header, by building a synthetic
"single macro group immediately followed by `};`" fragment around the
real, two-field `runtime/contracts/detail/engagement_entity_ref.inc`
fixture (read-only; no new fixture file was added) --

- `test_expand_header_field_incs_preserves_newline_before_closing_brace` --
  the strict `\n\}};` form (no `?`) matches a fully macro-owned struct.
- `test_expand_header_field_incs_does_not_swallow_neighbouring_struct` --
  a struct placed immediately after the macro-owned one is not pulled into
  the first struct's body.
- `test_expand_header_field_incs_keeps_consecutive_include_lines_on_separate_lines`
  -- two back-to-back `#include` lines inside one struct also stay
  newline-separated at their shared boundary, not just at the closing brace.
- `test_expand_binding_field_incs_preserves_newline_before_following_code` --
  the binding-side sibling function gets the same fix (shared regex).

All four were confirmed red against the pre-fix helper (temporary
`git stash` of only `xmacro_text.py`) before being confirmed green against
the fix, so they are proven to exercise the defect rather than passing
vacuously.

**Four regex sites unified to the strict `\n\}};` form** (the `\n?\}};`
relaxation is retired everywhere): `test_engagement_contract_shape.py::_struct_body`
and `test_runtime_dto_contracts.py::_struct_body` had their pattern's
`\n?\}};` tail restored to strict `\n\}};`. The third adaptation this
iteration's task brief flagged as possibly needing a tweak -- I35's
bare-declaration assertion list in `test_dto_domain_shell_guard.py` (e.g.
`"shared_core_type shared_core;"` rather than `"...shared_core{};"`) --
turned out to need none: that list is a plain substring-containment check
against `_rendered_header_field`'s separate "omit the trailing `{}` for a
value-initialized default" rendering convention, which is orthogonal to the
newline this fix restores, so the list stays byte-for-byte unchanged and
still passes. The two latent sites this ledger named
(`test_typed_platform_spawn_contracts.py`, `test_policy_contract_shape.py`)
needed no code change either, and are no longer merely accidentally green:
with the helper itself fixed, their strict `\n\}};` form is now correct
regardless of whether their scanned structs become fully macro-owned in a
future iteration.

**Full-repo scan**: searching for the literal `\n?\}};` source spelling now
returns zero hits inside `.py` files. The only remaining hits
are historical prose in this ledger and in
`docs/plan/repository_consolidation/README.md`/`.zh.md`'s I33 register row,
both accurately describing -- in the past tense -- the relaxation I33
actually made at the time; those historical rows are intentionally left
unedited.

**Verification** (this worktree, `CMO_BUILD_DIR=<worktree>/build-local-win`):

```
pytest -q tests/support/test_xmacro_text.py
-> 4 passed (new; each independently confirmed red on the pre-fix helper)

pytest -q tests/runtime/engagement/test_engagement_contract_shape.py
-> 6 passed

pytest -q tests/architecture/runtime_facade/test_runtime_dto_contracts.py
-> 7 passed (zero reds; the four test_wp22_* reds this ledger's section 5
   lists live in test_runtime_escape_hatches.py, a different file, not here)

pytest -q tests/architecture/command_tasking/test_dto_domain_shell_guard.py
-> 11 passed

pytest -q tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py
-> 2 passed, 1 failed -- test_wp24_python_command_chain_business_writes_use_maintained_contracts
   fails identically with xmacro_text.py reverted to its pre-I37 state, i.e.
   unrelated to this defect. Lineage triage by the I37 review (isolated clean
   checkouts): green at 48c86c4b (I33), red from c2952d61 (I34) onward -- the
   I34 landing sank the command-chain write calls into _shared_ops.py, which
   this text guard's synthesized file set does not scan (adapter.py itself
   still carries the tokens at all three commits; the guard's vec_env
   synthesis and the cooperative module are the two spots that went blank).
   Behavior tests (test_world_batch_vec_env_command_chain.py, 23/23) stay
   green, so this is a guard-adaptation gap, not a functional regression.
   Registered in section 6 below; repair direction: add _shared_ops.py to
   the guard's scan set. Out of this iteration's write set and left untouched

pytest -q tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py
-> 5 passed

pytest -q tests/runtime/mission/test_policy_contract_shape.py
-> 8 passed

pytest -q tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py
-> 13 passed

pytest -q tests/architecture/runtime_facade/test_runtime_facade_contract_boundaries.py
-> 8 passed

python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
-> 439 passed, 45 subtests passed (unchanged from this iteration's starting
   baseline; tests/support/test_xmacro_text.py was not added to the smoke
   manifest, so it did not participate in this count)

ruff check .        -> All checks passed!
git diff --check    -> clean
```

## 3. Task B fix (this iteration, I36): retained-artifact rewrite side effect

**Root cause**: `tests/architecture/damage_model/test_release_signoff_gate.py::test_release_signoff_gate_cli_writes_default_artifacts`
was the only test in its file that did not use `tmp_path`; it invoked
`tools/maintenance/damage_model.py release-governance source-release-signoff`
with no `--output-dir`/`--report` override, so the CLI's argparse defaults
(`DEFAULT_OUTPUT_DIR`/`DEFAULT_REPORT_PATH`) pointed the write straight at
the real retained-artifact location:
`docs/task/air_combat/archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/res001_release_signoff_20260531/{manifest.json,res001_release_signoff_gate.json}`
plus the sibling report
`validation_res001_release_signoff_gate_20260531.zh.md`. Re-running the
generator recomputes several `sha256` fields against on-disk source-payload
bytes; on this CRLF checkout the recomputed `gate_sha256` differed from the
checked-in value (confirmed: `822c496d...` checked-in vs `809dfe67...`
regenerated), so every run rewrote all three files -- a retained-archive
immutability violation that twice produced false "dirty worktree" reports.
`tools/maintenance/release_governance/source_release_signoff.py`'s Windows
`\r\n` write-text behavior is I19's deliberately preserved convention and
was correctly left untouched; this iteration's write set was the test file
only.

**Fix**: redirected the CLI invocation to `tmp_path` via the CLI's own
`--output-dir`/`--report` flags (bringing this test in line with the other
four tests in the same file, all of which already use `tmp_path`), and added
a separate, I/O-free assertion pinning `DEFAULT_OUTPUT_DIR`/`DEFAULT_REPORT_PATH`
so the default-argument wiring stays regression-guarded without ever writing
to the real location.

**Verification**: target file run twice consecutively --
`git status` reported zero changes to the three retained files both before
and after both runs; the three files are byte-identical to HEAD throughout.

## 4. Held and in-progress DTO residuals

### 4.1 I31: `ExecutionBatchStepResult` held (preprocessor comma)

`ExecutionBatchStepResult` (15 fields) stays fully hand-written, held out of
`tools/maintenance/dto_schema` single-source ownership: its
`std::vector<std::array<double, 4>>` field contains an angle-bracket comma
that the X-macro preprocessor would mis-split into an extra macro argument
(the preprocessor pairs only parentheses, not angle brackets), and a
type-alias workaround would break token-for-token type equivalence with the
hand-written declaration. No target iteration is assigned; this row is a
pointer for whichever future DTO-family iteration finds a non-token-breaking
encoding (e.g. a dedicated alias registered in the schema's extension slots).

### 4.2 I33: `RecentEngagementEvents` handoff (I35 in progress)

`RecentEngagementEvents` (`src/core/engine/engagement_event_types.h`, 14
fields, "identically clean shape" per I33's survey) sits outside I33's
declared write-set boundary and was recorded as the natural next DTO
single-sourcing candidate -- that candidate designation is recorded in I33's
own register row in `docs/plan/repository_consolidation/README.md`. Per this
iteration's (I36) task brief, I35 is handling the migration itself; as of
this ledger's writing I35's own migration register row does not yet exist
(in progress, not landed).
This ledger tracks it as a pointer only and does not duplicate or race the
migration.

## 5. Local environment red list (as of c2952d61)

Five categories of pre-existing, machine/worktree-local reds have been
independently reproduced across I31, I33, and I34's isolated-baseline
checks. This iteration re-confirmed each category directly on this exact
worktree (`CMO_BUILD_DIR=<worktree>/build-local-win`), naming exact node IDs
where the category resolves to a small, enumerable set.

| Item | I36 direct re-verification | Register pointer |
| --- | --- | --- |
| 5 flecs static-lib link-signature reds | Reproduced the failure class: `tests/architecture/compatibility_quarantine/test_guard_enforcement.py` and `tests/architecture/runtime_spine/test_clock_domain_enforcement.py` both raise `AssertionError: Could not find include directory for CMake dependency 'flecs'` at collection time against this worktree's `build-local-win` snapshot. | I31/I33/I34 rows (independently reproduced on isolated baselines each time; I34: "same 5 flecs reds") |
| Diagnostics lazy-load `common.ef_py` attribute gap | `pytest tests/runtime/bindings/test_lazy_binding_resolution.py::LazyBindingResolutionTests::test_common_import_prefers_repo_build_ef_py` fails: `AttributeError: module 'tools.diagnostics.common' has no attribute 'ef_py'. Did you mean: '_ef_py'?` (the module only exposes the private `_ef_py()` lazy-load helper). | I31 row ("one pre-existing `common.ef_py` attribute gap") |
| 4 `test_wp22_*` reds | Named by node ID, all in `tests/architecture/runtime_facade/test_runtime_escape_hatches.py`: `test_wp22_naval_screen_raw_unit_state_seam_stays_named_and_localized`, `test_wp22_tasking_bridge_quarantines_raw_mission_and_command_chain_sync_helpers`, `test_wp22_scripted_opponent_kernel_access_stays_named_and_localized`, `test_wp22_loading_world_layout_kernel_apply_stays_named_and_localized`; each asserts a refactored symbol (e.g. `class LoaderOwnedScriptedOpponentKernelView:`) that this worktree's `python/rl/tasking/bridge.py` does not yet contain -- a lineage gap against whichever branch landed that wp22 refactor, not a regression introduced by this iteration. The I35 review's superset regression sweep surfaced one further red of the same family: `test_wp12_runtime_facade_does_not_gain_a_second_maintained_injection_api` (same file), reproduced on a clean-baseline worktree and added here at the I35 landing. | I33 row ("the four `test_wp22_*` directory reds"); I35 review |
| `leader_phase_manager_approach_arm` contract | `python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/comm/leader_phase_manager_approach_arm.json` fails: `expected approach-arm transition count mismatch: 0`. | I34 row |
| `tests/gpu` `build-gpu`-absent red | `pytest tests/gpu/test_cuda_import_order.py::CudaImportOrderTests::test_world_batch_vec_env_import_after_torch_runtime_setup` fails: the subprocess it launches raises `ModuleNotFoundError: No module named 'ef_py'` because `build-gpu/` does not exist in this worktree (only `build-local-win/` does). | I34 row |
| Diagnostics script-governance red | `tests/architecture/governance/test_tools_script_governance.py::test_diagnostics_top_level_entrypoints_are_governed_by_function` -- first reproduced by the I35 review on a clean 48c86c4b checkout; re-confirmed during the I38 review; added at the I38 landing. | I35/I38 reviews |
| 2 air-combat calibration-drift reds | `tests/runtime/air_combat/test_component_failure_probability_surface.py::test_mlf5c_direct_hit_load_floor_prevents_blast_tail_valley` and `tests/runtime/air_combat/test_live_detonation_event_surface.py::test_live_detonation_exports_standard_warhead_spatial_and_component_events` (signature `'detonated_no_effect' == 'damage_applied'`). The I38 review reproduced both against the 2026-07-18 pre-change binary -- a stronger inherence proof than same-binary stash comparison -- confirming they are machine-baseline product/calibration drift unrelated to any landed iteration; same family as the I28-adjudicated drift classes. | I38 review |

Baseline gate counts carried forward from I34's independent re-run and used
as this iteration's starting baseline: maintained smoke `436 passed, 45
subtests`; focused `world_batch`+leader+facade selection `282 passed`, same
5 flecs reds, `1 skipped`, `22 subtests`.

## 6. I34: command-chain text-guard adaptation gap (wp24)

Registered at the I37 landing from the I37 review's lineage triage
(isolated clean checkouts per commit):

| Item | Detail |
| --- | --- |
| Failing node | `tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py::test_wp24_python_command_chain_business_writes_use_maintained_contracts` |
| Lineage | green at `48c86c4b` (I33); red from `c2952d61` (I34) onward; unrelated to I35/I36/I37 write sets |
| Mechanism | I34 sank the command-chain write calls into `python/rl/runtime/world_batch/_shared_ops.py`; the guard's synthesized scan set (adapter plus vec_env synthesis plus cooperative module) does not include `_shared_ops.py`, so the vec_env-synthesis and cooperative probes went blank while `adapter.py` still carries its tokens |
| Behavior evidence | `test_world_batch_vec_env_command_chain.py` 23/23 green at all commits -- maintained-contract write paths function correctly; this is a guard-adaptation gap, not a functional regression |
| Repair direction | add `_shared_ops.py` to the guard's scan set (guard intent unchanged); owner: T6, attributed to I34 |

## Related

- [Repository Consolidation Plan](../repository_consolidation/README.md)
  (I28, I31, I33, I34 register rows cited above)
- [SCAL Conformance Census (2026-07-20)](scal_conformance_census_20260720.md)
  (sibling `reference`-kind register; structural precedent for this document)
- `tests/runtime/air_combat/weapon_guidance_realism/README.md` (wrapper/mixin
  collection contract referenced in section 1)
