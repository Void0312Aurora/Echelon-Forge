# A2 G5-R Uncertainty / Independence Audit - 2026-06-02

状态：`2026-06-02 / G5-R-D-UNCERTAINTY-AUDIT / pass / research_candidate / non_authoritative`。

本文审查 `G5-R` proxy chain 的不确定性覆盖和输入独立性。它只支持 research packet
整合，不授予 `pk_authority` 或 `deterministic_fuze_authority`。

## Audit Matrix

| audit id | target | check | result | residual boundary |
|---|---|---|---|---|
| `G5UNC-001` | source uncertainty | all G5 source inputs have class, scope, confidence and replacement rule | `pass` | public / community / repo-internal inputs are not truth |
| `G5UNC-002` | model-form uncertainty | each event stage separates ordinal labels from probability claims | `pass` | no calibrated probability output |
| `G5UNC-003` | scope uncertainty | chain scope remains AIM-120C-class / F-16C candidate research surface | `pass` | no all-target / all-weapon extrapolation |
| `G5UNC-004` | fuze independence | fuze proxy branch consumes boundary docs and public terminology only | `pass` | no deterministic trigger admission |
| `G5UNC-005` | G4 dependency independence | G4 mechanism and fragility packets remain dependencies, not validation truth | `pass` | no kill-chain authority inherited from G4 |
| `G5UNC-006` | runtime/report independence | consequence flags are reporting surface only | `pass` | no reward / combat-win truth claim |
| `G5UNC-007` | result independence | aggregate proxy output has no reviewer-accepted truth status | `pass` | later review must be separate if authority is requested |

## Sensitivity Triggers

| trigger | required action |
|---|---|
| new guidance / miss-distance benchmark packet | update `G5EVT-001` and source confidence |
| new fuze evidence packet | update `G5EVT-002`; do not set authority without separate gate |
| updated G4 mechanism-load packet | update `G5EVT-003` and propagate model-form uncertainty |
| updated G4 fragility surface | update `G5EVT-004` and component-response uncertainty |
| runtime consequence schema change | update `G5EVT-005` and re-run guard grep |
| any request for stock / release behavior | move to authority backlog; do not mutate G5-R packet |

## Independence Verdict

`G5-R` passes research-level independence because:

- source scan, proxy boundary design, event-chain map and audit are separate documents;
- no stage consumes its own output as source evidence;
- G4 packets are referenced as research dependencies only;
- runtime reports are treated as observations, not calibration labels;
- forbidden claims are recorded before integration.

This verdict does not close `RES-013/014` as authority residuals. It only confirms that the
research proxy packet can be integrated without confusing proxy design with Pk or fuze authority.

## Worker Packet

```md
status: pass
touched files:
- docs/task/air_combat/a2_high_fidelity_damage_model/g5_research_uncertainty_independence_audit_20260602.zh.md
commands/outcomes:
- pending integration validation
remaining paths:
- G5-R-INTEGRATION
behavior risks:
- aggregate proxy labels being reused outside research context
- G4 dependency updates not propagating through G5 uncertainty notes
integration notes:
- Integration should keep RES-013/014 authority deferred.
research boundary confirmation:
- `pk_authority=false`
- `deterministic_fuze_authority=false`
- `stock_descriptor_created=false`
```
