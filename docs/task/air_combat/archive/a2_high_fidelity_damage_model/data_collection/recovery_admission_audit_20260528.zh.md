# A2 数据收集回收与准入审计 - 2026-05-28

状态：`recovered / admission-audit / non-authoritative`。本文档审计 A2 高保真空战毁伤模型的公开来源收集包是否遵守 [公开数据来源准入标准](../../../../standards/foundation/public_data_source_admission.zh.md) 与 [A2 数据来源准入规则](source_admission_rules_20260528.zh.md)。它不创建 runtime descriptor，不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

## 审计结论

当前九个数据包均为 `candidate / non-authoritative`。它们可以作为 source ledger、method reference、benchmark design、validation criteria、reproducibility 或 residual register 的候选输入；没有任何包满足 runtime authoritative descriptor 的完整条件。

本轮审计未发现应被理解为运行时授权的结论。文档中出现 `calibrated`、`Pk`、`deterministic fuze`、`effect-scale` 或 `component-failure probability` 时，均用于说明禁止项、缺口、门控边界或未来 residual，不是当前放行。

## 包级审计

| 包 | 文件 | 准入字段覆盖 | 可支持 | 不能支持 |
|---|---|---|---|---|
| [f16c_block50_target_geometry](f16c_block50_target_geometry/README.zh.md) | README + source ledger | source_ref、发布方、权利、Tier、scope、交叉验证、residual、admission/authority 已记录 | F-16 低精度外形、总质量/总燃油量级、粗组件区和工程缺口 | 内部结构、材料、装甲、油箱分隔、线束/管线、组件失效概率 |
| [aim120c_warhead_fuze](aim120c_warhead_fuze/README.zh.md) | README + source ledger | source_ref、发布方、权利、scope、residual、拒绝项已记录 | AIM-120 系列公开尺寸/质量量级、blast-fragmentation family、active radar/TDD 术语 | AIM-120C 真实装药、破片数/速度/方向图、真实引信参数、Pk |
| [mechanism_model_public_methods](mechanism_model_public_methods/README.zh.md) | README + source ledger | 公开方法、权利、scope、交叉验证和拒绝项已记录 | Hopkinson-Cranz/Sachs、Mott/Gurney、BLE、连续杆等方法候选 | 直接生成 calibrated component row 或杀伤概率 |
| [component_fragility_vulnerability](component_fragility_vulnerability/README.zh.md) | README + source ledger | 方法来源、拒绝清单、residual 和 schema 边界已记录 | component kill criteria、validation criteria、component-fragility 方法 | JMEM/J-ACE/AJEM/COVART 数据、真实组件概率 |
| [guidance_miss_distance_public_methods](guidance_miss_distance_public_methods/README.zh.md) | README + source ledger | guidance/miss-distance 来源、权利、scope 和拒绝项已记录 | PN/APN、miss-distance、seeker/filter benchmark 候选 | 现代 AAM Pk、真实制导性能或确定性引信 |
| [f16c_material_fuel_fire_systems](f16c_material_fuel_fire_systems/README.zh.md) | README + source ledger | 24 条公开候选记录 source_ref、发布方、权利、Tier、scope、交叉验证、residual 和 authority | 燃油火灾机制轴、材料防火测试、engine/dry-bay fire、系统依赖和 damaged-aircraft consequence | Block 50 真实材料、油箱、管线、线束、engine bay/dry bay layout、防火系统参数 |
| [vps_blast_fragmentation_methods](vps_blast_fragmentation_methods/README.zh.md) | README + source ledger + benchmark matrix | source_ref、权利、Tier、pending_acquisition、benchmark/residual 和 authority 边界已记录 | blast-fragmentation mechanism-load surrogate 方法和 toy benchmark 设计 | AIM-120C 真实战斗部、F-16C 真实组件概率、Pk、确定性引信 |
| [component_fragility_benchmark_methods](component_fragility_benchmark_methods/README.zh.md) | README + source ledger + schema mapping | source_ref、发布方、权利、Tier、scope、交叉验证、residual 和 rejected list 已记录 | component kill criteria、failure probability surrogate benchmark、redundancy/dependency validation | calibrated component probability rows、真实 F-16C Pcd|h、JMEM/COVART 数据 |
| [guidance_evasion_benchmark_methods](guidance_evasion_benchmark_methods/README.zh.md) | README + source ledger + benchmark matrix | source_ref、权利、Tier、scope、benchmark role、residual 和拒绝项已记录 | PN/APN、terminal evasion、seeker/filter、6DOF/fly-out benchmark 组合 | 现代空空导弹 Pk、真实引信触发、ECCM/notch/clutter/decoy 性能 |

## Pending / Residual 汇总

| residual | 影响 | 当前处理 |
|---|---|---|
| F-16C Block 50 内部材料、油箱、防火、液压、电气、飞控 routing 缺公开来源 | 阻止 target-specific material/fire/dependency authority | 只保留 generic method 和 consequence candidate |
| AIM-120C 真实战斗部、破片场、引信 trigger/safe-arm/reliability 缺公开来源 | 阻止 warhead/fuze/Pk/deterministic-fuze authority | 只保留 family-level 和术语来源 |
| Kingery-Bulmash、Gurney、DDESB/BEC-O 等部分方法来源仍需官方版本、rights、checksum 固定 | 阻止 blast-frag benchmark 进入 acquired input | 标为 `pending_acquisition`，不得消费为已采集数据 |
| NASA/FAA/NIST/FOI 等来源多为民用、通用或方法性 scope | 阻止外推到 fighter target-specific fragility | 明确 `generic-aircraft` / `civil-transport` / `method-only` |
| 公开 component fragility calibration dataset 缺失 | 阻止 `external_calibration_dataset` | 只做 schema/method/benchmark design |
| benchmark artifact hash、生成脚本、验收阈值尚未冻结 | 阻止 `validated_physics_surrogate` | 后续需 validation manifest、seed、checksum、metric 和 reviewer notes |
| Pk 和 deterministic fuze 缺独立 kill-chain admission manifest | 阻止 Pk / deterministic fuze authority | 继续 deferred，不由 vulnerability descriptor 或 data collection 放行 |

## 拒绝来源覆盖

各包共同拒绝或降级以下来源类型：

- F-16 technical order、维修/结构/IPB/接口手册镜像、论坛附件、网盘 PDF；
- 受限、FOUO、CUI、ITAR、EAR、leaked、承包商附件或不可再分发材料；
- JMEM、JWS、J-ACE、JAAM、AJEM、COVART、FASTGEN、SLATE、ACEL、Endgame Manager、BlueMax 等受控工具或底层数据；
- CMANO/CMO DB、DCS、War Thunder、游戏配置、论坛、民间 missile/weapon DB；
- 第三方教材/论文 PDF 镜像、Scribd/Studylib/PDFCoffee 等非官方副本；
- 匿名 Pk 曲线、hit probability 表、lethal radius、fuse radius、damage scalar、战损照片或新闻叙述。

这些来源可记录拒绝原因或在明确隔离下用于 sanity check，但不得作为 `source_ref` 写入 calibrated row。

## 下一步入口

1. 先把 `vps_blast_fragmentation_methods` 中的 pending sources 固定为官方公开版本，或明确排除。
2. 为 `BFM-BM-001..006` 建立 `validation_manifest` 草案，保持 `validation_status=not_run`。
3. 将 guidance/evasion benchmark 从文档候选推进到自生成 toy benchmark manifest，记录 seed、dt、metric、checksum。
4. 将 component fragility benchmark 方法用于 schema/residual 设计，不创建真实 probability row。
5. 所有后续运行时接入必须回到 [公开数据来源准入标准](../../../../standards/foundation/public_data_source_admission.zh.md) 的 authority gate 规则。
