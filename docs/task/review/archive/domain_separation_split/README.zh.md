# 域分离大拆分

状态：`2026-06-10` archived accepted integration surface，用于直接推进 Air / Naval / Ground 域拆分；本轮不保留旧 domain-split 兼容入口。

语言：

- 英文规范页：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- [审查任务区](../../README.zh.md)
- [域分离现状审计 2026-06-09](../../domain_separation_audit_20260609.zh.md)
- [子项目创建标准](../../../../agent/rules/subproject_creation_standard.zh.md)
- [文档权威图](../../../../agent/rules/document_authority_map.zh.md)
- [标准总览](../../../../standards/README.zh.md)
- [源码层级地图](../../../../manual/reference/src_layer_map.zh.md)

## 目的

本子项目把 2026-06-09 的域分离审计转成可持续执行的“大拆分”表面。本工作不再以
“先做某个示范域”为前置门槛，而是直接围绕 `components/`、`systems/`、`models/`
三层拆分 Air、Naval、Ground 和 common 的所有权。

该工作会跨组件 schema、ECS system、model routing、已退役公开路径、测试和文档，因此必须拆成有限任务簇，并明确 write set 与验收门槛。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 审计基线 | active input | [domain_separation_audit_20260609.zh.md](../../domain_separation_audit_20260609.zh.md) | 审计事实是输入，不是实现证明。 |
| Air system ownership | pass | `src/systems/domains/air/`、`src/components/domains/air/platform/`；旧 physics/tuning 路径已退役 | runtime/tuning owner 已拆分；generic physics/logistics 通过 `components/physics/propulsion_readouts.h` 读取 propulsion 指标，不再消费 Air system helper。 |
| Combat damage component | pass | `src/components/combat/{common,air,naval,ground}/damage_*.h`；`src/components/combat/damage.h` 已退役 | consumer 直接 include owner header；Ground damage 仍是 ownership shell，不是完整 runtime 声明。 |
| Combat damage system | pass | `src/systems/combat/damage_system_{common,air,naval,ground}.h`；`src/systems/combat/damage_system.h` 已退役 | kernel 直接注册 common、air、naval、ground registrar；Ground damage system 仍是 no-op placeholder。 |
| Weapon component | pass | `src/components/combat/{common,air,naval,ground}/weapon_*.h`；`src/components/combat/weapon.h` 已退役 | consumer 直接 include owner header；Ground weapon 仍是 ownership shell。 |
| Platform system | pass | `src/systems/domains/naval/naval_logistics_system.h`、`src/systems/systems/logistics_system.h`、`src/components/physics/propulsion_readouts.h` | Naval underway resupply 已抽出；Air propulsion readout 不再通过 Air system helper 暴露。 |
| Model layer | pass | `src/models/weapons/detail/default_effects_domain_routing_detail.inc`、`src/models/domains/air/default_effects_air_domain.h`、`src/models/domains/naval/naval_sensor_maritime_adapter.h` | effects 与 sensor ship-specific ownership 已通过 domain helper 路由；Naval/Ground effects 仍是 placeholder。 |
| Architecture guards | pass | `tests/architecture/structural_boundaries/test_structural_guardrails.py`、`tests/architecture/compatibility_quarantine/test_guard_enforcement.py` | 聚焦退役路径 guard、完整 structural-boundary guard 与 compatibility quarantine 均通过。 |

## 范围

范围内：

- 将 common、air、naval、ground damage 类型迁入 owner header 后，退役 `components/combat/damage.h`，但不借此宣称新增完整域真实性。
- 将 common routing 与 air/naval/ground update path 迁入 owner system header 后，退役 `src/systems/combat/damage_system.h`。
- 将 common、air、naval、ground weapon 类型迁入 owner header 后，退役 `components/combat/weapon.h`。
- 将 air-only runtime system 与 tuning 迁到 `systems/domains/air`、`components/air`，consumer 改为直接使用 owner 路径后删除旧 `physics` include 路径。
- 从 generic platform/model 文件中抽出 naval-specific logistics 和 sensor 依赖。
- 为 effects/sensor 建立 model-layer domain routing，并写清 common、air、naval、ground ownership 边界。
- 增加架构守卫和聚焦 runtime/build 验证。

范围外：

- 把 Naval 作为全局示范域前置门槛。
- 仅因存在 owner 目录或骨架 struct 就宣称完整 Ground movement、sensing、fires 或 damage runtime。
- 重新平衡武器杀伤、飞行动力学、海军生存性或训练行为，除非为保持拆分前行为必须。
- 删除本审计包之外的无关历史兼容表面。
- 归档或重写无关 review/task 记录。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 固化权威、非目标与任务簇。 | 审计已存在。 | README、状态、队列和任务簇计划存在。 | pass |
| `P1 Components` | 拆分 damage 与 weapon component ownership。 | P0 文件存在。 | common/air/naval/ground 头文件可编译，旧公开聚合头已删除。 | pass |
| `P2 Systems` | 拆分 ECS system ownership。 | P1 component surface 可编译。 | damage、air、naval logistics 与 propulsion readout ownership 已分离，不保留旧公开 wrapper。 | pass |
| `P3 Models` | 按域路由 default effects 和 sensor 行为。 | P1/P2 surface 存在。 | generic model 文件不再直接拥有 domain-only struct 依赖，除非通过 router/adapter。 | pass |
| `P4 Validation` | 增加并运行 build、runtime、architecture guard。 | 实现簇落地。 | 聚焦检查通过，残余风险记录。 | pass |
| `P5 Closure` | 同步文档、索引和退役路径说明。 | P4 evidence 存在。 | acceptance 文件更新，且不夸大整体域成熟度。 | pass |

## 任务簇

- 任务簇计划：[domain_separation_split_task_clusters_20260609.zh.md](domain_separation_split_task_clusters_20260609.zh.md)
- 当前状态：[domain_separation_split_current_status_20260609.zh.md](domain_separation_split_current_status_20260609.zh.md)
- 派发队列：[domain_separation_split_dispatch_queue_20260609.zh.md](domain_separation_split_dispatch_queue_20260609.zh.md)
- 验收门槛：[domain_separation_split_acceptance_20260609.zh.md](domain_separation_split_acceptance_20260609.zh.md)

## 输出与证据

- `src/components/domains/air/platform/`、`src/components/combat/{common,air,naval,ground}/` 或获准本地约定下的 domain-owned component header。
- `src/systems/domains/air/`、`src/systems/combat/`、`src/systems/domains/naval/` 以及真实所有权成立后的 `src/systems/domains/ground/`。
- `src/models/domains/air/`、`src/models/domains/naval/`、`src/models/domains/ground/` 与 common model helper 下的 domain routing/adapter。
- architecture guard 与 acceptance evidence 中记录的退役公开 include 路径。
- 防止 air/naval/ground-only 类型回流 generic 文件的 architecture test。
- 聚焦 build/runtime 验证证据。

## 验收门槛

本子项目只有在以下条件满足时才可标记 accepted：

- `damage.h`、`damage_system.h`、`weapon.h` 三个混合热点已退役为公开入口，consumer 直接使用 common/domain owner header。
- generic `systems/physics`、`systems/systems`、`models/systems` 文件不再直接拥有 Air/Naval/Ground-only 逻辑，除非通过命名 adapter。
- 既有公开行为可编译，并通过 acceptance 文档列出的聚焦 runtime/architecture gate。
- 新增 Ground-owned shell 若无 runtime 和测试，只能标注为 ownership placeholder。
- review、manual 与 source README 索引反映新所有权，且不宣称完整域成熟度。

## Follow-up 边界

- 校准和真实性升级不属于本所有权拆分。
- 本轮清理后不刻意保留 domain-split compatibility wrapper；无关 legacy
  compatibility surface 不属于本包。
- 完整 Ground runtime 成熟度需要后续 movement/sensing/fires/damage 实现包。
- 若 model routing 暴露行为漂移，先记录 first failing stage，再讨论新增机制。

## 归档

本 accepted 子项目已归档到 [review archive](../README.zh.md)。若未来追加本子项目内部的
被取代派发包、worker report 或 closeout note，则继续通过
[archive/README.zh.md](archive/README.zh.md) 追踪。
