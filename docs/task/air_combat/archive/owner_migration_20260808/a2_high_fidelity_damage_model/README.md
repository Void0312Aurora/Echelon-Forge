# A2 High-Fidelity Damage Model

Status: `2026-07-15` active follow-on index plus local archive registry. The
sealed base A2 research/candidate package remains in the outer air-combat
archive:
[archive/a2_high_fidelity_damage_model](../../a2_high_fidelity_damage_model/README.md).
Completed or superseded local MLF follow-ons have been physically moved under
this directory's [archive/](../../../a2_high_fidelity_damage_model/archive/README.md) tree and are registered in
[archive_registry.md](archive_registry.md).

This root intentionally keeps only live, retained, or planning entries so the
A2 follow-on surface does not flatten into a long list of completed projects.

## Live / Retained Entries

- [damage_consequence_reward_surface/README.md](../../../../../learning/work/active/air_combat_damage_consequence_reward/README.md):
  active bounded training-feedback work for damage consequences rather than a
  single kill flag.
- [missile_lethality_target_geometry/README.md](../../../../../systems/effects/reviews/f16c_target_geometry_20260614/README.md):
  accepted / retained follow-on promoted from the hitbox-geometry gap issue. It
  keeps reviewable F-16C outer regions, component bindings, distance diagnostics,
  fine geometry proxies, surface/internal receiver priors, and cross-region
  split receiver handoff evidence. It does not claim true F-16 engineering
  geometry, default runtime replacement, training benefit, structural breakup,
  debris/wreck, Pk, or weapon-specific lethality.
- [kill_chain_guidance_lethality_calibration_20260621.zh.md](../../../../../systems/weapons/reviews/kill_chain_guidance_mechanism_20260715/kill_chain_guidance_lethality_calibration_20260621.zh.md):
  retained Chinese research note for the 8 km / 30 deg AIM-120C guidance and
  near-fuze lethality calibration question. It separates current engineering
  proxy behavior from any real weapon/target authority and recommends a bounded
  follow-on gate.
- [kill_chain_expectation_standardization/README.md](../../../../../domains/air/reviews/kill_chain_expectation_standardization_20260706/README.md):
  accepted / retained task-local docs-only standardization follow-on that defines an AIM-120C-like
  engineering-proxy kill-chain expectation contract, range x offset-angle
  heatmap, sampling-density estimate, P3 metric mapping, and P4 harness plan
  before runtime retuning. P0-P5 are pass; P5 keeps it as a task-local
  docs-only standard and does not write into `docs/standards` in this batch. It
  now has a post-P5 initial before-report harness wrapper and a full
  constant-velocity `78` case anchor before report with per-component
  `component_detail` retention through the shared projection helper, reviewable
  heatmap visualization, first-review-stage attribution, component-response
  local diagnosis, a post-P5 docs-only component-response quantization addendum,
  and a standards-layer air planning supplement for the v0 expectation envelope:
  [Air-To-Air Kill-Chain Expectation Envelope](../../../../../domains/air/work/issues/kill_chain_expectation_envelope.md).
  The current tracked follow-on point is to emit the addendum's read-only
  quantized fields and the envelope's `envelope_cell_status` /
  `envelope_owner_stage` labels in future harness summaries if machine
  consumption is needed. KCES does not maintain its own component-attribution
  rules, and still refuses real weapon, real target, deterministic-fuze, Pk, or
  calibration authority.
- [kill_chain_mechanism_decoupling_analysis_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_mechanism_decoupling_analysis_20260621.zh.md):
  completed retained Chinese mechanism analysis for decoupling the kill chain
  into approach, fuze decision, warhead load field, component response, and
  consequence projection. It now links the read-only diagnostic evidence and
  the P2 runtime facade, P3 default-off policy, P4 named load factors, P5
  response owner rows, and bounded P6 calibration boundary.
- [kill_chain_decoupling_stage_abstraction_slice_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_decoupling_stage_abstraction_slice_20260621.zh.md):
  retained Chinese implementation note for the first read-only process-probe
  diagnostic slice. It adds stage abstractions and coupling-flag summaries on
  top of existing lethality-chain rows without retuning runtime parameters.
- [kill_chain_decoupling_probe_results_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_decoupling_probe_results_20260621.zh.md):
  retained Chinese baseline report for the reusable decoupling probe that runs
  the 8 km / 30 deg AIM-120C offset cases and a blast-fragmentation proximity
  sweep through the five-stage diagnostic view.
- [kill_chain_scalar_coupling_ledger_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_scalar_coupling_ledger_20260621.zh.md):
  retained Chinese implementation note for the scalar producer/owner/consumer
  ledger. It identifies owner leaks and cross-stage scalar consumption before
  any runtime retuning or calibration admission.
- [kill_chain_effect_scale_decomposition_probe_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_effect_scale_decomposition_probe_20260621.zh.md):
  retained Chinese P1 diagnostic slice that exposes existing spatial,
  armor/exposure, threshold, and vulnerability factors behind aggregate
  `effect_scale`; the current P4 runtime surface also exposes named load
  factors without changing default lethality parameters.
- [kill_chain_component_load_factor_view_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_component_load_factor_view_20260621.zh.md):
  retained Chinese P1-b diagnostic slice that adds per-component load-factor
  rows and residual proxies for `component_load.effect_scale`; runtime named
  factors are now available without changing lethality parameters.
- [kill_chain_component_response_boundary_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_component_response_boundary_20260621.zh.md):
  retained Chinese P5 response-owner boundary slice that classifies
  per-component load-only, compatibility-coupled, and response fields, and
  records the `rows_with_response_fields_on_load_row=0` runtime-owner migration
  result.
- [kill_chain_decoupled_facade_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_decoupled_facade_20260621.zh.md):
  retained Chinese P2 historical diagnostic-facade precursor that projects the
  current evidence into ApproachFact/FuzeDecision/WarheadLoadField/
  ComponentResponse/ConsequenceProjection-shaped structures.
- [kill_chain_runtime_facade_slice_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_runtime_facade_slice_20260621.zh.md):
  Chinese P2/P5 runtime-facade cleanup slice. The probe now reads
  component-load named factors and component-response owner rows from the
  runtime DTO-backed structure.
- [kill_chain_fuze_damage_policy_slice_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_fuze_damage_policy_slice_20260621.zh.md):
  Chinese P3 cleanup slice. The legacy `fuze_quality -> effective.damage`
  multiplier surface has been removed from runtime, DTO, bindings, and
  diagnostics.
- [kill_chain_calibration_admission_gate_20260621.zh.md](../../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_calibration_admission_gate_20260621.zh.md):
  retained Chinese P6 calibration-admission gate slice. It splits fuze,
  warhead, target-response, and consequence calibration into mutually exclusive
  layer admissions. Repository engineering-proxy evidence currently admits
  guarded single-layer dry-run plans for all four layers; real-world authority,
  default-database retuning, deterministic-fuze, and Pk claims remain fail-closed
  because no external authority record is admitted.

## Archived / Registered Entries

Use [archive_registry.md](archive_registry.md) for the compact registry. The
physical evidence packets are under [archive/](../../../a2_high_fidelity_damage_model/archive/README.md):

- [archive/missile_lethality_model_foundation/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_model_foundation/README.md):
  MLF-1 chain-contract foundation and phase-boundary evidence.
- [archive/missile_lethality_geometry_fuze/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_geometry_fuze/README.md):
  MLF-2 missile approach-geometry and fuze-evaluation evidence.
- [archive/missile_lethality_proximity_fuze_realism/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_proximity_fuze_realism/README.md):
  accepted-with-residuals proximity-fuze realism evidence slice.
- [archive/missile_lethality_warhead_effects/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_warhead_effects/README.md):
  MLF-3 generic warhead-effects, fragment/blast-load, and diagnostics evidence.
- [archive/missile_lethality_continuous_rod/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_continuous_rod/README.md):
  MLF-4 continuous-rod and cutting-mechanism fact evidence.
- [archive/missile_lethality_component_failure/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_component_failure/README.md):
  MLF-5 component vulnerability and failure-fact evidence.
- [archive/missile_lethality_structural_failure/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_structural_failure/README.md):
  accepted / archived MLF-6 structural-failure and airframe-breakup fact writer.
- [archive/missile_lethality_secondary_consequence_coupling/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_secondary_consequence_coupling/README.md):
  accepted / archived MLF-7 secondary consequence coupling. The runtime bridge
  consumes archived MLF-6 breakup facts, writes bounded consequences into
  maintained aircraft damage, platform damage, and loss-state surfaces, and
  emits chain-linked `platform_consequence` diagnostics.
- [archive/missile_lethality_debris_wreck_lifecycle/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_debris_wreck_lifecycle/README.md):
  accepted / archived MLF-8 debris and wreck lifecycle evidence. The runtime
  records diagnostics-only detached-part and terminal-wreck lifecycle facts
  linked to accepted MLF-6/MLF-7 evidence, while keeping first-class debris/wreck
  entities, debris physics, reward authority, Pk, and calibration authority
  refused.
- [archive/missile_lethality_pk_statistical_trends/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_pk_statistical_trends/README.md):
  accepted / archived MLF-9 Pk/statistical trend evidence. It consumes
  replayable MLF-5 through MLF-8 simulation facts through an explicit metric
  contract and exposes bounded diagnostics trend reports, while refusing real
  weapon-specific Pk, target-specific lethality, reward authority, and
  calibration authority.
- [archive/missile_lethality_calibration_gates/README.md](../../../a2_high_fidelity_damage_model/archive/missile_lethality_calibration_gates/README.md):
  accepted / archived MLF-10 calibration-gate infrastructure. It inventories
  existing evidence, defines a fail-closed admission contract, and retains a
  deterministic current-repository report with zero admitted records. It does
  not release real Pk, deterministic fuze, stock weapon/target lethality,
  reward authority, entity-deletion authority, calibration authority, or
  runtime parameter retuning.

The current geometry-fidelity gap is tracked on the issue board:
[Lethality Hitbox Geometry Fidelity Gap](../../../../../systems/effects/work/issues/lethality_hitbox_geometry_fidelity_gap/README.md).
The first mainline execution entry for that issue has been closed against the
geometry-only acceptance gate:
[missile_lethality_target_geometry/README.md](../../../../../systems/effects/reviews/f16c_target_geometry_20260614/README.md).

MLF-8, MLF-9, and MLF-10 are accepted and archived under [archive/](../../../a2_high_fidelity_damage_model/archive/README.md);
their old active compatibility pointer directories were removed on
`2026-06-20` so the root remains limited to live or retained follow-ons. Use the
local [archive registry](archive_registry.md) for those records.
Do not continue inside archived MLF-1 through MLF-10 or proximity-fuze realism
packages. These follow-ons do not reopen the sealed A2 package or create A9.

Reopen this line only through an explicit authority-promotion or new research
request. Default air-combat work continues from [../README.md](../README.md).
