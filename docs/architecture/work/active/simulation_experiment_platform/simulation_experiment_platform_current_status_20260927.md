# Simulation Experiment Platform Current Status

Status: `2026-11-16` P0/P1/P2 are complete. P3 supports the selected native
CPU checkpoint/session lifecycle, typed flight controls, explicit speed-change
scoring, and a fixed branch comparison with verified replay. P4-A now provides
an audited lineage-preserving trace projection with fixed training/evaluation
seed splits. P4-A now has an explicit RuntimeFacade Agent-packet bridge and
optional persisted EpisodeStore exports for selected native branches. P3-A/B
now includes the maintained C++ identity/child owner and an explicit Python
session owner-injection path, validated through nested branches and Agent packet
reads. Broader mission coverage and durable recovery remain incomplete.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/simulation_experiment_platform_current_status_20260927.md`
Owner: `cross-domain architecture`
Last verified: `2026-11-16`

## 2026-11-16 Local Stack Verification

This recheck uses implementation and fresh artifacts rather than treating the
historical records below as current-main acceptance. `origin/main` is pinned at
`23a936694`. The GitHub API recheck on `2026-11-16` found PRs `#325`, `#326` and
`#327` open and draft, at heads `9b4102bce`, `98e334167` and `4502b7618`.
The following local fixes have not been pushed or merged:

| Local line | Tested change | Revision |
| --- | --- | --- |
| `exp/pr2-native-branch` | Carries episode identity, exact double clock/frame count, generation-aware census and scenario settings; fixes repeatable Flecs patch application | `87f4f653c`, `3ecb79938`, `eac68f669`, `487241cb3` |
| `exp/pr2-native-branch` | Enforces native sibling horizon, copies remaining checkpoint budget, isolates default journal owners, and rejects content not carried into a fresh child | `f7335bc74` |
| `fix-experiment-runtime-session` | Stacks the existing Python runtime adapter on that native line; rejects exhausted session horizons before backend dispatch | `a5f1558f6` |
| `exp/pr2-native-branch` | Exposes a read-only optional episode seed from the exact serialized native world used for the state digest | `1fe9367e2` |
| `fix-experiment-runtime-session` | Requires the declared session seed to match native owner facts; compares the complete declared AgentObservation projection during replay | `5c3d87a27` |

Fresh Windows/MSVC Release verification used Python 3.12 and both newly built
extensions, `ef_py` and `ef_runtime_candidate_py`. Old binaries omitted the new
branch cases and bindings and are not counted as current validation.

| Executed check | Result | Evidence boundary |
| --- | --- | --- |
| Focused native CTest: host candidate, kernel candidate, candidate parity, authority, recorder and boundary checks | 8/8 passed | Includes Route B budget rejection, checkpoint independence, loaded-raster rejection and caller-owned explicit journal preservation |
| Facade/native journal Python tests plus state-transfer contract and Flecs patch tests | 23 passed | Includes two processes with the same temporary root and host identity; the surviving process keeps its WAL and continues after the other owner exits |
| Structural boundaries, state-transfer candidate contract and Flecs patch tests | 38 passed | Source ownership, include boundaries, generation-aware state-transfer metadata and patch repeatability |
| Native facade identity and branch Python tests | 8 passed | Includes seed zero, maximum uint32 seed, read-only seed facts and nested checkpoint/fork preservation |
| Full `tests/experiment` on the repaired session line and fresh native extensions | 581 passed | Includes 120 complete-projection cases, wrong-seed rejection without resetting setup, actual aircraft/facade replay and observation-only drift rejection; no skipped native-binding cases in this run |
| Document tier census | 9 passed | Refreshes the pre-existing 991-document record to the measured 1007 tracked documents on this stack; no document tier or translation policy was changed |

The focused native command was:

```powershell
ctest --test-dir <build> --output-on-failure `
  -R 'runtime_(kernel_candidate|host_candidate|authority_contract|run_recorder|contracts_boundary)'
```

The Python commands used `CMO_BUILD_DIR` and `PYTHONPATH` pointing to that fresh
build, then ran the focused files and `python -m pytest -q tests/experiment`.
Ruff and CRLF-aware `git diff --check` passed on the edited source/test files.

The new bounded behavior is explicit: a sibling may perform only its admitted
number of successful steps. Checkpointing preserves its remaining budget;
retaining a zero-budget checkpoint is valid, and a new fork requires a new
positive horizon. Session validation rejects over-budget dispatch before a
backend call. Historical tests that continued for two or four steps now request
those budgets rather than relying on the old unenforced limit.

Loaded unit catalogs, Arnis terrain rasters and field overlays remain outside
the current child-content codec. Their transfer is rejected instead of
silently substituting a built-in catalog or default terrain. The default WAL
uses an atomically reserved per-owner directory; an explicit `journal_path`
remains caller-owned and is preserved for reopening.

The initial 445-test pass did not establish observation replay equality or bind
the session seed to its native owner. Round 2 closes the bounded checks below;
production mission reward semantics, portable recovery, GPU parity and learner
improvement remain outside this evidence. The generic kernel candidate's zero
reward is still a diagnostic placeholder.

### Round 2: Seed And Observation Identity

The native seed is read from `identity.episode_seed` in the same serialized world
payload used by `state_digest`, not from a construction config. Facade and kernel
facts expose the original uint64 value as a read-only optional field. Missing,
boolean, out-of-range or mismatched seed facts are rejected by the session;
valid seed zero is admitted. The shared SessionSpec integer domain remains
unchanged. No validation path resets an already set-up world.

The packet-capable replay path freezes an immutable digest when each observation
is captured. Replay compares the checkpoint observation and every subsequent
endpoint, using positions relative to the source branch's origin. The declared
projection covers every bound AgentObservation field and all ordered TrackData,
RWR and ESM fields. Finite doubles retain exact hexadecimal values; uint64 ids
retain exact typed decimal values. Own-entity ids are normalized to the session
Agent only after the requested ref, packet ref and observed id agree. Sensor ids
remain significant, so owner-local sensor-id changes conservatively fail replay.

Packet ids, transport version and source-version tokens remain owner-local:
each packet must carry internally consistent native tokens. Their full strings
are not a cross-owner state identity. The maintained facade currently derives
its packet version from ref count (a single-Agent packet stays at version one),
whereas native children use step plus one. That existing discrepancy is not
rewritten here. Semantic provenance, source time and complete declared observed
values are compared, alongside the existing native state/event/RNG/step trace.
InstrumentState is not part of this declared AgentObservation projection.
Backends without a packet reader retain state-only replay and advertise
`can_verify_observation_replay=False`.

The seed DTO change exposed stale MSVC objects with zero Ninja dependencies in
an incremental build. A clean 180-step rebuild removed the mixed ABI. Caller,
candidate-test and Python-binding objects subsequently reported 315, 335 and
426 valid dependencies respectively; the 8 native CTest gates then passed on
the consistent artifacts. Earlier ABI-crashing runs are not counted as passes.

### Independent Input-Lock Artifact Handoff

The `input-lock-artifact-binding` line at `5a7b0da1f`, based on `5c3d87a27`,
exports two explicit file roles: the complete resolved-experiment projection for
the existing Python loader, and canonical input-lock payload bytes for native
raw-file hashing. The pair is validated before use; the payload's raw SHA-256
must equal the existing input-lock digest. This creates no additional receipt,
manifest, runtime DTO or ledger and does not claim a two-file transaction.

The focused exporter, existing resolved-input-lock and native receipt
qualification combination passed 53 tests using the fresh native executable.
It checks the real collector, durable reopen, stored payload bytes and existing
Python assertion, including a negative control that mistakenly supplies the
full projection to the native payload slot. Production Air current-attempt
recorder integration remains a separate gate; a dark receipt does not establish
that input-lock semantics were executed.

### Independent Environment Handoff

The `environment-query-contract` line at `e2c94a8ce`, based directly on
`origin/main` at `23a936694`, adds the candidate raw raster point observation.
It pairs height and surface from one cell, reports availability and original
frame/datum/source metadata, and preserves legacy scalar consumers. It neither
accepts the complete Environment P2 contract nor carries loaded raster content
through the native branch codec.

Its focused target passed 9 cases / 6950 assertions and its CTest entry passed;
the full native suite passed 371 cases with 1 skipped, and the selected Ground
native subset passed 6 cases / 55 assertions. The Python combination had
88 passed, 2 failed and 4 subtests. The failures remain open: the blocked Ground
position test still expects z zero after the existing movement code projects it
to source height, and the Gym position Box still permits z only in [-1, 1].
The affected movement, adapter, probe and test blobs are identical to main.
These failures are not counted as green or repaired by the new query.

The Environment line also retains a pre-existing census failure: main has 1001
tracked documents but records 873, and the candidate adds only one tier-B page.
That branch's broad baseline was not refreshed as part of the point-query API.
This is distinct from the census reconciliation already owned by the #327
evidence stack above. The next Ground slice must resolve the height assertion
and Gym observation-space contract before a consumer migration is accepted.

## Baseline Revision

- Preparation branch: `codex/counterfactual-experiment-prep`
- Initial baseline: `origin/main` at `9ee4558e` (2026-09-27)
- Current baseline checked for the preflight: `origin/main` at `81bf21f093` on 2026-10-14
- Existing preparation package: `docs/learning/work/issues/adaptive_counterfactual_search/`
- P3 preflight: [`p3_runtime_owner_decision_preflight_20261014.md`](p3_runtime_owner_decision_preflight_20261014.md)
- P3-B native branch design: [`p3b_native_branch_consumer_design_20261014.md`](p3b_native_branch_consumer_design_20261014.md)
- Native session checkpoint/replay: [`native_session_checkpoint_replay_20261015.md`](native_session_checkpoint_replay_20261015.md)
- Native flight-control comparison: [`native_pilot_action_comparison_20261015.md`](native_pilot_action_comparison_20261015.md)

## What Changed Since The Initial Baseline

- `origin/main` landed the long-horizon architecture governance program. It
  owns `ExperimentRequest`, `ResolvedCompositionPlan`, `RunReceipt`, the native
  `StateCheckpoint`, and the `echelon_forge.canonical_json.v2` envelope. This
  package now routes durable authority there instead of defining its own.
- P0-A closure: owner/index links, document metadata, the bilingual registry
  entries for the two edited owner README pairs, and the document tier census
  were reconciled. The README and this file no longer carry two different
  residual lists.

## Evidence Census

| Surface | Finding | Evidence boundary |
| --- | --- | --- |
| Runtime facade | Maintained batch setup, stepping, observations, tasking, events, window execution, native identity facts, and an opaque CPU child branch exist. | The branch is in-process; Python publication requires an explicit caller-owned action/ref translator and does not provide portable recovery. |
| Python runtime | `WorldBatchVecEnv` owns maintained batch adapter behavior and SB3-compatible lifecycle. | It must not become the long-term branch graph owner. |
| Provenance | Agent-shim vocabulary distinguishes maintained observation, decision belief, raw truth, and diagnostics. | Branch traces must retain these labels. |
| Replay | CUDA resident replay contracts define selected-field comparison and snapshot-version reporting. | They are candidate backend replay evidence, not a generic counterfactual contract. |
| Episode storage | `EpisodeStore` stores arrays and optional expert actions. | It lacks immutable branch lineage, runtime profile, and manifest identity. |
| Native checkpoint | Route B branch execution and opaque checkpoint cloning reuse the native transfer authority; the local generation-6 census has thirteen categories, including scenario settings. Older censuses explicitly record categories they do not carry. | In-process, dark/shadow, one CPU world; loaded content is rejected, with no portable checkpoint format or production publication. |
| Toy canary | Candidate selection, deterministic toy branches, horizon effects, and interaction residual are tested. | Results are synthetic/toy only. |
| Candidate discovery | `python/experiment/candidate_discovery.py` branches a synthetic causal world through the reference session and compares uniform, reward, TD, and oracle selectors on held-out seeds. | Synthetic only; results live in the counterfactual search issue. |
| Experiment contracts | The reference session and native CPU candidate adapter produce the shared session, snapshot, branch, transition, and manifest contracts. | Python retains identity projections and opaque handles; authoritative payloads stay native. |

## Maturity Matrix

| Capability | State | Next gate |
| --- | --- | --- |
| Stable experiment ownership | accepted | P0-A closed |
| Versioned session/branch contracts | pass (P1-A) | P2-A reference session consumes them |
| Canonical trace/manifest | pass (P1-B) | P2-A reference session emits them |
| Reference timeline backend | pass (P2-A) | P2-B toy evidence labels; P3 owner decision |
| CPU runtime candidate adapter | Selected flight controls, explicit scoring, saved checkpoint restore, replay, maintained facade identity, native child owner, and injected Python branch-owner tests pass | Mission-specific owners, broader mission coverage, and durable recovery |
| Native full-state snapshot | Selected CPU checkpoint continuation, historical/nested forks, and trace replay pass | Broader owner coverage and durable recovery remain unproven |
| Training projections | partial (P4-A) | `trace_projection.py`, `numeric_observation_adapter.py`, and `runtime_facade_observation.py` provide lineage-safe projections, a RuntimeFacade Agent-packet bridge, and optional persisted `EpisodeStore` exports; the fixed native pilot remains open-loop |
| GPU/distributed execution | deferred | P5 selected-slice parity |

## Explicit Non-Claims

This package currently does not establish:

- causal validity of counterfactual results;
- generic or persisted runtime snapshot/restore support; the session restores
  explicitly saved in-process CPU checkpoints into fresh continuation branches;
- generic action-dependent combat comparisons; the demonstrated comparison is
  one fixed open-loop flight-control diagnostic with a declared speed evaluator;
- policy improvement or knowledge transfer;
- combat effectiveness, lethality, or real-world validity;
- GPU or distributed branch throughput;
- superiority of reward-triggered or TD-triggered candidate selection.

## Immediate Sequence

1. Review and integrate the verified native, session and evidence follow-ups in
   `#325` → `#326` → `#327` order, retaining the selected-slice limits above.
2. Integrate explicit action/ref owners for additional mission surfaces while
   keeping native state ownership in the maintained C++ facade.
3. Broaden scenario and state-owner coverage beyond the fixed flight-control
   diagnostic, retaining explicit action and evaluator definitions.
4. Broaden maintained runtime numeric observation sources and direct
   learner-dataset exports beyond the fixed pilot across admitted mission
   surfaces; keep the native candidate evidence label.
5. Extend durable recovery through the existing native checkpoint authority,
   then qualify alternate backends under the shared semantics.

The checkpoint/session integration is implemented: save a native clone, advance
the source, restore or fork from saved history, fork descendants through their
own handle, and verify a recorded continuation before adding it to the manifest.
Three real aircraft seeds exercise this lifecycle. Source traces and siblings
stay unchanged, and failed replay attempts do not enter the manifest.

Done since the initial baseline: the toy uniform selector now probes evenly
spaced points and the doubling-horizon stopping hazard is pinned (P2-B baseline
correction); P1-A/P1-B contracts landed; the P2-A reference session passes
determinism, restore, and sibling-isolation tests, and mutation probes confirmed
those tests fail when isolation, intervention, fork admission, seed binding, or
determinism is broken. P2-B passed: the Phase 1 candidate-discovery benchmark
runs every oracle branch through a pluggable reference world, labels its output
`synthetic`, and binds each seed to a trace-manifest digest.

## Residual Register

This is the single residual register for the package.

| ID | Owner | Reason | Exit condition |
| --- | --- | --- | --- |
| `R1` | `architecture/runtime-facade` with the long-horizon governance checkpoint owner | Native CPU checkpoint, typed flight actions, explicit scoring, and fixed comparison pass; broader mission/owner coverage and durable recovery remain incomplete. | Broader declared mission coverage and durable recovery pass continuation/isolation/provenance tests beyond the fixed flight diagnostic. |
| `R2` | `architecture/runtime-workflow` | The Python world-batch adapter still owns substantial step-time orchestration. | A session adapter consumes maintained facade request/result contracts only. |
| `R3` | `learning/training` | The fixed native pilot captures maintained Agent packets at native export barriers; a RuntimeFacade packet bridge and optional persisted PPO `EpisodeStore` export now exist, but production publication across admitted mission surfaces and BC/world-model coverage remain unproven. | The maintained RuntimeFacade-backed packet provider feeds admitted mission surfaces and persists learner-compatible PPO/BC/world-model exports while preserving the projection digest and split boundary. |
| `R4` | `architecture/runtime-backend` | GPU-resident replay contracts are backend-specific and quarantined. | P5 selected-slice parity contract is shared by each admitted backend. |
| `R5` | `learning/training` | The adaptive toy canary has synthetic evidence only. | An adaptive-selection experiment runs on maintained mission observations with a fixed protocol; the candidate flight diagnostic alone does not close this residual. |

## Status Rule

The package stays `active` while P0/P1 contracts are being implemented. It may
not be marked `accepted` from toy tests alone. Runtime and training claims need
their own evidence records and acceptance gates.
