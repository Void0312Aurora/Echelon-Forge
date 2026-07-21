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

Status: T8 (information-state architecture) first-slice register for the
[Unified Architecture Program](README.md). It records (a) the maintained
observation/reward consumer census, (b) where the G4 layer-declaration
mechanism was landed this slice, and (c) the World-Truth direct reads on policy
paths, each adjudicated. Per the
[SCAL Conformance Census](scal_conformance_census_20260720.md) precedent this is
a descriptive register (`reference`): it changes no runtime behavior. The G4
declaration mechanism is pure metadata plus an architecture test; this slice
only inventories and registers the truth leaks — it closes none of them. Closing
a leak means a later T8 slice migrates that consumer onto a declared
`ObservationViewSpec` export and flips its verdict here.

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

This slice ships the declaration + presence gate; the AST truth-read ban that G4
anticipates ("enforcement moves from documentation to AST gates", design doc §15)
is deferred to a later slice and is seeded by the inventory in §3.

## 2. Maintained observation/reward consumer census

Every maintained observation/reward consumption path on the `gym_envs/**` and
`python/rl/**` surfaces (plus `tools/eval/**` direct reads). "Declared view?"
records whether the read already flows through a declared view/seam.

| # | Consumer | Data surface read | G4 layer | Declared view? |
|---|----------|-------------------|----------|----------------|
| C1 | `gym_envs/scenario_loader/mission_observation.py` — Python-owned modes (`naval_screen_station_v1`, `air_combat_c2_roe_v1/v2`) | `truth.contacts`, `truth.missiles_remaining`, `truth.x/y`; support `get_agent_observation`/`get_unit_position`; support `get_unit_messages` | consumes World Truth + Shared Tactical Picture; produces Agent Observation | **Declared this slice** (was V4 leak) |
| C2 | `gym_envs/scenario_loader/mission_observation.py` — compiled modes (`basic`/`nav_v1`/`nav_v2`/…) | compiled `ef_py.compute_mission_observation` from `mission_command_view` + route guidance (truth passed in) | produces Agent Observation (compiled) | compiled facade path; covered by C1 module declaration |
| C3 | `python/rl/runtime/world_batch/observation_batching.py` + `_observation_mixin.py` | `state.last_truth`/`state.last_inst` (truth/instrument cache), `truth.x/y`, `inst.alt_baro` → compiled batch | consumes World Truth (cache) → produces Agent Observation | **Yes** — I32 stage contract (`state_read`/`observation_build`), already conformant |
| C4 | `gym_envs/scenario_loader/reward_runtime/air_combat.py` | `truth.missiles_remaining`; `sim.export_recent_engagement_events`; `sim.debug_get_aircraft_damage_state`/`debug_get_ground_contact_state`; `sim.is_unit_active` | consumes World Truth; produces reward | **Declared this slice** (was V5 leak) |
| C5 | `gym_envs/scenario_loader/reward_runtime/naval.py` | `truth.x/y`, `truth.contacts`; `sim.get_unit_position`/`get_agent_observation` (other units); `sim.get_unit_messages` | consumes World Truth + Shared Tactical Picture; produces reward | **Declared this slice** (was V6 leak) |
| C6 | `gym_envs/scenario_loader/reward_runtime/safety.py` | own-ship `truth.health/z/pitch/speed` | consumes World Truth; produces reward inputs | **Declared this slice** (own-ship read) |
| C7 | `gym_envs/scenario_loader/reward_runtime/shaping_inputs.py` | own-ship `truth.z/speed` + instrument vector | consumes World Truth; produces reward inputs | **Declared this slice** (own-ship read) |
| C8 | `gym_envs/scenario_loader/reward_runtime/objectives.py` | own-ship `truth.z/health/heading/x/y/missiles_remaining`; target `truth.contacts`, `sim.is_unit_active`/`get_unit_health` | consumes World Truth; produces reward/objective inputs | **Declared this slice** (own + target read) |
| C9 | `gym_envs/scenario_loader/reward_runtime/compiled_runtime.py` | assembles pre-built input DTOs; no direct information-layer read | — (assembler, not a direct consumer) | N/A — excluded from registry |
| C10 | `gym_envs/scenario_loader/core.py::get_policy_agent_observation` / `get_policy_instrument_state` | `sim.get_agent_observation`/`get_instrument_state` (facade-backed proxy on batch path) | the World-Truth read seam itself (V3) | maintained seam; T8 target is the `ObservationViewSpec` export point |
| C11 | `gym_envs/scenario_loader/step_evaluation.py` | own-ship `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health`; orchestrates reward surfaces | stage-bundling aggregator (V7) | Deferred — 待裁定 (P9+P10 bundle) |
| C12 | `gym_envs/scenario_loader/execution_runtime/mainline.py` | orchestrates the execution step; reward/observation via loader | orchestrator | Deferred — 待裁定 |
| C13 | `gym_envs/leader_env_parts/decision_runtime/observations.py::build_observation` | mostly `inst.*`; `truth.x/y` for ILS/runway/anchor geometry; delegates nav to `get_mission_observation` | produces Agent Observation; consumes World Truth (position) | Deferred — 待裁定 (leader path) |
| C14 | `python/rl/tasking/leader_tasking.py` | `get_policy_agent_observation`/`get_policy_instrument_state` at multiple sites | scripted director; consumes World Truth | Deferred — 待裁定 (scripted-director epistemics) |
| C15 | `tools/eval/waypoint_eval_utils.py`, `tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | eval-tool reads | eval/diagnostics surface — outside the maintained policy path |
| C16 | `gym_envs/universal_env.py::UniversalEnv` class constructor | — | demoted fail-fast shell (`__init__` raises `RuntimeError`) | Dead path — no declaration needed. This is the removed raw-kernel env only; it is distinct from the still-active `build_universal_observation` it re-exports (see C17). |
| C17 | `gym_envs/universal_env_parts/observations.py::build_universal_observation` — active universal policy-observation assembly, called by `CooperativeWorldBatchVecEnv` and `MultiAgentWorldRuntimeView` | `truth.x/y` (ILS query), `truth.contacts`, `truth.rwr_warnings` (Python fallback path); compiled path passes `truth` to `ef_py.compute_execution_observation_runtime_numpy`; delegates the mission vector to `get_mission_observation` | consumes World Truth; produces Agent Observation | **Declared this slice** (repair round: split out of the first-slice C16, which misread this active path as dead) |
| C18 | `gym_envs/scenario_loader/navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` — direct waypoint reward-input consumer, called by `step_evaluation.py`/`execution_runtime/mainline.py` via `loader._build_waypoint_step_state` | own-ship `truth.x/y` (distance-to-fix and route reference); builds `ef_py.WaypointRewardInputs` | consumes World Truth; produces reward inputs | **Declared this slice** (repair round: missed by the first-slice census) |
| C19 | `gym_envs/scenario_loader/navigation_runtime/guidance.py` — shared route-guidance geometry helper (`query_route_guidance_result`, `compute_waypoint_guidance_state`, `apply_waypoint_guidance_update`, …) | own-ship `truth.x/y/speed` (route guidance geometry; `get_policy_agent_observation` fallback) | spans command-delivery (P3/P4 autopilot target) + reward-support (P10); not a single Agent-Observation-facing consumer | Deferred — 待裁定 (mixed guidance/command helper, not force-classified; repair round) |

Registered (declared) this slice: C1, C4, C5, C6, C7, C8, C17, C18 (the eight
modules in `MAINTAINED_INFORMATION_LAYER_CONSUMERS`; C17/C18 added this repair
round). Already conformant: C3. Excluded as non-consumer: C9. Dead: C16. Deferred
with rationale (宁缺毋滥, not force-classified): C11, C12, C13, C14, C19. Outside
the maintained policy path: C15.

## 3. Truth-leak inventory

World-Truth direct reads on policy paths (policy/observation construction or
reward that reads truth while representing an Agent-Observation-facing consumer).
Verdicts: **diagnostic** = legitimate diagnostic use; **leak** = needs T8
view-convergence; **exempt** = legitimized by a declaration/seam.

| ID | Location | Reads | Verdict | Note |
|----|----------|-------|---------|------|
| TL1 | `mission_observation.py::_air_combat_c2_roe_vector` (`_target_track`, `_truth_missiles_remaining`) | `truth.contacts` (target range / track age / classification), `truth.missiles_remaining` | **leak** (other-entity + own weapon count) | V4. Now G4-declared (C1 CONSUMED World Truth). T8: read a declared track/observation export instead of raw `truth.contacts`. |
| TL2 | `mission_observation.py::_naval_screen_station_vector` | `truth.x/y` (own), `truth.contacts` (target present); `runtime_view.get_agent_observation`/`get_unit_position` (support units) | **leak** (own-ship + other-entity) | V4. Now G4-declared (C1). Support truth-obs and target contacts are god's-eye reads pending convergence. |
| TL3 | `mission_observation.py::_naval_screen_station_vector` | `runtime_view.call_optional("get_unit_messages", support)` (report chain) | **exempt** | Shared Tactical Picture: link-distributed reports are a legitimate declared layer (C1 CONSUMED Shared Tactical Picture), not raw truth. |
| TL4 | `reward_runtime/air_combat.py::_truth_missiles_remaining` (`_air_combat_observed_release_count`, `_apply_release_shaping`) | `truth.missiles_remaining` | **leak** (own weapon state via truth) | V5. Now G4-declared (C4). Own-ship weapon count, low-risk, but read from raw truth. |
| TL5 | `reward_runtime/air_combat.py::_recent_engagement_events` / `_standard_damage_fact_projections` | `sim.export_recent_engagement_events()` (damage/lifecycle/consequence events) | **leak** (engagement evidence) | V5. Partially self-gated: `consumer_visibility == "diagnostics_only"` events are filtered out. T8: route through a declared engagement-evidence view. |
| TL6 | `reward_runtime/air_combat.py::_damage_consequence_snapshot`, `_ground_contact_terminal_state` | `sim.debug_get_aircraft_damage_state`, `sim.debug_get_ground_contact_state` | **diagnostic** | Explicit `debug_*` APIs used for damage-consequence reward shaping; acceptable diagnostic use. |
| TL7 | `reward_runtime/air_combat.py::combat_entity_terminal_state` | `sim.is_unit_active(target)` | **leak** (other-entity liveness) | V5. Target liveness is authoritative truth; T8: derive from a declared engagement/observation view. |
| TL8 | `reward_runtime/naval.py::_station_reward_terms` / `apply_naval_reward_surface` | `truth.x/y` (own), `truth.contacts` (target), `sim.get_unit_position(support)`, `sim.get_agent_observation(support)` | **leak** (own-ship + other-entity) | V6. Now G4-declared (C5). Other-unit positions/observations are god's-eye reads pending convergence. |
| TL9 | `reward_runtime/naval.py::_support_received_target_report` | `sim.get_unit_messages(support)` (report chain) | **exempt** | Shared Tactical Picture (C5 CONSUMED Shared Tactical Picture): legitimate link-distributed report. |
| TL10 | `reward_runtime/safety.py::build_safety_runtime_inputs` | own-ship `truth.health/z/pitch/speed` | **leak** (own-ship self-read, low-risk) | Now G4-declared (C6). Own-ship state is observable; converge onto a declared own-ship observation view. |
| TL11 | `reward_runtime/shaping_inputs.py::build_flight_shaping_runtime_inputs` | own-ship `truth.z/speed` | **leak** (own-ship self-read, low-risk) | Now G4-declared (C7). |
| TL12 | `reward_runtime/objectives.py::build_conditional_objective_inputs`, `_combat_target_snapshot` | own-ship `truth.z/health/heading/x/y/missiles_remaining`; target `truth.contacts` range, `sim.is_unit_active`/`get_unit_health(target)` | **leak** (own-ship + other-entity) | Now G4-declared (C8). Target health/liveness are god's-eye reads pending convergence. |
| TL13 | `scenario_loader/core.py::get_policy_agent_observation` / `get_policy_instrument_state` | `sim.get_agent_observation`/`get_instrument_state` (facade-backed proxy on batch path) | **exempt** (maintained seam) | V3. The single maintained read chokepoint; on the batch path `sim` is `_ScenarioLoaderRuntimeProxy` (facade-backed). T8 target: turn this seam's return into a declared `ObservationViewSpec` export so C1/C4/C5/C6/C7/C8 stop reading raw truth. |
| TL14 | `scenario_loader/step_evaluation.py` (`build_execution_runtime_state`, reward-input assembly) | own-ship `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health` | **leak** (own-ship, aggregator; deferred) | V7. Stage-bundling orchestrator; declaration deferred (待裁定) rather than force-classified. |
| TL15 | `leader_env_parts/decision_runtime/observations.py::build_observation` | own-ship `truth.x/y` (ILS/runway/anchor geometry) | **leak** (own-ship position; deferred) | Leader observation path; declaration deferred (待裁定). |
| TL16 | `python/rl/tasking/leader_tasking.py` (multiple sites) | `get_policy_agent_observation`/`get_policy_instrument_state` | **leak** (scripted-director; deferred) | Scripted director consuming World Truth; epistemic layer (maintained doctrine vs diagnostics-only) deferred (待裁定). |
| TL17 | `tools/eval/waypoint_eval_utils.py`, `tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | **exempt** (eval surface) | Eval/diagnostics tooling, outside the maintained policy path; not a maintained-surface leak. |
| TL18 | `universal_env_parts/observations.py::build_universal_observation` | `truth.x/y` (ILS query), `truth.contacts`, `truth.rwr_warnings` (Python fallback); compiled path passes `truth` to `ef_py.compute_execution_observation_runtime_numpy` | **leak** (own-ship + other-entity tracks/warnings) | Now G4-declared (C17). Active policy-observation path (`CooperativeWorldBatchVecEnv`/`MultiAgentWorldRuntimeView`) that the first-slice census misread as dead; T8: read a declared observation export instead of raw truth. |
| TL19 | `navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` | own-ship `truth.x/y` (distance-to-fix, route reference) → `ef_py.WaypointRewardInputs` | **leak** (own-ship position via raw truth) | Now G4-declared (C18). Own-ship position feeding waypoint reward inputs; converge onto a declared own-ship observation view. |
| TL20 | `navigation_runtime/guidance.py` (`query_route_guidance_result`, `compute_waypoint_guidance_state`, `apply_waypoint_guidance_update`, …) | own-ship `truth.x/y/speed` (route guidance geometry) | **leak** (own-ship; deferred) | Shared route-guidance helper spanning command-delivery (autopilot target) and reward-support; declaration deferred (待裁定) rather than force-classified (C19). |

## 4. Verdict distribution

| Verdict | Count | Entries |
|---------|-------|---------|
| leak — needs T8 view-convergence | 15 | TL1, TL2, TL4, TL5, TL7, TL8, TL10, TL11, TL12, TL14, TL15, TL16, TL18, TL19, TL20 |
| exempt — legitimized by declaration/seam | 4 | TL3, TL9, TL13, TL17 |
| diagnostic — legitimate diagnostic use | 1 | TL6 |

Of the 15 leaks, 11 are now G4-declared (TL1, TL2, TL4, TL5, TL7, TL8, TL10,
TL11, TL12 on C1/C4/C5/C6/C7/C8, plus TL18 on C17 and TL19 on C18 added this
repair round — the eight declared consumers) and 4 are deferred
aggregator/leader/guidance paths (TL14, TL15, TL16, TL20). Declaring a leak does
not close it: the declaration makes the current truth read visible and testable,
and the T8 convergence target is the single `ObservationViewSpec` export at TL13
so downstream consumers read Agent Observation instead of raw World Truth.

## 5. Next slices (not done here)

- Materialize `ObservationViewSpec` as a runtime facade export at the TL13 seam
  and migrate the declared consumers (C1/C4/C5/C6/C7/C8/C17/C18) to read through
  it (closes TL1/TL2/TL4/TL5/TL7/TL8/TL10/TL11/TL12/TL18/TL19).
- Adjudicate and declare the deferred aggregator/leader/guidance paths (C11–C14,
  C19; TL14–TL16, TL20).
- Add the G4 AST gate that bans non-diagnostic World-Truth reads on declared
  consumers once the view export exists (design doc §15; census §3 part 3).

## Related

- [Unified Architecture Program](README.md)
- [SCAL Conformance Census (2026-07-20)](scal_conformance_census_20260720.md)
  (V3–V7 register; first-batch consumer priority; structural precedent)
- [T6 Residual Ledger (2026-07-20)](t6_residual_ledger.md) (sibling `reference`
  register)
- [Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md)
  (§3 information-state layers; §6 P0-P10 stages; §15 G4; §16 representation strategy)
- Facility: `python/architecture/information_layer.py`
- Gate: `tests/architecture/information_state/test_g4_layer_declarations.py`
