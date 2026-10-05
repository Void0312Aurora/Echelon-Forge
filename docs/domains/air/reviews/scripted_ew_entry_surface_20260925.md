# Scripted Air EW Entry Surface Review — 2026-09-25

- Document kind: review
- Lifecycle: maintained
- Owner: air/scripted-agent
- Scope: entry surface for an RL-independent scripted electronic-warfare role
- Verdict: `entry_surface_incomplete`

## 2026-10-05 recheck

The entry surface remains incomplete, but the earlier jammer-owner statement
is no longer current. The opt-in `air_ew_hybrid_v2` vector now carries a
transmit bit and technique code, `PilotAction` and the legacy command bridge
resolve that request, and `EW_Jammer_Control` owns the native state transition
and instrument projection. The compiled head-on demo observed matching jammer
request and native transmit steps. ESM interpretation, effectiveness,
multi-aircraft coordination, terminal objectives, and canonical action-mode
admission remain open.

## Verified current surfaces

| Surface | Current evidence | Consequence |
| --- | --- | --- |
| EW data | `examples/config/database/aircraft/modules/ew_suites/gen4_standard.json` declares an RWR, a 1000 W noise-barrage jammer, chaff/flare counts, a release interval, and auto mode. The loader now preserves `ew_suite_ref` through the deferred materialize boundary. | Database data can now reach native EW component initialization for spawned units, but it still does not admit a maintained scripted EW action path. |
| Native components | `src/components/systems/ew.h` defines `Jammer`, `Countermeasures`, `RWR`, `EmitterDetection`, and `ESMReceiver`. | The component vocabulary can carry EW state, ESM detections, and resource/cooldown data. |
| Native EW systems | `src/systems/systems/ew_system.h` owns jammer command/state projection, chaff release, flare release, and lifetime management. | Countermeasure and jammer activation/state projection have native owners; jammer effectiveness and ESM decision effects remain open. |
| Observation | `gym_envs/universal_env_parts/observations.py` exports `rwr` rows as bearing, signal strength, lock, and launch-warning fields; instruments also expose `rwr_active`. Native MAWS now records active inbound missiles by launch platform and exposes source-specific `is_launch` rows through `SimulationKernel::get_agent_observation`. The maintained `InstrumentState` read surface now projects chaff/flare counts, release interval, last release time, and auto mode, with `-1` for an absent component. | A scripted agent can consume declared RWR/MAWS evidence without World Truth, and a maintained report can read native countermeasure state. ESM/jammer state is not part of the maintained observation payload shown here. |
| Command transport | `PilotAction` and `legacy_command_bridge.h` resolve chaff/flare requests plus the opt-in jammer transmit and technique fields. | The low-level transport is maintained for `air_ew_hybrid_v1` countermeasures and the opt-in `air_ew_hybrid_v2` jammer extension; neither is canonical action-mode admission. |
| Current action mapping | `air_ew_hybrid_v1` preserves the existing 14-element prefix and `air_ew_hybrid_v2` appends two jammer fields. | The scripted EW model can now drive native countermeasure and jammer requests through explicit versioned surfaces. ESM interpretation, effectiveness, and canonical action-mode admission remain open. |
| Versioned action extension | `air_ew_hybrid_v1` adds chaff/flare tail fields; `air_ew_hybrid_v2` adds jammer transmit and technique fields without changing existing indices. The standalone and composed scripted Air models drive both through registered action surfaces. | The compiled single-aircraft terminal surrogate and hostile cooperative 2v2 route now observe jammer request/transmit steps with native state readback; the extension remains outside the canonical `python.env_config.ACTION_MODES` list pending broader acceptance and multi-aircraft terminal evidence. |
| Scripted producer | `python/tasking_contracts/air/ew/model.py` is registered in the aggregate Air registry as `air.ew.rwr_response_scripted` (`adapter`, `air_ew_controller`). It emits typed RWR-derived countermeasure and jammer intents. | The producer now has maintained versioned native action seams, but it is not an accepted canonical action mode and does not change the EW capability label. |

## Boundary

The current evidence supports an EW **response** role with native
countermeasure and jammer command/state seams, including a native MAWS
launch-warning fact, a database-backed EW **state** vocabulary, typed
RWR-derived intents, a maintained compiled countermeasure action/replay trace,
and native jammer state reporting, plus a bounded single-aircraft terminal
surrogate. It does not support a playable EW decision claim. The versioned
action extensions remain outside canonical action-mode admission, while
calibrated ESM/effectiveness semantics and cooperative terminal ownership
remain incomplete.

## Direct observation probe

The Stage 3 limited-weapons Air scenario was run with the maintained
RL-independent phase execution model, the compiled runtime, `mission_obs_mode=basic`,
seed `0`, and a `2400`-step trace budget. A non-zero RWR row first appeared at
step `441` and remained observable through step `2121`; the run itself remained
active with mission status `[1, 0, 0, 0]`. This is direct evidence that a
scripted unit can receive the existing RWR observation product. It does not
show a launch-warning-driven countermeasure action, jammer state transition, or
terminal EW objective.

The native Air fixture separately fired a real missile from `Red_Fighter` to
`Blue_Fighter` and observed a source-specific `rwr_warnings` row with
`is_launch=true` and `source_id=Red_Fighter`. The `ef_py` target was rebuilt in
the Visual Studio developer environment; the Air fixture and EW contract tests
passed (`5 passed` each). This closes the native launch-warning observation
fact and its reset path. It does not prove that a scripted EW action was
accepted, that inventory changed through a maintained action mode, or that an
EW episode terminates.

The probe, producer, and maintained demo close the observation and decision
transport sides of the EW boundary. The action and native-owner slices below
remain required before an EW role can be admitted as a consumed adapter or a
playable unit.

The maintained demo command
`python tools/diagnostics/air_ew_scripted_demo.py --max_steps 120` used the
head-on fixture, compiled `WorldBatchVecEnv`, `air_ew_hybrid_v1`, and the
registered `air.ew.rwr_action_scripted` model. It observed launch-warning
steps `[42, 82]` and emitted countermeasure request steps `[42, 82]`. The
instrument report observed chaff `[60, 59]` at the two request steps and flare
`30` at both steps, matching the native release interval. The episode remained
running; this is maintained action/resource evidence, not terminal or
playable EW evidence.

With the explicit `flare_only` doctrine, the same maintained scenario produced
flare `[30, 29]` while chaff stayed `[60, 60]`. The doctrine split is an
action/resource trace only; it does not change the canonical action-mode or
playable verdict.

The same maintained demo was then run twice in one process with the same seed.
`tests/runtime/air_combat/test_air_ew_replay.py` passed and compared the full
warning/request/resource trace, termination fields, decision count, and
scripted runtime identity. This is a bounded single-agent replay check; it does
not cover cooperative roster replay or canonical action-mode admission.

The existing two-member cooperative cruise roster also accepts
`air_ew_hybrid_v1`. A focused runtime test routes chaff only to Lead and flare
only to Wing for 42 compiled steps; each slot's native inventory changes only
on its own requested resource and the `ElementLead`/`Wingman` identities remain
attached to the reports. This scenario has no hostile launcher or launch
warning, so it is transport/resource isolation evidence rather than
multi-aircraft EW response evidence.

The maintained hostile cooperative scenario
`scenarios/air_combat/cooperative_air_2v2_scripted_ew_response_v1.json` now
provides the next bounded slice. Its CLI uses two independent scripted EW
agents over the Lead/Wing roster and two world-owned Red scripted opponents.
At seed `20260516`, the compiled 204-step run produced warning/request steps
Lead `[162, 202]` and Wing `[202]`; native chaff samples were Lead `[60, 59]`
and Wing `[60]`. The owner loader held two opponent controllers while the
non-owner loader held none, and both opponent reports remained active.

The scenario intentionally has no terminal combat objective. Its evidence is
hostile two-aircraft observation/action/resource routing and owner isolation,
not complete formation combat, target destruction, jammer/ESM behavior, or
playable mission closure.

The cooperative CLI was then run twice with the same seed. The paired-run
regression reproduced the owner counts, opponent reports, warning/request
steps, native resource samples, and runtime identities exactly. This closes a
bounded hostile cooperative EW replay gate while leaving full formation mission
replay and terminal combat outside this review.

The maintained single-aircraft terminal surrogate
`air_combat_1v1_c2_roe_ew_terminal_v1.json` composes the same C2/ROE
engagement prefix with the versioned EW tail and a world-owned scripted Red
missile opponent. At seed `20260516`, the v2 run accepted and executed the
Blue release at step `2`, observed continuous launch-warning and
countermeasure requests from step `163` through terminal step `201`, observed
native jammer transmission through step `200`, and terminated with
`combat_win`. The v1/v2 and same-seed replay tests reproduce these records.
This is a single-aircraft generic-surrogate terminal adapter; it does not
close cooperative terminal EW, calibrated jammer/decoy effects, or canonical
action-mode admission.

The EW path must remain Air-owned for jammer modes, RWR/ESM interpretation,
countermeasure resources, release cadence, and threat-response doctrine. Only
the identity, authority, clock, provenance, communication, and lifecycle
envelope may be shared with other domains.

## Required closure slices

1. **Observation contract:** RWR/MAWS source-specific launch evidence and its
   reset path are now native and directly tested. ESM fields, freshness,
   confidence, lock semantics, and negative controls for hidden target truth
   remain to be maintained and documented.
2. **Countermeasure action contract:** the versioned `air_ew_hybrid_v1`
   extension exposes chaff/flare request fields and maps them to `PilotAction`
   without changing existing full/hybrid indices. The compiled head-on demo,
   single-aircraft terminal surrogate, and hostile cooperative scenario now
   show launch-warning-driven requests and native chaff consumption through
   maintained paths. Canonical action-mode admission remains open.
3. **Jammer command contract:** the v2 jammer fields now have a native Air
   command owner and instrument projection for active state, technique, and
   transmit start time. Bounded noise-jammer beam/band suppression is tested;
   calibrated burn-through, RF-band semantics, DRFM effects, and resource
   limits remain open.
4. **Direct scenario gate:** the single-aircraft terminal surrogate now
   combines finite inventory, release interval, hostile launch warning, C2/ROE
   release acceptance, jammer state readback, and terminal `combat_win` in one
   replayed trace. Cooperative terminal EW and calibrated effect ownership
   remain open.
5. **Replay and multi-aircraft gate:** single-aircraft v1/v2 reset/replay and
   hostile cooperative v2 request/native projection are now covered. Full
   cooperative terminal EW replay and any `playable` label remain open.
6. **Cooperative hostile-threat owner:** scripted opponents are now built and
   updated once by the shared-world routing loader; non-owner slot loaders do
   not duplicate those controllers. The maintained 2v2 scenario proves this
   owner split, source-driven response, and paired-run replay. Its terminal
   combat and broader formation contracts remain open.

## Non-goals for this review

- No generic cross-domain `ElectronicWarfare` mega-schema.
- No direct writes to `Countermeasures`, `Jammer`, or RWR state from a Python
  scripted model.
- No capability promotion based on database presence, an observation row, or a
  model output that the runtime does not consume.
