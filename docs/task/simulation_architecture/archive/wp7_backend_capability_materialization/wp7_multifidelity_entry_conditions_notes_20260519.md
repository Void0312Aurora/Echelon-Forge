# WP7-D Implementation Notes: Multi-Fidelity Entry Conditions

Status: `2026-05-19` implementation-ready notes for the WP7-D first design
refinement wave.

Language:

- English canonical: `wp7_multifidelity_entry_conditions_notes_20260519.md`
- Chinese companion:
  [wp7_multifidelity_entry_conditions_notes_20260519.zh.md](wp7_multifidelity_entry_conditions_notes_20260519.zh.md)
- Dispatch sheet:
  [wp7_multifidelity_entry_conditions_cluster_20260519.md](wp7_multifidelity_entry_conditions_cluster_20260519.md)

## 1. Operating Rule

WP7-D defines request vocabulary and entry gates only. A fidelity profile request
can ask for an execution shape, but maintained support still comes only from:

1. accepted backend profile metadata,
2. accepted parity or tolerance budget,
3. accepted validation gate evidence,
4. facade-visible projection that reports declared support conservatively.

Request labels must therefore be stored and reported as requested intent, not as
capability truth. If a runtime later cannot satisfy a request with maintained
metadata, the result must be rejected, downgraded to diagnostics-only, or routed
to the maintained baseline according to the mismatch policy.

## 2. Request Vocabulary

| Request label | Allowed use | Required binding | Minimum facade evidence |
|---------------|-------------|------------------|-------------------------|
| `exact_evaluation` | Evaluation, benchmark, regression comparison, promotion review. | `backend_profile_id=cpu_exact.reference` unless a later exact profile is promoted; `parity_budget.cpu_exact.reference.v1`; exact model family scope; WP5 replay/evidence gate. | Request id, selected exact profile, budget id/version, comparison reference, snapshot version, event-order evidence, validation gate result. |
| `fast_training` | Training throughput experiments, curriculum sweeps, diagnostics runs. | A maintained exact baseline for evaluation; any approximate or diagnostics path must carry a tolerance or diagnostics budget and cannot be labeled truth. | Request id, selected training profile, exact evaluation reference, tolerance/diagnostics label, mismatch policy, quarantine status. |
| `sensor_heavy` | Sensor scan, track, shared picture, observation, belief, and information-state stress. | Backend profile covering observation/track scope; observation envelope budget; WP5 information/belief and replay gates. | Visibility label, source snapshot version, observation schema, track/observation provenance, selected backend profile, validation gate. |
| `weapon_effects_heavy` | Launch, munition, effect, damage, reward, termination, and trace ancestry stress. | Backend profile covering engagement/effect scope; event-order and diagnostics trace budgets; WP5 trace/replay gate. | Launch/event ancestry, damage/effect source ids, reward/termination provenance, mismatch domain, validation gate. |
| `large_scale_swarm` | Scale-oriented many-platform or many-agent runs. | Backend profile and budget covering scheduler, observation, engagement, and snapshot scopes used by the swarm. | Agent/platform count, shard-version map, barrier ids, selected profile, budget id/version, mismatch policy. |
| `single_platform_physics` | Focused platform physics/control analysis for a named family. | Backend profile covering physics/control scope; exact or explicit numeric tolerance budget; WP5 design/replay gate. | Platform/model family id, physics state shard versions, comparator/tolerance fields, selected profile, validation gate. |

## 3. Binding Record Shape

Future implementation should treat a fidelity request as a record similar to:

```yaml
fidelity_request_id: stable-request-id
fidelity_profile_request: exact_evaluation
backend_profile_id: cpu_exact.reference
parity_budget_ref: parity_budget.cpu_exact.reference.v1
model_family_scope:
  lifecycle_stages: [P0, P1, P2, P3, P4, P5, P6, P7, P8, P9, P10]
  families: [physics, sensor, engagement, observation]
validation_gate:
  wp5_tiers: [trace_conformance, replay_evidence_conformance]
facade_evidence:
  required_fields:
    - fidelity_request_id
    - fidelity_profile_request
    - selected_backend_profile_id
    - selected_budget_id
    - selected_budget_version
    - comparison_reference
    - source_snapshot_version
    - resulting_snapshot_version
    - sync_barrier_id
    - mismatch_policy
    - diagnostics_label
```

This shape is descriptive, not a runtime schema commitment. WP7-A may revise
field names during registry materialization, but it must preserve the same
semantic obligations.

## 4. Backend, Budget, Model, Gate, Evidence Matrix

| Request label | Backend profile rule | Parity/tolerance budget rule | Model family rule | Validation gate rule | Facade-visible evidence rule |
|---------------|----------------------|------------------------------|-------------------|----------------------|------------------------------|
| `exact_evaluation` | Use `cpu_exact.reference` until another exact profile is promoted. | Exact domains from `parity_budget.cpu_exact.reference.v1`; no numeric tolerance unless a future exact profile says so. | All families that influence maintained output must be inside the exact lifecycle path. | WP5 replay/evidence plus relevant trace, boundary, and information gates. | Must expose exact profile and budget ids, event order, snapshot identity, and structured diagnostics ancestry. |
| `fast_training` | May use maintained exact for evaluation and diagnostics/candidate paths for speed only when labeled. | Approximate output needs explicit tolerance; diagnostics output uses report-only budget. | Training model family must say whether it feeds policy input, reward, or diagnostics. | Evaluation uses exact gate; training-only diagnostics may use report-only gate. | Must expose that training output is not exact truth and name the exact comparison reference. |
| `sensor_heavy` | Must bind observation/track backend profile scope; resident-state candidates remain unmaintained. | Observation envelope exactness is required; payload tolerance must be field-specific. | Sensor, track, data-link, observation, and belief families must name visibility boundaries. | WP5 information/belief leakage and replay gates. | Must expose visibility label, source snapshot, observation schema, and diagnostics label. |
| `weapon_effects_heavy` | Must bind engagement/effect backend profile scope. | Event order and diagnostics trace ancestry remain exact; numeric effect tolerances must be named. | Weapon, effect, damage, reward, and termination families must name source event ancestry. | WP5 trace conformance and replay gates. | Must expose launch id, munition/effect ids, damage ancestry, reward/termination provenance. |
| `large_scale_swarm` | Must bind every backend profile used across scheduler, observation, and engagement scopes. | Scale does not relax event order or snapshot identity without a named budget. | Agent/platform model families must identify which state shards they read/write. | WP5 design, boundary, trace, and replay gates. | Must expose shard-version map, barrier sequence, selected profiles, and quarantine status. |
| `single_platform_physics` | Must bind physics/control backend profile scope. | Numeric tolerance requires field family, comparator, threshold, and reference. | Platform family, control law, and physics model family must be named. | WP5 design/replay gate plus any future physics model certification gate. | Must expose platform id, model family id, state shard versions, comparator, and validation gate. |

## 5. ModelProvider Boundary

WP7-D may use these vocabulary terms:

| Term | WP7-D status | Required before maintained use |
|------|--------------|--------------------------------|
| Analytical provider | Vocabulary only. | Interface, parameters, domain validity, parity budget, replay evidence. |
| Table provider | Vocabulary only. | Table identity, version, interpolation rule, provenance, tolerance budget. |
| Surrogate provider | Vocabulary only. | Training/calibration data, domain limits, uncertainty reporting, tolerance budget. |
| Learned provider | Vocabulary only. | Training pipeline, artifact identity, evaluation split, safety envelope, validation evidence. |
| Hybrid provider | Vocabulary only. | Ownership split, switch policy, mismatch policy, rollback/quarantine evidence. |
| Diagnostics provider | Vocabulary only. | Diagnostics labeling, non-interference rule, export-only evidence. |

No `ModelProvider` term may imply maintained support until the provider is bound
to backend metadata, model artifact identity, budget, validation gate, and
facade evidence.

## 6. Adaptive Fidelity Scheduling Entry Gate

Adaptive scheduling cannot start as runtime work until a future task can prove:

1. State shard versioning exists for every switchable shard, including host and
   backend-resident ownership if any.
2. Replay evidence can reconstruct pre-switch, switch, and post-switch
   snapshots with exact barrier identity.
3. Mismatch policy defines `fail`, `report_only`, `quarantine`, and `rollback`
   outcomes by profile class.
4. Scheduling contract names allowed switch points, forbidden lifecycle stages,
   barrier requirements, and who owns committed state at each point.
5. Rollback/quarantine can prevent candidate or approximate output from
   contaminating maintained state.
6. Facade evidence records requested fidelity, selected backend profile, model
   family, budget version, switch reason, and switch ancestry.

Until all six exist, `adaptive` and `adaptive fidelity scheduling` are planning
terms only.

## 7. Future Test Hooks

No runtime test is required in this first design wave. If WP7-D later adds
architecture tests, they should be doc/schema checks that assert:

1. request labels are not projected as maintained capability flags,
2. every request record has backend, budget, model, validation gate, and facade
   evidence fields,
3. `ModelProvider` entries stay deferred unless model/training evidence exists,
4. adaptive scheduling entries fail closed without state shard versioning,
   replay evidence, mismatch policy, scheduling contract, and quarantine rules.

## 8. Open Risks

1. WP7-A may rename registry field shapes; WP7-D should adapt names without
   relaxing the binding obligations.
2. Future approximate profiles need explicit tolerance budgets before they can
   be used for anything beyond diagnostics or training-only experiments.
3. Learned or surrogate providers can easily blur truth and diagnostics; they
   require facade-visible labeling before promotion.
