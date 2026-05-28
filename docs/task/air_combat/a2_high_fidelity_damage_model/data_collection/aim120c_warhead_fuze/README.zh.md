# AIM-120C-class 战斗部 / 引信公开来源收集

状态：`2026-05-28` 数据收集候选。本文只整理公开来源和准入边界，不授予 Pk、deterministic fuze、effect-scale、component-failure probability 或型号级真实战斗部/引信 authority。

本包 scope：

- weapon：`AIM-120C-class`，只按公开资料允许的 AMRAAM / AIM-120 系列量级归类；
- warhead family：`blast_fragmentation`；
- fuze evidence：公开描述中的 active-radar / proximity / target-detection-device / safe-arm 类别描述；
- method evidence：公开 blast / fragmentation 通用工程方法，作为 `validated_physics_surrogate` 的候选方法来源；
- out of scope：真实 AIM-120C 引信触发门限、TDD 信号处理、safe-arm 细节、破片质量/速度/方向分布、战斗部结构、杀伤概率和任何受限或不可再分发数据。

父目录规则：

- [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)
- [A2 Vulnerability Evidence Schema v1](../../vulnerability_evidence_schema_v1.zh.md)
- [Fuze release evidence checklist](../../fuze_authority/fuze_release_evidence_checklist_20260528.zh.md)

## 当前公开结论

公开官方/准官方材料能够支持的低风险结论：

| 主题 | 可记录结论 | 证据角色 | 当前 authority |
|---|---|---|---|
| 尺寸/质量 | AIM-120 系列公开量级约 12 ft 长、7 in 直径、340-358 lb；NAVAIR 公开页列出 C/C-4 约 348 lb、C-5/6/7 约 356 lb | `warhead_model` 的 missile envelope sanity / public metadata | `non-authoritative` |
| 战斗部类别 | AMRAAM / AIM-120 公开描述为 high-explosive blast-fragmentation / directed-fragmentation 类空空导弹战斗部 | `warhead_model.weapon_family=blast_fragmentation` candidate | `non-authoritative` |
| 战斗部大致质量 | 美国空军博物馆对其 AIM-120A 展品给出 40 lb 级 high-explosive warhead 公开描述；C 型官方公开 fact sheet 通常不给型号级战斗部质量 | AIM-120 系列 sanity / `warhead_model.public_mass_envelope` with variant caveat | `non-authoritative` |
| 引信类型 | AMRAAM 为主动雷达制导空空导弹；公开 NAVAIR/ACC/USAF 描述可支持 radar / proximity / target-detection-device 类候选 | `fuze_evidence.fuze_type_public_description` candidate | `non-authoritative` |
| C 型具体改型差异 | C-5/C-7/C-8 等公开资料对弹体、电子、TDD 或 lethality upgrade 有描述，但不足以生成型号级 fuze/warhead 参数 | residual / gap | `deferred` |

因此，当前最多可进入候选包的字段是：

| 字段 | 推荐值 / 表达 | 来源条件 | 备注 |
|---|---|---|---|
| `weapon_family` | `blast_fragmentation` | 至少一条官方/公开工程材料支持战斗部类别 | 可作为 family-level candidate，不代表 AIM-120C 真实破片云 |
| `warhead_model.public_mass_envelope` | `public_early_aim120_40_lb_class / aim120c_specific_unknown` | 只能用官方早期系列公开描述和 C 型缺口一起记录 | 不得写成 AIM-120C calibrated mass |
| `warhead_model.public_platform_envelope` | missile length / diameter / total weight 公开范围 | NAVAIR / USAF / Navy / ACC fact sheet | 只用于量级、空间尺度和 source ledger |
| `fuze_evidence.public_type` | `radar_proximity_or_target_detection_device_public_description` | NAVAIR / ACC / USAF 等公开描述 | 不得导出触发半径、SNR、delay 或可靠性 |
| `validated_physics_surrogate.method_refs` | `UFC_3_340_02`, `DDESB_TP20_BEC_O`, `UN_IATG_01_80`, `DDESB_TP15/TP16 if acquired` | 公开标准/工具/方法，可复现并有 validation manifest | 只能作为通用方法来源，不是 AIM-120C 真值 |

## 可进入候选、仅 sanity check、必须拒绝

### 可进入 `warhead_model` / `fuze_evidence` candidate

- 官方/军方公开 fact sheet 中的 AIM-120 系列尺寸、全弹质量、基本用途、主动雷达制导描述；
- NAVAIR / Navy / USAF / ACC 等公开页中对 AMRAAM active radar、all-weather、fire-and-forget、proximity/TDD 或 high-explosive blast-fragmentation 类描述；
- 有报告编号、公开发布方、Distribution Statement A 或明确公共网页的标准/工程方法，用于通用 blast / fragmentation surrogate。

写入时必须保留：

- `source_ref`；
- 发布方；
- 可公开性/权利；
- scope 匹配轴；
- 交叉验证状态；
- 不确定性和 residual；
- `authority_status=non-authoritative`，除非后续另有完整 validation manifest。

### 只能作为 `sanity_check_only`

- Wikipedia、Designations-Systems、MissileThreat、MilitaryToday、CMANO / Command DB、DCS/游戏/仿真配置、论坛汇编；
- 二手资料里的 45 lb、50 lb 战斗部质量、WDU-33/B、WDU-41/B、FZU-* 等部件号；官方早期 AIM-120 40 lb 线索仍不得外推成 C 型真值；
- 未能追溯到公开官方/标准来源的 C-variant 改型差异；
- 单点 kill radius、fuse radius、damage value、fragment count、fragment velocity 或 Pk 曲线。

这些资料只可用于问：候选量级是否明显离谱。不能单独写入 runtime descriptor row，不能授予 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。

### 必须拒绝

- 标注受限、受控、FOUO/CUI/ITAR/EAR-restricted、不可再分发或来源不清的手册、训练材料、数据库导出；
- 论坛、CMANO、游戏数据库或民间表格中的单点 fuze radius / warhead mass / damage 值作为权威；
- 无 source_ref、无发布方、无权利状态、无法审计 provenance 的截图、转帖或摘录；
- 任何可反推出 AIM-120C 真实引信触发逻辑、信号处理、safe-arm 细节、破片云、战斗部结构或杀伤概率的非公开数据。

## 通用物理 surrogate 方向

可公开通用模型只能作为 `validated_physics_surrogate` 方法候选。推荐把型号级缺口和方法模型分开：

| 机制 | 公共方法候选 | 可生成的 A2 机制字段 | 必须保留的限制 |
|---|---|---|---|
| blast | Hopkinson-Cranz / Sachs scaled distance；Kingery-Bulmash / CONWEP 类自由场爆轰关系 | `min/max_blast_scaled_distance_m_kg13`、候选 overpressure / impulse proxy | 需要装药等效 TNT 质量与环境假设；公开 AIM-120C 真值缺失 |
| fragmentation | Gurney velocity、Mott / primary fragment mass distribution、球面稀释/方向 pattern 的公开工程模型 | `min/max_fragment_energy_j`、`min/max_fragment_areal_density_per_m2` | 缺少 AIM-120C 壳体、装药、预制破片和方向性真值 |
| combined blast-frag | blast 与 fragment 两条机制并联，最终只输出 mechanism-load vector | `weapon_family=blast_fragmentation` 的 surrogate method refs | 不直接输出 Pk；必须经 validation report 和 residual closeout |

进入 `validated_physics_surrogate` 前最低要求：

- 代码/配置/参数版本固定；
- 方法来源和 benchmark 来源分离；
- `validation_manifest.schema_version=a2.vulnerability_surrogate_validation.v1`；
- benchmark ref、metrics ref、acceptance criteria ref 非空；
- validation scope 逐项匹配 target / weapon family / aspect / closure / miss-distance；
- validation artifact sha256 非空；
- residual register 明确列出 AIM-120C 型号级 warhead/fuze 未知项。

## 公开可信缺口

当前公开来源无法关闭：

- AIM-120C 具体战斗部型号、装药质量、TNT 等效、壳体/预制破片设计、破片数量/质量/速度/方向分布；
- C-variant 之间战斗部和 TDD 的具体差异；
- 引信 arming、radar proximity/TDD 触发门限、目标特征处理、delay、可靠性、false/missed trigger；
- 对 F-16C Block 50 的型号级 component fragility、conditional failure probability、mission-kill/Pk；
- 近炸几何与真实 detonation point error / timing error 的校准数据。

因此，本包结论应作为“公开候选来源台账”，而不是 warhead/fuze 校准数据包。

## 文件

- [source_ledger.zh.md](source_ledger.zh.md)：逐条候选来源、sanity check 和拒绝记录。
- [source_pin_update_20260528.zh.md](source_pin_update_20260528.zh.md)：本轮 source pin、字段级支持边界和 warhead/fuze authority gap 更新。
