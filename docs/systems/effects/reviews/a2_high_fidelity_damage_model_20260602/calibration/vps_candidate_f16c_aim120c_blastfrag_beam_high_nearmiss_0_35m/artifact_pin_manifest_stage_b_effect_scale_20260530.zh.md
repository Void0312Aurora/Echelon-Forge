# Artifact Pin Manifest - Stage B Effect Scale

状态：`author_frozen_pin_manifest / candidate / non-authoritative`。

本文档把当前 Stage B `effect_scale_authority_only` 候选包真正引用或显式拒绝的
artifact pin 状态固化下来。它的作用是回答两件事：

1. 当前 package 到底消费了哪些 official / third-party / community artifacts；
2. 哪些条目只是 candidate、sanity、pending 或 rejected，绝不能被误写成 authority。

本文档不授予任何 runtime authority，也不关闭 `RES-001 source provenance`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `primary_release_scope` | `effect_scale_authority_only` |
| `manifest_status` | `author_frozen_pending_independent_review` |
| `package_provenance_status` | `official_public_artifacts_partially_verified_release_grade_closeout_pending` |
| `third_party_policy` | `allowed_as_candidate_or_sanity_only_when_rationality_and residuals are explicit; never auto-authoritative` |
| `forbidden_release_action` | `do not treat pending, verified-candidate or sanity-only artifacts as acquired calibration inputs` |

## 2. Artifact Pin Table

| `artifact_id` | `source_id` | `source_tier` | `source_ref` | `access_status` | `artifact_status` | `sha256` | `retention_ref` | `consumption_status` | `candidate_use` | `authority_boundary` | residuals |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `PIN-F16-001` | `F16-TG-SRC-002` | `Tier A` | Shaw AFB F-16C fact sheet | public HTML route | `reference_only_html` | `hash_not_applicable_html_not_archived` | [f16c source pin update](../../data_collection/f16c_block50_target_geometry/source_pin_update_20260528.zh.md) | `acquired_for_candidate` | Block 50/52 scope anchor、尺寸/发动机/radar family 量级 | 不是内部组件几何、材料或 vulnerability truth | `RES-001`, `RES-003` |
| `PIN-F16-002` | `F16-TG-SRC-004` | `Tier B` | GE F110 family / F110-GE-129 datasheets | public PDF route recorded | `candidate_route_recorded` | `pending_in_subledger` | [f16c source pin update](../../data_collection/f16c_block50_target_geometry/source_pin_update_20260528.zh.md) | `acquired_for_candidate` | aft engine region family-level candidate | 不是 F-16 安装边界、附件、管路或 vulnerability truth | `RES-001`, `RES-003` |
| `PIN-F16-003` | `F16-TG-3P-006` | `Tier C` | JSBSim `aircraft/f16` commit `3e1a5cfa5c9a1243db8893cd00932f8f68e1a692` | local clone succeeded in source audit | `open_source_config_candidate` | `git_commit_only` | [third-party/community geometry audit](../../data_collection/f16c_block50_target_geometry/source_pin_update_third_party_community_20260528.zh.md) | `sanity_only` | parser/schema、粗坐标和 visual sanity | 不是 F-16C Block 50 geometry authority | `RES-001`, `RES-003` |
| `PIN-AIM120-001` | `AIM120-GMF-WF-006` | `Tier A` | govinfo Federal Register PDF `FR-2011-10-25/pdf/2011-27552.pdf` | official PDF acquired | `official_public_pdf` | `bbc0eff2811a0e87ece25d24b3966ad7e0280c3ef4dd7f0f1832467c16c381fb` | [warhead/fuze geometry-material pin update](../../data_collection/aim120c_warhead_fuze/source_pin_update_geometry_material_fuze_20260528.zh.md) | `acquired_for_candidate` | public TDD / burst-point terminology and field naming | 不支持 trigger threshold、delay、reliability 或 deterministic fuze | `RES-001`, `RES-004`, `RES-014` |
| `PIN-AIM120-002` | `AIM120-GMF-PHYS-001` | `Tier A` | UFC 3-340-02 public PDF | official PDF acquired | `official_public_pdf` | `1eb51e42757c86fa4385c509f149e5496c27c80b378c66b6c496c24199a5cafa` | [warhead/fuze geometry-material pin update](../../data_collection/aim120c_warhead_fuze/source_pin_update_geometry_material_fuze_20260528.zh.md) | `acquired_for_candidate` | blast scaled-distance / pressure / impulse method route | 不是 AIM-120C explosive truth 或 calibrated effect row | `RES-001`, `RES-004`, `RES-006` |
| `PIN-BFM-001` | `VPS-BFM-014` | `Tier A candidate` | DENIX TP-20 PDF + BEC-O-V1.xlsx public artifacts | official public artifacts externally verified (HTTP 200 / content-type pinned) | `verified_candidate_artifact_bundle / retention_pending` | `TP-20 PDF: 293c5fd15a56b7ec4e6f4ad37d35f73a8e010083ce20baad56e39fb8423f165f; BEC-O-V1.xlsx: 82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc` | [vps validation gap update](../../data_collection/vps_blast_fragmentation_methods/validation_gap_update_20260528.zh.md) | `not_consumed_for_stage_b_release` | future blast implementation comparison route | official artifact verification does not imply Stage B release ingestion、benchmark-output admission 或 runtime authority | `RES-001`, `RES-006` |
| `PIN-BFM-002` | `VPS-BFM-015` | `Tier A candidate` | DENIX TP-21 public artifact | official public artifact externally verified (HTTP 200 / content-type pinned) | `verified_candidate_artifact / retention_pending` | `84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8` | [vps validation gap update](../../data_collection/vps_blast_fragmentation_methods/validation_gap_update_20260528.zh.md) | `not_consumed_for_stage_b_release` | future debris / areal-density vocabulary route | official artifact verification does not imply Stage B release ingestion、benchmark-output admission 或 runtime authority | `RES-001`, `RES-005`, `RES-011` |
| `PIN-BFM-003` | `VPS-BFM-009` | `rejected` | UFC 3-340-01 public page only | official rejection evidence recorded | `rejected_for_public_admission` | `not_applicable` | [vps source ledger](../../data_collection/vps_blast_fragmentation_methods/source_ledger.zh.md) | `rejected` | rejection evidence only | 受限分发，禁止镜像回填 | `RES-001` |
| `PIN-AIM120-TPC-001` | `AIM120-TPC-001/002/006` | `Tier C` | third-party/community C-class 40 lb / 18 kg mass-claim cluster | metadata only | `third_party_candidate_cluster` | `not_frozen_for_release` | [third-party/community warhead audit](../../data_collection/aim120c_warhead_fuze/source_pin_update_third_party_community_20260528.zh.md) | `sanity_only` | mass-envelope sanity / sensitivity discussion | 绝不写成 AIM-120C mass truth 或 runtime row | `RES-001`, `RES-004` |
| `PIN-AIM120-TPC-REJ` | `AIM120-TPC-REJ-001..005` | `rejected` | forum / game / RPG / inaccessible third-party leads | various unstable or unsuitable routes | `rejected` | `not_applicable` | [third-party/community warhead audit](../../data_collection/aim120c_warhead_fuze/source_pin_update_third_party_community_20260528.zh.md) | `rejected` | rejection guard only | DCS / War Thunder / forum / tabletop values 永不进入 authority path | `RES-001`, `RES-004`, `RES-013`, `RES-014` |

## 3. 当前 pin 规则

- `acquired_for_candidate` 只表示该 artifact 可以支撑 candidate 文档、method route 或 scope 语言；
- `sanity_only` 只允许做量级、命名或 sensitivity sanity；
- `verified_candidate_artifact` / `verified_candidate_artifact_bundle` 表示 official public artifact 的 URL、content-type 和 sha256 已完成外部核验，但该 artifact 仍未作为 Stage B release retained input、benchmark-output pin 或 runtime authority 被消费；
- `pending_acquisition` 表示 official route 已识别，但 artifact/hash/rights 还没冻结；
- `rejected` 表示即使可访问也不允许进入 Stage B release path。

## 4. 当前判定

当前判定为：

> `the Stage B package now has an explicit artifact-pin surface with externally verified DENIX public artifacts, but release-grade provenance remains open because retention, output-policy and benchmark-consumption closeout are still pending`.
