# WP8 Learning Face Acceptance Review

Status: `2026-05-20` acceptance rules hardened; acceptance not yet granted.

Language:

- English canonical: `wp8_learning_face_acceptance_review_20260520.md`
- Chinese companion:
  [wp8_learning_face_acceptance_review_20260520.zh.md](wp8_learning_face_acceptance_review_20260520.zh.md)

Reviewed inputs:

- [WP8 SCAL Learning Face](../simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.md)
- [WP7.5 Training Path Facade Bridge](../simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)

## 1. Required Acceptance Artifacts

The `WP8` acceptance packet is incomplete unless all artifacts below exist and
stay aligned:

- `docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.md`
- `docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.zh.md`
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
| `WP8-A Curriculum And Scenario Generation` | `fail` | The task family defines the stream and gate rules, but this review does not yet record concrete curriculum/scenario-generation request fields or a checked artifact beyond the planning document itself. | No gate-specific validation command or checked artifact has been recorded yet. |
| `WP8-B Evaluation And Capability Profiling` | `fail` | The task family defines benchmark/profile scope and gate rules, but this review does not yet record a checked benchmark/profile artifact, score-attribution evidence, or profile-verification command. | No gate-specific validation command or checked artifact has been recorded yet. |
| `WP8-C World-Model Interface And Learning Evidence` | `fail` | The task family defines the intended `ObservationPacket` / `DecisionBelief` / `World Truth` separation, but this review does not yet record a checked evidence-boundary artifact or provenance verification command. | No gate-specific validation command or checked artifact has been recorded yet. |
| `WP8-D Integration And Index Sync` | `pass` | Required artifacts now exist, `WP8` cites `WP7.5` as the maintained training-path bridge, and the bilingual pair has been created as part of this packet. | Documentation checks completed from the current worktree; no runtime blocker applies to artifact existence. |

Overall decision: `fail`.

Reason:

- Acceptance rules are now explicit and review artifacts exist.
- `WP8-A/B/C` still lack the required checked artifacts and gate-specific
  evidence, so the line cannot be reported as accepted.
