# Benchmark Gap Update：PN/APN / miss-distance / terminal evasion / seeker-filter

状态：`2026-05-28 benchmark-gap / non-authoritative`。

本文档补充 [source_ledger.zh.md](source_ledger.zh.md) 与 [benchmark_matrix.zh.md](benchmark_matrix.zh.md) 的 gap 判断。它只定义 method/reference 与 benchmark design 的准入边界，不生成 artifact，不运行验证，不授予 runtime authority。

## Family 判定

| family | 可作为 `method_reference` | 可作为 `benchmark_design_reference` | 仍缺内容 | 当前最高结论 |
|---|---|---|---|---|
| PN / classical homing | `GEB-SRC-001/002/019`；Zarchan、JHU/APL Basic、Nesline/Zarchan | `GEB-BM-001`, `GEB-BM-002` 可用 Lukenbill / NASA generic fly-out 形状交叉 | 统一 sign convention、LOS-rate 输出、truth min-distance interpolation、self-generated artifact sha256 | 可设计 PN toy benchmark；不能声明 modern AAM validation |
| APN / target acceleration | `GEB-SRC-003/007/020/001`；JHU/APL Modern、Singer、Ding/Mao、Zarchan | `GEB-BM-003` 仅在 target acceleration estimate / filter state 被显式记录时可推进 | target-accel estimator manifest、filter covariance/proxy、APN vs biased-PN 命名审计 | 可写 APN admission criteria；没有 estimator 时不得称 APN |
| Miss-distance dynamics | `GEB-SRC-001/011/016/017/019`；Zarchan、NASA-TM-109057、NACA/NASA memos、Nesline/Zarchan | `GEB-BM-001/002/008/011` | closest approach substep/interpolation residual、dynamic fly-out test grid、reason-for-miss taxonomy、output hashes | 可做 method and metric benchmark；不能导出 Pk |
| Terminal evasion | `GEB-SRC-009/010/012/014/015/008`；Straight、McNamara、Swee、Shinar/Steinberg、Ben-Asher/Cliff、Lukenbill | `GEB-BM-004/005/006`，只限 simplified/old-scope maneuver timing sweep | AFIT/NTIS/NPS fulltext acquisition、rights、OCR、scenario parameter manifest、old-scope flag | 可设计 terminal evasion sweep；不得声明现代战术有效性 |
| Seeker / filter / noise | `GEB-SRC-004/007/016/017/021`；JHU/APL Guidance Filter、Singer、NASA/NACA glint/noise、Stone Soup scaffold | `GEB-BM-007/009` | noise distributions、sample rate、filter tau、dropout/memory manifest、commit/dependency pin、artifact hash | 可做 track-quality proxy benchmark；不能声明 ECM/ECCM/notch/clutter truth |
| 6DOF / dynamic fly-out architecture | `GEB-SRC-005/006/011/013/018`；JHU/APL 6DOF/Jackson、NASA generic AAM、AD769595、MIL-HDBK-1211 | `GEB-BM-010/011` | AD769595/MIL-HDBK artifact and rights, module manifest, state vector, integrator, output metric list | 可做 architecture checklist；不能声明 weapon-specific aero/propulsion/guidance truth |

## Benchmark 包最小状态

| package | 推荐来源 | 允许产物 | 必须补齐后才能生成 benchmark artifact | 明确禁止 |
|---|---|---|---|---|
| `pn_classical_miss_distance_v1` | `GEB-SRC-001/002/008/011/019` | non-authoritative generated toy dataset；PN implementation and miss-distance criteria | scenario manifest、dt/integrator、navigation ratio sweep、truth vs runtime min distance、seed、sha256、source artifact hash | 真实 Pk、型号级命中包线 |
| `apn_target_accel_v1` | `GEB-SRC-003/007/020/001` | APN admission criteria and estimator stress test | target acceleration process、measurement model、filter state/covariance/proxy、APN naming check | 没有 estimator 时写 APN；把 target maneuver 直接转 Pk |
| `terminal_evasion_sweep_v1` | `GEB-SRC-009/010/012/014/015/008` | constant-turn、jink/switch、bang-bang、roll-rate bound、9-g target maneuver timing sweep | official fulltext/abstract boundary、rights、OCR、scenario axes、old-scope label、hash | 现代 fighter tactic truth、AIM/R series Pk |
| `seeker_filter_noise_v1` | `GEB-SRC-004/007/016/017/021` | bearings/range/elevation noise, filter tau, dropout, track memory benchmark | Stone Soup or A2 commit pin、dependency lock、noise distribution manifest、track state output、sha256 | ECCM、notch、clutter、decoy真实性能 |
| `dynamic_flyout_vs_envelope_v1` | `GEB-SRC-011/005/018` | dynamic fly-out vs static envelope comparison criteria | test grid, launch conditions, reason-for-miss categories, compute-cost note, output metric hash | NASA generic Pk 直接转 A2 Pk |
| `sixdof_module_boundary_v1` | `GEB-SRC-005/006/013/018` | module checklist and output metric schema | official artifact pin for AD769595/MIL-HDBK if used, module boundary table, state vector and integrator manifest | 具体导弹气动/推进数据库 |

## Source kind 映射

| source kind | 可包含 | 本目录示例 | authority 边界 |
|---|---|---|---|
| `method_reference` | 方程族、术语、建模结构、metric 定义 | Zarchan、JHU/APL、Singer、Nesline/Zarchan、NASA/NACA memos | 不能单独变成 dataset 或 row |
| `validation_criteria_reference` | 应检查的状态量和残差轴 | LOS-rate、closing speed、commanded/achieved acceleration、filter covariance/proxy、miss-distance interpolation | 不能写 validation passed |
| `benchmark_design_reference` | 可复现实验形状、scenario axes、toy benchmark structure | Lukenbill、Swee、NASA-TM-109057、NACA/NASA beam-rider/homing memos | 只有生成脚本、manifest 和 hash 完整后才有 artifact |
| `reproducibility_candidate` | commit/tag、license、dependency and command route | Stone Soup pinned tag/commit；A2 internal harness | 只证明可复跑，不证明真实性 |
| `sanity_check_only` | 开源 toy、论坛、游戏、第三方镜像 | sign convention / unit sanity check | 不进入 source ledger acquired inputs |

## Gap register

| `gap_id` | 影响范围 | 当前状态 | 关闭条件 |
|---|---|---|---|
| `GEB-GAP-001 source-artifact-pin` | all packages | source_ref 多数已有，artifact sha256 多数为空 | 每个使用来源固定 acquisition date、official URL、sha256、rights、OCR/转录状态 |
| `GEB-GAP-002 benchmark-output-hash` | all generated packages | 未生成 non-authoritative outputs | 输出路径、manifest、metrics、random seed、sha256 和 reviewer note 完整 |
| `GEB-GAP-003 validation-independence` | PN/miss-distance/APN | 同源公式自实现不能做独立 validation | 区分 unit check、cross-check、external validation；没有外部校准数据时保持 candidate |
| `GEB-GAP-004 fulltext-rights` | AFIT/NPS/AIAA/IEEE/Springer/NTIS | 部分只有题录、摘要或付费全文 | 只用官方入口；获取合法全文后记录 rights/hash；不使用镜像正文 |
| `GEB-GAP-005 seeker-ecm-gap` | seeker/filter/noise | 公开来源支持 track/noise proxy，不支持 ECM/ECCM | 另开 ECM evidence gate；本包只输出 track state and filter residual |
| `GEB-GAP-006 apn-estimator-gap` | APN | 当前 benchmark 设计尚未固定 target-accel estimator | manifest 中存在 target acceleration estimate、filter state 或等价模型后，才允许写 APN |
| `GEB-GAP-007 terminal-evasion-old-scope` | terminal evasion | old thesis / linearized 2D / simplified PN scope | 每个 scenario 写 old/simplified validity flag，不外推 modern BVR |
| `GEB-GAP-008 runtime-authority-deferred` | all | 本目录没有 validated surrogate 或 external calibration dataset | 未来另行通过 A2 authority gate；当前所有 rows remain non-authoritative |

## Matrix 修订说明

- `GEB-BM-001` 到 `GEB-BM-003` 可优先推进为 generated toy benchmark，但 source kind 应写 `method_reference` + `benchmark_design_reference`，不是 `benchmark_dataset` 已采集完成。
- `GEB-BM-004` 到 `GEB-BM-006` 的 evasion 包必须先关闭 `GEB-GAP-004` 与 `GEB-GAP-007`；否则只允许写 maneuver taxonomy 和 timing axes。
- `GEB-BM-007` 和 `GEB-BM-009` 可使用 Stone Soup 或 A2 harness 做 filter scaffold；必须 pin tag/commit/dependency，不得把 scaffold 写成 seeker truth。
- `GEB-BM-010` 与 `GEB-BM-011` 的 NASA/MIL-HDBK/NTIS 来源只能支持 architecture and metric checklist；不得生成 weapon-specific 6DOF truth。
- `GEB-BM-012 a2_effects_bridge` 只能消费 miss distance、closure、fuze evidence 和 DamageReport 字段；不得把 threshold 或 compatibility hit probability 变成 deterministic fuze authority。
