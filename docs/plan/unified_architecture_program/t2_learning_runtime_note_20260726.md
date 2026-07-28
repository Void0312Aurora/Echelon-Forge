# T2 Learning Runtime Conformance Note

Languages:
- English canonical: `t2_learning_runtime_note_20260726.md`
- Chinese companion: [t2_learning_runtime_note_20260726.zh.md](t2_learning_runtime_note_20260726.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/t2_learning_runtime_note_20260726.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-26`
Baseline commit: `0aa76a00`

Status: T2 closing deliverable (amendment candidate (e)). This is a read-only
conformance census. Zero code changes, zero behavior change.

## 0. Method And Scope

The baseline's Learning face landed at I29 as
[simulation system architecture design](../architecture/simulation_system_architecture_design.md)
section 17, which defines three contracts. Amendment candidate (e) is therefore
already accepted *into the baseline*; what the program README's T2 row still
owes is this document — a conformance verdict for the maintained Python learning
runtime against those three contracts.

Scope of the census: `python/rl/runtime/world_batch/**`,
`python/rl/policy_algo/**`, `python/training/**`, `python/rl/tasking/**`,
`python/rl/runtime/agent_shim.py`. Read-only; every verdict cites `file:line`.

Non-goals, per the program README: this document does not amend the baseline
(amendments go through the architecture workline's governance), does not
propose code fixes, and does not schedule work in other tracks. Gaps are
*routed*, not solved.

## 1. The Three Contracts

Quoted from baseline section 17 (`:837-850`):

1. **Env-as-View contract.** The RL environment "is a view adapter over the
   simulation facade, not an authoritative runtime owner. It consumes
   observation packets, injects actions through facade contracts, and mirrors
   episode state. It must not own authoritative simulation truth or episode
   phase."
2. **Rollout collection contract.** Rollout data "is collected at
   facade-declared barriers. The collection cadence is a policy clock domain.
   Rollout provenance must record observation snapshot versions and action
   effective times."
3. **Policy bridge contract.** A policy "is a replaceable decision model
   attached to an AgentRole," and the bridge "declares its information-state
   source, observation version requirements, and action interface."

## 2. Contract 1 — Env-as-View: CONFORMS WITH QUALIFICATION

The environment reads truth through the facade rather than owning it. Each
batch read goes through the adapter's observation packet, not a stored world:

- `python/rl/runtime/world_batch/vec_env.py:380-392` —
  `_read_truth_and_inst_batch` calls
  `self._runtime_adapter.read_observation_packet(...)` and derives
  `truth_list` / `inst_list` from the returned packet's fields. Truth is
  *re-read per batch*, not held.
- `python/rl/runtime/world_batch/adapter.py:312-316` — the adapter constructs
  `ef_py.RuntimeFacade(self._world_count)` and raises if the bindings are
  absent. This is the single maintained cross-boundary construction path
  (consistent with G1; see the T0 SCAL census's bypass inventory).

The per-world `handle.last_truth` / `handle.last_inst` fields
(`vec_env.py:508-509`, read at `:459`) are a **cache of the last packet**, not
an authority: they are assigned from packet contents and are re-populated on
each read. `_command_chain_entity_active` (`:457-465`) treats a missing
`last_truth` as a permissive default rather than as authoritative state, which
is the behavior of a mirror, not an owner.

The episode-phase clause ("must not own authoritative simulation truth or
episode phase", baseline `:840-841`) needs a more careful adjudication than
the truth clauses. On the default path, Python owns episode stepping state:
both execution episode controller flags default off (`vec_env.py:147-148`),
the step counter advances Python-side (`handle.steps += 1`, `vec_env.py:675`),
and `terminated` / `truncated` are computed by Python-side loader evaluation,
not read from any facade episode surface (default branch calling
`_compute_loader_step_outcome`, `vec_env.py:728-739`; `done` at `:821`).
Episode state flows through the facade's episode surface only on the opt-in
controller path (`vec_env.py:723-727`), and even there the authority direction
is Python-to-facade: `_sync_execution_episode_controller_runtime_state` primes
the facade surface *from* the loader via
`handle.loader.build_execution_episode_state()`
(`python/rl/runtime/world_batch/_execution_episode_mixin.py:181-191`, through
`python/rl/runtime/world_batch/adapter.py:886-887`).

Adjudication: at this baseline the loader evaluation surface is the *interim
owner* of episode phase, and the opt-in execution episode controller is the
convergence path toward the facade-owned episode surface the contract
describes. The interim ownership is declared and flag-gated rather than a
hidden authority (cf. `EpisodeLifecycleContract`, baseline `:432`, which
forbids advancing a *private* authoritative state machine); the mainline flip
is a learning-runtime follow-on outside T2 scope.

Verdict: **conforms, with qualification**. The truth-ownership clauses are met
outright, per the citations above. The episode-phase clause is met only in the
qualified sense just given: on the default path Python owns episode stepping
state, "mirrors episode state" currently describes the opt-in controller
path — which itself mirrors loader state into the facade, not the reverse —
and the clause becomes fully verifiable only once the episode-controller
mainline flip lands.

## 3. Contract 2 — Rollout Collection: DOES NOT CONFORM

Two of this contract's three clauses are unmet, and the failure is
structural rather than incidental.

**Barriers are surfaced but not declared at the collection point.**
`barrier_trace` exists on the adapter's window result
(`python/rl/runtime/world_batch/adapter.py:58`, populated at `:469`), so the
facade does expose barrier information. But no rollout-collection code consumes
it.

**Rollout provenance records neither snapshot versions nor action effective
times.** A search of `python/rl/policy_algo/**` and `python/training/**` for
`snapshot_version` and `effective_time` returns **zero hits**. The rollout
buffer (`python/rl/policy_algo/device_dict_rollout_buffer.py:19`) extends SB3's
`DictRolloutBuffer` and its documented purpose is device-placement efficiency
(`:20-25`) — it carries no provenance fields at all.

This is the contract's own explicit requirement ("Rollout provenance **must**
record observation snapshot versions and action effective times"), so this is a
non-conformance rather than a partial.

Note the direct dependency on T10: the evidence spine census records that
`packet.snapshot_version` still derives from `next_snapshot_version(index)`
(`index + 1`, resetting per export), so even if rollout collection recorded a
snapshot version today, the recorded value would not be run-globally
monotone. The VA-2 producer itself already exists at this baseline —
`RuntimeFacade::allocate_run_snapshot_version` landed at I54
(`src/runtime/facade/runtime_facade.h:172`) and is consumed opt-in by the
adapter behind `use_facade_evidence_producers`
(`python/rl/runtime/world_batch/adapter.py:400-402`) — so what remains gated
on T10 is wiring that producer into the default export path, not creating the
producer and not merely adding a field.

Verdict: **does not conform**. Gaps G2-1 and G2-2 below.

## 4. Contract 3 — Policy Bridge: PARTIALLY CONFORMS

The bridge declares more than any other surface in the learning runtime, and
its vocabulary is already the right shape:

- **Information-state source: declared.** `agent_shim.py:141-148` emits
  `information_state_layer`, `source_label`, `maintained_status`,
  `observation_packet_ids`, and `source_observation_versions`.
- **Observation version requirements: declared.**
  `source_observation_versions` is a first-class tuple field
  (`agent_shim.py:557`, normalized at `:572-573`) and `consumed_snapshot_version`
  feeds it (`:140`).
- **Decision model attached to a role: declared.** `decision_model_ref` is a
  structured mapping (`agent_shim.py:222`, defensively copied at `:231`,
  exported at `:248` and `:275`, constructed at `:303` and `:335`) carrying
  `kind` and `id`. This matches T9's `AUTHORITY_ROLES[*].decision_model_ref`
  vocabulary in `python/tasking_contracts/agency_registry.py`.

The gap is that these declarations are **self-asserted strings, not gated
against the G4 registry**. `agent_shim` does not appear anywhere in
`python/architecture/information_layer.py` — grep returns zero hits — so its
`information_state_layer` value is unconstrained by the G4 vocabulary
whitelist and unvalidated by the declaration gate that governs the thirteen
registered consumers (`MAINTAINED_INFORMATION_LAYER_CONSUMERS`: nine
view-converged plus four declared-deferred,
`python/architecture/information_layer.py:84-129`; the declared view owner
`gym_envs.observation_view` is a separate constant, not a consumer). The
policy bridge declares its epistemic layer in a vocabulary the G4 gate does
not check.

Verdict: **partially conforms** — all three clauses are declared; none is
enforced. Gap G3-1 below.

## 5. Gap Register And Track Routing

| Gap | Contract | Statement | Routed to |
| --- | --- | --- | --- |
| G2-1 | Rollout collection | Rollout provenance records no observation snapshot version. Requires a run-globally monotone version to record, so it depends on T10's VA-2 producer being wired into the export path. | **T10** (evidence spine), then a follow-on T2/learning slice |
| G2-2 | Rollout collection | Rollout provenance records no action effective time. No `effective_time` field exists anywhere in the collection surface. | **T10** for the vocabulary; learning-runtime slice for the plumbing |
| G2-3 | Rollout collection | `barrier_trace` is exposed by the adapter but consumed by no rollout collector, so "collected at facade-declared barriers" is unverified rather than false. | Learning-runtime follow-on; no cross-track blocker |
| G3-1 | Policy bridge | `agent_shim`'s `information_state_layer` is self-asserted and absent from the G4 registry, so the declaration is ungated. | **T8** (extend the G4 registry/gate to the policy bridge) |
| G3-2 | Policy bridge | `decision_model_ref` duplicates T9's registry vocabulary without referencing the registry as owner, so the two can drift. | **T9**, but note T9's semantic convergence is held pending doctrine authority |

None of these gaps is closable inside T2. T2's own remaining scope is
discharged by this document.

## 6. Where The Baseline And The Code Disagree

One substantive disagreement, flagged as the most useful output of this census.

**Section 17 assigns "model checkpointing" to the Learning face** (`:854-855`)
and assigns curriculum, evaluation protocol, and experiment composition to the
Experiment face (`:852-854`). But checkpoint *compatibility* is currently
adjudicated through `ObservationViewSpec`, a DTO that I60 extended with
`view_id` / `information_layer_produced` / `information_layer_consumed` /
`semantic_stage` and exported from the runtime facade. So the checkpoint
compatibility surface is owned by the facade's observation-view vocabulary
(T8's territory), not by the Learning face.

This is not a defect in either place — it is an unassigned seam. Recommend the
architecture workline decide whether checkpoint compatibility is a Learning-face
concern that consumes a facade-declared view spec, or a facade concern that the
Learning face merely reads. Routed to the **architecture workline**, not
resolved here.

A second, smaller mismatch: section 17 says the collection cadence "is a policy
clock domain," but multi-rate clock domains remain registered-but-held behind
exact-runtime WP4/WP5 (`kClockDomainAdvisoryOnly` is still `true`,
`src/runtime/contracts/stage_node_manifest_registry.h:13`). So this
clause is not currently falsifiable — there is one effective rate. Recorded as
context, not as a gap.

## 7. Verification

Docs-only iteration; no build or behavior surface is touched.

- Document link audit: run before and after the bilingual cluster registry
  refresh; the registry-match gate is expected red until the refresh, per the
  pattern recorded at every prior census landing.
- CI smoke suite.
- `git diff --check`.

Pre-existing reds not caused by this iteration: four subtest failures in
`tests/runtime/mission/test_mission_command_roe_fields.py` arising from a stale
shared `ef_py` binary whose equivalence function predates the shared-core
consolidation; three `damage_model` path-separator reds owned by the concurrent
T6 clearance pack; and flecs/spdlog collection errors in build trees lacking
`_deps` sources (root-caused at I65 as build-snapshot completeness, not a
lineage red).

## 8. Related Authority

- [Unified architecture program](README.md) (T2 track row; this document closes its (e) deliverable)
- [Simulation system architecture design](../architecture/simulation_system_architecture_design.md) section 17 (the baseline contracts this document is measured against)
- [T8 G4 truth-leak inventory](t8_g4_truth_leak_inventory.md) (G3-1's destination)
- [T10 evidence spine census](t10_evidence_spine_census_20260721.md) (G2-1/G2-2's dependency)
- [Agency authority census](agency_authority_census_20260721.md) (G3-2's `decision_model_ref` vocabulary)
- [exact runtime refactor plan](../exact_runtime/cpp_exact_runtime_refactor_plan.md) (the held clock-domain context in section 6)
