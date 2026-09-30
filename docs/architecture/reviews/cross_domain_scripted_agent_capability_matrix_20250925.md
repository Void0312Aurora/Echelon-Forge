# Scripted Agent Capability Evidence Matrix

- Document kind: review
- Lifecycle: maintained
- Date: 2026-09-25
- Last verified: 2026-09-27
- Owner: architecture/cross-domain-agency
- Scope: current evidence boundary for the independent scripted-agent line

This matrix is a reporting boundary. It does not promote a domain because a
model is registered, an action call succeeds, or a focused proxy test is green.
The final `playable` label requires the scenario, runtime, CLI, visualization,
reset/replay, authority, and report evidence named in the plan.

## Current domain matrix

| Domain | Registration | Current label | Evidence retained | Accepted claims | Deferred claims |
| --- | --- | --- | --- | --- | --- |
| Air | `air.execution.phase_scripted` (`maintained`, `autopilot_controller`); `air.engagement.c2_roe_scripted` (`adapter`, `air_tactical_engagement_controller`); `air.ew.rwr_response_scripted` (`adapter`, `air_ew_controller`); `air.ew.rwr_action_scripted` (`adapter`, `air_ew_action_controller`) | `playable_candidate` | `python/tasking_contracts/air/execution/model.py`; `python/tasking_contracts/air/engagement/model.py`; `python/tasking_contracts/air/strategy/planning.py`; `python/tasking_contracts/air/strategy/weapons.py`; `python/tasking_contracts/air/strategy/assessment.py`; `python/tasking_contracts/air/ew/model.py`; `python/simulation/air/tasking_runtime.py`; `examples/config/database/weapons/air_to_air/aim_120c.json`; `scenarios/air_combat/1v1/air_combat_1v1_c2_roe_terminal_generic_aircraft_surrogate_v1.json`; `scenarios/air_combat/cooperative_air_2v2_scripted_ew_response_v1.json`; `scenarios/air_combat/cooperative_air_4v4_scripted_ew_response_v1.json`; `scenarios/air_combat/cooperative_air_2v1_scripted_c2_roe_engagement_v1.json`; `scenarios/air_combat/cooperative_air_2v2_scripted_c2_roe_terminal_v1.json`; `scenarios/air_combat/cooperative_air_4v4_scripted_c2_roe_terminal_v1.json`; `scenarios/combined/takeoff_to_landing_c2_task_demo_v1.json`; `tools/diagnostics/flight_trajectory/takeoff_to_landing.py`; `tools/diagnostics/air_cooperative_ew_scripted_demo.py`; `tools/diagnostics/air_cooperative_combat_scripted_demo.py`; neutral lifecycle and manifest-resolution tests; runway-geometry correction tests; leader adapter; task-eval and manifest-driven viz route tests; direct static and randomized full single-world successes plus full same-process randomized reset/replay recorded in the plan ledger; direct no-RL C2 sequence and landing record with a native report-validity result; bounded cooperative roster trace with Lead/Wing roles; roster-driven two-element four-slot EW trace with world-owned opponent roster and same-seed replay; direct Stage 1 C2/ROE hybrid scenario probe with accepted scripted fire and native release; scripted selector regression proving compiled station-1 database munition selection; native Stage 1 near-approach/fuze packet with a non-terminal damage outcome; maintained MQ-9 live damage/effects fixtures at 8 km and 14 km; compiled generic-Aircraft surrogate terminal chain with native `combat_win`; native MAWS launch-warning fixture with source-specific `is_launch`; direct RWR observation probe and typed EW producer/action-extension tests; compiled `air_ew_hybrid_v1` demo with launch-warning-driven chaff/flare requests and InstrumentState native chaff report; paired-run replay regression for the same compiled EW trace; bounded cooperative EW resource-routing test; single-countermeasure doctrine trace for maintained flare consumption; hostile cooperative 2v2 EW demo with world-owned scripted-opponent updates and paired-run replay; native delayed `online_sensor` burst projection regression with stored detonation-coordinate diagnostics; cooperative `air_combat_hybrid_v1` gate/finalizer compatibility regression; paired-run two-aircraft scripted C2/ROE release and terminal demo; cooperative roster mission-override target-owner regression; paired-run two-aircraft/two-target scripted C2/ROE terminal demo; paired-run four-aircraft/two-element scripted C2/ROE terminal demo; pure tactical-planner and planner-integrated engagement regressions; source-backed weapon-envelope parse and planner-constraint regressions; conservative scripted post-launch assessment and 4v4 regression | takeoff, stable-flight, and landing controller composition through a neutral lifecycle; no-RL model construction path; manifest-driven compiled single-world route; complete single-world mission success under one static and one randomized seed; exact full reset/replay for the tested randomized seed; direct no-RL task-driven C2 route updates `TASK_SCRAMBLE -> TASK_CAP -> TASK_RTB -> TASK_RECOVER_LAND`, reports a valid final report, and lands within runway geometry; tactical model emits radar/TMS/master-arm/fire request fields only from declared C2/ROE observation fields; the maintained hybrid Air combat scenario consumes the adapter and reports `fire_once_requested`, `fire_once_accepted`, and `release_executed`; the scripted release selects the database `AIM-120C-7` station profile instead of the legacy fallback and reaches the native near-approach/fuze path; the maintained MQ-9 live fixtures record native component/spatial damage and a mission-kill consequence while preserving non-authoritative vulnerability metadata; the declared generic-Aircraft surrogate reaches native terminal `combat_win`; cooperative runtime routes two active roster members with distinct takeoff clearance segments, accepts the same native Air event-action contract per slot, and applies roster-owned target/C2 fields to slot-local mission state; the roster-driven 4v4 EW demo routes four Blue slots across two elements against four Red scripted opponents with owner count `[4, 0, 0, 0]`, non-empty per-slot warning/request traces, isolated native countermeasure resource samples, and same-seed replay parity; the bounded 2v1 cooperative combat demo routes two scripted Blue slots in one shared world, records both native `fire_once_accepted` and `release_executed`, and reaches shared `combat_win` against the declared generic `Aircraft` surrogate with paired-run parity; the bounded 2v2 two-target demo resolves `Red_A`/`Red_B` from roster-owned mission overrides, records native release from both slots, and reaches shared `combat_win` with paired-run parity; the bounded 4v4 two-element demo resolves four roster-owned targets, records four roster-owned targets, records native release from all four slots, and reaches shared `combat_win` with paired-run parity; the RL-independent planner evaluates finite hold/intercept/reposition candidates from declared track geometry, filters authority/window/assessment/budget constraints, emits auditable utility/reason codes, and preserves the native terminal 4v4 trace after correction; the optional weapon profile consumes only declared database tuning, records source fields, adds a soft guidance-opportunity score, and prevents scripted commit when an explicit opportunity is closed without claiming calibrated WEZ/Pk; the post-launch estimator consumes only declared event/mission facts, requires explicit target-effect evidence for `terminal_observed`, reports `inconclusive` on contact loss or missing effect evidence, and gates scripted reattack without writing native or RL state; EW producer interprets only declared RWR/MAWS rows, emits a typed intent with native-owner residual, maps an opt-in 14-element transport extension to `PilotAction`, the compiled demo emits matching warning/request steps, the maintained instrument read surface reports native chaff and single-doctrine flare consumption, the paired-run test reproduces the trace, cooperative Lead/Wing routing isolates the requested native countermeasure resource per slot, the maintained hostile 2v2 demo routes two active Blue EW agents against two Red scripted opponents with owner counts `[2, 0]`, deterministic warning/request/resource traces, and paired-run parity, and delayed online-sensor resolution preserves the trigger-frame burst geometry under the maintained coarse-step regression | accepted seed coverage; visualization process/render acceptance; complete named-platform tactical engagement terminal success and calibrated post-launch outcome assessment; calibrated target vulnerability/Pk/fuze authority and stable terminal kill consequence (the live MQ-9 fixtures remain synthetic and unvalidated); EW/EMCON and data-link constraints; canonical action-mode/config admission, complete cadence/report closure and terminal EW objective; jammer command owner; communication-loss and tactical-reassignment parity; formation mission parity; joint tasking; visualization and broader large-scale terminal combat beyond the bounded 4v4 surrogate |
| Naval | `naval.station.screen_hold` (`adapter`, `naval_warfare_commander`) | `bounded_adapter` | `python/tasking_contracts/naval/execution.py`; scoped `naval_station_policy_eval.py`; N4 station surface and manifest-resolution tests; direct eight-step report recorded in the plan ledger | zero station-order baseline can enter the common scripted lifecycle while the naval scenario runtime owns contact, station geometry, reporting, recovery, and reward; manifest-driven route; required terms and forbidden-term checks passed in the bounded report | fleet combat, weapon employment, general naval maneuver policy, reset/replay, full naval playable label |
| Joint | `joint.coordination.task_graph_scripted` (`adapter`, `joint_coordination_director`) | `bounded_adapter` | `python/tasking_contracts/joint/coordination.py`; versioned task-graph parser; neutral roster and projection tests; direct compiled `CoordinationIntentPacket` authorization probe | graph-scoped Air/Naval node declaration, authority/support edges, neutral runtime provenance, and compiled coordination DTO projection with explicit omitted-field residuals | maintained joint scenario, command-link delivery, domain execution/report closure, communication loss, reset/replay, joint CLI/viz, and any cross-domain playable label |
| Ground | no scripted model registration | `held` | `scenarios/ground/*`; native G1 static schema and realism-gradient guardrails | static task/status shell and explicit deferred claims | movement, terrain interaction, sensing/track export, fires, effects, damage, and playable runtime |

The fixed-route Air C2 demonstration has both a native seed-7
`LeaderTrainingEnv` record and a direct no-RL seed-0 record. The direct route
executes all four task phases, produces a valid final report, enters the
landing command, and stops inside runway geometry. Broader seed coverage and
the visualization gate remain open. The Air label stays
`playable_candidate`.

### Air Algorithm Substitution Status

The Air row above records the current planner, weapon-profile, and conservative
assessment evidence. Their pure modules are physically layered under
`python/tasking_contracts/air/strategy/`; the former flat paths have been
removed. They remain independently testable and RL/native independent.

- accepted: complete-model replacement through `DecisionModelRegistry`;
  typed planner, assessor, observation, and action protocols; independently
  injectable default implementations; weapon-profile provenance; and compiled
  2v1 terminal parity between default and recording observation/action adapters;
- conditional: a versioned second strategy profile remains ALG-4 work only
  when a second maintained consumer is named. No parallel global strategy
  registry is admitted;
- promotion rule: algorithm substitution evidence does not close command/report,
  named-platform effects, EW, visualization, or the full Air `playable` gate.

The standalone Air CLI now completes the maintained single-world flight
scenario without a training configuration or checkpoint for the recorded
seed-0 run. Its shared world-batch substrate still lives in `python.rl.runtime`;
the successful CLI record does not establish package-level RL isolation.

## Label rules

The following labels are intentionally ordered by evidence strength:

- `held`: runtime capability or required owner is absent; no playable claim is
  allowed.
- `bounded_adapter`: a maintained domain path can consume the common lifecycle,
  but the adapter delegates domain semantics to an existing scoped runtime.
- `playable_candidate`: the domain has an independent scripted producer and a
  concrete vertical path, but one or more final runtime/entry-point gates are
  open.
- `playable`: only after the promotion gate in
  `cross_domain_scripted_agent_system_plan.md` is satisfied and the evidence
  bundle names the exact scenario, commit, test, CLI, visualization, and
  replay records.

RL participation is orthogonal to these labels. A learned or RL adapter may
consume the same neutral contracts after the scripted path is accepted; its
presence cannot raise a label.

### 2026-09-27 evidence supplement

- The Joint row's accepted evidence now also includes
  `python/tasking_contracts/joint/runtime.py` and the
  `ScriptedJointRuntimeConsumer` regression. A versioned graph can resolve its
  active Air, Naval, and Joint nodes through their domain-owned registries and
  run them in one neutral replayable roster. This remains a bounded common
  runtime consumer; no compiled Joint command-link storage or mixed-world
  scenario owner has been admitted.
- The same Joint line now includes
  `python/tasking_contracts/joint/command_link.py`: delayed opaque envelopes
  preserve endpoint validation, sequence order, and clock monotonicity before
  domain adapters receive them. This is a neutral transport sub-gate and does
  not change the Joint `bounded_adapter` label.
- A direct mixed-roster facade probe now verifies both the Air command route
  and the maintained `DDG-51_Flight_I_ASW_Helo_MVP` Naval route when the
  `WorldSpawnRequest.is_agent` contract is enabled. Batch spawn now materializes
  the zero-latency local `CommandLink` required by the maintained command
  surface; the router reads back Air `command_code=2` and Naval
  `command_code=32` with `station_radius_m=14000`. A non-agent Naval spawn
  remains outside this command route by design. This closes command delivery
  for the admitted mixed roster but does not change Naval or Joint labels.
- The same probe now includes `JointFacadeReportRouter`: maintained Air and
  Naval pilot reports are submitted by explicit domain builders and read back
  through the facade's common `active`/`sender_id` fields. This is report
  transport evidence only; report validity and full scenario lifecycle remain
  deferred.
- The Air command/report line now has a direct facade regression proving that
  declared ROE, target provenance, engagement authority, task-group, and
  threat fields persist through a native step. This closes a field-persistence
  sub-gate only; the direct task-driven C2 episode is now also closed for its
  recorded seed. Named-platform terminal, broader seed, visualization, and
  final `playable` claims remain deferred.
- The direct trajectory entry now admits `AirScriptedTaskingRuntime` for
  scenarios that declare `meta.initial_c2_task`. The C2 manager runs between
  navigation and the existing leader command-chain owner, records the full
  `TASK_SCRAMBLE -> TASK_CAP -> TASK_RTB -> TASK_RECOVER_LAND` sequence, and
  preserves the existing pending recovery-vector gate. The seed-0 C2 demo
  terminates with `success_objective`, `mission_status=[4,1,1,1]`, a valid
  final report, and runway geometry; this is a single-seed direct closure, not
  a final Air promotion.

## Required machine-readable manifest shape

The scenario-manifest slice now attaches an additive object to three
representative maintained entry points. The keys below are the minimum review
shape;
the object must preserve domain-owned payloads rather than flattening them into
a mega-schema:

```json
{
  "scripted_capability": {
    "version": "scripted_capability.v1",
    "domain": "air",
    "label": "playable_candidate",
    "model_id": "air.execution.phase_scripted",
    "role_id": "autopilot_controller",
    "lifecycle": "reset_decide_close",
    "evidence_refs": [
      "commit:...",
      "test:...",
      "scenario:...",
      "cli:...",
      "viz:...",
      "replay:..."
    ],
    "deferred_claims": []
  }
}
```

`evidence_refs` are references, not proof by themselves. The evidence bundle
must still be inspected, and proxy evidence must remain marked as proxy.
The dependency-light parser in
`python/tasking_contracts/common/scripted_capability.py` validates this shape; it does
not grant runtime admission and is not yet wired into the scenario loader.

## Open acceptance gates

1. Air: static single-world completion and one full randomized reset/replay
   gate are satisfied; add accepted seed coverage and visualization
   process/render evidence.
2. Air tactical/EW: admit sensor/track-based engagement and EW roles only with
   declared information provenance, ROE/resource constraints, and negative
   tests for privileged geometry or hidden truth.
3. Air multi-unit: the bounded four-slot EW route, per-member target/task
   ownership, and two-aircraft shared-world weapon route are now evidenced;
   close formation mission parity and visualization, then extend the same
   roster contract to joint tasking and a terminal large-scale demonstration.
4. Naval: keep the N4 station adapter scoped; the direct runtime report gate is
   satisfied, while combat, fleet, reset/replay, and full playable coverage
   remain open.
5. Joint: keep the label `bounded_adapter` until a maintained Air plus Naval
   or Ground scenario closes task/order/report delivery, communication and
   replay gates through domain-owned execution consumers.
6. Ground: leave the label `held` until every deferred runtime owner is
   admitted with evidence.
7. All domains: attach the manifest object to maintained scenarios and reports
   only after the corresponding gate passes.
