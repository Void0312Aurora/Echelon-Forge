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
iteration and adds this iteration's (I36) direct re-verification evidence.
It makes no new adjudications and closes no residual; closing a row here
means the owning iteration fixed it (recorded as such) or a future iteration
still owns it.

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

## 2. I33: xmacro helper newline defect and two latent strict-regex sites

**Root cause** (registered by I33, not yet fixed; write-protected until I35
lands per this iteration's instructions): `tests/support/xmacro_text.py::expand_header_field_incs`
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

**Status**: pending unified fix after I35 lands. Per this iteration's
directive, `tests/support/xmacro_text.py` and the two files above are
out of this iteration's write set and were not touched; this row is a
pointer only.

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

Baseline gate counts carried forward from I34's independent re-run and used
as this iteration's starting baseline: maintained smoke `436 passed, 45
subtests`; focused `world_batch`+leader+facade selection `282 passed`, same
5 flecs reds, `1 skipped`, `22 subtests`.

## Related

- [Repository Consolidation Plan](../repository_consolidation/README.md)
  (I28, I31, I33, I34 register rows cited above)
- [SCAL Conformance Census (2026-07-20)](scal_conformance_census_20260720.md)
  (sibling `reference`-kind register; structural precedent for this document)
- `tests/runtime/air_combat/weapon_guidance_realism/README.md` (wrapper/mixin
  collection contract referenced in section 1)
