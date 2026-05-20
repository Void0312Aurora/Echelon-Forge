# WP8 Learning Face Acceptance Review

Status: `2026-05-20` accepted documentation-only Learning-face task family.

Language:

- English canonical: `wp8_learning_face_acceptance_review_20260520.md`
- Chinese companion:
  [wp8_learning_face_acceptance_review_20260520.zh.md](wp8_learning_face_acceptance_review_20260520.zh.md)

Reviewed inputs:

- [WP8 SCAL Learning Face](../simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.md)
- [WP8-A Curriculum And Scenario Generation](../simulation_architecture/wp8_learning_face/wp8_curriculum_scenario_generation_cluster_20260520.md)
- [WP8-B Evaluation And Capability Profiling](../simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.md)
- [WP8-C World-Model Interface And Learning Evidence](../simulation_architecture/wp8_learning_face/wp8_world_model_interface_and_learning_evidence_cluster_20260520.md)
- [WP7.5 Training Path Facade Bridge](../simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)

## 1. Required Acceptance Artifacts

The `WP8` acceptance packet is incomplete unless all artifacts below exist and
stay aligned:

- `docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.md`
- `docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.zh.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_curriculum_scenario_generation_cluster_20260520.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_curriculum_scenario_generation_cluster_20260520.zh.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.zh.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_world_model_interface_and_learning_evidence_cluster_20260520.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_world_model_interface_and_learning_evidence_cluster_20260520.zh.md`
- `docs/task/review/wp8_learning_face_acceptance_review_20260520.md`
- `docs/task/review/wp8_learning_face_acceptance_review_20260520.zh.md`

Missing artifact rule:

- Any missing artifact forces the overall result to `fail`.
- A present artifact without gate verdicts and required evidence also forces
  `fail`.

## 2. Review Decision Vocabulary

Each gate and the overall line may end only as:

- `pass`: all required evidence is present and not contradicted.
- `fail`: required evidence is missing, contradicted, or replaced by
  intention-only wording.
- `blocked`: environment or machine limitations prevent a required check. This
  keeps the gate open and does not count as acceptance.

Blocked wording rule:

- A blocked gate must name the exact command, exact blocker, and next
  environment needed.
- `Blocked` must not be restated as “ready”, “accepted pending tests”, or any
  equivalent soft pass.

## 3. Gate Checklist

| Gate | Required evidence that must appear in this review | Decision rule |
|------|---------------------------------------------------|---------------|
| `WP8-A Curriculum And Scenario Generation` | Curriculum and scenario-generation documents checked, the request/versioning fields required by the task line, and the exact validation commands or document checks used to confirm those requests stay explicit and versioned. | Pass only with explicit request/versioning evidence and no hidden simulation authority. |
| `WP8-B Evaluation And Capability Profiling` | Benchmark/profile artifacts checked, the representation of score attribution and capability evidence, and the exact validation commands or review checks used to prove profiles stay metadata rather than hidden support claims. | Pass only with evidence-backed profile discipline and no support claims inferred from helper or probe presence. |
| `WP8-C World-Model Interface And Learning Evidence` | Observation/evidence boundary documents checked, the rule separating `ObservationPacket`, `DecisionBelief`, and `World Truth`, and the exact validation commands or document checks used to verify provenance and replay/diagnostics ancestry. | Pass only with explicit boundary and provenance evidence, without turning learning into a truth source. |
| `WP8-D Integration And Index Sync` | Confirmation that all required artifacts exist, `WP7.5` remains the cited maintained training-path bridge, and the bilingual pair stays aligned. | Pass only if publication, cross references, and bridge ownership are internally consistent. |

## 4. Reviewer Recording Rule

For every gate, this review should record:

1. The verdict: `pass`, `fail`, or `blocked`.
2. The required evidence actually observed.
3. The exact commands run, if any.
4. The exact blocker and next environment, if blocked.

Absence rule:

- If the review does not explicitly record the verdict and required evidence for
  a gate, that gate is `fail`.

## 5. Current State

Gate snapshot as of `2026-05-20`:

| Gate | Verdict | Evidence observed in this review | Commands / blocker |
|------|---------|----------------------------------|--------------------|
| `WP8-A Curriculum And Scenario Generation` | `pass` | Checked `wp8_curriculum_scenario_generation_cluster_20260520.md` and `.zh.md`. The contract lists `request_id`, `request_version`, `contract_version`, `scenario_set_id`, `scenario_family_id`, `selection_policy_id`, `selection_constraints`, `seed_policy_id`, `seed_mode`, `seed_source`, `seed_scope`, `curriculum_phase_id`, `phase_order`, `entry_condition`, `exit_condition`, `generation_request_version`, `requested_output_shape`, `input_refs`, `result_id`, `result_version`, `status`, `generated_scenario_set_id`, and `result_refs`. The slice states that generation requests are explicit requests, not hidden simulation authority. | `git diff --check` passed. `rg -n "WP8-A|curriculum|scenario selection|scenario-set|seed policy|curriculum phase|generation request|request/result|version" docs/task/simulation_architecture/wp8_learning_face docs/task/simulation_architecture/wp75_training_path_facade_bridge docs/task/review` passed. |
| `WP8-B Evaluation And Capability Profiling` | `pass` | Checked `wp8_evaluation_capability_profiling_cluster_20260520.md` and `.zh.md`. The contract defines benchmark protocol fields, separates metadata from profile claims and hidden support claims, decomposes score attribution, and states that helper/probe presence may explain observability or deployment state but must not prove support. | `git diff --check` passed. `rg -n "WP8-B|benchmark protocol|profile schema|score attribution|capability evidence|hidden support|helper|probe|support claim|WP7.5" docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520*.md docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520*.md docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520*.md` passed. |
| `WP8-C World-Model Interface And Learning Evidence` | `pass` | Checked `wp8_world_model_interface_and_learning_evidence_cluster_20260520.md` and `.zh.md`. The contract keeps `ObservationPacket`, `DecisionBelief`, `World Truth`, and `LearningEvidenceBundle` separate, requires observation/belief/replay/diagnostics ancestry, and states that evidence bundles do not mutate state or become support claims without the relevant `WP8-B` gate. | `git diff --check` passed. `rg -n "WP8-C|world-model|World Truth|ObservationPacket|DecisionBelief|learning evidence|provenance|replay|diagnostics ancestry|WP7.5" docs/task/simulation_architecture/wp8_learning_face/wp8_world_model_interface_and_learning_evidence_cluster_20260520*.md docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520*.md docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520*.md docs/task/review` passed. |
| `WP8-D Integration And Index Sync` | `pass` | Required artifacts exist, `WP8` cites `WP7.5` as the maintained training-path bridge, the WP8 task family links A/B/C task slices, `docs/task/simulation_architecture/README.md` and `.zh.md` list the accepted WP8 outputs, and this review pair records gate-level evidence. | `git diff --check` passed. `rg -n "WP8|Learning face|curriculum|evaluation|capability profiling|scenario generation|world-model|learning evidence" docs/plan/architecture docs/task/simulation_architecture docs/task/review` passed. |

Overall decision: `pass`.

Reason:

- `WP8-A/B/C` now have checked bilingual task slices with explicit contract
  fields and doc-only validation evidence.
- `WP8-D` publication/index sync is complete, and `WP8` continues to cite
  `WP7.5` for the maintained training-path bridge.
- WP8 remains documentation-only; no local RL training, benchmark run, or
  world-model implementation was required for this acceptance.
