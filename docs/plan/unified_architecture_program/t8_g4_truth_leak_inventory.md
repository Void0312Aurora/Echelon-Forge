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
is flipped here. The **third slice (§7, 2026-07-21)** adjudicates and declares the
five remaining deferred consumers (C11–C14, C19; TL14–TL16, TL20): each now
carries a G4 declaration (its information-state layer and semantic stage). In the
independent-review repair round (§7.5) the leader observation producer (C13) was
additionally migrated onto the declared view — its own-ship reads are
token-isomorphic to `own_ship_field`, and element-exact numeric parity with the
fae17eb8 baseline function is pinned by a new focused test — flipping TL15 to
*converged*; C11/C12/C14/C19 keep their reads per their adjudications
(*declared-but-open*, 宁缺毋滥). Declarations are pure metadata (zero behavior
change); the C13 migration is a mechanical read relocation with pinned parity.

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
| C11 | `gym_envs/scenario_loader/step_evaluation.py` | own-ship `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health`; orchestrates reward surfaces | consumes World Truth (own-ship); stage-bundling aggregator (V7); P10 ObservationExport | **Declared (§7)**; reads kept (orchestrator bundling DTOs, not leaf reads) — declared-but-open (TL14) |
| C12 | `gym_envs/scenario_loader/execution_runtime/mainline.py` | own-ship `truth.z/x/y/vx/vy`; orchestrates the execution step; reward/observation via loader | consumes World Truth (own-ship); execution step controller; P10 ObservationExport | **Declared (§7)**; reads kept (orchestrator) — declared-but-open |
| C13 | `gym_envs/leader_env_parts/decision_runtime/observations.py::build_observation` | mostly `inst.*`; own-ship x/y for ILS/runway/anchor geometry; delegates nav to `get_mission_observation` | consumes World Truth (position); produces Agent Observation; P10 ObservationExport | **Converged (§7.5 repair round)** — own-ship reads via `observation_view.own_ship_field`; ban-gated; parity pinned by `tests/leader/test_leader_observation_view_parity.py` |
| C14 | `python/rl/tasking/leader_tasking.py` | `get_policy_agent_observation`/`get_policy_instrument_state` at multiple sites | consumes World Truth (own-ship); scripted C2/leader director (maintained doctrine); P2 TaskingIntent + P3 CommandDelivery | **Declared (§7)**; migration forbidden (would add `python.rl`→`gym_envs` reverse dep) — declared-but-open (TL16) |
| C15 | `tools/eval/waypoint_eval_utils.py`, `tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | eval-tool reads | eval/diagnostics surface — outside the maintained policy path |
| C16 | `gym_envs/universal_env.py::UniversalEnv` class constructor | — | demoted fail-fast shell (`__init__` raises `RuntimeError`) | Dead path — no declaration needed. This is the removed raw-kernel env only; it is distinct from the still-active `build_universal_observation` it re-exports (see C17). |
| C17 | `gym_envs/universal_env_parts/observations.py::build_universal_observation` — active universal policy-observation assembly, called by `CooperativeWorldBatchVecEnv` and `MultiAgentWorldRuntimeView` | `truth.x/y` (ILS query), `truth.contacts`, `truth.rwr_warnings` (Python fallback path); compiled path passes `truth` to `ef_py.compute_execution_observation_runtime_numpy`; delegates the mission vector to `get_mission_observation` | consumes World Truth; produces Agent Observation | **Converged this slice** (§6; reads via declared view; repair-round add) |
| C18 | `gym_envs/scenario_loader/navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` — direct waypoint reward-input consumer, called by `step_evaluation.py`/`execution_runtime/mainline.py` via `loader._build_waypoint_step_state` | own-ship `truth.x/y` (distance-to-fix and route reference); builds `ef_py.WaypointRewardInputs` | consumes World Truth; produces reward inputs | **Converged this slice** (§6; own-ship read via declared view; repair-round add) |
| C19 | `gym_envs/scenario_loader/navigation_runtime/guidance.py` — shared route-guidance geometry helper (`query_route_guidance_result`, `compute_waypoint_guidance_state`, `apply_waypoint_guidance_update`, …) | own-ship `truth.x/y/speed` (route guidance geometry; `get_policy_agent_observation` fallback) | consumes World Truth (own-ship); spans command-delivery (P3/P4 autopilot target) + reward-support (P10); not a single Agent-Observation-facing consumer | **Declared (§7)**; migration awaits a command/guidance read owner (an observation view is not the right owner for command-delivery reads) — declared-but-open (TL20) |

Converged onto the declared observation view: C1, C4, C5, C6, C7, C8, C17, C18
(second slice, §6; C17/C18 added in the first-slice repair round) plus C13 (third
slice repair round, §7.5) — the nine modules in
`VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS`. Declared (third slice, §7) with
reads not yet view-converged (declared-but-open, in
`DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS`): C11, C12, C14, C19.
`MAINTAINED_INFORMATION_LAYER_CONSUMERS` is the union of those two sets (13
declared consumers). Already conformant: C3. Excluded as non-consumer: C9. Dead:
C16. Outside the maintained policy path: C15.

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
| TL14 | `scenario_loader/step_evaluation.py` (`build_execution_runtime_state`, reward-input assembly) | own-ship `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health` | **declared-but-open** (own-ship, aggregator) | V7 (C11). Declared 2026-07-21 (§7): CONSUMED World Truth, PRODUCED (), stage P10 ObservationExport (I32 closure; P9 removed in the §7.5 repair). Reads kept, not view-converged: a stage-bundling orchestrator assembling reward/observation input DTOs, not a leaf observation-read surface. |
| TL15 | `leader_env_parts/decision_runtime/observations.py::build_observation` | own-ship x/y (ILS/runway/anchor geometry) | **converged** (declared view; §7.5 repair round) | C13. Declared 2026-07-21 (§7): CONSUMED World Truth, PRODUCED Agent Observation, stage P10 ObservationExport. Converged in the §7.5 repair round: own-ship reads via `observation_view.own_ship_field` (token-isomorphic replacement of `getattr(truth, "x"/"y", 0.0)`); ban-gated; element-exact parity with the fae17eb8 baseline pinned by `tests/leader/test_leader_observation_view_parity.py` (incl. the no-x/y default-firing scenario and a view-seam corruption red-proof). |
| TL16 | `python/rl/tasking/leader_tasking.py` (multiple sites) | `get_policy_agent_observation`/`get_policy_instrument_state` | **declared-but-open** (scripted-director) | C14. Declared 2026-07-21 (§7): CONSUMED World Truth, PRODUCED (), stages P2 TaskingIntent + P3 CommandDelivery. Adjudicated as maintained doctrine (a scripted C2/leader director legitimately consuming own-ship truth), not diagnostics-only. Migration forbidden: routing its reads through `gym_envs.observation_view` would add a `python.rl`→`gym_envs` reverse dependency; the declaration is neutral (`python.architecture`). |
| TL17 | `tools/eval/waypoint_eval_utils.py`, `tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | **exempt** (eval surface) | Eval/diagnostics tooling, outside the maintained policy path; not a maintained-surface leak. |
| TL18 | `universal_env_parts/observations.py::build_universal_observation` | `truth.x/y` (ILS query), `truth.contacts`, `truth.rwr_warnings` (Python fallback); compiled path passes `truth` to `ef_py.compute_execution_observation_runtime_numpy` | **converged** (declared view) | C17. Leaf reads via `observation_view.own_ship_attr` / `contacts` / `rwr_warnings`. The compiled path still passes the whole `truth` object to the kernel — a whole-object transfer, not a leaf read; out of scope this slice. |
| TL19 | `navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` | own-ship `truth.x/y` (distance-to-fix, route reference) → `ef_py.WaypointRewardInputs` | **converged** (declared view) | C18. Own-ship `truth.x/y` via `observation_view.own_ship_field`; the guidance helper (C19/TL20) delegation is unchanged (deferred). |
| TL20 | `navigation_runtime/guidance.py` (`query_route_guidance_result`, `compute_waypoint_guidance_state`, `apply_waypoint_guidance_update`, …) | own-ship `truth.x/y/speed` (route guidance geometry) | **declared-but-open** (own-ship) | C19. Declared 2026-07-21 (§7): CONSUMED World Truth, PRODUCED (), stages P3 CommandDelivery + P4 PlatformControl + P10 ObservationExport. A shared helper spanning command-delivery (autopilot target) and reward support; migration deferred until a command/guidance read owner exists (an observation view is not the right owner for command-delivery reads). |

## 4. Verdict distribution

| Verdict | Count | Entries |
|---------|-------|---------|
| converged — reads via the declared observation view (§6; TL15 in §7.5) | 12 | TL1, TL2, TL4, TL5, TL7, TL8, TL10, TL11, TL12, TL15, TL18, TL19 |
| declared-but-open — G4 declaration landed (§7), reads not yet view-converged | 3 | TL14, TL16, TL20 |
| exempt — legitimized by declaration/seam | 4 | TL3, TL9, TL13, TL17 |
| diagnostic — legitimate diagnostic use | 1 | TL6 |

The 12 converged entries are the nine converged consumers' leaf reads (TL1, TL2,
TL4, TL5, TL7, TL8, TL10, TL11, TL12 on C1/C4/C5/C6/C7/C8, TL18 on C17, TL19 on
C18, and TL15 on C13 since the §7.5 repair round), now flowing through the
declared observation-view owner (`gym_envs/observation_view.py`) rather than raw
World Truth. The 3 declared-but-open entries are the aggregator/director/guidance
paths (TL14, TL16, TL20): each carries a G4 declaration (§7) but keeps its raw
reads for the reasons adjudicated there (orchestrator DTO-bundling;
`python.rl`→`gym_envs` reverse-dep bar; command/guidance read owner not yet
built). "Declared" is not "converged": the declaration is pure metadata, so those
three paths still read raw World Truth structurally until a later slice converges
them — but there are no longer any *undeclared* leaks on the maintained surface.
The exempt/diagnostic reads (TL3, TL6, TL9, TL13, TL17) keep their verdict; where
they sit on a migrated consumer they are routed through the view's
Shared-Tactical-Picture / diagnostic faces for consistency. A full typed
`ObservationViewSpec` facade export at the TL13 seam (so the seam's return itself
is a typed spec) remains a later step.

## 5. Next slices (not done here)

- Turn the TL13 seam's return into a full typed `ObservationViewSpec` facade
  export. The second slice (§6) materialized the declared read view over the
  seam's `truth`/`sim` output and migrated the eight consumers onto it; the typed
  spec export (so the seam itself returns a typed view object) remains.
- Converge the declared-but-open consumers (§7) onto the view, per their
  adjudicated blockers:
  - C19 (TL20): build a command/guidance read owner (a peer of the observation
    view) for the command-delivery reads, then converge the reward-support reads
    onto the observation view.
  - C11/C12 (TL14): converge the aggregators' own-ship reads once the
    reward/observation input-DTO assembly can source them from the view without
    perturbing the compiled runtime.
  - C14 (TL16): stays declared-only unless a neutral read owner reachable from
    `python.rl` without a `python.rl`→`gym_envs` edge is introduced.
- Extend the G4 AST truth-read ban as those declared-but-open consumers converge:
  move each path from `DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS` into
  `VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS`. The ban already covers the eight
  migrated consumers (§6; `tests/architecture/information_state/test_g4_truth_read_ban.py`).

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

## 7. Third slice: deferred-consumer adjudication and declaration (I56, 2026-07-21)

The third T8 slice closes the §5 "adjudicate and declare the deferred paths" item
for the five consumers the first two slices left 待裁定 (C11–C14, C19; TL14–TL16,
TL20). Each is given an epistemic-layer verdict and a G4 declaration (three
module-level constants). The declarations are pure metadata (zero behavior
change; the five-consumer behavior test set is bit-identical before/after). In
the independent-review repair round (§7.5), C13 — the one consumer whose reads
are token-isomorphic to an existing view face — was additionally migrated onto
the view with a new pinned parity test, flipping TL15 to *converged*; the other
four keep their reads per §7.3 (宁缺毋滥: a read is only relocated when it is
zero-risk and carries element-exact numeric-parity evidence against the baseline
function).

### 7.1 Per-consumer adjudication

| Consumer (TL) | CONSUMED | PRODUCED | SEMANTIC_STAGE | Verdict | Migrate? | Rationale |
|---------------|----------|----------|----------------|---------|----------|-----------|
| C11 `step_evaluation` (TL14) | World Truth | () | P10 ObservationExport | declared-but-open | No (declare-only) | Stage-bundling aggregator: its own-ship reads feed reward/observation input-DTO assembly, not a leaf observation surface. Orchestrators declare but do not migrate. Stage per I32 closure (§7.5 P2 repair: P9 removed — it reads damage facts, produces no effects). |
| C12 `execution_runtime/mainline` | World Truth | () | P10 ObservationExport | declared-but-open | No (declare-only) | Execution step controller (reward/termination/status + combat-terminal / damage-consequence overrides). Orchestrator; declare, don't migrate. Stage per I32 closure (§7.5 P2 repair: P9 removed — the overrides read already-produced damage/liveness facts). |
| C13 `leader .../observations::build_observation` (TL15) | World Truth | Agent Observation | P10 ObservationExport | converged | **Yes (§7.5 repair round)** | A clean Agent-Observation producer whose own-ship x/y reads were token-isomorphic to `observation_view.own_ship_field` (the migrated C17/C18 shape). Migrated as a mechanical `own_ship_field` move; element-exact parity with the fae17eb8 baseline pinned by `tests/leader/test_leader_observation_view_parity.py`; in the ban-gate scan set. |
| C14 `python/rl/tasking/leader_tasking` (TL16) | World Truth | () | P2 TaskingIntent, P3 CommandDelivery | declared-but-open | No (migration forbidden) | Adjudicated as **maintained doctrine** (a scripted C2/leader director that legitimately consumes own-ship truth to author tasking intent and commands), not diagnostics-only. Declaration is neutral (`python.architecture`), but migration would route `python.rl` reads through `gym_envs.observation_view`, adding a `python.rl`→`gym_envs` reverse dependency — forbidden. |
| C19 `navigation_runtime/guidance` (TL20) | World Truth | () | P3 CommandDelivery, P4 PlatformControl, P10 ObservationExport | declared-but-open | No (needs a command owner) | A mixed command/reward helper: its own-ship reads feed both the autopilot command target (command delivery) and waypoint reward support. An observation view is not the right owner for command-delivery reads, so migration awaits a separate command/guidance read owner. |

Notes:
- **Stages.** Semantic stages follow the codebase's authoritative usage (the I32
  stage contract in `python/rl/runtime/world_batch/core.py`): reward and
  observation build both close at P10 ObservationExport (`observation_build` and
  `reward_episode` both declare P10; `reward_episode` adds P1 WorldSetup solely
  for the episode-autoreset sub-stage, which lives in the vec env, not in
  C11/C12); tasking-intent/behavior at P2, command delivery at P3, platform
  control at P4. No I32 batch-step stage or sub-stage declares P9 EffectsDamage —
  P9 is the kernel effects/damage system's *production* stage, and C11/C12 only
  read already-produced damage facts — so the aggregators declare P10 only
  (§7.5 P2 repair; the first cut over-declared P9 and was corrected).
- **PRODUCED.** Reward inputs, tasking/command artifacts and guidance/command
  targets are not information layers, so those consumers declare `PRODUCED = ()`;
  only C13, an observation producer, declares `Agent Observation`.

### 7.2 Registry and gate changes

- `python/architecture/information_layer.py`: the maintained registry is split
  into `VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS` (ban-gated; the eight §6
  consumers plus C13 since the §7.5 repair round — nine) and the new
  `DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS` (declaration-gated only; C11,
  C12, C14, C19 — four). `MAINTAINED_INFORMATION_LAYER_CONSUMERS` is now the
  union of the two (13 consumers).
- Declaration gate (`test_g4_layer_declarations.py`): now parametrizes over all 13
  maintained consumers (the five new declarations included) and adds a partition
  test (converged ∩ deferred = ∅; union = maintained).
- Ban gate (`test_g4_truth_read_ban.py`): scan set extended to the nine converged
  consumers (C13 added in §7.5), plus a load-bearing test that each
  declared-deferred consumer is excluded from the scan *and still performs raw
  truth reads* — so the deferral is real, and converging one later (which removes
  its raw reads) forces moving it into the converged, ban-gated set.
- New parity harness: `tests/leader/test_leader_observation_view_parity.py`
  (§7.5) pins C13's output element-exactly against the fae17eb8 baseline
  function on synthetic scenarios and proves the reads flow through the view
  seam (monkeypatch corruption red-proof).

### 7.3 Migration outcomes

C13 is migrated (§7.5): its own-ship x/y reads were token-isomorphic to
`own_ship_field` (exactly the C17/C18 shape), the module imports without
`stable_baselines3`, and the missing numeric harness was added rather than
waited for — the new focused test pins `build_observation`'s output
element-exactly against the fae17eb8 baseline function (extracted via
`git show`), including the no-x/y default-firing scenario, and a one-off dual-run
compared baseline vs migrated element-identically across the same scenarios.
The other four keep their reads: C11/C12 are orchestrators (declare-only by
design — their reads feed input-DTO assembly, not a leaf observation surface),
C14's migration is barred by the `python.rl`→`gym_envs` reverse-dependency rule,
and C19 needs a command/guidance read owner first (an observation view is not
the right owner for command-delivery reads).

### 7.4 Verification (zero behavior change)

- `tests/architecture/information_state` — 37 passed (was 26; +5 declaration
  parametrizations for the new consumers, +1 registry-partition test, +4
  declared-deferred ban-exclusion parametrizations, +1 ban-scan parametrization
  for the migrated C13).
- New parity harness `tests/leader/test_leader_observation_view_parity.py` —
  3 passed (two pinned-baseline scenarios + view-seam red-proof); corrupting the
  view face reds the pins (load-bearing evidence, §7.5).
- Five-consumer behavior set (`tests/leader`, `tests/runtime/execution`,
  `tests/runtime/mission`, `tests/runtime/navigation`, with the new parity file
  excluded for set-identity), identical before/after: 179 passed, 234 subtests
  passed, 1 collection error
  (`tests/leader/test_leader_runtime_control_contracts.py`; `stable_baselines3`
  absent — machine baseline).
- The declarations add no imports and no logic; the C13 migration relocates the
  own-ship leaf reads only (parity pinned as above).

### 7.5 Independent-review repair (2026-07-21)

The independent review of this slice returned needs-repair on two findings; both
were repaired in place the same day (all §7.4 gates re-run):

- **P1 — C13 deferral rationale was factually wrong (adjudication).** The first
  cut deferred C13's migration claiming "the leader-env numeric-parity tests are
  `stable_baselines3`-gated". The review disproved this: no numeric test covers
  `build_observation` at all (the sole SB3 collection error comes from
  runtime-control tests that never call it), and the module imports cleanly
  without SB3. Repair: C13 was migrated onto the declared view (the mechanical
  `own_ship_field` move the adjudication already called migration-ready), and the
  *missing harness* was built instead of being waited for —
  `tests/leader/test_leader_observation_view_parity.py` pins the output
  element-exactly against the fae17eb8 baseline function on x/y-sensitive
  synthetic scenarios (plus the no-x/y default-firing case) and proves the pin is
  load-bearing through the view-seam corruption red-proof. A one-off dual-run
  (baseline module exec'd from `git show`, live module imported) confirmed
  element-identical outputs and that corrupting `own_ship_field` diverges them.
  TL15 flips to *converged*; registry moves C13 into the ban-gated converged set
  (9/4 split).
- **P2 — C11/C12 over-declared P9 EffectsDamage (stage closure).** The first cut
  declared the aggregators at P9+P10. The I32 stage contracts in
  `python/rl/runtime/world_batch/core.py` close reward and observation assembly
  at P10 (`observation_build` P10; `reward_episode` P10 + P1-for-autoreset-only;
  even the event-driven `post_launch_assessment` sub-stage declares P4/P5/P10) and
  declare P9 nowhere — P9 is the kernel effects/damage system's production stage,
  while C11/C12 only *read* already-produced damage facts. Repair: both
  `SEMANTIC_STAGE` tuples are now `("P10 ObservationExport",)`; the §7.1 matrix,
  §2 census rows and TL14 note were corrected accordingly.

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
