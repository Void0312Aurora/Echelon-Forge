# 地面域系统归属准入

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/reviews/ground_systems_owner_admission_20260921/README.md`
Owner: `domains/ground`
Last verified: `2026-09-22`

状态：`2026-09-21` 已接受。轮 10 授权了收尾。范围与边界已冻结；声明簇已收口，`DM-G1` 成因已定位，
系统归属已准入且守卫已更新。关卡结果见
[验收记录](ground_systems_owner_admission_acceptance_20260921.md)，各轮授权关系见
[Review Log](ground_systems_owner_admission_current_status_20260921.md)。

生命周期说明 `2026-09-22`：本包是作为 provenance 保留的已接受 review 记录。它记录的
`DM-G1` 残余已由
[Ground Damage Effects Route Repair](../../work/active/ground_damage_effects_route_repair/README.md)
包在同日结清：effects 路由现在在组合路径按 world 解析一次组件 id，并且可达。本包、Review
Log、验收记录或簇计划里凡说 effects 路由不可达之处，都是**审核当时**的状态，修复前的测量是
有意保留的。本包做出的能力拒绝没有改变、依然生效；修复包也不因可达性而声明任何 Ground 能力。

语言：

- 英文主文：`README.md`
- 中文辅文：[README.zh.md](README.zh.md)

输入：

- [地面域 owner README](../../README.zh.md)
- [地面域专业化基线](../../standards/specialization_baseline.zh.md)
- [地面域最小任务结构](../../standards/minimal_task_structure.zh.md)
- [地面域缺陷清单](../../reviews/ground_domain_defect_inventory_20260522.zh.md)
- [模块化计划 —— Ground 系统缺口](../../../../architecture/work/issues/modularization_plan.md)
- [DM-G1 地面损伤可达性诊断](../../../../systems/combat/reviews/ground_damage_reachability_20260921.md)
- [域系统层边界](../../../../../src/systems/domains/README.zh.md)
- [战斗系统层边界](../../../../../src/systems/combat/README.zh.md)
- [子项目创建规范](../../../../engineering/automation/rules/subproject_creation_standard.zh.md)

## 目的

注册表里带 `domain = ground` 标签的有两行：stage 10 的共享 ground-contact 原语，与
stage 30 的地面损伤响应。真正作为地面自有机制落地的是后者；在本包之前它住在
`src/systems/combat/` 下，而该目录自己的边界 README 把 "ground fires, ground
damage, or land-domain combat runtime ownership" 列为 **Prohibited**。模块化计划把
它描述为 no-op 注册壳、并记录"不存在 Ground systems owner"；地面域专业化基线把它
描述为 placeholder 路由。三份维护中的描述加一条目录边界与已落地的代码互相矛盾，
而这个域此前没有任何工作包来收口这些矛盾。

本子项目把 `src/systems/domains/ground/` 准入为地面域的每 tick 系统归属目录，把
损伤系统搬进去，并收口目前与它冲突的声明。准入这个归属目录本来就是模块化计划
写明的前置条件；它此前缺席是一项被接受的架构状态，而本包正是请求改变该状态的
工作面。

本包同时**诊断**（不修复）`DM-G1` 可达性缺陷，使新的归属目录继承的是一条实测过的
状态说明，而不是一个未言明的假设。

## 当前状态

| 领域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 地面损伤机制 | 已实现；effects 路由在**审核当时**不可达（自 `2026-09-22` 起可达） | `src/systems/domains/ground/damage_system_ground.h`；`src/core/engine/system_contribution_registry.cpp` 中 stage 30 的 `builtin.system.ground_damage`；[DM-G1 诊断](../../../../systems/combat/reviews/ground_damage_reachability_20260921.md) | 无论可达与否都不证明任何地面战斗能力；per-tick 系统能匹配，审核当时一次命中走 placeholder 兜底 |
| 系统归属目录 | 已准入（`GA-B`） | `src/systems/domains/ground/` 存在并拥有损伤系统；治理守卫现在断言该目录存在而不是其缺席 | 该目录只拥有一个系统，不是 ground runtime |
| 目录边界 | 已解决（`GA-B`） | `src/systems/combat/README.md` 的 Prohibited 段，**未编辑** | 搬迁让禁令重新成立，这正是"不该去改禁令"的原因 |
| 地面域专业化基线 | 已收口并晋升（`GA-A` → `pass`，在 `f3f85859`；页面在 `2d0addf7` 之后于 `0fec39bb` 闭合） | [specialization_baseline.zh.md](../../standards/specialization_baseline.zh.md) 已把所有权、注册与可达性状态三者分开陈述；不再有 placeholder 路由表述 | 本包之后，地面损伤仍然不被声明为能力；该节现为"已注册且可达，但不构成能力" |
| 模块化计划 | 已更新（`GA-C`） | 计划现在把 `ground` 列为已准入的 systems owner，并描述损伤响应而不是 no-op 壳 | 计划归架构侧所有；本包只提出文本，不拥有它 |
| P2 stage node | held | stage node 注册表共 5 个节点，`P2 TaskingIntent` 一个都没有 | 不在本包范围；需独立包 |
| 地面域工作包 | 本包 | 授权窗口由[地面域 owner README](../../README.zh.md) 拥有；本行不重述它 | 第一个被授权的地面包 |

## 范围

范围内：

- 以 `src/systems/domains/` 根对子目录要求的边界 README 为准，准入
  `src/systems/domains/ground/`；
- 把 `damage_system_ground.h` 搬进去，并更新
  `src/core/engine/system_contribution_registry.cpp` 的 include，保持已注册的
  contribution id 与 stage 不变；
- 更新 `src/systems/domains/` 的 README（中英），它当时解释的是"为什么没有地面
  归属目录"；
- 收口地面域专业化基线与 owner README，使它们与代码一致，同时继续拒绝能力声明；
- 向架构侧提出模块化计划的文本修改；
- 更新那条当时断言目录缺席的治理守卫；
- 仅以探针方式诊断 `DM-G1`。

范围外：

- 地面机动、路线跟随、地形、感知、火力、后勤、观测导出；
- 任何地面战斗能力声明 —— effects 路由在独立修复包收口前保持不可达（已于 `2026-09-22`
  由
  [修复包](../../work/active/ground_damage_effects_route_repair/README.md)
  收口，留存下来的是能力拒绝这一部分）；
- `DM-G1` 的修复本身；
- P2 stage node 与任何 facade 可见性提升；
- 编辑 `src/systems/combat/README.md`；
- 新开测试文件；
- 对共享 combat / effects / physics 代码的广泛重写。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结范围、写入集与禁止声明。 | 本次请求与几处互相矛盾的描述 | 本 README 与父 README 链接存在 | accepted（轮 10） |
| `P1 Evidence` | 枚举搬迁触及的每一处锁定字符串、守卫、fixture 与注册行。 | `P0` | cluster 计划写明每个写入集与验证命令 | accepted（轮 10） |
| `P2 Declaration Reconciliation` | 使地面域自有页面与代码一致。 | `P1` | 没有任何地面域页面把该机制描述为 placeholder | accepted（轮 3） |
| `P3 Owner Admission` | 建目录、搬迁系统、更新注册 include 与治理守卫。 | `P2` | 目录存在、组合校验通过、守卫已更新 | accepted（经由轮 5 对 `GA-B` 的授权） |
| `P4 Validation` | 运行组合、地面域与治理关卡。 | `P3` | 命名命令通过且无新增失败 | accepted（经由轮 5 对 `GA-C` 的授权） |
| `P5 Closure` | 写验收、当前状态与 owner 索引更新。 | `P4` | 包被接受，或以具名 blocker 明确 held | accepted（轮 10） |

## 任务簇

- 任务簇计划：
  [ground_systems_owner_admission_task_clusters_20260921.md](ground_systems_owner_admission_task_clusters_20260921.md)

## 产出与证据

- `src/systems/domains/ground/README.md` 与搬迁后的损伤系统；
- 注册项保持不变（`builtin.system.ground_damage`，stage 30），仅 include 路径更新；
- 收口后的地面域声明，把"所有权"与"能力"分开陈述；
- 更新后的治理守卫与模块化计划提案；
- 一次 `DM-G1` 测量：要么给出有界成因，要么记录成因位于 kernel 组装路径；
- 组合契约、地面域套件与治理守卫的验证输出。

## 验收门

只有在下列条件全部满足时，本子项目才可标记为 accepted：

- `src/systems/domains/ground/` 存在，并拥有此前归档在 `src/systems/combat/` 下的
  损伤系统；
- 默认组合仍然通过校验，组件与系统 contribution 计数不变，地面域注册项保持
  原有 id 与 stage；
- 没有任何维护中的页面把地面损伤路由描述为 placeholder，也没有任何页面声称它
  能用；
- `src/systems/combat/` 的边界 README **未被编辑**却重新成立；
- 治理守卫反映已准入的归属，而不再断言缺席；
- `DM-G1` 有记录在案的测量；修复只在它自带独立包时才算完成；
- 地面域套件与架构套件通过，无新增失败。

## 残余与下一步

- `DM-G1` 在审核时仍然 open，成因已定位，而且比最初报的更窄：工厂与注册 TU 把
  `GroundPlatformDamageState` 解析为组件 `94`，effects TU 解析出一个重复的 `105`，
  因此**只有 effects 路由**不可达；per-tick 系统能匹配，不受影响。测量过程与它逼出的
  更正都在 [DM-G1 诊断](../../../../systems/combat/reviews/ground_damage_reachability_20260921.md)
  里。**已于 `2026-09-22` 由
  [修复包](../../work/active/ground_damage_effects_route_repair/README.md)结清**，它正是该
  残余所要求的独立包。它留下的是仍带一个 `xfail(strict=True)` 的 mobility 投影期望，以及
  始终未被观测到的重复 id 创建点。
- P2 stage node 是任务侧的独立包；地面域唯一声明的阶段目前没有注册节点。
- 那 4 个 `xfail(strict=True)` 节点不适合进 CI 冒烟；同一文件里未加标记的单调性
  测试可能经由 placeholder 兜底通过。两者都是修复包要处理的证据诚实性问题。
  **已于 `2026-09-22` 处理**：三个标记被移除且对应节点通过，单调性节点被重新钉住，第四个
  节点保留的标记指向 mobility 期望而不是可达性。
- 已退役的 `docs/task/ground/` 记录在归档登记表里仍无恢复地址；这属于文档治理
  owner。
- 双语登记表里的 `last_verified` 是工具盖上的"哈希基线刷新日"，不是页面头部的副本，
  也没有门禁比对二者。审核实测 148 个已登记文件里有 42 个存在头部/戳不一致，所以
  对齐本包触及的那几对并不能修掉这一类问题；它属于文档治理。
- 机动、地形、感知与火力保持 held，直到各自的包写明架构标准要求的那些声明。

## 归档

被接受或被取代的记录移入 `docs/domains/ground/reviews/`，不留在已退役的任务根下。
本包一旦被接受、且持久事实已提升进地面域标准，就不得继续留在 `work/active/` 下。
**已满足**：本包在审阅轮 10 被接受，现位于
`docs/domains/ground/reviews/ground_systems_owner_admission_20260921/`。
