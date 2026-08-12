# A2 guidance / evasion benchmark 公开候选来源续收集

状态：`2026-05-28 data-collection / benchmark-methods-only / non-authoritative`。

本目录继续收集 A2 guidance、miss-distance 与 terminal evasion benchmark 的公开候选来源。它只服务于可复现实验设计、validation criteria 和后续 benchmark manifest；不新增运行时代码，不放行 deterministic fuze，不授予真实 Pk、effect-scale 或 component-failure probability authority。

本目录必须与以下仓库准则共同使用：

- [source_admission_rules_20260528.zh.md](../source_admission_rules_20260528.zh.md)
- [guidance_miss_distance_evasion_evidence_route_20260528.zh.md](../../guidance_miss_distance/guidance_miss_distance_evasion_evidence_route_20260528.zh.md)
- [guidance_miss_distance_public_methods](../guidance_miss_distance_public_methods/README.zh.md)
- [benchmark_gap_update_20260528.zh.md](benchmark_gap_update_20260528.zh.md)

## 本轮结论

公开材料可以支撑的最高等级仍是 `benchmark_dataset_candidate`、`validation_criteria_candidate` 和 `reproducibility_candidate`。更具体地说：

- PN/APN 教材、JHU/APL 文章、AIAA 论文和 NPS/AFIT 论文能支持 guidance-law、LOS-rate、target-acceleration、autopilot lag、miss-distance sensitivity 的 benchmark 设计。
- NASA/NACA、NTIS、MIL-HDBK 和 JHU/APL 的公开材料能支持 seeker/filter/noise、6DOF module boundary、dynamic fly-out vs launch-envelope 的 validation criteria。
- Shinar/Steinberg、Ben-Asher/Cliff、Straight、McNamara、Swee、Lukenbill 等公开记录能支持 terminal evasion maneuver taxonomy、timing sweep 和 miss-distance metric。
- Stone Soup 等开源 tracking framework 可作为可复现 filter benchmark scaffold，但只能做工具或 sanity check，不能成为导弹性能或杀伤 authority。

没有任何本轮来源可直接进入 A2 runtime authoritative descriptor。所有结论默认 `non-authoritative`。

## 推荐 benchmark 组合

| 组合 | 候选来源 | 主要用途 | 可声明 | 不可声明 |
|---|---|---|---|---|
| `pn_classical_miss_distance_v1` | Zarchan、JHU/APL Basic、Nesline/Zarchan、Lukenbill、NASA/NACA miss-distance 备忘录 | 2D/3D PN toy benchmark；LOS-rate、closing speed、time-to-go、autopilot lag、accel saturation 对 miss distance 的影响 | `benchmark_dataset_candidate`、`validation_criteria_candidate` | 现代 AAM 参数、真实 Pk、近炸引信确定触发 |
| `apn_target_accel_v1` | JHU/APL Modern、Zarchan、Ding/Mao APN、Singer tracking model | APN/optimal guidance 与 target acceleration estimate 的准入条件 | APN criteria、target-accel estimator residual | 没有 estimator 时声明 APN；现代武器制导律 |
| `terminal_evasion_sweep_v1` | Shinar/Steinberg、Ben-Asher/Cliff、Straight、McNamara、Swee、Lukenbill | constant turn、switch/jink、bang-bang、roll-rate bound、9-g target maneuver、timing sensitivity | 老式/简化 terminal evasion miss-distance benchmark | 现代 fighter tactic 有效性、AIM/R 系 Pk |
| `seeker_filter_noise_v1` | JHU/APL Guidance Filter、Singer、NASA beam-rider glint/noise、Stone Soup | bearing/range/elevation noise、filter tau、track dropout、covariance、glint/noise sensitivity | filter/noise validation criteria 和可复现 scaffold | ECCM、notch、clutter、decoy 真实性能 |
| `sixdof_flyout_arch_v1` | JHU/APL 6DOF、NTIS AD769595、MIL-HDBK-1211、NASA generic air-to-air model、Jackson flight-control | 6DOF module boundary、actuator/autopilot high-low fidelity、dynamic fly-out vs static envelope | simulation architecture criteria、output metric checklist | 武器型号级气动/推进/制导数据库 |
| `a2_internal_geometry_bridge_v1` | A2 当前 P0 guidance matrix + 上述公开方法 | head-on、tail-chase、beam、high-off-boresight 的内部回归与外部方法口径对齐 | internal reproducibility bridge | 外部验证数据或 calibrated authority |

## Benchmark 准入边界

| evidence role | 可进入内容 | 必须保留的限制 |
|---|---|---|
| `benchmark_dataset` | 公开论文/报告中的简化场景描述，或根据公开方程和合法代码自生成的 toy dataset | 记录 source_ref、参数范围、dt、integrator、seed、metric、checksum；论文表格/图不能未经权利审计复制入仓 |
| `validation_criteria` | PN/APN、filter、autopilot、6DOF、evasion timing、noise sensitivity 的验收准则 | criteria 不能替代 calibration data |
| `reproducibility` | DOI、handle、NTRS/NTIS/Calhoun record、代码版本、环境和生成脚本 | reproducibility 只证明实验可重跑，不证明真实导弹性能 |
| `sanity_check` | 开源 tracking/missile toy code、论坛/游戏模型、第三方 PDF 镜像 | 只能帮助发现 sign convention、单位或边界错误 |

## 明确禁止

- 不把教材公式、论文示例、开源仿真或论坛/游戏模型直接提升为 Pk。
- 不把 miss-distance threshold、lethal radius、fuse radius 或 hit probability 表当作 deterministic-fuze authority。
- 不把 NASA generic model 中的 Pk 讨论转写成 A2 Pk；本目录只采纳其 dynamic fly-out、miss-distance metric 和 test-condition comparison 思路。
- 不把 old thesis、beam-rider、SAM handbook 或 simplified 2D benchmark 外推为 AIM-120、AIM-9X、R-77 等现代型号事实。
- 不复制受版权保护的教材、AIAA/Springer/Sage 正文、图表、companion code 或第三方镜像 PDF。

## 后续数据包要求

每个后续 benchmark 包至少应包含：

- `source_refs`: 指向 [source_ledger.zh.md](source_ledger.zh.md) 中的 source_id。
- `rights`: 公开性、许可证、再分发限制。
- `scope`: guidance law、target maneuver、seeker/filter、autopilot/6DOF、miss-distance metric 的适用范围。
- `scenario_manifest`: 初始几何、速度、目标机动、noise/dropout、dt、integrator、seed。
- `outputs`: truth min distance、runtime proximity min distance、time of closest approach、LOS/range/filter state、commanded/achieved acceleration、fuze/effects evidence。
- `cross_validation`: 至少一个 Tier A/B 方法来源与一个 A2 internal regression 或独立实现交叉。
- `residual`: 权利、scope、现代性、缺少全文、缺少真实参数、缺少 external calibration data 等未关闭项。

## 当前 residual

| residual | 影响 | 关闭条件 |
|---|---|---|
| `RES-GEB-001 no-public-modern-aam-pk` | 不能授权真实 Pk 或 deterministic fuze。 | 获得公开、scope 匹配、权利明确、带 validation manifest 的外部校准数据。 |
| `RES-GEB-002 old-simplified-benchmark-scope` | NACA/NASA/AFIT/NPS/NTIS 老材料多为 2D、beam-rider、SAM 或简化 terminal homing。 | 每个 benchmark manifest 明确 old/simplified scope，不外推现代 BVR。 |
| `RES-GEB-003 full-text-rights` | AIAA、Springer、Sage、部分 NTIS 正文可能受限或需合法获取。 | 只记录 source_ref 和摘要；获取全文后记录 checksum 和 rights，不复制受限内容。 |
| `RES-GEB-004 seeker-ecm-gap` | 公开 filter/noise 来源不足以校准 clutter、notch、decoy、ECCM。 | 另开 ECM evidence gate；本目录只做 track-quality proxy benchmark。 |
| `RES-GEB-005 reproducible-output-gap` | 来源多数提供方法，不提供可直接入仓的数据集。 | 后续自生成 benchmark dataset，附脚本、seed、hash 和审计报告。 |
