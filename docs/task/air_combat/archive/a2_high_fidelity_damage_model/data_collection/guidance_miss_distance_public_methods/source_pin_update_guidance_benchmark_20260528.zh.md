# Source Pin Update：guidance benchmark public methods

状态：`2026-05-28 source-pin / guidance-benchmark / non-authoritative`。

本文档只补强 [source_ledger.zh.md](source_ledger.zh.md) 的公开来源固定与准入边界。它不生成 benchmark artifact，不复制受限正文，不写运行时数据行，不授予命中概率、确定性引信、effect-scale 或 component-failure probability 权威。

遵循准入规则：

- [公开数据来源准入标准](../../../../../standards/foundation/public_data_source_admission.zh.md)
- [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)

## 本轮 source pin

| `pin_id` | 覆盖来源 | 官方 / 稳定入口核对 | 发布方与权利 | 可采纳角色 | ingestion 状态 | residual |
|---|---|---|---|---|---|---|
| `GMD-PIN-GB-001` | `GMD-SRC-001`, `GEB-SRC-001` | MathWorks 书页核到 *Tactical and Strategic Missile Guidance*、Paul Zarchan、AIAA、ISBN `978-1-62410-537-1`；AIAA course page 作为出版方路线交叉 | AIAA / Paul Zarchan；书籍和 companion material 受版权/平台条款约束 | `method_reference`、`validation_criteria_reference` for PN/APN、adjoint、miss-distance、filter/noise terminology | `source_ref_pinned / artifact_not_acquired` | 不复制正文、图表、表格或代码；教材例题不是外部校准数据；后续自实现 benchmark 需脚本、seed、hash |
| `GMD-PIN-GB-002` | `GMD-SRC-002` to `006`, `GEB-SRC-002` to `006` | JHU/APL article pages 核到 `Basic Principles of Homing Guidance`、`Modern Homing Missile Guidance Theory and Techniques`、`Guidance Filter Fundamentals`、`Six-Degree-of-Freedom Digital Simulations for Missile Guidance, Navigation, and Control`；Jackson PDF 返回 `application/pdf` | Johns Hopkins University Applied Physics Laboratory；公开可读但版权归 JHU/APL | `method_reference`、`validation_criteria_reference`、`benchmark_design_reference` for homing, LOS, filters, autopilot/6DOF module boundary | `source_ref_pinned / public_page_checked` | 不给 weapon-specific seeker/noise/autopilot/airframe 参数；不得复制长文或图表；benchmark 输出仍需独立 manifest |
| `GMD-PIN-GB-003` | `GMD-SRC-008` | DOI content negotiation 核到 Springer-Verlag、DOI `10.1007/b97614`、title *Missile Guidance and Control Systems*、issued 2004 | Springer / George M. Siouris；publisher page 公开，正文版权受限 | `method_reference`、`validation_criteria_reference`、`background_only` | `source_ref_pinned / fulltext_rights_pending` | 不能作为 benchmark dataset；不从非官方 PDF 镜像摘录 |
| `GMD-PIN-GB-004` | `GMD-SRC-009`, `GEB-SRC-007` | DOI content negotiation 核到 IEEE、DOI `10.1109/TAES.1970.310128`、title *Estimating Optimal Tracking Filter Performance for Manned Maneuvering Targets*、issued July 1970 | IEEE / Robert A. Singer；题录公开，正文版权受限 | `method_reference`、`validation_criteria_reference` for maneuvering target tracking and filter/noise stress design | `source_ref_pinned / fulltext_rights_pending` | 只支持 target/process-noise/filter criteria；不是 evasion tactic、seeker truth 或 kill data |
| `GMD-PIN-GB-005` | `GMD-SRC-010`, `GEB-SRC-008` | `hdl.handle.net/10945/27627` 返回 302 到 Calhoun handle；Calhoun target page/API 在本环境超时/空响应 | Naval Postgraduate School / Calhoun；稳定 handle 可引用，具体 PDF/scan rights/hash 未固定 | `benchmark_design_reference_pending_artifact` for classical PN / miss-distance toy suite | `pending_acquisition` | 需要官方 PDF acquisition date、sha256、OCR/转录审计、scenario manifest；当前不得把图表或参数写成 acquired data |
| `GMD-PIN-GB-006` | `GMD-SRC-011`, `GEB-SRC-009` | NTIS `ADA136834` URL 在本环境返回 Cloudflare blocked page | AFIT / NTIS；官方题录路线存在于 ledger，但本轮无法核正文或下载 | `method_reference_pending_acquisition` for terminal evasion taxonomy only | `pending_acquisition` | 未获取官方全文、rights、checksum、TACTICS IV reproducibility；不得采集第三方镜像或转写数值 |
| `GMD-PIN-GB-007` | `GMD-SRC-012`, `GEB-SRC-010` | NTRS `19840020657` 页面返回 Public / Distribution 元数据；NASA STAR PDF `19840020657.pdf` 返回 `application/pdf`、content-length and ETag | NASA STAR / AFIT / NTIS；公开摘要集合可读，full thesis rights pending | `method_reference`、`benchmark_design_reference_pending_fulltext` for evasion sensitivity axes | `abstract_acquired / fulltext_pending` | NASA STAR 摘要不等于 thesis dataset；无 fulltext sha256、仿真配置或表格转录前不得生成数据包 |
| `GMD-PIN-GB-008` | `GEB-SRC-011`, `GEB-SRC-016`, `GEB-SRC-017` | NTRS records 核到 NASA-TM-109057 / `19940031931`、NACA-RM-A57F26 or NASA-MEMO-2-12-59A / `19930089891` and `19980230603`、NASA-MEMO-2-13-59A / `19980228243`，均显示 Public metadata | NASA / NACA；NTRS public record | `method_reference`、`benchmark_design_reference` for generic fly-out, glint/noise, theoretical miss-distance criteria | `source_ref_pinned / public_page_checked` | 旧式/generic/beam-rider scope；不得外推 active radar AAM、ECCM、modern BVR 或可消费运行时证据 |
| `GMD-PIN-GB-009` | `GEB-SRC-019`, `GEB-SRC-014`, `GEB-SRC-015` | DOI content negotiation 核到 AIAA / DOI metadata for Nesline-Zarchan miss-distance dynamics, Shinar-Steinberg optimal evasion, Ben-Asher-Cliff optimal evasion | AIAA；题录公开，正文版权受限 | `method_reference`、`validation_criteria_reference`；部分可做 `benchmark_design_reference_pending_fulltext` | `source_ref_pinned / fulltext_rights_pending` | DOI metadata 不能替代全文或数据；不复制 AIAA 正文、图表、公式细节或付费内容 |
| `GMD-PIN-GB-010` | `GEB-SRC-020` | BUAA article page 核到 *Miss Distance Analysis in APN Guided Radar Homing Missiles*、Ding Chibiao、Mao Shiyi、Journal of Beijing University of Aeronautics and Astronautics、1998、24(1) | BUAA journal；HTML/abstract 公开，rights per journal | `method_reference`、`validation_criteria_reference` for APN miss-distance/noise formula family | `source_ref_pinned / rights_review_needed` | 需要语言、公式转录、全文权利和 scope 审计；不作为 dataset |
| `GMD-PIN-GB-011` | `GEB-SRC-012`, `GEB-SRC-015` VT thesis route | `hdl.handle.net/10945/9385` 返回 302 到 Calhoun handle but target page timed out；VT `hdl:10919/51126` page 核到 *Optimal evasion against a proportionally guided pursuer*、Ben-Asher、Cliff、Virginia Tech | NPS / Calhoun and Virginia Tech repository；record pages public, artifacts require per-copy audit | `benchmark_design_reference_pending_artifact` for PN/CLOS/hybrid and optimal evasion design | `pending_acquisition` | Need PDF acquisition date, license/rights, sha256, OCR and Matlab/Simulink or thesis artifact manifest |
| `GMD-PIN-GB-012` | `GEB-SRC-021` | Stone Soup GitHub raw `LICENSE` 核到 MIT License；`git ls-remote` observed tag `v1.8` dereferenced commit `a890a748f937112c7c6cd827492b0b55a1d9ca6d`; main head `9a2903a2e9189182d519fa8f33bcdacf97def1f6` | UK Dstl-led open-source project；MIT License | `reproducibility_candidate` and `sanity_check_only` for filter scaffold | `source_ref_pinned / version_pin_required_per_use` | Must pin tag/commit/dependencies and output hash per benchmark; framework is not missile seeker validation data |
| `GMD-PIN-GB-013` | `GEB-SRC-018`, `GEB-SRC-013` | DLA QuickSearch and NTIS routes did not return parseable metadata in this run; Document Center route for MIL-HDBK-1211 also yielded no parseable source metadata | DoD handbook / NTIS indexed reports; official artifact access unresolved | `validation_criteria_reference_pending_artifact` only | `pending_acquisition` | Cannot use handbook/report body until official artifact, distribution statement, rights and checksum are fixed |

## Family-level admission

| family | strongest public pins | 可用于 | 不可用于 |
|---|---|---|---|
| PN / LOS-rate | `GMD-PIN-GB-001`, `002`, `005`, `009` | PN sign convention, LOS-rate, closing speed, navigation-ratio and miss-distance method criteria | modern AAM truth, runtime guidance parameter authority |
| APN / target acceleration | `GMD-PIN-GB-001`, `002`, `004`, `010` | APN admission criteria, target-acceleration estimator requirements, filter/noise sensitivity | declaring APN without estimator/filter state |
| Miss-distance dynamics | `GMD-PIN-GB-001`, `005`, `008`, `009` | closest-approach metric, lag/noise/maneuver sensitivity, dynamic fly-out comparison | 概率类杀伤、确定性触发、lethal radius or hit-probability authority |
| Terminal evasion | `GMD-PIN-GB-006`, `007`, `011`, `009` | old-scope maneuver taxonomy, timing/switching/linearized optimal evasion design | modern fighter tactic truth or direct final probability adjustment |
| Seeker / filter / noise | `GMD-PIN-GB-002`, `004`, `008`, `012` | track-quality proxy, measurement-noise/filter-lag/dropout benchmark design | ECCM, notch, clutter, decoy or seeker classified performance |
| 6DOF / fly-out architecture | `GMD-PIN-GB-002`, `008`, `013` | module-boundary checklist, state-vector/integrator/output metric design | weapon-specific aero/propulsion/autopilot database |

## Pending / not-admitted handling

| class | Examples | Current handling | Reason |
|---|---|---|---|
| NTIS full-text not reached | Straight `ADA136834`, Ball/Lee/Lewis `AD769595`, Swee `ADA378653` via NTIS | `pending_acquisition` | Official record route exists in ledger, but this environment could not verify/download artifact or rights. |
| Paywalled publisher content | AIAA, IEEE, Springer full texts | `source_ref_pinned / fulltext_rights_pending` | DOI metadata is public; body text, figures, tables and equations require lawful access and cannot be copied into repo. |
| Calhoun handle slow/unavailable after redirect | NPS `10945/27627`, `10945/9385` | `pending_acquisition` | Handle stability is useful, but official artifact hash and OCR status remain missing. |
| Non-official mirrors | third-party thesis PDFs, PDF mirrors, forums, game data | `not_admitted` | Rights, provenance, completeness and checksum chain do not satisfy source admission. |
| Generated benchmark outputs | future PN/evasion/noise sweeps | `not_generated` | Generated outputs require script/commit/config/seed/metric/hash manifest before citation. |

## Runtime authority boundary

- 所有本文件来源最高只支持 `method_reference`、`validation_criteria_reference`、`benchmark_design_reference`、`reproducibility_candidate` 或 `sanity_check_only`。
- `pending_acquisition` 条目不能向 benchmark artifact 提供已采集数据；只能作为搜索/设计线索。
- 任何后续 benchmark 包都必须另行记录 source artifact hash、scenario manifest、脚本/commit、seed、metric、output sha256、rights 和 residual。
- 本文件没有 external calibration dataset，没有 validated surrogate manifest，没有可消费运行时证据行。
