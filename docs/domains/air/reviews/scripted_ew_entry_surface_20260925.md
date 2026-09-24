# Scripted Air EW Entry Surface Review — 2026-09-25

- Document kind: review
- Lifecycle: maintained
- Owner: air/scripted-agent
- Scope: entry surface for an RL-independent scripted electronic-warfare role
- Verdict: `entry_surface_incomplete`

## Verified current surfaces

| Surface | Current evidence | Consequence |
| --- | --- | --- |
| EW data | `examples/config/database/aircraft/modules/ew_suites/gen4_standard.json` declares an RWR, a 1000 W noise-barrage jammer, chaff/flare counts, a release interval, and auto mode. | Database data is sufficient to describe a candidate EW suite, but does not create an agent action path. |
| Native components | `src/components/systems/ew.h` defines `Jammer`, `Countermeasures`, `RWR`, `EmitterDetection`, and `ESMReceiver`. | The component vocabulary can carry EW state, ESM detections, and resource/cooldown data. |
| Native EW systems | `src/systems/systems/ew_system.h` runs chaff release, flare release, and lifetime management. | Countermeasure effects have a system owner; jammer activation and ESM decision effects do not have a comparable command system in this header. |
| Observation | `gym_envs/universal_env_parts/observations.py` exports `rwr` rows as bearing, signal strength, lock, and launch-warning fields; instruments also expose `rwr_active`. | A scripted agent can consume declared RWR evidence without World Truth. ESM/jammer state is not part of the maintained observation payload shown here. |
| Command transport | `PilotAction` exposes `program_chaff` and `program_flare`; `legacy_command_bridge.h` resolves those fields into countermeasure commands. | The low-level transport exists, but it is not exposed by the maintained `full` or `air_combat_hybrid_v1` action vectors. |
| Current action mapping | `gym_envs/universal_env_parts/actions.py` sets `program_chaff` and `program_flare` to `False` for the maintained action modes. | A scripted EW model cannot currently perform countermeasure actions through the normal Air action path. There is no maintained jammer action field. |
| Scripted producer | `python/tasking_contracts/air_scripted_ew.py` is registered in the aggregate Air registry as `air.ew.rwr_response_scripted` (`adapter`, `air_ew_controller`). It emits a typed RWR-derived intent and marks `native_action_owner_required`. | The producer is a contract/decision slice only. It is not an accepted countermeasure or jammer action, and it does not change the EW capability label. |

## Boundary

The current evidence supports an EW **observation** role, a database-backed
EW **state** vocabulary, and a typed RWR-derived scripted producer. It does
not support a playable EW decision claim. The producer output is not consumed
by the maintained Air action path, so it remains adapter/probe evidence rather
than native EW runtime evidence.

## Direct observation probe

The Stage 3 limited-weapons Air scenario was run with the maintained
RL-independent phase execution model, the compiled runtime, `mission_obs_mode=basic`,
seed `0`, and a `2400`-step trace budget. A non-zero RWR row first appeared at
step `441` and remained observable through step `2121`; the run itself remained
active with mission status `[1, 0, 0, 0]`. This is direct evidence that a
scripted unit can receive the existing RWR observation product. It does not
show a launch-warning-driven countermeasure action, jammer state transition, or
terminal EW objective.

The probe and producer therefore close only the observation and decision
contract sides of the EW boundary. The action and native-owner slices below
remain required before an EW role can be admitted as a consumed adapter or a
playable unit.

The EW path must remain Air-owned for jammer modes, RWR/ESM interpretation,
countermeasure resources, release cadence, and threat-response doctrine. Only
the identity, authority, clock, provenance, communication, and lifecycle
envelope may be shared with other domains.

## Required closure slices

1. **Observation contract:** declare RWR and ESM fields, freshness, source,
   confidence, lock/launch semantics, and negative controls for hidden target
   truth.
2. **Countermeasure action contract:** expose chaff/flare request fields in a
   versioned Air-owned action extension or a new maintained action mode; map
   those fields to `PilotAction` without changing the existing full-action
   indices silently.
3. **Jammer command contract:** decide whether jammer activation is a direct
   Air intent or a command-layer product, then add a native owner for
   activation, bandwidth/angle/type, power/resource limits, and shutdown.
4. **Direct scenario gate:** build a lock/launch-warning scenario with finite
   inventory, release interval, communication state, and a report that proves
   the scripted action was accepted and changed native EW state.
5. **Replay and multi-aircraft gate:** repeat the EW scenario under reset/replay
   and route distinct EW roles through the existing cooperative roster before
   any `playable` label.

## Non-goals for this review

- No generic cross-domain `ElectronicWarfare` mega-schema.
- No direct writes to `Countermeasures`, `Jammer`, or RWR state from a Python
  scripted model.
- No capability promotion based on database presence, an observation row, or a
  model output that the runtime does not consume.
