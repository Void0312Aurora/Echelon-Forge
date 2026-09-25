# Scripted Air EW Entry Surface Review — 2026-09-25

- Document kind: review
- Lifecycle: maintained
- Owner: air/scripted-agent
- Scope: entry surface for an RL-independent scripted electronic-warfare role
- Verdict: `entry_surface_incomplete`

## Verified current surfaces

| Surface | Current evidence | Consequence |
| --- | --- | --- |
| EW data | `examples/config/database/aircraft/modules/ew_suites/gen4_standard.json` declares an RWR, a 1000 W noise-barrage jammer, chaff/flare counts, a release interval, and auto mode. The loader now preserves `ew_suite_ref` through the deferred materialize boundary. | Database data can now reach native EW component initialization for spawned units, but it still does not admit a maintained scripted EW action path. |
| Native components | `src/components/systems/ew.h` defines `Jammer`, `Countermeasures`, `RWR`, `EmitterDetection`, and `ESMReceiver`. | The component vocabulary can carry EW state, ESM detections, and resource/cooldown data. |
| Native EW systems | `src/systems/systems/ew_system.h` runs chaff release, flare release, and lifetime management. | Countermeasure effects have a system owner; jammer activation and ESM decision effects do not have a comparable command system in this header. |
| Observation | `gym_envs/universal_env_parts/observations.py` exports `rwr` rows as bearing, signal strength, lock, and launch-warning fields; instruments also expose `rwr_active`. Native MAWS now records active inbound missiles by launch platform and exposes source-specific `is_launch` rows through `SimulationKernel::get_agent_observation`. The maintained `InstrumentState` read surface now projects chaff/flare counts, release interval, last release time, and auto mode, with `-1` for an absent component. | A scripted agent can consume declared RWR/MAWS evidence without World Truth, and a maintained report can read native countermeasure state. ESM/jammer state is not part of the maintained observation payload shown here. |
| Command transport | `PilotAction` exposes `program_chaff` and `program_flare`; `legacy_command_bridge.h` resolves those fields into countermeasure commands. | The low-level transport exists, but it is not exposed by the maintained `full` or `air_combat_hybrid_v1` action vectors. |
| Current action mapping | `gym_envs/universal_env_parts/actions.py` sets `program_chaff` and `program_flare` to `False` for the maintained action modes. | A scripted EW model cannot currently perform countermeasure actions through the normal Air action path. There is no maintained jammer action field. |
| Versioned action extension | `air_ew_hybrid_v1` adds two explicit tail fields for chaff and flare and maps them to `PilotAction`; it remains outside the canonical `python.env_config.ACTION_MODES` list until a scenario/config owner and acceptance gate are admitted. `tools/diagnostics/air_ew_scripted_demo.py` drives this mode with the registered scripted EW action model. | The transport shape is testable without changing existing full/hybrid indices. The maintained demo observed launch-warning rows at steps 42 and 82, requested both countermeasures at those steps, and reported native chaff consumption from 60 to 59 after the release interval. Flare remains unconsumed in that trace because both requests share the native release cadence. |
| Scripted producer | `python/tasking_contracts/air_scripted_ew.py` is registered in the aggregate Air registry as `air.ew.rwr_response_scripted` (`adapter`, `air_ew_controller`). It emits a typed RWR-derived intent and marks `native_action_owner_required`. | The producer is a contract/decision slice only. It is not an accepted countermeasure or jammer action, and it does not change the EW capability label. |

## Boundary

The current evidence supports an EW **observation** role, including a native
MAWS launch-warning fact, a database-backed EW **state** vocabulary, a typed
RWR-derived scripted producer, a maintained compiled countermeasure action
trace, and native countermeasure state reporting. It does not support a
playable EW decision claim. The 14-element action extension remains outside
the canonical action-mode admission, and jammer command/state/report
ownership remains incomplete.

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
   without changing existing full/hybrid indices. The compiled head-on demo
   and Air fixture now show launch-warning-driven requests and native chaff
   consumption through the maintained WorldBatch path. A scenario/config
   owner, flare/cadence report, and canonical action-mode admission remain
   open.
3. **Jammer command contract:** decide whether jammer activation is a direct
   Air intent or a command-layer product, then add a native owner for
   activation, bandwidth/angle/type, power/resource limits, and shutdown.
4. **Direct scenario gate:** build a lock/launch-warning scenario with finite
   inventory, release interval, communication state, and a report that proves
   the scripted action was accepted and changed native EW state. Native
   launch-warning observation, low-level inventory decrement, and maintained
   chaff consumption are now verified independently; a complete cadence,
   flare, and terminal scripted-action report remains open.
5. **Replay and multi-aircraft gate:** repeat the EW scenario under reset/replay
   and route distinct EW roles through the existing cooperative roster before
   any `playable` label.

## Non-goals for this review

- No generic cross-domain `ElectronicWarfare` mega-schema.
- No direct writes to `Countermeasures`, `Jammer`, or RWR state from a Python
  scripted model.
- No capability promotion based on database presence, an observation row, or a
  model output that the runtime does not consume.
