# Public Source Pin Integration：guidance / miss-distance / evasion

状态：`2026-05-28 integration-note / evidence-route-only / non-authoritative`。

本文档把数据收集目录中的公开 source pin 和 benchmark gap 更新接入本 evidence route。它不修改 C++/Python/runtime/config，不运行 benchmark，不放行 deterministic fuze，也不声明已有 Pk authority。

## 读法

| 文档 | 用途 | 最高可支持结论 |
|---|---|---|
| [guidance_miss_distance_public_methods/source_ledger.zh.md](../data_collection/guidance_miss_distance_public_methods/source_ledger.zh.md) | guidance、miss-distance、terminal evasion、seeker/filter/noise 的候选来源台账 | source candidate / method and criteria |
| [source_pin_update_20260528.zh.md](../data_collection/guidance_miss_distance_public_methods/source_pin_update_20260528.zh.md) | 固定本轮核对到的官方入口、发布方、权利、scope 和 residual | `method_reference`、`validation_criteria_reference`、`benchmark_design_reference` |
| [guidance_evasion_benchmark_methods/source_ledger.zh.md](../data_collection/guidance_evasion_benchmark_methods/source_ledger.zh.md) | PN/APN、miss-distance、evasion、seeker/filter、6DOF/fly-out 公开候选 | benchmark method candidate |
| [benchmark_matrix.zh.md](../data_collection/guidance_evasion_benchmark_methods/benchmark_matrix.zh.md) | 把来源映射到可复现实验设计 | generated benchmark plan only |
| [benchmark_gap_update_20260528.zh.md](../data_collection/guidance_evasion_benchmark_methods/benchmark_gap_update_20260528.zh.md) | 说明各 benchmark family 的 artifact/hash/validation 缺口 | gap register / no runtime authority |

## Evidence route 接入点

| evidence-route area | 可接入来源角色 | 需要输出字段 | 不允许 |
|---|---|---|---|
| PN / LOS baseline | Zarchan、JHU/APL Basic、Nesline/Zarchan、Lukenbill / NASA generic fly-out as design reference | LOS angle/rate、closing speed、navigation ratio、commanded/achieved acceleration、truth/runtime min distance | 把 PN 公式写成 calibrated AAM guidance truth |
| APN / target maneuver | JHU/APL Modern、Singer、Ding/Mao、Zarchan as method/reference | target acceleration estimate、filter state/covariance/proxy、time-to-go、estimator residual | 没有 estimator 时声明 APN |
| Terminal evasion | Straight、McNamara、Swee、Shinar/Steinberg、Ben-Asher/Cliff、Lukenbill as old-scope design references | maneuver start time、switch time、target achieved g/roll-rate, miss-distance delta、old-scope flag | 直接乘 final Pk 或声明现代战术有效性 |
| Seeker/filter/noise | JHU/APL Guidance Filter、Singer、NASA/NACA glint/noise、Stone Soup pinned scaffold | measurement noise、sample rate、filter tau、track dropout、memory timeout、covariance/proxy、miss distance | ECCM/notch/clutter/decoy truth |
| Dynamic fly-out / 6DOF architecture | JHU/APL 6DOF/Jackson、NASA-TM-109057、AD769595/MIL-HDBK pending artifacts | module manifest、state vector、dt/integrator、commanded vs achieved response、reason-for-miss | weapon-specific aero/propulsion database |
| Fuze/effects bridge | A2 internal event fields + public miss-distance criteria | miss_distance_m、closure、local detonation point、fuze type/signature/quality、warhead footprint evidence、DamageReport | deterministic fuze authority or Pk authority |

## Gate posture

| gate | 当前状态 | 原因 |
|---|---|---|
| `source_ref` | partially pinned | 官方入口、DOI、NTRS、handle、GitHub repo/tag 已有一批稳定引用。 |
| `rights` | partially pinned | JHU/APL、NASA/NACA、MathWorks/AIAA、Stone Soup license 等已记录公开性；AIAA/IEEE/Springer/NTIS/NPS fulltext rights 仍需逐 artifact 固定。 |
| `scope` | documented old/simplified/generic | 多数来源是教材、old thesis、beam-rider、SAM handbook 或 generic fly-out；不能外推 modern AAM。 |
| `artifact_sha256` | missing | 本轮未下载并保留 canonical artifacts；未生成 benchmark outputs。 |
| `validation_manifest` | missing | 没有冻结 metrics、acceptance criteria、reviewer notes 或 output hash。 |
| `runtime authority` | closed | 没有 external calibration dataset 或 validated physics surrogate；不得写 authority row。 |

## Integration notes

- 当前 A2 evidence route 可以继续使用这些来源来强化 G1-G3 的 method/benchmark 设计：geometry PN、seeker/track、energy maneuver 和 miss-distance chain。
- G4 fuze-warhead bridge 只能消费 miss distance、closure 和 event evidence；source pin 不改变 deterministic fuze deferred 的状态。
- G5 calibrated BVR 仍 blocked by data：没有公开、scope 匹配、权利明确、带 validation manifest 的 external calibration dataset 或 validated surrogate。
- 后续若生成 benchmark 包，必须把 source ledger id、source pin residual、scenario manifest、script/commit、seed、metric、sha256 和 rights 一起写入；只跑出数值不构成 validation。
