# T8 G4 Truth-Leak Inventory (2026-07-21)

Language:
- English canonical: `t8_g4_truth_leak_inventory.md`
- Chinese companion: [t8_g4_truth_leak_inventory.zh.md](t8_g4_truth_leak_inventory.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/t8_g4_truth_leak_inventory.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-21`
Baseline commit: `8bd21d86`

Status: T8 (information-state architecture) register for the
[Unified Architecture Program](README.md). It records (a) the maintained
observation/reward consumer census, (b) where the G4 layer-declaration
mechanism was landed, and (c) the World-Truth direct reads on policy paths, each
adjudicated. Per the
[SCAL Conformance Census](scal_conformance_census_20260720.md) precedent this is
a descriptive register (`reference`): it changes no runtime behavior. The first
slice landed the G4 declaration mechanism (pure metadata plus an architecture
test) and inventoried the truth leaks without closing any. The **second slice
(§6, 2026-07-21)** materializes a declared observation view on the TL13 read seam
and migrates the eight declared consumers to read through it, structurally
converging 11 of the declared leaks; the migration is a pure mechanical
relocation of the leaf reads into a layer-tagged owner with bit-for-bit
identical numeric results. Converging a leak means the consumer no longer reads
raw World Truth: its reads flow through the declared view owner, and its verdict
is flipped here.

The G4 vocabulary used throughout is the authoritative six-layer information-state
set from the
[Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md)
§3, reused verbatim from the I32 stage-contract whitelist in
`python/rl/runtime/world_batch/core.py` (pinned by
`tests/world_batch/test_world_batch_core.py`): World Truth, Sensed State, Track
State, Shared Tactical Picture, Agent Observation, Decision Belief.

## 1. G4 declaration mechanism (Python side)

Kernel Invariant G4 ("every observation/reward consumer declares its
information-state layer") is realized on the Python-owned surface as a
lightweight, zero-runtime-overhead facility, following the mechanism the T0
census proposed (census §3):

- **Facility**: `python/architecture/information_layer.py` — a neutral,
  stdlib-only module (dependency direction `gym_envs -> python.architecture <-
  python.rl`, mirroring `python.tasking_contracts`). It publishes the
  authoritative layer vocabulary (`AUTHORITATIVE_INFORMATION_LAYERS`), the
  canonical P0-P10 stage vocabulary (`CANONICAL_SEMANTIC_STAGES`), the G5
  registry of declared consumers (`MAINTAINED_INFORMATION_LAYER_CONSUMERS`), and
  the shared checker `validate_information_layer_declaration` reusable by a future
  AST gate.
- **Declaration**: each maintained consumer declares three module-level
  constants — `INFORMATION_LAYER_CONSUMED`, `INFORMATION_LAYER_PRODUCED`,
  `SEMANTIC_STAGE` — as tuples of authoritative strings. These are plain
  assignments (no per-step or import-time cost) styled on the I32 stage-contract
  declarations and the `mission_obs_taxonomy` OWNER-mapping precedent.
- **Gate**: `tests/architecture/information_state/test_g4_layer_declarations.py`
  asserts every registered consumer carries a valid declaration, cross-checks the
  facility vocabulary against the I32 stage-contract whitelist (both directions),
  and confirms it covers every layer/stage `core.py` actually declares. Both the
  whitelist test and `core.py` are read by static AST parsing, never imported, so
  the gate carries no `ef_py`/runtime dependency and stays runnable without a
  build. The declaration extractor is tuple-only (a list literal is treated as a
  missing declaration), and the gate proves it is load-bearing: removing,
  corrupting, or list-forming a declaration goes red.

The first slice shipped the declaration + presence gate. The **second slice
(§6)** adds the declared observation-view owner
(`gym_envs/observation_view.py`) and the AST truth-read ban that
G4 anticipates ("enforcement moves from documentation to AST gates", design doc
§15): the ban (`tests/architecture/information_state/test_g4_truth_read_ban.py`)
forbids raw World-Truth reads in the migrated consumers, whitelisting the view
owner and explicit diagnostic reads, seeded by the inventory in §3.

## 2. Maintained observation/reward consumer census

Every maintained observation/reward consumption path on the `gym_envs/**` and
`python/rl/**` surfaces (plus `tools/eval/**` direct reads). "Declared view?"
records whether the read already flows through a declared view/seam.

| # | Consumer | Data surface read | G4 layer | Declared view? |
|---|----------|-------------------|----------|----------------|
| C1 | `gym_envs/scenario_loader/mission_observation.py` — Python-owned modes (`naval_screen_station_v1`, `air_combat_c2_roe_v1/v2`) | `truth.contacts`, `truth.missiles_remaining`, `truth.x/y`; support `get_agent_observation`/`get_unit_position`; support `get_unit_messages` | consumes World Truth + Shared Tactical Picture; produces Agent Observation | **Converged this slice** (§6; reads via declared view; was V4 leak) |
| C2 | `gym_envs/scenario_loader/mission_observation.py` — compiled modes (`basic`/`nav_v1`/`nav_v2`/…) | compiled `ef_py.compute_mission_observation` from `mission_command_view` + route guidance (truth passed in) | produces Agent Observation (compiled) | compiled facade path; covered by C1 module declaration |
| C3 | `python/rl/runtime/world_batch/observation_batching.py` + `_observation_mixin.py` | `state.last_truth`/`state.last_inst` (truth/instrument cache), `truth.x/y`, `inst.alt_baro` → compiled batch | consumes World Truth (cache) → produces Agent Observation | **Yes** — I32 stage contract (`state_read`/`observation_build`), already conformant |
| C4 | `gym_envs/scenario_loader/reward_runtime/air_combat.py` | `truth.missiles_remaining`; `sim.export_recent_engagement_events`; `sim.debug_get_aircraft_damage_state`/`debug_get_ground_contact_state`; `sim.is_unit_active` | consumes World Truth; produces reward | **Converged this slice** (§6; reads via declared view; was V5 leak) |
| C5 | `gym_envs/scenario_loader/reward_runtime/naval.py` | `truth.x/y`, `truth.contacts`; `sim.get_unit_position`/`get_agent_observation` (other units); `sim.get_unit_messages` | consumes World Truth + Shared Tactical Picture; produces reward | **Converged this slice** (§6; reads via declared view; was V6 leak) |
| C6 | `gym_envs/scenario_loader/reward_runtime/safety.py` | own-ship `truth.health/z/pitch/speed` | consumes World Truth; produces reward inputs | **Converged this slice** (§6; own-ship read via declared view) |
| C7 | `gym_envs/scenario_loader/reward_runtime/shaping_inputs.py` | own-ship `truth.z/speed` + instrument vector | consumes World Truth; produces reward inputs | **Converged this slice** (§6; own-ship read via declared view) |
| C8 | `gym_envs/scenario_loader/reward_runtime/objectives.py` | own-ship `truth.z/health/heading/x/y/missiles_remaining`; target `truth.contacts`, `sim.is_unit_active`/`get_unit_health` | consumes World Truth; produces reward/objective inputs | **Converged this slice** (§6; own + target read via declared view) |
| C9 | `gym_envs/scenario_loader/reward_runtime/compiled_runtime.py` | assembles pre-built input DTOs; no direct information-layer read | — (assembler, not a direct consumer) | N/A — excluded from registry |
| C10 | `gym_envs/scenario_loader/core.py::get_policy_agent_observation` / `get_policy_instrument_state` | `sim.get_agent_observation`/`get_instrument_state` (facade-backed proxy on batch path) | the World-Truth read seam itself (V3) | maintained seam; the declared observation view (§6) now reads from this seam's `truth`/`sim` output; a full typed `ObservationViewSpec` facade export remains a later step |
| C11 | `gym_envs/scenario_loader/step_evaluation.py` | own-ship `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health`; orchestrates reward surfaces | stage-bundling aggregator (V7) | Deferred — 待裁定 (P9+P10 bundle) |
| C12 | `gym_envs/scenario_loader/execution_runtime/mainline.py` | orchestrates the execution step; reward/observation via loader | orchestrator | Deferred — 待裁定 |
| C13 | `gym_envs/leader_env_parts/decision_runtime/observations.py::build_observation` | mostly `inst.*`; `truth.x/y` for ILS/runway/anchor geometry; delegates nav to `get_mission_observation` | produces Agent Observation; consumes World Truth (position) | Deferred — 待裁定 (leader path) |
| C14 | `python/rl/tasking/leader_tasking.py` | `get_policy_agent_observation`/`get_policy_instrument_state` at multiple sites | scripted director; consumes World Truth | Deferred — 待裁定 (scripted-director epistemics) |
| C15 | `tools/eval/waypoint_eval_utils.py`, `tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | eval-tool reads | eval/diagnostics surface — outside the maintained policy path |
| C16 | `gym_envs/universal_env.py::UniversalEnv` class constructor | — | demoted fail-fast shell (`__init__` raises `RuntimeError`) | Dead path — no declaration needed. This is the removed raw-kernel env only; it is distinct from the still-active `build_universal_observation` it re-exports (see C17). |
| C17 | `gym_envs/universal_env_parts/observations.py::build_universal_observation` — active universal policy-observation assembly, called by `CooperativeWorldBatchVecEnv` and `MultiAgentWorldRuntimeView` | `truth.x/y` (ILS query), `truth.contacts`, `truth.rwr_warnings` (Python fallback path); compiled path passes `truth` to `ef_py.compute_execution_observation_runtime_numpy`; delegates the mission vector to `get_mission_observation` | consumes World Truth; produces Agent Observation | **Converged this slice** (§6; reads via declared view; repair-round add) |
| C18 | `gym_envs/scenario_loader/navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` — direct waypoint reward-input consumer, called by `step_evaluation.py`/`execution_runtime/mainline.py` via `loader._build_waypoint_step_state` | own-ship `truth.x/y` (distance-to-fix and route reference); builds `ef_py.WaypointRewardInputs` | consumes World Truth; produces reward inputs | **Converged this slice** (§6; own-ship read via declared view; repair-round add) |
| C19 | `gym_envs/scenario_loader/navigation_runtime/guidance.py` — shared route-guidance geometry helper (`query_route_guidance_result`, `compute_waypoint_guidance_state`, `apply_waypoint_guidance_update`, …) | own-ship `truth.x/y/speed` (route guidance geometry; `get_policy_agent_observation` fallback) | spans command-delivery (P3/P4 autopilot target) + reward-support (P10); not a single Agent-Observation-facing consumer | Deferred — 待裁定 (mixed guidance/command helper, not force-classified; repair round) |

Declared (first slice) and converged onto the declared observation view (second
slice, §6): C1, C4, C5, C6, C7, C8, C17, C18 (the eight modules in
`MAINTAINED_INFORMATION_LAYER_CONSUMERS` / `VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS`;
C17/C18 added in the first-slice repair round). Already conformant: C3. Excluded
as non-consumer: C9. Dead: C16. Deferred with rationale (宁缺毋滥, not
force-classified): C11, C12, C13, C14, C19. Outside the maintained policy path:
C15.

## 3. Truth-leak inventory

World-Truth direct reads on policy paths (policy/observation construction or
reward that reads truth while representing an Agent-Observation-facing consumer).
Verdicts: **converged** = the leaf read now flows through the declared
observation view (§6); **leak** = still needs T8 view-convergence (deferred);
**exempt** = legitimized by a declaration/seam; **diagnostic** = legitimate
diagnostic use (routed through the view's diagnostic face).

| ID | Location | Reads | Verdict | Note |
|----|----------|-------|---------|------|
| TL1 | `mission_observation.py::_air_combat_c2_roe_vector` (`_target_track`, `_truth_missiles_remaining`) | `truth.contacts` (target range / track age / classification), `truth.missiles_remaining` | **converged** (declared view) | V4 (C1 CONSUMED World Truth). Converged 2026-07-21 (§6): reads via `observation_view.target_track` / `own_missiles_remaining` instead of raw `truth.contacts`/`truth.missiles_remaining`. |
| TL2 | `mission_observation.py::_naval_screen_station_vector` | `truth.x/y` (own), `truth.contacts` (target present); `runtime_view.get_agent_observation`/`get_unit_position` (support units) | **converged** (declared view) | V4 (C1). Own `truth.x/y` via `observation_view.own_ship_field`; target via `target_track`; support obs/position via `support_agent_observation`/`support_unit_position` (Shared Tactical Picture face). |
| TL3 | `mission_observation.py::_naval_screen_station_vector` | `runtime_view.call_optional("get_unit_messages", support)` (report chain) | **exempt** | Shared Tactical Picture (C1). Now routed via `observation_view.support_unit_messages_optional`; link-distributed reports remain a legitimate declared layer, not raw truth. |
| TL4 | `reward_runtime/air_combat.py::_truth_missiles_remaining` (`_air_combat_observed_release_count`, `_apply_release_shaping`) | `truth.missiles_remaining` | **converged** (declared view) | V5 (C4). Reads via `observation_view.own_missiles_remaining`; own-ship weapon count, low-risk. |
| TL5 | `reward_runtime/air_combat.py::_recent_engagement_events` / `_standard_damage_fact_projections` | `sim.export_recent_engagement_events()` (damage/lifecycle/consequence events) | **converged** (declared view) | V5 (C4). Reads via `observation_view.recent_engagement_events` (engagement-evidence face); `consumer_visibility == "diagnostics_only"` filtering unchanged. |
| TL6 | `reward_runtime/air_combat.py::_damage_consequence_snapshot`, `_ground_contact_terminal_state` | `sim.debug_get_aircraft_damage_state`, `sim.debug_get_ground_contact_state` | **diagnostic** | Explicit `debug_*` APIs for damage-consequence shaping; now routed via `observation_view.debug_aircraft_damage_state`/`debug_ground_contact_state` (the view's explicit diagnostic face). Acceptable diagnostic use. |
| TL7 | `reward_runtime/air_combat.py::combat_entity_terminal_state` | `sim.is_unit_active(target)` | **converged** (declared view) | V5 (C4). Reads via `observation_view.unit_active` (engagement-evidence face); other-entity liveness. |
| TL8 | `reward_runtime/naval.py::_station_reward_terms` / `apply_naval_reward_surface` | `truth.x/y` (own), `truth.contacts` (target), `sim.get_unit_position(support)`, `sim.get_agent_observation(support)` | **converged** (declared view) | V6 (C5). Own `truth.x/y` via `own_ship_field`; target via `naval_target_track` (naval-guard variant, `target_id <= 0` uncoerced); support position/obs via `support_unit_position`/`support_agent_observation`. |
| TL9 | `reward_runtime/naval.py::_support_received_target_report` | `sim.get_unit_messages(support)` (report chain) | **exempt** | Shared Tactical Picture (C5). Now routed via `observation_view.support_unit_messages`; legitimate link-distributed report. |
| TL10 | `reward_runtime/safety.py::build_safety_runtime_inputs` | own-ship `truth.health/z/pitch/speed` | **converged** (declared view) | C6. Reads via `observation_view.own_ship_field`; own-ship self-read, low-risk. |
| TL11 | `reward_runtime/shaping_inputs.py::build_flight_shaping_runtime_inputs` | own-ship `truth.z/speed` | **converged** (declared view) | C7. Reads via `observation_view.own_ship_field`; own-ship self-read, low-risk. |
| TL12 | `reward_runtime/objectives.py::build_conditional_objective_inputs`, `_combat_target_snapshot` | own-ship `truth.z/health/heading/x/y/missiles_remaining`; target `truth.contacts` range, `sim.is_unit_active`/`get_unit_health(target)` | **converged** (declared view) | C8. Own-ship via `own_ship_field`; target `truth.contacts` via `contacts`; `sim.is_unit_active`/`get_unit_health` via `unit_active`/`unit_health`. |
| TL13 | `scenario_loader/core.py::get_policy_agent_observation` / `get_policy_instrument_state` | `sim.get_agent_observation`/`get_instrument_state` (facade-backed proxy on batch path) | **exempt** (maintained seam) | V3. The single maintained read chokepoint; on the batch path `sim` is `_ScenarioLoaderRuntimeProxy` (facade-backed). The declared observation view (§6) now reads from this seam's `truth`/`sim` output; turning the seam's return into a full typed `ObservationViewSpec` facade export remains a later step. |
| TL14 | `scenario_loader/step_evaluation.py` (`build_execution_runtime_state`, reward-input assembly) | own-ship `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health` | **leak** (own-ship, aggregator; deferred) | V7. Stage-bundling orchestrator; declaration deferred (待裁定) rather than force-classified. |
| TL15 | `leader_env_parts/decision_runtime/observations.py::build_observation` | own-ship `truth.x/y` (ILS/runway/anchor geometry) | **leak** (own-ship position; deferred) | Leader observation path; declaration deferred (待裁定). |
| TL16 | `python/rl/tasking/leader_tasking.py` (multiple sites) | `get_policy_agent_observation`/`get_policy_instrument_state` | **leak** (scripted-director; deferred) | Scripted director consuming World Truth; epistemic layer (maintained doctrine vs diagnostics-only) deferred (待裁定). |
| TL17 | `tools/eval/waypoint_eval_utils.py`, `tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | **exempt** (eval surface) | Eval/diagnostics tooling, outside the maintained policy path; not a maintained-surface leak. |
| TL18 | `universal_env_parts/observations.py::build_universal_observation` | `truth.x/y` (ILS query), `truth.contacts`, `truth.rwr_warnings` (Python fallback); compiled path passes `truth` to `ef_py.compute_execution_observation_runtime_numpy` | **converged** (declared view) | C17. Leaf reads via `observation_view.own_ship_attr` / `contacts` / `rwr_warnings`. The compiled path still passes the whole `truth` object to the kernel — a whole-object transfer, not a leaf read; out of scope this slice. |
| TL19 | `navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` | own-ship `truth.x/y` (distance-to-fix, route reference) → `ef_py.WaypointRewardInputs` | **converged** (declared view) | C18. Own-ship `truth.x/y` via `observation_view.own_ship_field`; the guidance helper (C19/TL20) delegation is unchanged (deferred). |
| TL20 | `navigation_runtime/guidance.py` (`query_route_guidance_result`, `compute_waypoint_guidance_state`, `apply_waypoint_guidance_update`, …) | own-ship `truth.x/y/speed` (route guidance geometry) | **leak** (own-ship; deferred) | Shared route-guidance helper spanning command-delivery (autopilot target) and reward-support; declaration deferred (待裁定) rather than force-classified (C19). |

## 4. Verdict distribution

| Verdict | Count | Entries |
|---------|-------|---------|
| converged — reads via the declared observation view (§6) | 11 | TL1, TL2, TL4, TL5, TL7, TL8, TL10, TL11, TL12, TL18, TL19 |
| leak — still needs T8 view-convergence (deferred) | 4 | TL14, TL15, TL16, TL20 |
| exempt — legitimized by declaration/seam | 4 | TL3, TL9, TL13, TL17 |
| diagnostic — legitimate diagnostic use | 1 | TL6 |

The 11 converged entries are the eight declared consumers' leaf reads (TL1, TL2,
TL4, TL5, TL7, TL8, TL10, TL11, TL12 on C1/C4/C5/C6/C7/C8, plus TL18 on C17 and
TL19 on C18), now flowing through the declared observation-view owner
(`gym_envs/observation_view.py`, §6) rather than raw World Truth.
The 4 remaining leaks are the deferred aggregator/leader/guidance paths (TL14,
TL15, TL16, TL20), still 待裁定. The exempt/diagnostic reads (TL3, TL6, TL9,
TL13, TL17) keep their verdict; where they sit on a migrated consumer they are
routed through the view's Shared-Tactical-Picture / diagnostic faces for
consistency. A full typed `ObservationViewSpec` facade export at the TL13 seam
(so the seam's return itself is a typed spec) remains a later step.

## 5. Next slices (not done here)

- Turn the TL13 seam's return into a full typed `ObservationViewSpec` facade
  export. The second slice (§6) materialized the declared read view over the
  seam's `truth`/`sim` output and migrated the eight consumers onto it; the typed
  spec export (so the seam itself returns a typed view object) remains.
- Adjudicate and declare the deferred aggregator/leader/guidance paths (C11–C14,
  C19; TL14–TL16, TL20), then converge them onto the declared view.
- Extend the G4 AST truth-read ban as those deferred consumers converge. The ban
  already covers the eight migrated consumers (§6;
  `tests/architecture/information_state/test_g4_truth_read_ban.py`).

## 6. Second slice: declaration-view convergence (2026-07-21)

The second T8 slice materializes a declared observation view on the TL13 read
seam and migrates the eight declared consumers to read through it, structurally
converging 11 declared leaks (TL1, TL2, TL4, TL5, TL7, TL8, TL10, TL11, TL12,
TL18, TL19). It is a pure mechanical relocation: every view function performs the
exact same underlying read (same function/attribute, same argument, same order)
the consumer did before, so observation and reward results are bit-for-bit
identical.

### 6.1 View owner and gate

- **View owner:** `gym_envs/observation_view.py` — a dependency-terminal,
  stdlib-only read owner (G2 neutral leaf) at the `gym_envs` parent-package
  layer, the common lower layer of both consumer subpackages (per G2 "shared
  needs sink downward, never sideways"; `universal_env_parts` keeps zero lateral
  imports of `scenario_loader`). It exposes layer-tagged read faces: own-ship
  World Truth (`own_ship_field` / `own_ship_attr` / `own_missiles_remaining`),
  Track State (`contacts` / `rwr_warnings` / `target_track` /
  `naval_target_track` — the mission-observation and naval track-lookup guard
  variants are kept as separate faces for fidelity), Shared Tactical Picture
  (`support_agent_observation` / `support_unit_position` / `support_unit_messages`
  / `support_unit_messages_optional`), engagement evidence
  (`recent_engagement_events` / `unit_active` / `unit_health`), and explicit
  diagnostic reads (`debug_aircraft_damage_state` / `debug_ground_contact_state`).
  It resolves every attribute/method by dynamic lookup at call time and binds
  nothing at import, so the loader / `sim` / `get_policy_agent_observation`
  monkeypatch seams keep working.
- **Ban gate:** `tests/architecture/information_state/test_g4_truth_read_ban.py`
  forbids raw World-Truth reads (`truth.<attr>` / `getattr(truth, ...)`) in the
  migrated consumers, whitelisting the view owner and explicit diagnostic-marked
  reads, with a load-bearing negative self-proof (injecting a raw read goes red).
  Registry: `MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS` /
  `VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS` in
  `python/architecture/information_layer.py`.

### 6.2 Per-consumer read → view-face migration

| Consumer | Raw read (before) | Declared view face (after) |
|----------|-------------------|----------------------------|
| C1 `mission_observation` | own `truth.z/heading/speed/x/y`; `truth.contacts` (via `_target_track`); `truth.missiles_remaining`; support `get_agent_observation`/`get_unit_position`/`call_optional("get_unit_messages")` | `own_ship_field`; `target_track`; `own_missiles_remaining`; `support_agent_observation`/`support_unit_position`/`support_unit_messages_optional` |
| C4 `air_combat` | `truth.missiles_remaining`; `sim.export_recent_engagement_events()`; `sim.is_unit_active`; `sim.debug_get_aircraft_damage_state`/`debug_get_ground_contact_state` | `own_missiles_remaining`; `recent_engagement_events`; `unit_active`; `debug_aircraft_damage_state`/`debug_ground_contact_state` |
| C5 `naval` | own `truth.x/y`; `truth.contacts` (via `_target_track`); `sim.get_unit_position`/`get_agent_observation`/`get_unit_messages` | `own_ship_field`; `naval_target_track` (naval-guard variant); `support_unit_position`/`support_agent_observation`/`support_unit_messages` |
| C6 `safety` | own `truth.health/z/pitch/speed` | `own_ship_field` |
| C7 `shaping_inputs` | own `truth.z/speed` | `own_ship_field` |
| C8 `objectives` | own `truth.z/health/heading/x/y/missiles_remaining`; target `truth.contacts`; `sim.is_unit_active`/`get_unit_health` | `own_ship_field`; `contacts`; `unit_active`/`unit_health` |
| C17 `universal observations` | `truth.x/y`; `truth.contacts`; `truth.rwr_warnings` | `own_ship_attr`; `contacts`; `rwr_warnings` |
| C18 `waypoint_rewards` | own `truth.x/y` | `own_ship_field` |

### 6.3 Deferrals (kept as-is this slice, with rationale)

- **Compiled whole-object transfers.** C17's compiled path passes the whole
  `truth` object into `ef_py.compute_execution_observation_runtime_numpy(inst,
  truth, …)`. This is a whole-object transfer into the compiled kernel, not a
  leaf field read, so it is out of scope for this read-convergence slice and
  stays unchanged (TL18 note).
- **Deferred consumers (待裁定).** `step_evaluation.py` (C11/TL14),
  `execution_runtime/mainline.py` (C12), the leader path
  (`leader_env_parts/decision_runtime/observations.py` C13/TL15,
  `python/rl/tasking/leader_tasking.py` C14/TL16), and the shared route-guidance
  helper (`navigation_runtime/guidance.py` C19/TL20) are not migrated: their
  epistemic layer is still 待裁定, so they are left untouched per 宁缺毋滥.
- **Report-chain / diagnostic reads.** TL3/TL9 (report chain) and TL6 (`debug_*`)
  were already exempt/diagnostic, not leaks; they are routed through the view's
  Shared-Tactical-Picture and diagnostic faces for consistency but keep their
  verdict.

### 6.4 Verification (zero behavior change)

- `tests/architecture/information_state` — 26 passed (was 14; +12 for the new
  ban gate: 8 per-consumer no-raw-read cases + view-owner declaration +
  load-bearing negative proof + diagnostic-marker whitelist + owner-exclusion).
- Targeted consumer integration tests, identical before/after: 60 passed, 15
  subtests passed, 4 failed — the 4 failures are a pre-existing NumPy
  `asarray(copy=)` machine red in
  `python/rl/runtime/cooperative_world_batch_vec_env.py` (out of scope) across
  `tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py`,
  `tests/runtime/air_combat/test_air_combat_reward_surface.py`,
  `tests/runtime/naval/test_naval_station_policy_surface.py`,
  `tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`.
- `tests/runtime/mission` + `tests/world_batch` + `tests/runtime/engagement`,
  identical before/after: 255 passed, 8 subtests passed, 4 `stable_baselines3`
  collection errors (machine baseline).

These integration tests assert exact observation-vector fields and reward totals
through the real kernel, so their unchanged pass sets are the numeric-parity
evidence for the migration.

### 6.5 Independent-review repair (2026-07-21)

The independent review of this slice returned needs-repair on two findings; both
were repaired in place the same day (all §6.4 gates re-run, identical results):

- **P1 — C5 guard drift (behavior).** The first cut had C5 (`naval.py`) reuse
  the shared `target_track` face, whose guard is the mission-observation variant
  (`int(target_id) <= 0`); the naval original guards with `target_id <= 0` (no
  coercion). The variants diverge on non-int inputs — conversion count,
  exception propagation, boundary results (e.g. `target_id=0.5` with an `id=0`
  track returns the track under the naval guard but `None` under the coercing
  guard; a string id raises `TypeError` under the naval guard but can match
  under the coercing guard). The view now carries a separate
  `naval_target_track` face replicating the naval original token-for-token
  (AST-body-identical to baseline `1d25c4d1`, probe-verified on both reviewer
  scenarios), and C5 delegates to it. The C1 variant was audited against its own
  original and is token-identical; the remaining faces were re-audited for
  stray normalization (none found — coercions stay at call sites).
- **P2 — G2 lateral import (layering).** The view owner initially lived at
  `gym_envs/scenario_loader/observation_view.py`, which made the C17 migration
  add a lateral `universal_env_parts -> scenario_loader` sibling import (the
  baseline has none). The owner moved down to the parent-package layer
  `gym_envs/observation_view.py` — the common lower layer of both consumer
  subpackages (G2: shared needs sink downward, never sideways) — with the eight
  consumer imports, the registry owner path, the ban-gate message, and this
  register updated; no file or shim remains at the old path.

## Related

- [Unified Architecture Program](README.md)
- [SCAL Conformance Census (2026-07-20)](scal_conformance_census_20260720.md)
  (V3–V7 register; first-batch consumer priority; structural precedent)
- [T6 Residual Ledger (2026-07-20)](t6_residual_ledger.md) (sibling `reference`
  register)
- [Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md)
  (§3 information-state layers; §6 P0-P10 stages; §15 G4; §16 representation strategy)
- Facility: `python/architecture/information_layer.py`
- View owner: `gym_envs/observation_view.py`
- Gates: `tests/architecture/information_state/test_g4_layer_declarations.py`,
  `tests/architecture/information_state/test_g4_truth_read_ban.py`
