# Source Pin Update：guidance / miss-distance 公开来源

状态：`2026-05-28 source-pin / non-authoritative`。

本文档是 [source_ledger.zh.md](source_ledger.zh.md) 的补丁层，只固定公开入口、发布方、权利边界、scope、交叉验证和 residual。它不修改运行时，不创建 benchmark artifact，不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

准入继续服从：

- [公开数据来源准入标准](../../../../../standards/foundation/public_data_source_admission.zh.md)
- [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)

## 本轮核对结论

| 来源组 | 覆盖 `source_id` | 本轮固定的公开入口 | 发布方 / 权利 | 可作为 | 仍缺 / residual |
|---|---|---|---|---|---|
| Zarchan AIAA 教材 | `GMD-SRC-001`, `GEB-SRC-001` | MathWorks 书页确认 *Tactical and Strategic Missile Guidance*、Paul Zarchan、AIAA、ISBN `978-1-62410-537-1`；AIAA 课程页只作出版方/课程入口交叉 | AIAA / Paul Zarchan；正文与 companion material 受版权和平台条款限制 | `method_reference`、`validation_criteria_reference`；自实现 PN/APN/miss-distance toy benchmark 的公式和术语入口 | 不复制正文、图表、表格或 companion code；无 artifact sha256；不可作为 external calibration dataset |
| JHU/APL Technical Digest guidance family | `GMD-SRC-002` 至 `GMD-SRC-006`, `GEB-SRC-002` 至 `GEB-SRC-006` | JHU/APL 官方 article pages 和 PDF 路径返回公开页面；核对到 `Basic Principles of Homing Guidance`、`Modern Homing Missile Guidance Theory and Techniques`、`Guidance Filter Fundamentals`、`Six-Degree-of-Freedom Digital Simulations...`、`Overview of Missile Flight Control Systems` | Johns Hopkins University Applied Physics Laboratory；公开可读，JHU/APL copyright | `method_reference`、`validation_criteria_reference`、`benchmark_design_reference`；PN/LOS/filter/6DOF/autopilot module boundary | 不给 weapon-specific seeker、airframe、autopilot 或 noise 参数；不复制长文和图表；需要自生成 benchmark manifest |
| IEEE / AIAA / Springer DOI 文献 | `GMD-SRC-008`, `GMD-SRC-009`, `GEB-SRC-014`, `GEB-SRC-015`, `GEB-SRC-019` | DOI / publisher landing pages 可作为稳定 `source_ref`；AIAA DOI 页面可确认 DOI 路由；IEEE/Springer 页面可能只暴露有限元数据 | IEEE、AIAA、Springer；版权受限，只引用书目信息和少量摘要 | `method_reference`、`validation_criteria_reference`；Singer target tracking、Nesline/Zarchan miss-distance dynamics、optimal evasion criteria | 全文、公式细节、图表和表格不得从非官方镜像复制；无可再分发 dataset；artifact/hash 缺失 |
| NPS / Calhoun thesis records | `GMD-SRC-010`, `GEB-SRC-008`, `GEB-SRC-012` | `hdl.handle.net/10945/27627` 可跳转到 Calhoun handle；`hdl.handle.net/10945/9385` 作为稳定 handle 保留 | Naval Postgraduate School / Calhoun；公开记录入口，具体下载副本、OCR 和 checksum 需后续固定 | `benchmark_design_reference`；classical PN、2D/3D simplified engagement、PN/CLOS/hybrid terminal guidance | 本轮未固定官方 PDF sha256、OCR 状态或 Matlab/Simulink artifact 版本；在 hash/rights manifest 前只能做 method/design reference |
| AFIT / NTIS terminal evasion records | `GMD-SRC-011`, `GMD-SRC-012`, `GEB-SRC-009`, `GEB-SRC-010` | Straight 使用 NTIS `ADA136834` 题录入口；McNamara 使用 NASA STAR / NTRS `19840020657` 与 `AD-A136803` 摘要入口 | AFIT / NTIS / NASA STAR；NTIS 页面可能被访问控制或 Cloudflare 阻断；NASA STAR PDF 公开返回 | `method_reference`、`benchmark_design_reference_pending_artifact`；terminal jink/switching/timing taxonomy | 当前不得把第三方 PDF 镜像当 primary；full text、权利、checksum、仿真配置和表格转录均待补 |
| NASA / NACA NTRS miss-distance and fly-out records | `GEB-SRC-011`, `GEB-SRC-016`, `GEB-SRC-017` | NTRS `19940031931` 核对到 NASA-TM-109057、Public distribution；NTRS `19930089891` / `19980230603` 核对到 NACA-RM-A57F26 / NASA-MEMO-2-12-59A；NTRS `19980228243` 核对到 NASA-MEMO-2-13-59A | NASA / NACA；NTRS public record，U.S. Government public distribution metadata | `method_reference`、`benchmark_design_reference`；generic dynamic fly-out vs envelope、beam-rider/homing noise and theoretical minimum miss distance | 1950s/1990s old-scope；beam-rider/SAM/generic model 不等于 modern AAM；Pk discussion 不进入 A2 Pk authority |
| BUAA APN article | `GEB-SRC-020` | Journal page `https://bhxb.buaa.edu.cn/bhzk/en/article/id/11579` 保留为稳定 article page | Beijing University of Aeronautics and Astronautics journal；HTML/abstract 公开，rights per journal | `method_reference`、`validation_criteria_reference`；APN miss-distance formula family and radar measurement noise criteria | 语言、全文权利、公式转录和 scope 审计未完成；不作为 dataset |
| Stone Soup tracking framework | `GEB-SRC-021` | GitHub `dstl/Stone-Soup`；raw `LICENSE` 确认为 MIT；`git ls-remote` 本轮可见 tag up to `v1.8`, dereferenced commit `a890a748f937112c7c6cd827492b0b55a1d9ca6d`; main head `9a2903a2e9189182d519fa8f33bcdacf97def1f6` | UK Dstl-led open-source project；MIT License；copyright notices in license file | `benchmark_design_reference` for filter scaffold only, `reproducibility_candidate` if pinned to tag/commit | GitHub API rate-limited in this run；must pin release/tag/commit, dependency lock and local output hash before use；not missile seeker validation data |

## 来源角色修订口径

| family | 可采纳角色 | 不可采纳角色 |
|---|---|---|
| PN / LOS-rate / guidance-loop教材和论文 | `method_reference`、`validation_criteria_reference`、部分 `benchmark_design_reference` | `external_calibration_dataset`、Pk row、deterministic fuze row |
| NPS/AFIT old thesis | `benchmark_design_reference`；只有在官方全文、rights、OCR、checksum 和 scenario manifest 完整后，才能升级为 non-authoritative generated benchmark input | modern AAM truth、fighter tactic effectiveness truth、runtime calibration |
| NASA/NACA NTRS old reports | `method_reference`、`benchmark_design_reference`、old-scope fly-out/noise/miss-distance criteria | active radar seeker/ECCM truth、modern BVR validation、Pk authority |
| Stone Soup / open-source tracking code | `reproducibility_candidate` for filter scaffold and sanity checks after commit pinning | missile guidance/seeker authority、calibration dataset |

## Artifact / hash 缺口

| 缺口 | 影响 | 关闭条件 |
|---|---|---|
| `GMD-PIN-RES-001 source-artifact-hash` | 已固定 source_ref 不等于已获取可复核 artifact。 | 对每个使用的 PDF/HTML/release 记录 acquisition date、URL、sha256、license/rights、OCR/转录状态。 |
| `GMD-PIN-RES-002 generated-benchmark-manifest` | 方法来源不能直接变成 benchmark dataset。 | 自生成 benchmark 必须记录脚本、commit、dt、integrator、seed、输入参数、输出 metric、sha256。 |
| `GMD-PIN-RES-003 old-scope-modernity` | 老 thesis、NACA/NASA beam-rider 或 generic fly-out 会被误读为 modern AAM validation。 | 每个 manifest 显式标注 old/simplified/generic scope，并禁止外推到 AIM-120/AIM-9X/R-77 等型号。 |
| `GMD-PIN-RES-004 fulltext-rights` | AIAA/IEEE/Springer/NTIS/NPS 部分材料可能只有题录或受版权限制全文。 | 只引用官方入口；不复制受限正文、表格、图或第三方镜像。 |
| `GMD-PIN-RES-005 validation-independence` | 同一公开公式自实现并自检不能证明真实世界有效。 | 后续 validation report 必须区分 method implementation check、cross-check 和 external calibration；当前没有 validation pass。 |

## 拒绝项确认

| `rejection_id` | 类型 | 本轮处理 |
|---|---|---|
| `GMD-PIN-REJ-001` | 第三方教材/论文 PDF 镜像、网盘、Scribd/Studylib/PDFCoffee 类副本 | 不使用；只用 DOI、publisher、NTRS、NTIS、Calhoun、JHU/APL 官方入口。 |
| `GMD-PIN-REJ-002` | 游戏、论坛、民间 missile DB 的 fuze radius、lethal radius、Pk、命中率表 | 仍为 rejected 或 `sanity_check_only`，不得进入 benchmark design 或 descriptor。 |
| `GMD-PIN-REJ-003` | 受限工具、JMEM/JWS/J-ACE/AJEM/COVART/FASTGEN/Endgame Manager 输出 | rejected；不得摘要正文或派生参数。 |
| `GMD-PIN-REJ-004` | NASA generic fly-out report中的 Pk 表述直接转 A2 Pk | 明确拒绝；只保留 dynamic fly-out、miss-distance metric 和 test-condition comparison 思路。 |

## 后续写入要求

- 后续 benchmark 包必须引用 `source_ledger.zh.md` 中的 `source_id`，并在 manifest 中补本文件的 pin residual。
- 只要 `validation_artifact_sha256`、source artifact hash、scope manifest 或 rights 审计为空，就只能写 `candidate`、`pending` 或 `non-authoritative`。
- 若一个来源只能支持公式或术语，source kind 写 `method_reference` 或 `validation_criteria_reference`；若只支持实验形状，写 `benchmark_design_reference`。
- 不得写 `authority=true`、`validation_status=passed`、`calibration_status=calibrated` 或 calibrated runtime row。
