# Native Pilot Action Comparison

Status: `2026-10-17` selected CPU flight-control comparison, lineage-preserving
trace projection, and an optional persisted PPO `EpisodeStore` export from
captured Agent packets are verified. The fixed pilot remains open-loop;
production RuntimeFacade publication, broader mission coverage, and durable
recovery remain incomplete.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/native_pilot_action_comparison_20261015.md`
Owner: `cross-domain architecture`
Last verified: `2026-10-17`

## Result

The candidate now dispatches maintained `PilotAction` commands through the
existing native episode coordinator. A fixed open-loop comparison starts both
alternatives from the same opaque checkpoint, measures actual aircraft speed,
and verifies complete replay of both scored continuations. The source and
saved checkpoint remain unchanged.

The committed [summary report](evidence/native_pilot_comparison_20261015.json)
retains the fixed protocol, per-seed metadata, branch identities and the
digest of each `TraceManifest`. The full report, regenerated with the same
command without `--summary`, adds every action and integer reward. Neither
contains native checkpoint bytes or permits an offline restore by itself.

## Admission And Entity Identity

`WorldPilotActionAssignment` and `PilotAction` are reused from their maintained
owners. The source-only `ef_runtime_candidate_py` extension resolves the existing
binding types; production `ef_py` and facade-only packaging retain their
dependency boundary.

An optional action byte payload accompanies the existing episode intent. The
coordinator validates its SHA-256 and 64 KiB budget before idempotency lookup.
Its intent fingerprint also binds payload presence/size, so stripping bytes
cannot turn a typed command into a digest-only replay. Legacy digest-only
intent bytes remain unchanged. Reset cannot carry action bytes.

The candidate uses the existing canonical JSON authority to encode every
`PilotAction` field in a closed action transport. Unknown/missing fields,
coercions, nonfinite or out-of-range controls, duplicate entities, and foreign
world indices are rejected. The native callback validates every entity before
applying any control, then steps exactly once. If mutation has started and
native execution fails, an incomplete applied receipt fail-stops the
coordinator instead of reporting a clean rejection. Configured root run
recorders retain the actual action bytes beside their digest.

State transfer preserves logical entity names rather than source-local ECS
numbers. The candidate now honors `WorldSpawnRequest.entity_name`, rejects a
duplicate name before mutation, and resolves that name in each imported world.
The regression fixture demonstrates different source/target internal IDs and
checks speed equality at restore, actual control on the imported aircraft, and
source isolation. No source-local ID is silently treated as a child identity.

## Declared Actions, Scoring, And Provenance

`RuntimePilotActionBackend` binds its logical entity mapping, immutable action
catalog, evaluator identity, and scenario/protocol context in the session
configuration digest. Controls use exact integer thousandths in this metadata;
the binding receives the maintained numeric DTO. The session rejects a
different backend config digest or agent roster before execution. An unknown
action symbol cannot silently degrade to a no-op.

The evaluator `speed_change_mmps_v1` assigns each step:

```text
reward = round(speed_after_mps * 1000) - round(speed_before_mps * 1000)
```

This is a speed-change diagnostic. Evaluator values are read only for scoring
the native control probe and are not exposed to the fixed policy or used as
Agent learner observations.
Actions are scheduled open-loop: the trace explicitly records
`fixed_protocol_no_policy_observation`. The maintained packet allowlist remains
owned by tasking contracts; raw truth, diagnostic projections, and oracle
labels remain inadmissible policy inputs. The controlled backend rejects a
maintained packet label because this protocol did not read such a packet.

## Fixed Comparison

The scenario is one aircraft, altitude 3000 m, initial speed 150 m/s, and a
50 ms time step. One idle warm-up action establishes the currently supported
nonzero checkpoint boundary. Both alternatives then run 20 steps (1 second):
idle throttle and full throttle, with neutral pitch, roll, and rudder. Other
controls retain maintained DTO defaults with `active=true`.

| Seeds | Checkpoint speed (m/s) | Idle final speed (m/s) | Full final speed (m/s) | Full minus idle (m/s) |
| --- | --- | --- | --- | --- |
| 19, 83, 191 | 149.953 | 148.855 | 149.820 | 0.965 |

Both alternatives decelerate during this short initial flight interval. Their
reward sums are respectively -1098 and -133 mm/s; full throttle loses less
speed. Rounded endpoints reconstruct the telescoping integer rewards. This
fixture has no random disturbance, so identical results across three seeds
are expected and provide no statistical robustness claim.

For every seed and alternative, `session.replay` re-executes all 20 transitions
and compares actions, rewards, state identity, RNG identity, coordinator
sequence, termination, and provenance. Every replay passes. Two independent
CLI invocations produced byte-identical reports (SHA-256
`17615fbe740af01cd1f57ee2225cc1f3e02246ee90aae5024f4b6c9c95f15d36`).

## Trace Projection

The report regenerates the canonical manifests through
`python/experiment/trace_projection.py` for the four declared consumers:
`ppo`, `bc`, `world_model`, and `evaluation`. Seeds 19 and 83 are the fixed
training split; seed 191 is the fixed evaluation split. Every manifest's root,
child branches, and replay descendants remain in the same split. The summary
contains 243 projected rows: 162 training and 81 evaluation. Each consumer has
its own projection digest, while all rows retain the source manifest digest,
branch parent, state identities, actions, integer rewards, termination, and
observation provenance.

This is a compatibility projection of canonical traces. It has no fabricated
observation vectors. At each native export barrier the fixed pilot captures a
facade-shaped Agent packet from the shadow candidate owner; the report records
only the resulting PPO export metadata unless `--numeric-export-root` is
provided. With that option, selected idle/full branch arrays are written to
`EpisodeStore` directories and the report records the sidecar metadata digest.
The maintained
`python/experiment/numeric_observation_adapter.py` boundary accepts packets
from one declared Agent observation interface, records Agent and packet
identity/provenance, and writes `EpisodeStore` files with a sidecar that
preserves the projection digest and split/branch lineage. Replay and baseline
branches must be selected explicitly, so diagnostic branches cannot silently
become learner data. The adapter now exposes a RuntimeFacade Agent packet bridge
and an explicit branch-to-packet collector. They call
`read_observation_packet()` and reject raw fallback, missing maintenance status,
ambiguous refs, and missing packet identity. Selected idle and full branches
produce 21 packets and 20 transitions each for the PPO export;
baseline and replay branches are excluded. This remains `runtime_candidate`
evidence rather than production RuntimeFacade publication. The
`RuntimeFacadeAgentObservationProvider` adapts the maintained packet reader
with explicit Agent references and rejects missing or ambiguous surfaces.

```bash
PYTHONPATH=/tmp/cmo-routeb-build:. python -m python.experiment.native_pilot_comparison \
  --output /tmp/native_pilot_comparison.json
CMO_BUILD_DIR=/tmp/cmo-routeb-build PYTHONPATH=/tmp/cmo-routeb-build:. \
  python -m python.experiment.native_pilot_comparison \
  --output /tmp/native_pilot_comparison_persisted.json \
  --numeric-export-root /tmp/native_pilot_exports
CMO_BUILD_DIR=/tmp/cmo-routeb-build python -m pytest tests/experiment -q
ctest --test-dir /tmp/cmo-routeb-build --output-on-failure
```

`--report-envelope` optionally wraps the output in the existing experiment
report metadata envelope. Native extensions must be built first; missing
bindings fail the CLI instead of producing synthetic fallback results.

## Validation And Remaining Work

The experiment suite passes 373 tests and full CTest passes all 25 targets.
Native checks cover payload tampering,
oversize rejection, idempotency replay/conflict, closed DTO transport,
whole-batch preflight rejection, restored entity resolution, source isolation,
and actual scored continuations. Ruff, internal-code governance, and diff
checks pass. Repository governance has 210 passes, five pre-existing failures,
and one expected failure, matching the preceding checkpoint. Exact commands
and the retained failure categories appear in the
[integration verification](current_main_integration_20261014.md).

This remains in-process, single-world, CPU, dark/shadow candidate evidence.
The event cursor is the coordinator action sequence. The digest-only lifecycle
backend intentionally retains zero placeholder rewards. The selected flight
diagnostic establishes neither combat/task reward quality nor policy improvement,
causal or real-world validity, complete future state-owner coverage, persisted
recovery, or GPU/distributed execution.

Next work broadens the maintained observation/action coverage beyond the fixed
pilot diagnostic and wires the RuntimeFacade packet bridge into admitted
mission surfaces, while retaining branch ancestry, fixed splits, native
identity, and honest evidence labels. BC/world-model export coverage and
persisted recovery must continue through their existing owners.
