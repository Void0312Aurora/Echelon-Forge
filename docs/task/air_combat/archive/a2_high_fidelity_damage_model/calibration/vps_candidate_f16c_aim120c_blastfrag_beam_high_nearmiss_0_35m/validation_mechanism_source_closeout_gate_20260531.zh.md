# Validation Mechanism / Source Closeout Gate - 2026-05-31

状态：`generated_from_mechanism_source_closeout_gate / non-authoritative / blocked_author_side_review_ready`。

本文记录 `RES-003 target geometry`、`RES-004 warhead scope`、`RES-005 fragment mechanism`、`RES-006 blast mechanism` 的当前 mechanism/source closeout gate。它来自
[damage_model_scope_provenance.py](../../../../../../tools/maintenance/damage_model_scope_provenance.py) `mechanism-source-closeout`，汇总 source ledger、artifact pin、target geometry assumption、warhead scope/sensitivity、Stage B/C author-side mechanism-load evidence。

本文不修改 [residual_register.zh.md](residual_register.zh.md)，不创建 runtime descriptor，不授予 target geometry、warhead、fragment、blast、effect-scale、component probability、Pk 或 deterministic-fuze authority。

## 1. Retained Artifact

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.mechanism_source_closeout_gate.v1` |
| `tool_ref` | [damage_model_scope_provenance.py](../../../../../../tools/maintenance/damage_model_scope_provenance.py) `mechanism-source-closeout` |
| `retained_artifact` | [mechanism_source_closeout_gate.json](retained_artifacts/mechanism_source_closeout_20260531/mechanism_source_closeout_gate.json) |
| `retained_artifact_sha256` | `069d304edd711aae2c612f94c7ca0a7632496642302f1c054b64bd9cfe5881f0` |
| `review_target` | `res_003_004_005_006_mechanism_source_closeout_lane` |
| `overall_status` | `blocked_non_authoritative_mechanism_source_closeout_candidate` |
| `readiness_level` | `author_side_evidence_present_but_calibrated_authority_blocked` |

## 2. Current Gate Results

| residual | current gate result | true close by this gate | author-side subitems recorded | shortest remaining path |
|---|---|---:|---|---|
| `RES-003` target geometry | `blocked_author_side_review_ready` | `false` | public outer-dimension anchors、rough component-region assumptions、unsupported material/occlusion/exposed-area rows are traceable | freeze row-level geometry provenance and uncertainty bounds; obtain independent review that repo hitboxes are not true F-16 vulnerability geometry |
| `RES-004` warhead scope | `blocked_author_side_review_ready` | `false` | AIM-120C-class family label is separated from variant-specific truth; third-party/game/forum values are sanity-only or rejected | freeze release-grade class/sensitivity envelope without consuming toy mass as AIM-120C truth; keep fuze/Pk outside this gate |
| `RES-005` fragment mechanism | `blocked_author_side_review_ready` | `false` | fragment sampler、areal-density bookkeeping、source-trace hard gates and Stage C gate-band fields are recorded as author-side evidence | resolve Gurney official artifact or exclude it; freeze fragment pattern/casing/velocity and TP-21 retained/reference-output evidence with reviewer signoff |
| `RES-006` blast mechanism | `blocked_author_side_review_ready` | `false` | blast scaled-distance/unit/source-trace hard gates pass in author-side snapshot; DENIX TP-20/BEC-O artifact existence and sha256 are recorded candidate-only | resolve Kingery-Bulmash official artifact or exclude it; freeze TP-20/BEC-O retained refs, comparison-output hashes, tolerances and blast applicability envelope |

当前真实关闭的 residual：`none`。

## 3. Evidence Boundary

| area | current evidence | allowed interpretation | forbidden interpretation |
|---|---|---|---|
| target geometry | `F16-TG-SRC-001/002/004/005/012` source ledger rows, `PIN-F16-001/002/003`, target geometry assumption manifest | coarse F-16 outer-dimension and review-only witness bookkeeping are traceable | engineering hitbox、beam witness panel or component projection is true F-16 internal vulnerability geometry |
| warhead scope | `AIM120-WF-002/006/007`, `PHYS-BF-001/002/006`, artifact pin and warhead scope/sensitivity manifest | AIM-120C-class / blast-fragmentation family scope and rejected/sanity boundary are explicit | repo warhead mass, third-party 40 lb/18 kg cluster, lethal radius, fuze radius or TDD term is AIM-120C calibrated truth |
| fragment mechanism | `VPS-BFM-001/006/010/011/013/015`, `PIN-BFM-002`, Stage B/C mechanism-load summaries | toy sampler, areal-density and gate-band hygiene are review-ready evidence | fragment mass、velocity、direction pattern、penetration or areal density is calibrated fragment authority |
| blast mechanism | `VPS-BFM-001/002/003/014`, `PIN-AIM120-002`, `PIN-BFM-001`, Stage B/C mechanism-load summaries | scaled-distance and impulse proxy checks are author-side benchmark hygiene | toy blast overpressure/impulse proxy is calibrated pressure/impulse or aircraft structural-coupling authority |

## 4. Non-Authoritative Guards

| guard | current value |
|---|---:|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `target_geometry_authority_granted` | `false` |
| `aim120c_warhead_authority_granted` | `false` |
| `fragment_mechanism_authority_granted` | `false` |
| `blast_mechanism_authority_granted` | `false` |
| `effect_scale_authority_granted` | `false` |
| `component_failure_probability_authority_granted` | `false` |
| `pk_authority_granted` | `false` |
| `deterministic_fuze_authority_granted` | `false` |

`RES-013 Pk boundary` 和 `RES-014 deterministic fuze boundary` 仍不属于本 mechanism/source closeout gate；当前 gate 明确保持 `Pk=false`、`deterministic_fuze=false`。

## 5. Current Decision

当前可审计结论为：

> `RES-003/004/005/006 now have an author-side mechanism/source closeout gate and retained JSON artifact, but no residual is truly closed; each remains blocked pending release-grade source retention, benchmark comparison/output evidence, uncertainty/applicability bounds and independent review`.

行为风险：

- 如果忽略 `RES-003`，engineering hitbox 可能被误写为真实 vulnerability geometry。
- 如果忽略 `RES-004`，AIM-120C-class toy inputs 可能被误写为 variant-specific warhead or fuze truth。
- 如果忽略 `RES-005/006`，fragment/blast toy probes 可能被误写为 calibrated mechanism authority。
