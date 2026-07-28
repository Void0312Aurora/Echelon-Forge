# T6 Residual Ledger (2026-07-20)

Language:
- English canonical: `t6_residual_ledger.md`
- Chinese companion: [t6_residual_ledger.zh.md](t6_residual_ledger.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/t6_residual_ledger.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-26`
Baseline commit: `0aa76a00`

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

## 5. Local environment red list (complete open-red list; last refreshed at I65)

Categories of pre-existing, machine/worktree-local reds, independently
reproduced across I31, I33, and I34's isolated-baseline checks. I36
re-confirmed each category directly on its worktree
(`CMO_BUILD_DIR=<worktree>/build-local-win`), naming exact node IDs where the
category resolves to a small, enumerable set.

This section is maintained as the **complete** open-red list, not a snapshot:
reds surfaced by later sweeps are registered here rather than left only in the
iteration section that found them. I65 registered the two items section 8.9
surfaced (the Windows path-separator pair and the component-fragility
calibration drift) and recorded each row's current disposition inline, so the
`Reproduced`/`Governed`/`Fixed` state of every row is readable from this
table alone.

| Item | I36 direct re-verification | Register pointer |
| --- | --- | --- |
| 5 flecs static-lib link-signature reds | Reproduced the failure class: `tests/architecture/compatibility_quarantine/test_guard_enforcement.py` and `tests/architecture/runtime_spine/test_clock_domain_enforcement.py` both raise `AssertionError: Could not find include directory for CMake dependency 'flecs'` at collection time against this worktree's `build-local-win` snapshot. **Governed by conditional skip at I65 (section 9.4); root-caused there as a build-snapshot-completeness red (`_deps/flecs-build` present without `_deps/flecs-src`), not a lineage red -- a build tree carrying the dependency sources runs all of these green.** | I31/I33/I34 rows (independently reproduced on isolated baselines each time; I34: "same 5 flecs reds") |
| Diagnostics lazy-load `common.ef_py` attribute gap | `pytest tests/runtime/bindings/test_lazy_binding_resolution.py::LazyBindingResolutionTests::test_common_import_prefers_repo_build_ef_py` fails: `AttributeError: module 'tools.diagnostics.common' has no attribute 'ef_py'. Did you mean: '_ef_py'?` (the module only exposes the private `_ef_py()` lazy-load helper). **Guard-adapted to green at I57 (section 8.5).** | I31 row ("one pre-existing `common.ef_py` attribute gap") |
| 4 `test_wp22_*` reds | Named by node ID, all in `tests/architecture/runtime_facade/test_runtime_escape_hatches.py`: `test_wp22_naval_screen_raw_unit_state_seam_stays_named_and_localized`, `test_wp22_tasking_bridge_quarantines_raw_mission_and_command_chain_sync_helpers`, `test_wp22_scripted_opponent_kernel_access_stays_named_and_localized`, `test_wp22_loading_world_layout_kernel_apply_stays_named_and_localized`; each asserts a refactored symbol (e.g. `class LoaderOwnedScriptedOpponentKernelView:`) that this worktree's `python/rl/tasking/bridge.py` does not yet contain -- a lineage gap against whichever branch landed that wp22 refactor, not a regression introduced by this iteration. The I35 review's superset regression sweep surfaced one further red of the same family: `test_wp12_runtime_facade_does_not_gain_a_second_maintained_injection_api` (same file), reproduced on a clean-baseline worktree and added here at the I35 landing. **All four `test_wp22_*` guard-adapted to green at I57 (section 8.3); the `test_wp12_*` node -- which actually lives in `tests/architecture/policy_execution/test_intent_injection_authority_guard.py`, not this file -- guard-adapted to green at I57 (section 8.4).** | I33 row ("the four `test_wp22_*` directory reds"); I35 review |
| `leader_phase_manager_approach_arm` contract | `python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/comm/leader_phase_manager_approach_arm.json` fails: `expected approach-arm transition count mismatch: 0`. **Classified at I57 (section 8.8): lineage divergence -- the contract harness's `FakeLoader` lags this lineage's `approach_arm_require_runway_frame` arming gate; JSON/runner untouched.** | I34 row |
| `tests/gpu` `build-gpu`-absent red | `pytest tests/gpu/test_cuda_import_order.py::CudaImportOrderTests::test_world_batch_vec_env_import_after_torch_runtime_setup` fails: the subprocess it launches raises `ModuleNotFoundError: No module named 'ef_py'` because `build-gpu/` does not exist in this worktree (only `build-local-win/` does). **Governed by conditional `skipUnless(build-gpu present)` at I57 (section 8.7).** | I34 row |
| Diagnostics script-governance red | `tests/architecture/governance/test_tools_script_governance.py::test_diagnostics_top_level_entrypoints_are_governed_by_function` -- first reproduced by the I35 review on a clean 48c86c4b checkout; re-confirmed during the I38 review; added at the I38 landing. **Governed by `xfail(strict=True)` at I57 (section 8.6): the top-level consolidation this guard enforces never landed here and cannot be adapted without blessing the sprawl it forbids.** | I35/I38 reviews |
| 2 air-combat calibration-drift reds | `tests/runtime/air_combat/test_component_failure_probability_surface.py::test_mlf5c_direct_hit_load_floor_prevents_blast_tail_valley` and `tests/runtime/air_combat/test_live_detonation_event_surface.py::test_live_detonation_exports_standard_warhead_spatial_and_component_events` (signature `'detonated_no_effect' == 'damage_applied'`). The I38 review reproduced both against the 2026-07-18 pre-change binary -- a stronger inherence proof than same-binary stash comparison -- confirming they are machine-baseline product/calibration drift unrelated to any landed iteration; same family as the I28-adjudicated drift classes. **Governed by `xfail(strict=True)` at I65 (section 9.5), after re-proving inherence against a second, newer binary (2026-07-26) as well as the 2026-07-18 one.** | I38 review |
| `platform_spawn` spdlog collection error | `tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py` fails at collection with `Could not find include directory for CMake dependency 'spdlog'` -- same family as the flecs entry above but a different dependency and a file not previously listed; reproduced by the I44 review with a write set that touches nothing capable of affecting CMake dependency resolution. Added at the I44 landing. **Governed by conditional skip at I65 (section 9.4); root-caused there as a build-snapshot-completeness red, not a lineage red.** | I44 review |
| `source_evidence_governance` pre-existing red | `tests/architecture/damage_model/test_source_evidence_governance.py` fails pre-existing (standalone: 1 failed + 5 errors; mixed-run: 4 failed + 5 errors -- order-sensitive). Root cause chain sits entirely outside any landed write set: `tools/maintenance/source_governance/rights_output_policy.py:107` passes `None` into `re.sub`. `test_source_admission_audit.py` alone runs 6 passed. Surfaced by the I44 review's superset sweep; added at the I44 landing. **Fixed at I57 (section 8.2): `_pdf_text_probe` now captures raw bytes and strict-UTF-8-decodes them (undecodable output fails closed with zero statement hits) and `_normalize_statement_text` fail-closes on `None`; standalone now 22 passed.** | I44 review |
| 2 Windows path-separator reds (`retained_pack/manifest.json`) | `tests/architecture/damage_model/test_candidate_artifact_contracts.py` (line 611) and `test_component_probability_artifacts.py` (line 655) both assert `loaded["manifest_relative_path"].endswith("retained_pack/manifest.json")`, but the value is an absolute `tmp_path` with OS-native separators on Windows. Surfaced by the I57 full-directory sweep (section 8.9), registered into this section at I65. **Fixed at I65 (section 9.3): the assertions now compare `Path` objects against the constructed output dir -- an OS-agnostic and strictly stronger check. Root-caused as a test-assertion defect, not environmental.** | I57 sweep (section 8.9); fixed I65 |
| `component_fragility_benchmark` calibration-drift red | `tests/architecture/damage_model/test_component_fragility_validation.py::test_fragility_benchmark_compares_candidate_to_synthetic_sigmoid` -- its `synthetic_sigmoid_probability` rows come from the binary-computed component-failure-probability surface and read ~0.1699-0.1729 against the test's hard-coded `0.35168` reference (max relative difference 1.07). Surfaced by the I57 full-directory sweep (section 8.9), registered into this section at I65. **Governed by `xfail(strict=True)` at I65 (section 9.5); same binary-driven drift family as the two air-combat calibration reds above.** | I57 sweep (section 8.9); governed I65 |

Baseline gate counts carried forward from I34's independent re-run and used
as this iteration's starting baseline: maintained smoke `436 passed, 45
subtests`; focused `world_batch`+leader+facade selection `282 passed`, same
5 flecs reds, `1 skipped`, `22 subtests`.

## 6. I34: command-chain text-guard adaptation gap (wp24) (fixed at I39)

Registered at the I37 landing from the I37 review's lineage triage
(isolated clean checkouts per commit):

| Item | Detail |
| --- | --- |
| Failing node | `tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py::test_wp24_python_command_chain_business_writes_use_maintained_contracts` |
| Lineage | green at `48c86c4b` (I33); red from `c2952d61` (I34) onward; unrelated to I35/I36/I37 write sets |
| Mechanism | I34 sank the command-chain write calls into `python/rl/runtime/world_batch/_shared_ops.py`; the guard's synthesized scan set (adapter plus vec_env synthesis plus cooperative module) does not include `_shared_ops.py`, so the vec_env-synthesis and cooperative probes went blank while `adapter.py` still carries its tokens |
| Behavior evidence | `test_world_batch_vec_env_command_chain.py` 23/23 green at all commits -- maintained-contract write paths function correctly; this is a guard-adaptation gap, not a functional regression |
| Repair direction | add `_shared_ops.py` to the guard's scan set (guard intent unchanged); owner: T6, attributed to I34 |

**Sibling gap (registered at the I41 landing, same I34 attribution):**
`tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py::GroundRuntimeSourceBridgeTests::test_batch_envs_use_tasking_bridge_for_command_chain_sync`
-- surfaced by I41's focused regression and lineage-triaged by the I41
review on isolated clean checkouts (green at `48c86c4b`, red from
`c2952d61` onward): the guard still asserts vec_env/cooperative import
`build_kernel_mission_command` directly from `bridge.py`, while the I34
sink moved that call into `_shared_ops.py`; the I39 repair covered only the
wp24 guard file, not this one. Behavior unaffected (same mechanism as the
wp24 entry above). Repair direction: same as I39 -- include `_shared_ops.py`
in this guard's scan set, guard intent unchanged. Fixed at I42.

**Status**: fixed at I39. Section 6.1 below records the fix and its
re-verification.

### 6.1 I39 fix and re-verification

**Fix**: `test_wp24_python_command_chain_business_writes_use_maintained_contracts`
(`tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py`)
now folds `python/rl/runtime/world_batch/_shared_ops.py`'s source text into
its local `world_batch_vec_env`/`cooperative_vec_env` scan variables
(`world_batch_vec_env_source_text() + "\n" + shared_ops`, and the
cooperative module's own text plus that same `shared_ops` string) before
running both the positive maintained-token loop and the
forbidden-legacy-token loop that follow. The change is scoped to this one
test function only: `tests/architecture/runtime_facade/helpers.py`'s shared
`WORLD_BATCH_VEC_ENV_SOURCE_FILES` tuple (consumed by exactly one other
test, `test_scenario_setup_facade_boundary.py::test_wp24_public_vec_env_runtime_compatibility_flag_is_absent_from_maintained_adapters`)
is untouched, so no other guard's scan set changed. A new inline comment
records why: I34 sank both vec-env consumers' per-entity command-chain diff
and batch-submit calls into the shared `_shared_ops.py` module (imported as
`diff_single_entity_command_chain`/`submit_command_chain_assignments`), so
neither consumer's own source text still names the maintained assignment
classes/setters directly -- only `_shared_ops.py` does now. No assertion was
loosened; the fix only widens what text the existing assertions run
against, and it strengthens (rather than dilutes) the forbidden-legacy-token
loop, since that loop now also covers the module that physically issues the
writes for both consumers.

**Negative self-proof** (rehearsed against an in-memory copy; the
worktree's `_shared_ops.py` was never written to): a standalone script
living outside the worktree imported the real, unmodified test function,
used `unittest.mock.patch.object` to intercept `pathlib.Path.read_text` for
exactly the `_shared_ops.py` path so it returns a sabotaged copy with
`runtime_adapter.set_pilot_reports_maintained_batch(report_assignments)`
reverted to the legacy `runtime_adapter.set_pilot_reports_batch(report_assignments)`
(every other path's `read_text` fell through to the real file unchanged),
then called the test function directly:

```
--- sanity: guard passes against the REAL (unsabotaged) _shared_ops.py ---
OK: real worktree state is green, as expected.

--- negative self-proof: guard against a SABOTAGED in-memory copy ---
GUARD WENT RED AS EXPECTED. Traceback:
  File ".../test_tasking_batch_contract_boundaries.py", line 295, in
    test_wp24_python_command_chain_business_writes_use_maintained_contracts
    assert "set_pilot_reports_maintained_batch" in source
AssertionError

--- post-check: worktree _shared_ops.py is untouched on disk ---
OK: worktree _shared_ops.py byte-identical to before the rehearsal.
```

**Verification** (this worktree, `CMO_BUILD_DIR=<worktree>/build-local-win`):

```
pytest -q tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py
-> 3 passed (previously 2 passed, 1 failed)

pytest -q tests/architecture/runtime_facade
-> 67 passed, 4 failed -- the same four test_wp22_* nodes this ledger's
   section 5 already lists (test_runtime_escape_hatches.py); no new reds

pytest -q tests/architecture/policy_execution/test_intent_injection_authority_guard.py
-> 4 passed, 1 failed -- the same test_wp12_* node this ledger's section 5
   already lists; unaffected by this fix (different file, outside this
   fix's write set)

python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
-> 439 passed, 45 subtests passed -- measured before this ledger edit. The
   I39 review measured the final write set at 438 passed / 1 failed (the
   bilingual-registry flag raised by this very ledger edit, whose hash
   refresh is a landing-side duty per the iteration brief); resolved by the
   registry refresh at the I39 landing, re-verified green on the landed tree

ruff check tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py
-> All checks passed!

git diff --check    -> clean
```

Write set for this fix: `tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py`
(guard adaptation only) plus this ledger's own registration (this
section). No `python/rl/runtime/world_batch/**` production code changed --
this was a guard-adaptation gap, not a functional defect.

### 6.2 I42 fix and re-verification (sibling gap)

**Fix**: `test_batch_envs_use_tasking_bridge_for_command_chain_sync`
(`tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py`,
`GroundRuntimeSourceBridgeTests`) now reads
`python/rl/runtime/world_batch/_shared_ops.py`'s source text once and
appends it (joined with `"\n"`) onto each of the two per-file scan texts
(`vec_env.py`'s and `cooperative_world_batch_vec_env.py`'s own
`read_text()` result) before running the same nine `assertIn`/
`assertNotIn` checks the test already had. The change is scoped to this
one test function only; every other test in this file, and every other
guard anywhere else in the suite, is untouched. A new inline comment
(`NOTE(I42)`) records why, using the same local-splice pattern as I39's
wp24 guard repair (section 6.1 above,
`tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py`):
I34 sank both vec-env consumers' per-entity command-chain diff and
batch-submit calls -- including the `build_kernel_mission_command` call
this guard watches for -- into the shared `_shared_ops.py` module
(imported as `diff_single_entity_command_chain`/
`submit_command_chain_assignments`), so neither consumer's own source text
names `build_kernel_mission_command` or the maintained batch setters
directly anymore -- only `_shared_ops.py` does now. The comment also notes
that this guard's original "vec_env/cooperative import directly from
`bridge.py`" framing is now satisfied through their shared `_shared_ops.py`
dependency rather than a same-file import, so the framing is updated to
match that fact -- but no assertion was loosened or removed: every
positive check still requires the real token to be present somewhere in
the sunk call chain (`_shared_ops.py` carries all five positive tokens the
guard requires and none of the four forbidden legacy tokens, confirmed by
inspection before the edit -- the I42 review additionally ran the substring
check proving no maintained name contains a legacy name), and every
forbidden-legacy-token check is strengthened rather than weakened, since it
now also covers the module that physically performs the writes.

**Negative self-proof** (rehearsed against an in-memory copy; the
worktree's `_shared_ops.py` was never written to): a standalone script
living outside the worktree imported the real, unmodified
`GroundRuntimeSourceBridgeTests` test case, used `unittest.mock.patch.object`
to intercept `pathlib.Path.read_text` for exactly the `_shared_ops.py` path
so it returns a sabotaged in-memory copy with every
`build_kernel_mission_command` occurrence renamed to
`renamed_kernel_mission_command_symbol` (every other path's `read_text`
fell through to the real file unchanged), then ran the test case directly
via `TestCase.debug()`:

```
--- sanity: guard passes against the REAL (unsabotaged) _shared_ops.py ---
OK: real worktree state is green, as expected.

--- negative self-proof: guard against a SABOTAGED in-memory copy ---
GUARD WENT RED AS EXPECTED. Traceback:
  File ".../test_ground_runtime_lifecycle_bridge.py", line 129, in
    test_batch_envs_use_tasking_bridge_for_command_chain_sync
    self.assertIn("from python.rl.tasking.bridge import build_kernel_mission_command", text)
AssertionError: 'from python.rl.tasking.bridge import build_kernel_mission_command'
not found in '...renamed_kernel_mission_command_symbol...'

--- post-check: worktree _shared_ops.py is untouched on disk ---
OK: worktree _shared_ops.py byte-identical to before the rehearsal.
```

**Verification** (this worktree, `CMO_BUILD_DIR=<worktree>/build-local-win`):

```
pytest -q tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
-> 4 passed (previously 3 passed, 1 failed -- the node this section fixes)

pytest -q tests/runtime/mission
-> 90 passed, 8 subtests passed (previously 1 failed, 89 passed, 8 subtests
   passed -- the fixed node was this directory's only red; no other node
   changed)

python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
-> 446 passed, 45 subtests passed -- measured before this ledger edit.
   `tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py` is not a
   member of the smoke manifest (`tests/smoke/ci_smoke_suite.json` lists
   five other `tests/runtime/mission/*` files but not this one), so this
   guard's red/green state does not move this count either way.
   445 passed, 1 failed, 45 subtests passed -- measured after this ledger
   edit (this file plus its `.zh.md` peer): the one new red is the
   bilingual-registry hash flag this edit itself raises
   (`test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface`),
   same mechanism as the I39/I41 landings; its `clusters --write` refresh
   is a landing-side duty per the iteration brief, not part of this fix's
   write set. `python tools/maintenance/translate_docs_batch.py audit`
   (no `--write`; read-only comparison against the registry) confirms
   `pair_count: 80`, `synced: 79`, `diverged: 1`, with
   `plan/unified_architecture_program/t6_residual_ledger` (this document
   pair) as the sole diverged entry.

ruff check tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
-> All checks passed!

git diff --check    -> clean
```

Write set for this fix: `tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py`
(guard adaptation only) plus this ledger's own registration (this
section, both languages). No `python/rl/runtime/world_batch/**` production
code changed -- this was a guard-adaptation gap, not a functional defect,
same as the wp24 sibling this section's parent entry cross-references.

## 7. I41: T3 second slice -- six-item include-direction violation evaluation matrix (one converged, five deferred)

I38 ratcheted six pre-existing include-direction violations into
`tests/architecture/fixtures/cpp_include_direction_allowlist_20260720.json`
(see the I38 register row). I41 (T3's second slice) re-evaluated all six
against the "safe to converge now vs. genuinely deferred structural/design
gap" question, with a full consumer/binding census for each, and implemented
the one that came back low-risk. This section is the evaluation matrix and
disposition record the allowlist's own amendment note points at; the
allowlist entries themselves carry the same conclusions inline (see each
entry's `reason` field after the I41 amendment).

| # | Edge (`from_group` -> `to_group`) | Verdict | One-line reason |
| --- | --- | --- | --- |
| a | `components/combat/common/weapon_common.h:12` -> `models/weapons/kalman_seeker.h` | **Converged** | `SeekerEkfState`/`SeekerEkfParams` had exactly four touchpoints (the definition site, one embedding site, one math-function call site, one direct-include test) and zero Python bindings; relocating the two structs to a components-owned leaf closes the edge with a byte-identical type move. |
| b | `core/engine/world_batch_runtime.cpp:9` -> `gpu/gpu_interaction_broadphase_runtime.h` | Deferred | Four call sites inside the interaction-broadphase path call `gpu::` packed types/functions directly; closing this needs the GPU/engine integration seam itself, not a type move. |
| c | `core/engine/world_batch_runtime.h:12` -> `core/mission/episode/execution_episode_controller.h` | Deferred | `ExecutionEpisodeController` batch ownership is read/written by nine `WorldBatchRuntime` methods; relocating ownership is a WP4 hot-path design decision (the facade/mission-owned batch wrapper the I38 `next_gate` names), not a type move. |
| d | `core/engine/world_batch_runtime.h:13` -> `gpu/gpu_visual_runtime.h` | Deferred | `WorldBatchVisualBindingCompatibilityScene` is the return/parameter type of two public `WorldBatchRuntime` batch methods; same GPU/engine seam as (b). |
| e | `core/engine/world_batch_visual_binding_compatibility_helper.h:9` -> `gpu/gpu_visual_runtime.h` | Deferred | The helper's entire purpose is bridging to four `gpu::render_visual_*` entry points; same seam as (b)/(d), not an incidental include. |
| f | `runtime/contracts/world_batch_contracts.h:16` -> `core/mission/episode/execution_episode_batch_prepare.h` | Deferred | `StepEvaluationBatchConfig`/`StepEvaluationBatchEnvState` are consumed throughout `core/mission/episode` and `core/mission/runtime`, individually field-bound in `bindings_episode.cpp`, and `EnvState` alone embeds ten further mission-owned aggregate types by value; relocating verbatim only inverts the violation, and an independent contracts-owned mirror type would duplicate that whole nested-type graph -- a T1 DTO-family-completion-scale migration, not a mechanical move. |

### 7.1 (a) converged: `missile_seeker` EKF state relocated to a components leaf

**Census** (all touchpoints of `missile_seeker::SeekerEkfState`/`SeekerEkfParams`
and the `missile_seeker::` free functions, repo-wide): `src/models/weapons/kalman_seeker.h`
(definition site plus the EKF math functions that operate on the two
structs), `src/components/combat/common/weapon_common.h` (`Missile` embeds
`ekf_state`/`ekf_params` by value at lines 221-222), `src/models/weapons/default_guidance_model.cpp`
(calls `missile_seeker::ekf_init/ekf_predict/ekf_update/ekf_filtered_*/ekf_closing_speed_mps`,
but reached the free functions only *transitively* through
`core/interfaces/guidance_model.h` -> `weapon_common.h` -> `kalman_seeker.h`,
with no direct include of its own), and `src/tests/test_kalman_seeker.cpp`
(includes `kalman_seeker.h` directly; exempt `tests` group, unaffected by
direction policy either way). Neither struct, nor `Missile`, is ever passed
through `nb::class_<...>` -- grepping `src/interfaces/python/*.cpp` for
`Missile`/`ekf` finds only internal ECS `.get<Missile>()` calls, no binding.
`tools/maintenance/dto_schema` has zero references to either struct, so the
move does not touch schema/generator ownership.

**Fix**: new leaf header `src/components/combat/common/missile_seeker_state.h`
holds `namespace missile_seeker { struct SeekerEkfState {...}; struct
SeekerEkfParams {...}; }`, byte-identical to the definitions previously
inline in `kalman_seeker.h` (same field names, types, order, and default
values -- a pure text relocation, not a redesign, so C++ layout/ABI for both
structs and for `Missile` is unaffected by construction, not just by test
evidence). `kalman_seeker.h` now `#include`s this leaf back (`models ->
components`, already policy-allowed) instead of defining the structs itself.
`weapon_common.h`'s include of `models/weapons/kalman_seeker.h` is replaced
with the new leaf include (`components -> components`, same-group, always
allowed). `default_guidance_model.cpp` gained a direct `#include
"models/weapons/kalman_seeker.h"` (it is in the `models` group already, so
this is not a new direction edge) because breaking `weapon_common.h`'s
include of `kalman_seeker.h` also breaks the transitive chain that used to
hand it the EKF math functions -- an IWYU fix the relocation makes mandatory,
not optional. Four files touched (one new, three edited); zero CMake
changes (headers are found via `ef_core`'s public include directory, not
enumerated).

### 7.2 (b)/(c)/(d)/(e) deferred: the GPU/engine and mission-batch-ownership design gaps are real, not mechanical

All four sit on the WP4 hot-path/GPU integration seam the I38 `next_gate`
text already named. I41 re-verified each is a multi-site functional
coupling rather than an incidental include before deferring: (b)'s
`gpu::InteractionBroadphaseConfig`/`InteractionEntityPacked`/`InteractionQueryPacked`
and `gpu::build_interaction_broadphase_*_batch` are called at four sites
inside `world_batch_runtime.cpp`'s interaction-broadphase path; (c)'s
`std::vector<ExecutionEpisodeController> execution_episode_controllers_` is
read or written by `clear_execution_episode_controller_batch`,
`prime_execution_episode_controller_batch`,
`execution_episode_controller_ready`,
`export_execution_episode_states_batch`, `evaluate_execution_episode_batch`,
`step_execution_episode_batch`, `step_execution_episode_results_batch`, and
the two private `checked_execution_episode_controller` overloads -- nine
methods, not one field; (d)'s `WorldBatchVisualBindingCompatibilityScene`
is the return/parameter type of
`collect_visual_binding_compatibility_scenes_from_candidate_ids_batch` and
`collect_visual_binding_compatibility_scenes_batch`, two public batch
methods; (e)'s helper (`world_batch_visual_binding_compatibility_helper.h`)
exists specifically to build `gpu::VisualRenderRequest`/`VisibleObjectPacked`
values and branch between `gpu::render_visual_experiment(_batch_export)`
and `gpu::render_visual_reference_cpu(_batch)`, i.e. the gpu dependency is
the helper's entire reason for existing. None of the four can be closed by
relocating a type; each needs the GPU/engine integration seam (b/d/e) or the
facade/mission-owned batch wrapper (c) the I38 `next_gate` text already
calls for -- an architecture decision belonging to T4 (Exact-runtime
alignment, whose own key risk is exactly this WP4 double-ownership
transition) or the next T3 physical-split slice. Deferred untouched; the
allowlist entries' `reason` fields now record this I41 re-verification
inline (see the allowlist amendment note).

### 7.3 (f) deferred: the mission/contracts DTO pair is a T1-scale migration, not a mechanical relocation

Full consumer/binding census before concluding: `StepEvaluationBatchConfig`/`StepEvaluationBatchEnvState`
(`core/mission/episode/execution_episode_batch_prepare.h`) are consumed by
`core/mission/episode/execution_episode_controller.h`/`.cpp` (the
`evaluate`/`step`/`step_result` methods `WorldBatchRuntime` calls through
`WorldExecutionEpisodeStepRequest.config`/`.env_state`),
`core/mission/episode/detail/episode_transition_runtime.h`/`.cpp`, and
`core/mission/runtime/reward_runtime.h`; both types are individually
field-bound in `interfaces/python/bindings_episode.cpp` (`nb::class_<StepEvaluationBatchConfig>`/`<StepEvaluationBatchEnvState>`,
57 combined `def_rw` calls); and `StepEvaluationBatchEnvState` alone embeds
ten further mission-owned aggregate types by value (`ExecutionEpisodeState`,
`MissionObservationInputs`, `StepInfoInputs`, `SafetyRuntimeInputs`,
`WaypointRewardInputs`, `ApproachRewardInputs`, `ConditionalObjectiveSpec`,
`ConditionalObjectiveInputs`, `ObjectiveShapingConfig`,
`FlightShapingRuntimeInputs`), each also separately bound, and consumed from
four `python/rl/runtime/world_batch/**` call sites
(`vec_env.py`, `_observation_mixin.py`, `cooperative_world_batch_vec_env.py`,
`_execution_episode_mixin.py`).

This census forecloses both remedies the task brief posed as options.
Relocating either struct's physical ownership into `runtime/contracts`
verbatim would require the new contracts header to `#include` whichever of
the ten nested mission-owned types it still embeds by value --
`runtime_contracts`'s policy-allowed target set is `{components}` only (see
`tools/architecture/cpp_include_graph.FINE_GROUP_ALLOWED_TARGETS`), so that
merely inverts the violation into one or more `runtime_contracts ->
core_mission_runtime`/`core_mission_episode` edges, each strictly harder to
defend than the current one (a whole aggregate type embedded by value, not
two flat config/state structs). Defining an independent contracts-owned
transport shape instead of relocating avoids inverting the edge, but only
by duplicating the same ten-type nested graph under a second name that must
then be kept in sync by hand -- trading a governance-gate violation for a
silent-drift risk, and at a scope (ten aggregate types, ~57+ bound fields
across two Python-binding files) matching the T1 DTO-family-completion track
(the natural next single-sourcing candidate per the I31/I33/I35 lineage
already indexed in section 4 above), not a T3 second-slice mechanical
relocation. `python/rl/runtime/world_batch/**` is also outside this
iteration's write-set boundary (I40 is concurrently using it in a sibling
worktree per this iteration's task brief), which independently rules out
touching the Python-visible binding shape this iteration even if the C++
side were otherwise safe. Deferred; the allowlist entry's `reason` field
records this full census inline.

### 7.4 Verification (this worktree, `CMO_BUILD_DIR=<worktree>/build-local-win`, baseline `b618971f`)

```
cmake --build build-local-win --target ef_core ef_py -j4
-> succeeded (incremental; pre-existing third-party spdlog/nanobind template
   warnings only, unrelated to this iteration's diff)

pytest -q tests/architecture/governance/test_cpp_include_direction.py
-> 7 passed (allowlist entries 6 -> 5; the (a) fingerprint is correctly
   flagged stale by the gate before the allowlist edit, proving the gate
   detects the fix rather than the edit being unverified)

tools/maintenance/dto_schema/generate.py --check -> all artifacts up-to-date

ctest (build-local-win) -> 8/8 passed

ef_test.exe --source-file="*test_kalman_seeker*" -> 3 test cases, 17423
assertions, 0 failed (same EKF math now operating on the relocated structs)

pytest -q tests/world_batch tests/architecture/runtime_facade
  tests/runtime/bindings tests/runtime/mission tests/runtime/engagement
  tests/architecture/damage_model/test_release_signoff_gate.py
-> 471 passed, 6 failed, 1 skipped, 28 subtests. All six failures reproduced
   identically on the pre-edit baseline (verified via `git stash`): the four
   `test_wp22_*` nodes and the lazy-binding `common.ef_py` gap already
   indexed in section 5 above, plus one not yet indexed there --
   `tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py::GroundRuntimeSourceBridgeTests::test_batch_envs_use_tasking_bridge_for_command_chain_sync`
   (asserts `vec_env.py`/`cooperative_world_batch_vec_env.py` still import
   `build_kernel_mission_command` from `python.rl.tasking.bridge`; both now
   route command-chain sync through `_shared_ops.py` instead, the same I34
   sink already registered in section 6 -- apparently a sibling guard gap in
   a different test file that section 6's I39 fix did not cover). Confirmed
   unrelated to this iteration's diff (stash test: still red with this
   iteration's changes removed) and out of this iteration's write-set
   boundary (neither the test nor `vec_env.py`/`bridge.py` was touched);
   surfaced here for visibility only, not adjudicated or fixed by this
   section.

python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
-> 446 passed, 45 subtests passed (unchanged from this iteration's I38/I39
   baseline)

Cross-build parity: the (b)-(f) edges' types do carry Python bindings
elsewhere (`gpu::InteractionBroadphaseConfig`/packed views in
`bindings_gpu.cpp`, `ExecutionEpisodeController` in `bindings_episode.cpp`,
and `StepEvaluationBatchConfig`/`EnvState` field-bound per section 7.3), but
those five edges were untouched this iteration, so their binding surfaces
are unaffected by construction; the one converged move, (a), involves only
`Missile`/`SeekerEkfState`/`SeekerEkfParams`, which are never bound --
grepping `src/interfaces/python/*.cpp` finds no `nb::class_<Missile>` and no
`ekf`-named binding call. (Wording corrected at the I41 landing per review:
the original "zero of the six edges' types are ever bound" claim
contradicted section 7.3's own citation of the (f) bindings.) With zero Python-bound
classes actually affected by this iteration's one converged move, the
"affected classes" parity set is empty by construction; two sentinel
contracts classes (`WorldEntityRef`, `TypedPlatformSpawnRequest`) were
dumped (`dir()` plus a depth-4 recursive default-value snapshot) from both
the pre-existing `D:\workshop\Research\Echelon-Forge\build-local-win`
(2026-07-18) build and this worktree's rebuilt `ef_py`: both fields
(`dir_public`, `default_value_snapshot`) compared byte-identical for both
classes, evidencing the diffing harness itself is sound and this worktree's
rebuild introduced no incidental Python-surface drift.

ruff check .        -> All checks passed!
git diff --check    -> clean
```

Write set for this section's converged fix: `src/components/combat/common/missile_seeker_state.h`
(new), `src/components/combat/common/weapon_common.h`,
`src/models/weapons/kalman_seeker.h`, `src/models/weapons/default_guidance_model.cpp`
(4 files), plus the allowlist fixture (entry removed and remaining five
amended) and this ledger section. No `python/**` or `examples/**` touched;
no CMake target changes.

### 7.5 (f) re-adjudicated this iteration (2026-07-27): the T1 schema-ownership route is foreclosed; the edge is held

This iteration (queue I81, T1/T3; activation gate: the I80 evidence landed at
`407eea22`) re-opened section 7.3's deferral with one specific question the
I41 census had not directly answered: can `tools/maintenance/dto_schema`
own the borrowed types so that both sides generate from one source
byte-equivalently, the way the I33 engagement family's contracts-owned leaf
(`src/runtime/contracts/detail/engagement_entity_ref.inc`, included by
`engagement_contracts.h` and `bindings_runtime.cpp`, with mission including
contracts back along the policy-allowed direction) single-sources shared
types? Verdict: **held**, foreclosed on three grounds verified against
source this iteration:

1. **The I33 pattern requires a leaf-closed field list; this one is not.**
   The contracts-owned-leaf trick works when every field is a scalar,
   string, or vector thereof, so the generated `.inc` compiles inside
   `runtime/contracts` without further includes. `StepEvaluationBatchEnvState`
   embeds the ten mission-owned aggregates already censused in section 7.3,
   and the first of them, `ExecutionEpisodeState`
   (`core/mission/episode/execution_episode_state.h`), itself embeds
   `std::vector<SpatialRouteWaypoint>` from
   `core/geometry/spatial_query_runtime.h` (plus `MissionCommand` from
   `components/`, which is permitted). `runtime_contracts`' policy-allowed
   target set is `{components}` only, so a contracts-located definition
   needs new `runtime_contracts -> core_geometry` edges in addition to the
   `runtime_contracts -> core_mission_*` ones section 7.3 already ruled out
   -- a blocker the I41 census had not yet named.
2. **Schema-generated field lists do not evade the gate.** The
   include-direction scanner counts `.inc` textual includes as first-class
   edges (`SOURCE_SUFFIXES` includes `.inc` in
   `tools/architecture/cpp_include_graph.py`), so a contracts-located
   struct that textually includes
   `core/mission/runtime/detail/flight_shaping_shared_fields.inc` (the
   dual-expansion list already shared between `StepEvaluationBatchConfig`
   and `FlightShapingRuntimeInputs`) or any sibling mission-owned `.inc`
   would re-create the violation at the new location with a new
   fingerprint. Byte-equivalent generation of the *field lists* is
   achievable; byte-equivalent closure of the *include graph* is not.
3. **The one leaf-closed fragment is not worth moving.**
   `StepEvaluationBatchConfig` alone could relocate (it is flat once the
   shared flight-shaping `.inc` also moves to `runtime/contracts/detail/`,
   which mission may legally include back), but the allowlist fingerprint
   pins the `execution_episode_batch_prepare.h` include, which
   `env_state`'s type still forces; the entry would survive verbatim, the
   allowlist would not shrink, and the move would expose the
   `StepEvaluationBatchConfig` ABI (member order preserved but physical
   relocation churn across every mission consumer) for zero gate progress.

The binding surface was re-verified this iteration: 57 `def_rw` = 15
(`StepEvaluationBatchConfig`) + 42 (`StepEvaluationBatchEnvState`) in
`interfaces/python/bindings_episode.cpp`, unchanged from the I41 census.

Held-verdict artifacts (this iteration's write set): a dated adjudication
comment at the include site in `src/runtime/contracts/world_batch_contracts.h`
(the include moved line 16 -> 34, so the allowlist fingerprint's `line`
field was updated in the same edit); the allowlist entry
(`tests/architecture/fixtures/cpp_include_direction_allowlist_20260720.json`,
`allowlist_version` v2 -> v3) with the re-adjudication appended to its
`reason` and its `owner`/`next_gate` retargeted at the T1
DTO-family-completion migration; a dedicated held-edge pin test in
`tests/architecture/governance/test_cpp_include_direction.py`
(`test_the_contracts_to_mission_step_request_edge_stays_held_with_its_adjudication`)
asserting the single `runtime_contracts` entry, its adjudication markers,
the include-site comment, and the 15/42 binding split, so binding drift or
a second contracts violation forces explicit re-adjudication (the gate file
is already registered in `tests/smoke/ci_smoke_suite.json`, so no new
registration was needed); and this section plus its `zh` twin. The exit
condition for closing the edge is unchanged and now machine-pinned: the T1
DTO-family-completion migration that relocates or single-sources the full
nested type graph with 57-binding parity, editing the pin test explicitly.
The dependency direction is not to be reversed.

Verification (this worktree, `CMO_BUILD_DIR=D:\workshop\Research\EF-landing\build-local-win`,
baseline `1a456e29`): `pytest -q
tests/architecture/governance/test_cpp_include_direction.py` -> 8 passed
(7 pre-existing + the new held-edge pin);
`tools/maintenance/dto_schema/generate.py --check` -> all artifacts
up-to-date; maintained smoke recorded at this iteration's landing.

## 8. I57: T6 second residual-payoff pack (seven-item disposition)

Baseline commit `fae17eb8`; verified on this worktree against the shared
read-only CPU snapshot (`CMO_BUILD_DIR=D:\workshop\Research\EF-w2-training\build-local-win`;
no CMake/build was triggered, and the write set is pure Python/JSON/docs).
This iteration reproduced each of the seven governable reds section 5 tracks,
root-caused each from source (not from section 5's prior hypotheses), and
disposed each by nature. Notably, three reds section 5 provisionally read as
"the refactor landed on another lineage and never came here" turned out, on
direct inspection, to be reds where the refactor **did** land here but the
guard scans the pre-relocation location/spelling -- so they are guard-adapted
to green (I39/I42 precedent) rather than xfail-governed. Only one lineage red
(item 7) is genuinely unadaptable and is governed with `xfail(strict=True)`.

### 8.1 Disposition summary

| # | Node / target | Reproduced red | Root cause (source evidence) | Disposition |
| --- | --- | --- | --- | --- |
| 6 | `test_source_evidence_governance.py` (whole file) | standalone `1 failed, 16 passed, 5 errors` | `rights_output_policy.py` fed a `None` `result.stdout` into `re.sub` (line 107): `text=True` decoded pdftotext's valid-UTF-8 output with the Windows console codepage (GBK); the reader thread died mid en-dash sequence (`e2 80 93`, at its `0x93` byte), and `result.stdout` became `None` | **Real-defect fix -> green** (8.2) |
| 1 | four `test_wp22_*` in `runtime_facade/test_runtime_escape_hatches.py` | `4 failed` | each fails only at its "definition lives in `bridge.py`" assertion; I24 relocated the loader-owned seam classes/functions into `python/tasking_contracts/bridge_views.py` (bridge.py now re-exports the identical objects) -- rg confirms all definitions live there, all consumer files already use the named seams | **Guard adaptation -> green** (8.3) |
| 2 | `policy_execution/test_intent_injection_authority_guard.py::test_wp12_runtime_facade_does_not_gain_a_second_maintained_injection_api` | `1 failed` | the `run_window` API is present (`runtime_facade.h:116`) and the coordinator carries every asserted token; the only mismatch is C++ `&` binding style (`const RuntimeWindowRequest &request` vs the guard's `RuntimeWindowRequest& request`) | **Guard adaptation -> green** (8.4) |
| 3 | `runtime/bindings/test_lazy_binding_resolution.py::...::test_common_import_prefers_repo_build_ef_py` | `AttributeError: ... has no attribute 'ef_py'` | this lineage resolves ef_py through the private lazy `_ef_py()` helper (no eager module-level `ef_py` attribute; rg finds zero production consumers of `common.ef_py`) | **Guard adaptation -> green** (8.5) |
| 7 | `governance/test_tools_script_governance.py::test_diagnostics_top_level_entrypoints_are_governed_by_function` | `1 failed` (11 extra top-level scripts) | the diagnostics "governed by function" top-level consolidation to the 15-entry approved set never landed here; adapting the allowlist would bless the very sprawl the guard forbids | **`xfail(strict=True)`** (8.6) |
| 5 | `gpu/test_cuda_import_order.py::...::test_world_batch_vec_env_import_after_torch_runtime_setup` | `1 failed` (`ModuleNotFoundError: ef_py`) | the test hardcodes a `build-gpu/` GPU CUDA build tree that CPU-only worktrees never materialize | **Conditional skip** (8.7) |
| 4 | `run_scenario_contract.py --spec .../leader_phase_manager_approach_arm.json` | `expected approach-arm transition count mismatch: 0` | pure-Python phase-manager divergence: this lineage's `RuleBasedLeaderPhaseManager` gates arming on `approach_arm_require_runway_frame=True` via `loader.get_runway_local_frame(...)`, which the contract harness's `FakeLoader` never implements (and its `_activate_post_waypoint_transition(self)` also predates the current `sync_to_kernel=` call convention) | **Classified (lineage; harness lag)** (8.8) |

### 8.2 Item 6 -- real-defect fix: source-rights PDF probe None/locale-decode

**Root cause**: `tools/maintenance/source_governance/rights_output_policy.py::_pdf_text_probe`
ran `subprocess.run(["pdftotext", ...], capture_output=True, text=True)`.
`text=True` decodes the child's stdout with the console locale codec, which on
this Windows host is GBK. pdftotext (MiKTeX) emits the retained DENIX PDFs'
page text as **valid UTF-8** (fact corrected at the I57 review round, which
this iteration re-verified directly: strict UTF-8 decode of both retained
PDFs' raw probe bytes succeeds -- TP-20 14,413 bytes, TP-21 14,204 bytes --
and the `0x93` byte named by the GBK error `'gbk' codec can't decode byte
0x93 in position 70` sits at offset 70 inside the UTF-8 en dash `e2 80 93`
(`b"r \xe2\x80\x93 Op"`), not a cp1252 smart quote as this section first
claimed); the GBK reader thread raised `UnicodeDecodeError` mid-sequence, so
`result.stdout` came back `None`. `_public_distribution_statement(None)` then reached
`_normalize_statement_text` (line 107) which called `re.sub(r"\s+", " ", None)`
-> `TypeError: expected string or bytes-like object, got 'NoneType'`. The
whole-file run was `1 failed, 16 passed, 5 errors` (the module-scoped
`source_rights_policy_bundle` fixture crashed in setup, erroring its five
consumers; the CLI test failed via the same crash in a subprocess) -- and the
file's rights-inventory assertions additionally require the PDF statements to
actually be detected (`statement_id == "distribution_statement_a_public_release_unlimited"`
for TP-20, `"public_release_distribution_unlimited"` for TP-21), so a
None->fail-closed patch alone would have kept the file red.

**Fix** (production, pure-Python; hardened at the I57 review round):
`_pdf_text_probe` now captures raw bytes (drops `text=True`) and decodes them
as **strict** UTF-8; on `UnicodeDecodeError` the probe returns a dedicated
fail-closed shape (`extraction_status="pdf_text_probe_decode_error_fail_closed"`,
every statement flag `False`, `statement_locator` kept), following the
`pdftotext_missing`/`timeout` branches' convention, so undecodable output can
never produce a rights-statement hit. The first I57 patch had decoded with
`errors="ignore"`; the independent review showed that to be **fail-open** --
a forged stream carrying a malformed byte inside a rights phrase
(`b"RE\xffLEASE"`) had the byte silently dropped, splicing `"RELEASE"` back
together and false-positively yielding
`statement_id="public_release_distribution_unlimited"` (reproduced in-process
this round) -- and also unnecessary, since the real payload output is valid
UTF-8 (see the corrected root cause above); the lossy decode was replaced by
strict-decode-or-fail-closed within this same iteration.
`_normalize_statement_text` retains the `None`/empty guard that fail-closes
to `""` (pinning the caller contract's "no extractable statement" case to the
same verdict the `pdftotext_missing`/`timeout` branches already return).
Running the fixed probe end-to-end against the real retained payloads (real
pdftotext) confirms the strict path succeeds and detects
`distribution_statement_a_public_release_unlimited` for TP-20 and
`public_release_distribution_unlimited` for TP-21.

**Focused unit tests** (new, `tests/architecture/damage_model/test_rights_output_policy_probe.py`,
9 tests, hermetic -- monkeypatches `subprocess.run`, no real pdftotext/payload
needed). The fake `subprocess.run` stub itself locks the capture mode: it
asserts the probe passes `capture_output=True` and never
`text=True`/`universal_newlines=`/`encoding=`/`errors=` (review repair: the
first stub ignored kwargs and returned bytes regardless, so a future
`text=True` regression would have stayed green in the test while crashing the
real path). Coverage: `None`/empty normalization; `None` statement evaluation
fail-closed; strict decode of valid multi-byte UTF-8 (an en-dash payload
mirroring the real TP-20 content) detecting the correct `statement_id`; the
TP-21-style id; the review's forged malformed-byte stream failing closed with
zero hits; `stdout=None` handled without crash and with zero hits; and the
missing-binary branch. Test-nature accounting (correcting this section's
original "each test was red pre-fix" claim, which the review disproved --
three already passed at baseline): **six** tests pin new post-fix behavior
and are red against the pre-fix module (`..._tolerates_missing_text`,
`..._none_is_fail_closed` (statement), `..._decodes_utf8_multibyte_text`,
`..._public_release_without_statement_a`, `..._malformed_bytes_fail_closed`,
`..._none_stdout_is_fail_closed`); **three** are regression guards that
already passed pre-fix and pin unchanged behavior
(`..._collapses_whitespace_and_uppercases`, `..._detects_statement_a`,
`..._missing_binary_is_fail_closed`). Red->green for the review scenario,
demonstrated in-process: against the interim `errors="ignore"` logic the
forged stream yields `statement_detected=True` /
`statement_id='public_release_distribution_unlimited'` (fail-open); against
the strict-decode fix the same stream raises
`UnicodeDecodeError: ... can't decode byte 0xff in position 22` inside the
probe, which fail-closes with zero hits (the new
`test_pdf_text_probe_malformed_bytes_fail_closed` pins exactly this). The
original `None`-path red proof stands: the pre-fix
`_normalize_statement_text`/`_public_distribution_statement(None)` raise the
identical `TypeError: expected string or bytes-like object, got 'NoneType'`.

**Verification**:

```
pytest -q tests/architecture/damage_model/test_rights_output_policy_probe.py
-> 9 passed (6 new-behavior pins red pre-fix; 3 regression guards green pre-fix)

pytest -q tests/architecture/damage_model/test_source_evidence_governance.py
-> 22 passed   (was 1 failed, 16 passed, 5 errors; re-verified after the
   strict-decode hardening)
```

Mixed-run (order-sensitivity) is re-verified in 8.10's whole-`damage_model`
sweep.

### 8.3 Item 1 -- guard adaptation: four wp22 loader-owned-seam guards

**Root cause (source evidence)**: each of the four `test_wp22_*` guards in
`tests/architecture/runtime_facade/test_runtime_escape_hatches.py` fails only
at the assertion that a seam **definition** lives in
`python/rl/tasking/bridge.py` (e.g. `class LoaderOwnedRuntimeView:`,
`class LoaderOwnedScriptedOpponentKernelView:`,
`def apply_loader_owned_world_layout_to_kernel(...)`). bridge.py's own header
comment records that I24 relocated these loader-owned runtime views and the
profile-independent command-chain/mission-command seam helpers into the
neutral `python/tasking_contracts/bridge_views.py`; bridge.py now imports and
re-exports the identical objects. rg confirms every asserted definition
(classes at bridge_views.py:88/177, `get_unit_position/velocity`/`is_unit_active`
at 140/143/146, `loader_owned_runtime_view`/`loader_owned_scripted_opponent_kernel_view`/
`apply_loader_owned_world_layout_to_kernel` at 233/237/241, the four
`sync_task_order/leader_intent/pilot_report/mission_command` methods at
124-136, `sync_loader_mission_command`/`sync_loader_command_chain_reentrant`
at 312/335) lives in bridge_views.py, and every forbidden/legacy token asserted
absent (`loader_owned_raw_sim_compat`, `LoaderOwnedRawSimCompatibilityFacade`,
`*_compat`, `loader.sim.set_*`) has zero hits in either file. The consumer-file
assertions (naval_screen.py/scripted_opponents.py/loading.py already use the
named seams and no raw `loader.sim.*`) all already pass.

**Disposition (guard adaptation, I39/I42 precedent, no assertion weakened)**:
`tests/architecture/runtime_facade/helpers.py` gains a
`TASKING_BRIDGE_VIEWS` constant and a `_tasking_bridge_source()` helper that
returns bridge.py's text spliced with bridge_views.py's; the four guards now
read `bridge_text`/`text` from it. Every positive token is still required
present in the combined seam text; every forbidden token is now required
absent from **both** files, which strengthens (not loosens) the negative
checks. This is the exact "the write moved to a sibling module; widen the scan
set" move I39/I42 made for the `_shared_ops.py` command-chain sink.

Result: `test_runtime_escape_hatches.py` `4 failed -> 0 failed`.

### 8.4 Item 2 -- guard adaptation: wp12 facade run_window signature

**Root cause (source evidence)**: the RuntimeWindow machinery is fully present
in this lineage. `runtime_facade.h:116` declares
`RuntimeWindowResult run_window(const RuntimeWindowRequest &request);`;
`runtime_window_coordinator.h` carries `classify_runtime_window_inputs`
(line 55), `"source_layer is required"` (77), `"input_snapshot_version is
required"` (82); the three C++-compile wp12 tests in the same file pass; and
the facade header carries none of the forbidden second-injection-API tokens.
The guard's sole failing assertion differs from source only in C++ reference
binding style: it expects `RuntimeWindowRequest& request` (`&` bound to the
type) while this lineage's style is `RuntimeWindowRequest &request` (`&` bound
to the name) -- the identical declaration.

**Disposition (guard adaptation, no assertion weakened)**: the single
`run_window` assertion now compares with reference-parameter spacing collapsed
(`" &"`/`"& "` -> `"&"`) on both the needle and the header. The guard still
requires exactly this `RuntimeWindowResult run_window(const RuntimeWindowRequest&)`
declaration to be present -- only the semantically irrelevant `&` binding style
is tolerated. No C++ was touched (red-line honoured). Result: the guard passes.
(Correction to section 5's I35 note: this `test_wp12_*` node lives in
`tests/architecture/policy_execution/test_intent_injection_authority_guard.py`,
not `test_runtime_escape_hatches.py`.)

### 8.5 Item 3 -- guard adaptation: diagnostics common ef_py resolution

**Root cause (source evidence)**: `tools/diagnostics/common.py` resolves ef_py
lazily through a private `_ef_py()` helper (`import ef_py` inside the function
after `ensure_repo_imports()`); it exposes no eager module-level `ef_py`
attribute, so `common.ef_py` raises `AttributeError`. rg across the repo finds
`common.ef_py` referenced only by this test and this ledger -- zero production
consumers. This matches the file's own lazy-binding theme (the sibling tests in
the same module verify modules delay ef_py binding until runtime use).

**Disposition (guard adaptation, intent preserved)**: the assertion becomes
`self.assertEqual(common._ef_py(), ef_py)` -- the resolution API this lineage
actually exposes. This preserves the intent ("common prefers the repo-build
ef_py") without weakening it; the surrounding checks (module path under
`build_dir`, `ConditionalObjectiveProperty`/`WorldBatchRuntime` present) are
unchanged. Result: the node passes.

### 8.6 Item 7 -- xfail(strict): diagnostics top-level consolidation gap

**Root cause (source evidence)**:
`test_diagnostics_top_level_entrypoints_are_governed_by_function` asserts the
top-level `tools/diagnostics/*.py` set equals a 15-entry
`APPROVED_DIAGNOSTICS_TOP_LEVEL`. The actual set has 11 extra ungoverned
scripts (`kill_chain_decoupling_probe`, `kill_chain_expectation_harness`/
`_response_diagnosis`/`_stage_attribution`/`_visualize`,
`kill_chain_guidance_mechanism_ablation`/`_exact_mechanism_ablation`,
`lethality_chain_contract`, `mlf9_statistical_trends`,
`structural_breakup_export`, `calibration_admission_audit`): the "governed by
function" consolidation this guard enforces never landed on this lineage.

**Disposition (`xfail(strict=True)`, I28 precedent, test not deleted)**: this
is the one lineage red that cannot be adapted to green -- widening the allowlist
to admit the 11 extras would bless the exact top-level sprawl the guard exists
to forbid (one extra, `kill_chain_expectation_stage_attribution`, even trips the
guard's own `stage` forbidden-name-part check), so the guard's intent is
genuinely unmet here rather than merely relocated. The test carries
`@pytest.mark.xfail(strict=True, reason=...)` with a machine-readable reason
naming the missing consolidation refactor and pointing at this ledger. Strict
means a future diagnostics consolidation flips it to `XPASS(strict)` failure,
prompting removal of the marker. The file's three other governance tests stay
green.

### 8.7 Item 5 -- conditional skip: tests/gpu build-gpu absent

**Root cause**: `test_world_batch_vec_env_import_after_torch_runtime_setup`
hardcodes `build-gpu/` on `PYTHONPATH` and spawns a subprocess that imports
`world_batch_vec_env` (hence `ef_py`). CPU-only worktrees (this one points
`CMO_BUILD_DIR` at a shared `build-local-win` CPU snapshot) never materialize
`build-gpu/`, so the subprocess raises `ModuleNotFoundError: No module named
'ef_py'`.

**Disposition (conditional skip, not unconditional)**: the method now carries
`@unittest.skipUnless(os.path.isdir(_BUILD_GPU), reason=...)` with a
machine-readable reason pointing at this ledger's build-gpu-absent
environmental entry. On a GPU build tree the check runs unchanged; on CPU-only
trees it reports `SKIPPED` instead of a false red.

### 8.8 Item 4 -- classified: leader_phase_manager_approach_arm contract

**Root cause (source evidence)**: the check is pure Python. Its handler
(`python/testing/contracts/unit/leader.py::leader_phase_manager_approach_arm`)
builds a `FakeLoader` and asserts `loader.transition_calls == 1` after
`RuleBasedLeaderPhaseManager.reset()`. `transition_calls` only increments when
the manager calls `loader._activate_post_waypoint_transition(...)`, gated by
`_should_arm_approach(...)`. In this lineage
(`python/rl/tasking/leader_tasking.py`) that gate defaults
`approach_arm_require_runway_frame=True` (line 315) and returns `False` (line
702) whenever `loader.get_runway_local_frame(...)` does not yield a valid
frame -- and the harness `FakeLoader` never implements `get_runway_local_frame`
(the `try/except` sets `valid_runway_frame=False`), so arming never fires and
`transition_calls` stays `0`. Independently, the manager now calls
`_activate_post_waypoint_transition(sync_to_kernel=...)`, a kwarg the harness's
`_activate_post_waypoint_transition(self)` does not accept -- so even if arming
fired the harness would raise. Both are signs the contract harness (spec +
`FakeLoader`) models an older leader protocol than this lineage's phase
manager.

**Disposition (classified; JSON/runner/harness/production all untouched)**:
this is a lineage divergence between the contract harness and the production
phase-manager logic, not a calibration drift, not a C++/binary behavior, and
not an obvious zero-risk spec defect (making it green would require fabricating
runway-frame geometry in the harness and updating the sink signature -- neither
zero-risk nor within the "spec obvious-defect" fix lane, and modifying the
phase-manager production logic is out of scope by red-line). Per the contract-red
guidance it is registered here with evidence and left untouched. Because this is
a standalone contract-runner check (not a pytest node), it cannot be xfail-governed;
it remains an attributed, documented lineage red until a future iteration
re-syncs the contract harness with the runway-frame arming protocol (repair
direction: teach `FakeLoader` `get_runway_local_frame` + accept `sync_to_kernel=`
on `_activate_post_waypoint_transition`, then supply runway geometry satisfying
`approach_arm_along_min_m`/`approach_arm_cross_abs_max_m`).

### 8.9 Newly surfaced environmental red (full-directory sweep)

Running the whole `tests/architecture/damage_model` directory (prior gates ran
targeted files) surfaced a two-member red family outside the seven-item scope:
`test_candidate_artifact_contracts.py::test_candidate_retained_artifact_pack_writes_retained_files`
(line 611) and
`test_component_probability_artifacts.py::test_component_probability_retained_artifact_pack_writes_retained_files`
(line 655) both assert
`loaded["manifest_relative_path"].endswith("retained_pack/manifest.json")`,
but on Windows the value ends with `retained_pack\manifest.json` (backslash
separator), so the POSIX-slash suffix check fails. (`rg '\.endswith\("[^"]*/[^"]*"\)'`
over the directory confirms these two are the complete family.) This is a
Windows path-separator (OS-conditional) red in the test assertions, unrelated
to any landed write set and to this iteration's changes (they exercise
`retained_pack`/`component_probability` generators, not the source-governance
module). Classified as environmental (same "classify only" family as the
flecs/spdlog/calibration reds); left untouched this iteration.

The same sweep surfaced one further out-of-scope red,
`test_component_fragility_validation.py::test_fragility_benchmark_compares_candidate_to_synthetic_sigmoid`:
its `synthetic_sigmoid_probability` rows come from
`component_fragility_benchmark._comparison_rows`'s
`baseline["baseline_component_failure_probability"]`, i.e. the binary-computed
component-failure-probability surface, and now read ~0.170-0.173 against the
test's hard-coded `0.35168` reference (max relative difference 1.07). This is
product/calibration drift of the same binary-driven component-failure-probability
family section 5 already tracks for the two air-combat calibration-drift reds
(`test_component_failure_probability_surface.py` et al.), not a path/logic
issue -- classified as environmental (calibration), left untouched. Net:
`tests/architecture/damage_model` finishes `3 failed, 263 passed` (re-run
after the review-round strict-decode hardening; one more passed than the
first I57 sweep because the probe file grew from 8 to 9 tests), all three
failures environmental (two Windows path-separator + one calibration drift);
item 6's `test_source_evidence_governance.py` (22) and the new
`test_rights_output_policy_probe.py` (9) are green in this mixed run (the
order-sensitivity section 5 flagged is resolved).

### 8.10 Verification (this worktree, `CMO_BUILD_DIR=<shared CPU snapshot>`)

Per-item red->green (or governed) evidence is inline in 8.2-8.8. Consolidated
gates:

```
pytest -q tests/architecture/runtime_facade tests/architecture/policy_execution
       tests/runtime/bindings tests/architecture/governance
-> 233 passed, 1 xfailed, 1 failed. The xfail is item 7. The one failure is
   test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface
   -- the bilingual-registry hash flag this very ledger edit raises (landing-side
   `clusters --write` duty per the iteration brief, not a fix regression).
   Items 1/2/3 are green; no other reds.

pytest -q tests/architecture/damage_model
-> 3 failed, 263 passed (re-run after the review-round strict-decode
   hardening; the probe file grew 8 -> 9 tests). All three failures are
   environmental and out of the seven-item scope (section 8.9): two Windows
   path-separator reds and one component-fragility calibration-drift red.
   Item 6's test_source_evidence_governance.py (22) and the new
   test_rights_output_policy_probe.py (9) are green in this mixed run.

pytest -q tests/gpu/test_cuda_import_order.py
-> 1 skipped   (item 5 conditional skip)

ruff check .        -> All checks passed!
git diff --check    -> clean
python tools/maintenance/translate_docs_batch.py audit   (read-only)
-> pair_count 86, synced 85, diverged 1 (this ledger pair is the sole diverged entry)
```

Full smoke (`tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json`):
`1 failed, 458 passed, 45 subtests passed`. The smoke manifest is intentionally
left unchanged (none of the adapted guards are smoke members, and the new focused
probe test is kept out to match the suite's existing exclusion of source-governance
tests and its speed budget). The one failure -- and the `458` vs the `459`-passed
baseline -- is exactly the expected bilingual-registry hash flag this ledger edit
raises (`test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface`),
whose `clusters --write` refresh is a landing-side duty per the iteration brief.

### 8.11 Write set (this iteration)

- `tools/maintenance/source_governance/rights_output_policy.py` (item 6 production fix)
- `tests/architecture/damage_model/test_rights_output_policy_probe.py` (item 6 focused unit test, new)
- `tests/architecture/runtime_facade/helpers.py` (item 1 scan-set widening: `TASKING_BRIDGE_VIEWS` + `_tasking_bridge_source()`)
- `tests/architecture/runtime_facade/test_runtime_escape_hatches.py` (item 1 guard adaptation)
- `tests/architecture/policy_execution/test_intent_injection_authority_guard.py` (item 2 guard adaptation)
- `tests/runtime/bindings/test_lazy_binding_resolution.py` (item 3 guard adaptation)
- `tests/architecture/governance/test_tools_script_governance.py` (item 7 xfail-strict)
- `tests/gpu/test_cuda_import_order.py` (item 5 conditional skip)
- `docs/plan/unified_architecture_program/t6_residual_ledger.md` / `.zh.md` (this section + section 5 status updates)

No C++, `examples/**`, `docs/plan/repository_consolidation/**`, contract JSON,
or contract runner touched; no CMake/build triggered.

## 9. I65: T6 third residual-payoff pack (six-item disposition)

Baseline commit `0aa76a00` (I64). Tests and docs only -- no production code
touched. This iteration reproduced each of the six reds a prior scoping pass
listed as still open after I57, root-caused each from source, and disposed each
by nature. Two diagnoses **disagreed with the incoming classification** and are
called out explicitly in 9.2, because both change what the disposition means.

### 9.1 Disposition summary

| # | Node / target | Reproduced red | Root cause (source evidence) | Disposition |
| --- | --- | --- | --- | --- |
| 1 | `damage_model/test_candidate_artifact_contracts.py::test_candidate_retained_artifact_pack_writes_retained_files` (line 611) | `1 failed` | the assertion suffix-matches a POSIX-slash string against an **absolute `tmp_path`** value (`...\test_candidate_retained_artifa0\retained_pack\manifest.json`); production `_display_path` correctly emits posix only for repo-relative paths and falls back to `str(path)` for paths outside the repo root | **Test-assertion fix -> green** (9.3) |
| 2 | `damage_model/test_component_probability_artifacts.py::test_component_probability_retained_artifact_pack_writes_retained_files` (line 655) | `1 failed` | identical to item 1 (same assertion, same `_display_path` fallback in `component_probability_retained_pack.py`) | **Test-assertion fix -> green** (9.3) |
| 3 | `compatibility_quarantine/test_guard_enforcement.py` + `runtime_spine/test_clock_domain_enforcement.py` | collection error, whole files | module-level `dependency_include_path("flecs")` raises `AssertionError` at import, aborting collection for **every** test in both files -- including the 9 text/AST guards that need no C++ toolchain. The configured CPU snapshot ships `_deps/flecs-build` without `_deps/flecs-src` | **Conditional skip** (9.4) |
| 4 | `platform_spawn/test_default_factory_spawn_plan_resolution.py` | collection error, whole file | identical mechanism for `spdlog` (and `flecs`/`nlohmann_json`); aborted collection for the three header-text guards a later T11 slice gates on | **Conditional skip** (9.4) |
| 5 | `air_combat/test_component_failure_probability_surface.py::test_mlf5c_direct_hit_load_floor_prevents_blast_tail_valley` | `1 failed` | binary-side component-attribution drift: `component_primary_name` is now `left_horizontal_tail_actuator_or_surface_component`, not `engine_core` (line 319 -- **not** the load-floor assertion the ledger's row title implies) | **`xfail(strict=True)`** (9.5) |
| 6 | `air_combat/test_live_detonation_event_surface.py::test_live_detonation_exports_standard_warhead_spatial_and_component_events` | `1 failed` | binary-side effects drift: `effects.outcome_state == 'detonated_no_effect'` vs `'damage_applied'` -- the warhead detonates but applies no damage | **`xfail(strict=True)`** (9.5) |
| 7 | `damage_model/test_component_fragility_validation.py::test_fragility_benchmark_compares_candidate_to_synthetic_sigmoid` | `1 failed` | `synthetic_sigmoid_probability` traces through `component_fragility_benchmark._synthetic_baseline_rows` -> `surface_probe._sample_primary_event`, i.e. the same binary-computed surface as items 5/6; reads ~0.1699-0.1729 vs the hard-coded `0.35168` | **`xfail(strict=True)`** (9.5) |

### 9.2 Two diagnoses that disagreed with the incoming classification

**(a) The flecs/spdlog reds are not inherent to a CPU-only worktree.** They
were handed to this iteration as environmental, to be governed on the
section 8.7 precedent. Governing them is still correct, but the root cause is
narrower than "this machine cannot build flecs": the reds are a **build-snapshot
completeness** artifact. The snapshot section 8.10 used
(`EF-w2-training/build-local-win`) contains only `_deps/flecs-build`; a sibling
worktree's snapshot (`EF-w3-flightshaping/build-local-win`, built 2026-07-26)
carries the full `_deps` source trees (`flecs-src`, `spdlog-src`,
`nlohmann_json-src`, ...). Pointing `CMO_BUILD_DIR` at the complete tree runs
**all 24 tests across the three files green, with zero skips** (verification in
9.6). So the skip predicate had to key on actual dependency-include presence --
which it does -- and the skip must never fire on a properly configured tree.
This is recorded because it changes the repair direction for these rows: they
close by configuring/retaining a complete build tree, not by any code change.
It also means section 5's long-standing "5 flecs static-lib link-signature
reds" row was never a lineage or platform defect.

**(b) Item 5's ledger row mis-describes its own failure.** Section 5 and the
scoping pass both carry this node as a load-floor/blast-tail-valley red. It
does not fail there. It fails one assertion earlier, at line 319, on
**component attribution** (`engine_core` ->
`left_horizontal_tail_actuator_or_surface_component`); the load-floor
assertions on lines 320-324 are never reached. The disposition
(`xfail(strict=True)`) is unchanged, but the xfail reason names the actual
drift rather than the inherited mis-description, so a future recalibration is
diagnosed against the right symptom.

Neither disagreement upgraded a red into a genuine regression: see 9.5 for the
inherence proof that kept items 5-7 in the calibration-drift lane.

### 9.3 Items 1-2 -- test-assertion fix: Windows path separator

**Root cause (source evidence)**: both tests call
`load_retained_artifact_pack_manifest(repo_root=REPO_ROOT, output_dir=tmp_path / "retained_pack")`.
Both `component_probability_retained_pack.py` and the candidate-side
`effect_scale_retained_pack.py` compute the value with a local `_display_path`
that returns `path.relative_to(repo_root).as_posix()` **and falls back to
`str(path)` on `ValueError`**. `tmp_path` is outside the repo root, so the
fallback fires and the value is an absolute native-separator path. The reds are
therefore defects in the assertions, not in production code, and not
OS-conditional accidents of the generator.

**Fix (assertion strengthened, production untouched)**: each assertion now
compares a `Path` against the path the test itself constructed:

```python
assert (
  Path(loaded["manifest_relative_path"])
  == tmp_path / "retained_pack" / "manifest.json"
)
```

`Path` equality normalizes the separator on every platform, so the check is
OS-agnostic. It is **stronger** than the original: the suffix check accepted
any prefix, while this pins the full expected location. A substring/`in`
weakening was explicitly avoided. A comment records why the value is absolute,
so the next reader does not "fix" it back to a suffix match.

**Complete-family verification**: `rg '\.endswith\(\s*["'"'"'][^"'"'"']*/[^"'"'"']*["'"'"']\s*\)'`
across all of `tests/` returns exactly three sites -- the two above and
`tests/tools/test_airframe_geometry_review_cli.py:179`
(`...endswith("gltf/scene.gltf")`). The third is structurally exposed to the
same `ValueError -> str(path)` fallback (`airframe_review/filesystem.py:9`) but
is **green**, because its manifest path resolves under the repo root, so the
posix branch is taken. It is left untouched (no red to fix) and recorded here
so a future `tmp_path` change to that fixture is diagnosed immediately.
`rg 'manifest_relative_path'` across `tests/` confirms no other consumer.
Section 8.9's "these two are the complete family" claim is therefore confirmed
for reds, and refined: the *pattern* family has three members, of which two
are red.

### 9.4 Items 3-4 -- conditional skip: absent CMake dependency includes

**Root cause**: in all three files the dependency include paths are resolved at
**module scope**, so `dependency_include_path`'s `AssertionError` surfaces as a
collection error that discards the entire file. The collateral damage was the
larger problem: `test_guard_enforcement.py` has 16 tests of which only 7 compile
C++, and `test_default_factory_spawn_plan_resolution.py` has 7 of which only 4
do -- so 12 pure text/AST guards were being lost to a missing C++ header,
including the header-text guards a later T11 slice gates on.

**Disposition (conditional skip, section 8.7 precedent, nothing weakened)**:
each file gains a local `_optional_dependency_include()` that returns `None`
instead of raising, plus a `pytest.mark.skipif` predicated on that resolution:

- `requires_flecs` in `test_guard_enforcement.py` and
  `test_clock_domain_enforcement.py`, applied to the 7 and 1 compile-bound
  tests respectively.
- `requires_platform_spawn_includes` in
  `test_default_factory_spawn_plan_resolution.py`, applied to its 4
  compile-bound tests; its reason string interpolates the **actual** missing
  dependency names.

Every reason string names the missing dependency, the fact that
`_deps/<dependency>-src` is absent from the configured `CMO_BUILD_DIR`, and
points at section 5. The skip is conditional in the strong sense: on a build
tree carrying the dependency sources the predicate is False and all checks run
unchanged (proven in 9.6, `24 passed`, zero skipped). Net effect on the
incomplete snapshot: 12 previously-uncollectable guards now execute and pass;
only 12 genuinely toolchain-bound checks skip.

### 9.5 Items 5-7 -- xfail(strict): binary-side calibration drift

**Inherence proof (this is what licenses the xfail)**: the ledger's existing
proof for items 5-6 was reproduction against the 2026-07-18 pre-change binary.
This iteration added a second, independent axis:

- All three reds reproduce identically against **two different binaries** built
  from different points in the lineage -- the 2026-07-18 snapshot
  (`EF-w2-training`) and a 2026-07-26 snapshot (`EF-w3-flightshaping`), the
  latter postdating every C++ commit on this branch (latest: `cf172d8f`,
  2026-07-21). A regression introduced by a recent iteration would not survive
  being rebuilt after that iteration.
- `git log` on both air-combat test files shows no change since **2026-06-21**
  (`f2532638`), so the expectations are not newly-tightened assertions.
- Item 7's value provably originates in the same binary surface as items 5-6:
  `_synthetic_baseline_rows` calls `surface_probe._sample_primary_event` and
  reads `summary["component_failure_probability"]`. It is one drift, observed
  through three different tests, not three independent failures.

On that evidence all three stay in the calibration-drift lane. **No genuine
regression was found**; had the fresh-binary run turned any of them green, that
would have been reported as a stale-binary artifact instead.

**Disposition (`xfail(strict=True)`, section 8.6 / I28 precedent, no test
deleted or weakened)**: each node carries
`@pytest.mark.xfail(strict=True, reason=...)`. Each reason names the drifted
quantity with its observed-vs-expected values, states the two-binary inherence
evidence, points at section 5, and states that recalibration flips the node to
`XPASS(strict)` and requires removing the marker. Strict is the point: per the
program README's T6 key risk ("baseline repairs must not mask real
regressions"), a blanket skip would silently absorb a future recovery, whereas
`XPASS(strict)` is itself a failure that forces a revisit. No assertion was
relaxed and no reference value was re-baselined -- doing so would have
destroyed the drift evidence.

### 9.6 Verification (this worktree)

Both build trees are exercised deliberately: the **incomplete** snapshot
(`EF-w2-training/build-local-win`, `_deps/flecs-build` only) is where the
governed reds reproduce, and the **complete** snapshot
(`EF-w3-flightshaping/build-local-win`, full `_deps` sources) proves the skips
are conditional. No CMake/build was triggered; the write set is tests + docs.

```
tools\maintenance\cmo_env.ps1 validate       -> validation ok (both trees)

--- CMO_BUILD_DIR=EF-w2-training/build-local-win (incomplete snapshot) ---

BEFORE (baseline 0aa76a00):
  damage_model: candidate_artifact_contracts + component_probability_artifacts
    + component_fragility_validation      -> 3 failed, 61 passed
  compatibility_quarantine/test_guard_enforcement.py
    + runtime_spine/test_clock_domain_enforcement.py
    + platform_spawn/test_default_factory_spawn_plan_resolution.py
                                          -> 3 errors during collection
                                             (0 tests collected)
  air_combat: component_failure_probability_surface
    + live_detonation_event_surface       -> 2 failed, 11 passed

AFTER:
  the three collection-error files + the two air-combat files
                                          -> 23 passed, 12 skipped, 2 xfailed
     (every skip reason names its missing dependency; 12 of the 23 passes are
      previously-uncollectable guards, the other 11 are air-combat tests that
      were always collectable)
  damage_model (the three files)           -> 63 passed, 1 xfailed
     (was 3 failed, 61 passed: items 1-2 fixed, item 7 xfailed)

--- CMO_BUILD_DIR=EF-w3-flightshaping/build-local-win (complete snapshot) ---

  the three former collection-error files -> 24 passed, 0 skipped
     (proves items 3-4's skips are genuinely conditional, not latent
      unconditional skips)
  the two air-combat files                -> 2 failed, 11 passed at baseline
     (items 5-6 reproduce on the newer binary too: the inherence proof in 9.5)
  damage_model (the three files)          -> 3 failed, 61 passed at baseline
     (item 7 reproduces on the newer binary too)

--- gates ---

ruff check <the 8 changed test files>  -> All checks passed!
git diff --check                       -> clean

python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
-> 1 failed, 459 passed, 45 subtests passed. The one failure is the expected
   bilingual-registry hash flag this ledger edit raises
   (test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface),
   whose `clusters --write` refresh is a landing-side duty (same as 8.10).
   459 passed vs 8.10's 458: not attributable to this pack -- none of the
   files this write set touches (including the items 1-2 damage_model files)
   is a ci_smoke_suite member. The +1 is suite-content growth between the two
   measurements: the manifest itself is unchanged (fae17eb8..0aa76a00 does
   not touch ci_smoke_suite.json), and the only member whose test count
   changed is tests/runtime/test_agent_shim.py, which 1a2e64a5 grew from 21
   to 22 tests.

python tools/maintenance/translate_docs_batch.py audit   (read-only)
-> pair_count 86, synced 85, diverged 1 -- this ledger pair is the sole
   diverged entry, as at 8.10.

pytest -q tests/runtime
-> 21 failed, 879 passed, 35 xfailed, 467 subtests passed.
   None of the 21 is in this write set. Attribution checked explicitly:
   re-running the four failing files against the **complete/newer** snapshot
   recovers 16 of them (they are stale-binary artifacts of the 2026-07-18
   build, which predates the I54/I60 C++ commits). The residual 5 -- all in
   `tests/runtime/facade/test_runtime_facade_window_loop_injection.py` --
   were then re-measured with this iteration's write set **stashed**: the
   identical 5 fail at bare `0aa76a00`, so they are pre-existing and
   untouched by this pack. They are not registered into section 5 here
   because they are not local-environment reds of the governed kind; they
   need their own lineage triage.
```

### 9.7 Write set (this iteration)

- `tests/architecture/damage_model/test_candidate_artifact_contracts.py` (item 1 assertion fix)
- `tests/architecture/damage_model/test_component_probability_artifacts.py` (item 2 assertion fix)
- `tests/architecture/compatibility_quarantine/test_guard_enforcement.py` (item 3 conditional skip)
- `tests/architecture/runtime_spine/test_clock_domain_enforcement.py` (item 3 conditional skip)
- `tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py` (item 4 conditional skip)
- `tests/runtime/air_combat/test_component_failure_probability_surface.py` (item 5 xfail-strict)
- `tests/runtime/air_combat/test_live_detonation_event_surface.py` (item 6 xfail-strict)
- `tests/architecture/damage_model/test_component_fragility_validation.py` (item 7 xfail-strict)
- `docs/plan/unified_architecture_program/t6_residual_ledger.md` / `.zh.md` (this section + section 5 completion/registration)

No production code, C++, `examples/**`,
`docs/plan/repository_consolidation/**`, contract JSON, or contract runner
touched; no CMake/build triggered.

## 10. I72 follow-up: path-suffix matcher utility (assertion-form adjudication)

Strengthening follow-up to I65's items 1-2 (section 9.3). The queue row this
slice implemented predated I65 and prescribed repairing the two
`retained_pack/manifest.json` suffix reds (section 8.9) with a
component-normalized suffix matcher. I65 landed first and fixed both call
sites differently: full `Path` equality against the test-constructed
`tmp_path / "retained_pack" / "manifest.json"`. The overlap was adjudicated
before landing rather than double-repaired.

**Adjudication -- which assertion form survives**: I65's Path-equality form,
tested against the boundary-crossing `not_retained_pack/manifest.json` trap
(the discriminator that motivated the matcher), rejects it by construction --
the full compared path differs, so no suffix trap is reachable at all. It
additionally pins the entire prefix, which a two-component suffix match does
not. For these two call sites Path equality is therefore strictly stronger
than the matcher, and both assertions are left exactly as I65 wrote them
(section 9.3); this iteration changes neither repaired assertion.

**What this iteration adds (tests only)**: the matcher
`tests/architecture/damage_model/helpers.py::path_suffix_components(value,
count)` is kept as a reusable utility for the residual niche Path equality
cannot serve -- suffix checks whose full expected path a test cannot
construct (variable/unknown prefix), e.g. future assertions against producer
display text where only the tail is contractual. Its docstring records the
scope rule ("prefer full Path equality when the test can build the full
expected location") so it cannot be mistaken for the preferred form at
fixed-location call sites. The matcher is pinned by the new hermetic
sub-second `tests/architecture/damage_model/test_path_suffix_components.py`
(15 tests): positives cover the Windows-native absolute shape of the original
red, POSIX absolute, repo-relative, mixed-separator, and
separator-run/leading-separator forms; negatives prove rejection of wrong
directory component, wrong filename, right components in the wrong order,
fewer components than requested, and the boundary-crossing
`not_retained_pack/manifest.json` tail, for which the test first asserts
inline that raw `endswith` *does* accept it (the trap) before asserting the
matcher rejects it. Kept out of the smoke manifest per the I37
(`test_xmacro_text.py`) / I57 (`test_rights_output_policy_probe.py`)
exclusion precedent: a hermetic test-support unit test, not a drift gate.

**Verification** (this worktree,
`CMO_BUILD_DIR=D:\workshop\Research\EF-landing\build-local-win`):

```
pytest -q <the two I65-repaired nodes>
       tests/architecture/damage_model/test_path_suffix_components.py
-> 17 passed (the two Path-equality assertions green as I65 wrote them, plus
   the 15 matcher tests)
```

**Write set (this iteration)**:
`tests/architecture/damage_model/helpers.py` (matcher utility),
`tests/architecture/damage_model/test_path_suffix_components.py` (new), plus
this ledger pair (this section only -- the section 5 rows and section 9.3
are I65's records and are not re-stated). The two I65-repaired test files
are not modified by this iteration. No production code, no C++, no contract
JSON, no smoke-manifest change.

## 11. I97 reviewer repair: seven focused binary residuals

This section records the minimal follow-up to the I97 repair commit
`fdd9882764`. The earlier whole-test markers were narrowed so that each
implementation-independent binary residual has one strict-xfail assertion.
The same observation was reproduced with both the 2026-07-18 and 2026-07-26
`ef_py` binaries; this two-binary inheritance is evidence that the residual is
not a single-build artifact, not evidence that the expected behavior is
authoritative.

| Residual | Focused test node | Observed on both binaries | Expected after repair |
| --- | --- | --- | --- |
| I97-R1 | `test_mlf5c_direct_hit_component_primary_name_matches_engine_core` | direct-hit `component_primary_name='left_horizontal_tail_actuator_or_surface_component'` | `component_primary_name='engine_core'` |
| I97-R2 | `test_live_detonation_outcome_state_matches_damage_application` | `effects.outcome_state='detonated_no_effect'` | `'damage_applied'` |
| I97-R3 | `test_live_detonation_fragment_energy_is_positive` | `warhead.fragment_energy_j=0.0` | `>0.0` |
| I97-R4 | `test_live_detonation_blast_overpressure_is_positive` | `warhead.blast_overpressure_kpa=0.0` | `>0.0` |
| I97-R5 | `test_live_detonation_spatial_sample_count_is_positive` | `spatial.sample_count=0` | `>0` |
| I97-R6 | `test_live_detonation_exports_nonblank_component_source_rows` | zero nonblank `component_mechanism_load_rows` | at least one nonblank source row |
| I97-R7 | `test_fragility_benchmark_synthetic_sigmoid_outcome_matches_retained_reference` | synthetic vector `(0.17289200648782854, 0.1710962556841057, 0.16989812081797678)` | retained vector `(0.35168, 0.35168, 0.35168)` |

R1's companion assertion remains active and selects the `engine_core` row from
`component_mechanism_load_rows`, where the observed direct-hit blast load is
`588.6225285038623 kPa` (`>500`); the current selected primary row remains
actively checked only for its own positive/relative load properties. In the
live-event test, headers, event counts, cross-event equalities, and the
row-to-component mapping remain active. The fragility test likewise keeps
delta, ratio, candidate/synthetic means, mean absolute difference (MAD), and
the comparison boolean as active algebraic checks derived from the current
rows; only the retained three-point synthetic vector is residual.

Each marker is intentionally strict and has an independent reason containing
the observed/expected pair, the two-binary inheritance statement, and its
exact pointer (`T6 residual ledger section 11, I97-R1` through `I97-R7`). A
normal run therefore reports three passing structural tests and seven focused
xfails; `--runxfail` must turn exactly those seven nodes into failures.

**Write set (I97 reviewer repair)**:
`tests/runtime/air_combat/test_component_failure_probability_surface.py`,
`tests/runtime/air_combat/test_live_detonation_event_surface.py`,
`tests/architecture/damage_model/test_component_fragility_validation.py`,
and this ledger pair plus the maintained bilingual-cluster registry hash
refresh. No production code, C++, contract JSON, or smoke-manifest change.

## Related

- [Repository Consolidation Plan](../repository_consolidation/README.md)
  (I28, I31, I33, I34 register rows cited above)
- [SCAL Conformance Census (2026-07-20)](scal_conformance_census_20260720.md)
  (sibling `reference`-kind register; structural precedent for this document)
- `tests/runtime/air_combat/weapon_guidance_realism/README.md` (wrapper/mixin
  collection contract referenced in section 1)
- `tests/architecture/fixtures/cpp_include_direction_allowlist_20260720.json`
  (I38/I41 ratchet allowlist; section 7 above is this ledger's record of the
  I41 amendment)
