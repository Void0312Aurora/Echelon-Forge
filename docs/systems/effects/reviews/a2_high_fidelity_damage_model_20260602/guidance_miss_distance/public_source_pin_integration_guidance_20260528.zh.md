# Public Source Pin Integration：guidance benchmark update

状态：`2026-05-28 integration-note / guidance-benchmark / non-authoritative`。

本文档把本轮 guidance/miss-distance/evasion 公开来源核对接入 evidence route。它只说明文档和 benchmark design 如何引用来源；不修改 runtime，不生成 benchmark，不放行确定性引信，也不声明概率类杀伤或校准毁伤权威。

## 新增文档入口

| 文档 | 角色 | 最高用途 |
|---|---|---|
| [source_pin_update_guidance_benchmark_20260528.zh.md](../data_collection/guidance_miss_distance_public_methods/source_pin_update_guidance_benchmark_20260528.zh.md) | 固定 PN/APN、miss-distance、terminal evasion、seeker/filter/noise 来源的官方入口、权利、scope 和 acquisition 状态 | `method_reference`、`validation_criteria_reference`、`benchmark_design_reference` |
| [benchmark_gap_update_guidance_20260528.zh.md](../data_collection/guidance_evasion_benchmark_methods/benchmark_gap_update_guidance_20260528.zh.md) | 把来源映射到 benchmark family，并列出 artifact/hash/rights/old-scope gaps | generated non-authoritative benchmark planning only |
| [public_source_pin_integration_20260528.zh.md](public_source_pin_integration_20260528.zh.md) | 上一轮 integration note | background integration and gate posture |

## Evidence-route use

| Evidence route section | 本轮可接入 | 必须保留的限制 |
|---|---|---|
| G1 geometry PN | Zarchan, JHU/APL Basic, Nesline/Zarchan DOI, Lukenbill handle as design reference | Lukenbill body is `pending_acquisition`; use method shape until official artifact/hash/OCR is pinned. |
| G2 seeker/track | JHU/APL Guidance Filter, Singer DOI, Stone Soup MIT/tag/commit route | Track/filter proxy only; no ECM/ECCM/notch/clutter/decoy truth. |
| G3 energy / maneuver | JHU/APL 6DOF/Jackson, NASA generic fly-out, NASA/NACA noise/miss-distance records | Generic/old/simplified scope; no weapon-specific aero/propulsion/autopilot authority. |
| Terminal evasion route | Straight/McNamara/Swee/Shinar/Ben-Asher family | AFIT/NTIS and some NPS/AIAA artifacts are pending; only maneuver taxonomy and timing axes are admitted. |
| Fuze/effects bridge | Public miss-distance criteria plus A2 internal event fields | Fuze/effects bridge consumes miss-distance evidence only; it does not authorize deterministic triggering or final probability shortcuts. |

## Source acquisition posture

| status | Meaning | Affected groups |
|---|---|---|
| `source_ref_pinned` | Stable DOI/URL/NTRS/handle/repo route verified enough for citation | JHU/APL, NASA/NTRS, Zarchan/MathWorks, IEEE/AIAA/Springer DOI metadata, BUAA page, Stone Soup repo |
| `public_page_checked` | Public landing page or metadata page checked; body content may still require artifact manifest | JHU/APL, NASA/NACA/NTRS, BUAA |
| `abstract_acquired / fulltext_pending` | Public abstract or abstract collection available, but full source not acquired | McNamara via NASA STAR / NTRS `19840020657` |
| `pending_acquisition` | Official route exists or is listed, but this run did not acquire a usable artifact/hash/rights state | NTIS records, Calhoun target pages after handle redirect, MIL-HDBK/AD769595 route |
| `not_admitted` | Source class cannot enter benchmark design or runtime evidence | third-party mirrors, forums, game/community missile data, anonymous probability or radius tables |

## Runtime gate posture

| Gate item | Current conclusion |
|---|---|
| `source_ref` | Improved for method/design references; several official routes now pinned. |
| `rights` | Partial. Public pages and metadata are okay for citation; publisher/NTIS/NPS artifacts need per-copy rights and sha256 before body use. |
| `scope` | Explicitly old/simplified/generic for many evasion and miss-distance sources. |
| `artifact_sha256` | Missing for source bodies and generated outputs. |
| `validation_manifest` | Missing; no metrics/results/reviewer notes are frozen as a validation package. |
| `runtime authority` | Closed. No external calibration dataset or validated surrogate manifest exists here. |

## Integration rule

- Cite source ledger ids, not bare URLs, in future benchmark manifests.
- For `pending_acquisition` entries, only cite the source as a design lead; do not extract numbers, figures, tables or code.
- Generated benchmark outputs must include source artifact hashes where body content is used, plus script/commit/config/seed/metrics/output sha256.
- Evasion must enter through target maneuver, seeker/track quality, missile energy, miss distance and effects evidence fields; it must not enter as a direct final probability multiplier in any new benchmark claim.
- This route remains evidence-route-only until a separate authority gate is satisfied with full provenance, rights, scope, artifact hashes and residual closeout.
