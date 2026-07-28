# T7 I89 残留裁定（2026-07-27）

语言：
- 英文正本：[t7_i89_residual_disposition_20260727.md](t7_i89_residual_disposition_20260727.md)
- 中文对照：`t7_i89_residual_disposition_20260727.zh.md`

文档类型：`reference`
生命周期：`maintained`
正本：`docs/plan/unified_architecture_program/t7_i89_residual_disposition_20260727.md`
归属：`unified architecture program workline`
最近核验：`2026-07-27`
基线提交：`a272fc04`

状态：I89 窄修复包中对 I88 最终残留审计首轮发现与保留面的分类组件。同一 I89 包另负责 `sensor_refs` 平价修复和 T8/T9 维护文档更正；本文既不提升任何 held 面，也不授权清理。本文本身不改变运行行为、生成物、工作树或 Git 元数据。

## 1. 分类规则

- **已修复**：窄缺陷已有修复 owner 与证据；本文不重新实现，也不吸收该修复。
- **刻意保留**：两个面承担不同契约，并有门阻止意外漂移。
- **暂缓**：仓库仍缺少明确的语义决策、领域授权、性能结果或破坏性操作批准。暂缓不等于允许删除、规范化或静默扩面。
- **不经济**：原则上可以安全收敛，但当前维护风险低于改动量与兼容成本。

## 2. 计划面的逐项裁定

| ID | 表面与证据 | 裁定 | Owner | 缺失的授权或证据 | 下一道门 |
|---|---|---|---|---|---|
| D-01 | T1 GPU packed view 仍为手写：`src/gpu/gpu_execution_observation_runtime.h` 的 `InstrumentPacked`/`MissionPacked`、`gpu_interaction_broadphase_runtime.h`、`gpu_visual_runtime.h`；它们未注册进 `tools/maintenance/dto_schema`。 | **暂缓** | T1 DTO schema 工作线与 exact-runtime/GPU backend owner | 维护中的 GPU 布局/ABI 权威与获准的投影契约。当前 GPU helper 不是规范仿真真值。 | 仅在 exact-runtime 工作线接受维护 GPU 布局后重开；届时从与 CPU 描述相同的 schema group 生成 packed view，并补 ABI/字节 parity 与 freshness 门。 |
| D-02 | T2 I83 只把经测量的观测/证据 seam 抽进 `WorldBatchCore`；single、leader、cooperative 调用者仍在 `python/rl/runtime/{single_world_batch_runtime.py,leader_world_batch_runtime.py,cooperative_world_batch_vec_env.py}` 保留各自 episode、leader、共享内存与兼容行为。 | **暂缓** | T2 runtime substrate owner 与 T4 exact-runtime owner | 在不破坏活跃调用者与 monkeypatch seam 的前提下迁移剩余模式专属所有权所需的代表性 parity 与性能证据。 | WP4 controller/default 决策后，用经测量的重复切片和只减不增的调用者清单重开；不得预造 plugin 方法。 |
| D-03 | `examples/config/training/active/naval/` 下的 T5 naval active config 是 N4 入口/运行时 smoke gate，不是通用训练矩阵产物，因此未进入 air-combat/cooperative `Experiment` 生成器。 | **暂缓** | Naval N4 领域 owner 与 T5 experiment-space owner | 冻结 naval evaluation protocol 并授权将 smoke gate 转为 typed experiment 产物的领域验收。 | Naval Experiment 切片必须逐字节保持三条路径，新增 registry/freshness 门，并保留 N4 禁武器/禁伤害声明边界。 |
| D-04 | T5 在 `air_combat_matrix.py` 和 `cooperative_flight_matrix.py` 中各把 `MATRIX_DIR` 重复一次：一次是模块 API，一次是 `MatrixEntryBase` 子类契约。构造与 freshness 门会在二者漂移时失败。 | **刻意保留 / 不经济** | T5 experiment-space owner | 无。两个名称服务不同扩展/API 契约；替换四个被钉住的字面量几乎没有维护收益。 | 仅当第三个矩阵证明存在真实漂移，或 `MatrixEntryBase` 能在不改变公开 import 与输出字节的情况下获得唯一 owner 时重审。 |
| D-05 | T6 weapon-guidance 残留：33 个唯一受治理节点（含混合 subtest 的 `expectedFailure`）、7 个 I97 聚焦校准断言，以及 diagnostics 顶层脚本治理 strict xfail。工具链/GPU 条件 skip 按能力收窄。 | **治理形式刻意保留；产品预期暂缓** | T6 测试基础设施 owner；产品变化由 damage/calibration owner 负责 | 权威校准或获准的产品语义变更；无关结构断言必须继续活跃。 | 每次只修一个产品预期；恢复时 strict xfail 必须 XPASS，`--runxfail` 仍须暴露精确残留断言。条件 skip 仅可在声明依赖真实存在时解除。 |
| D-06 | I88 发现的 T8 过时 candidate/review 文案已在本 I89 包更正：权威清单现将 I87 记录为已接受/落地。剩余 declared-but-open 真值读取者已是显式语义延后，不是安全机械搬移。 | **文本已修；剩余语义暂缓** | T8 information-state owner | 对 held 读取者，需要具备正确空列表/来源语义的 typed view 与领域 parity。 | 保持 I87 状态与队列/台账一致；每个剩余读取者仅能连同自身 view 声明、裸读禁令和行为 parity 一起迁移。 |
| D-07 | T9 表示审查没有找到 echelon authority 到 action-interface authority 的合法映射。I89 刷新了过时的 adapter 源码指针；no-mapping 判定不变，行为收敛不能从名字相似性启动。 | **证据指针漂移已修；行为切片暂缓** | T9 agency/doctrine owner | 显式注册映射、委派与仲裁规则的领域证据。 | 仅经注册 authority owner、领域评审与可承载映射门重开；否则保持 no-mapping 裁定。 |
| D-08 | I96 已修复 capability bundle 畸形 flag；I89 进一步使有界 Python 推导与 C++ loader 的 `sensor_refs`“键存在且为数组”分支一致：空数组抑制 inline sensor，非数组落入 inline，数组中的非字符串元素与 loader 一样忽略，非空字符串数组产生 `sensor_refs`。 | **已修复** | T11 content-compilation owner | 对本次审计边缘无缺失授权；更广泛族扩张仍在受限 pilot 之外。 | 保持三形状加忽略元素的平价测试活跃；未来 loader-chain 变更必须同步更新 mirror 与参考路径平价。 |
| D-09 | T11 rollback guard 扫描 pilot 选定的维护 roots，但不含根入口与 `scripts/`；直接扩面可能把诊断/launcher 引用误判为默认路径 wiring。 | **暂缓** | T11 rollback-shell owner | 根入口与 `scripts/` 的维护调用者分类，包括明确的 diagnostics/tool 豁免。 | 仅连同默认路径正向清单和注入 offender 测试一起扩 scan；不得为保持门为绿而单纯扩 allowlist。 |

## 3. 源码 TODO 裁定

I88 找到的仅有三个源码 `TODO` 均位于 `src/systems/systems/logistics_system.h`。没有一个属于安全文字清理。

| ID | TODO | 裁定 | Owner | 缺失的授权或证据 | 下一道门 |
|---|---|---|---|---|---|
| D-10 | 第 49 行：燃油状态阻止动作时设置 flag 或禁用 `ActionCommand`。 | **暂缓** | Logistics behavior owner 与 command/tasking contract owner | 哪个 owner 记录 fuel-blocked intent、command 是拒绝还是保持、公开哪种 diagnostic/event 的决策。 | 改 command 状态前，先加入 typed rejection/hold 契约与端到端 command 行为测试。 |
| D-11 | 第 68 行：补给 stores 时遍历 `default_loadout`。 | **暂缓** | Logistics/store owner 与 T11 content owner | 获准的 loadout 补给语义、magazine 容量规则，以及与暂缓的 int-keyed `default_loadout` codec 的兼容结论。 | 先冻结 typed replenishment request/result，并对 authored loadout 做 fixture parity，再写遍历逻辑。 |
| D-12 | 第 92 行：若跟踪 drag，则外部挂载抛弃后降低 drag。 | **暂缓** | Logistics owner 与 aero/flight-model owner | 单一 drag-state owner 与经验证的外挂阻力模型；当前代码无法从 TODO 推导权威系数变化。 | 落地 model-owned jettison/drag 契约、前后 flight-model parity 与领域证据。 |

## 4. 工作区与 Git 状态裁定

| ID | 表面 | 裁定 | Owner | 缺失的授权或证据 | 下一道门 |
|---|---|---|---|---|---|
| D-13 | 主工作树在 58 个 `.tmp*`/`.pytest*` 目录下有 857 个 untracked 条目，内含 11,745 个文件、共 198.93 MiB，来源于 I83/I87 测试。它们是生成物，但审计未证明保留或消费状态。 | **暂缓** | 主工作树操作者 / artifact producer | 每个 artifact 可丢弃或可重现的确认，以及删除/搬移授权。 | 清点精确 producer 与恢复路径；只在明确清理授权下移除。 |
| D-14 | 六个非目标工作树为 dirty 且其 blob 不与 I88 head 完全相同：Ground（20 modified + 1 untracked）、i61 repair（4 staged + 5 unstaged）、w14 lineage（10 modified + 1 untracked）、w17 botfix（3 modified）、w18 botfix（5 modified）、w3 flightshaping（10 modified + 2 untracked）。 | **暂缓** | 各 worktree/branch owner | 逐工作树归属、发布/放弃决策与破坏性清理批准。 | 逐个记录 HEAD、branch/detached 状态、status、unique commits 与 recovery ref，再取得明确清理指示。本文不得 prune、reset、move 或 delete。 |
| D-15 | `git count-objects -vH` 将空目录 `.git/worktrees/EF-w24-i88/refs` 报为 garbage；该报告既不授权修改共享元数据，也不能证明 linked worktree 已 orphaned。 | **暂缓** | Repository/worktree 管理员 | 在验证活跃 I88 worktree 的 gitdir 映射后，修改共享 Git 元数据的批准。 | 先用 `git worktree list --porcelain` 与 path/gitdir 只读复核；dirty worktree 对账后，才可使用获准的 Git 原生 repair 操作。 |

## 5. 收账后果

I88 **不是 clean pass**：审计发现了需要本文明确裁定的表面，以及由其他 owner 承担的窄修复。本文只关闭分类缺口；不声称 held 项已经完成，也不允许 I90 忽略它们。I90 必须在其精确 checkout 上核验已修项，并针对当前调用者、门、工作树状态与 owner 授权重新证明每条 held/intentional 分类。

## 6. 相关权威

- [统一架构计划](README.zh.md)
- [I72+ 迭代队列](iteration_queue_i72_plus_20260726.zh.md)
- [T6 残留登记册](t6_residual_ledger.zh.md)
- [仓库整合计划](../repository_consolidation/README.zh.md)
- [Exact Runtime 重构计划](../exact_runtime/cpp_exact_runtime_refactor_plan.zh.md)
- [仿真系统架构设计](../architecture/simulation_system_architecture_design.zh.md)
