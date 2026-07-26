# 统一架构 I72+ 迭代队列（2026-07-26）

语言：
- 英文正本：[iteration_queue_i72_plus_20260726.md](iteration_queue_i72_plus_20260726.md)
- 中文伴随：`iteration_queue_i72_plus_20260726.zh.md`

文档种类：`plan`
生命周期：`maintained`
正本：`docs/plan/unified_architecture_program/iteration_queue_i72_plus_20260726.md`
所有者：`unified architecture program workline`
最后核验：`2026-07-27`
基线提交：`9362a136`

状态：未落地的 2026-07-23 草案（`iteration_queue_i67_plus_20260723.md`）的重编号后继版，
本文取代该草案。草案按 I61-I66 候选编号设计；该编号在 I61-I71 落地波登记时发生了变化，
下文各计划行按落地台账的编号重发同一队列内容（I72 除外，已按其行内说明调整；见第 0 节）。
I73 sim 接缝切片已落地；当前七行在实施中：I72、I74 与 I75（近期第 1 波），以及
I76、I77、I78（部分）与 I80（第 2 波，已构建并处于独立评审中）。其余各行仍为计划状态、
未标 accepted；其启动仍遵循仓库协议：聚焦验证、独立只读评审、必要时修复/复审、每迭代
一个提交、登记台账。

## 0. 编号说明

2026-07-23 草案按当时的候选台账把计划行编号为 I67-I85。落地台账实际把 I63（T8 门网）、
I65（T6 第三包）、I66（T11 航空束）、I67（T2 learning-runtime 说明）、I68（T9 A3
authority-default 命名；草案中的"I66"）、I69（T10 维护 run ReplayEnvelope 生产者；草案
中的"I65"）、I70（build-infra nanobind 回移）与 I71（本迭代队列文档）分配给了落地波，
因此草案的计划行按下表重编号（内容与顺序均不变；I72 除外，已按其行内说明调整）：

| 草案编号（2026-07-23） | 本队列编号 | 内容 |
|---|---|---|
| I67 | I72 | T6 路径后缀匹配器加固（进行中；已调整——I65 已落地原两断言修复） |
| I68 | I73 | T2/T3 `ScenarioLoader.sim` 接缝（已落地） |
| I69 | I76 | T8 维护消费者分类器 |
| I70 | I77 | T9 表示边界裁定 |
| I71 | I78 | T1/T10 谱系词汇 |
| I72 | I79 | T10 切片 6A ancestry |
| I73 | I74 | T11 舰船/潜艇束（进行中；为束 4，修正草案的"束 3"——航空束才是束 3） |
| I74 | I75 | T5 实验矩阵加固（进行中） |
| I75 | I80 | T4 exact-runtime 覆盖前置 |
| I76 | I81 | T1/T3 contracts 边界 |
| I77 | I82 | T3/T4 所有权迁移 |
| I78 | I83 | T2 `WorldBatchCore` 第一切片 |
| I79 | I84 | T10 切片 7 |
| I80 | I85 | T11 能力束 |
| I81 | I86 | T9 行为切片 |
| I82 | I87 | T8 类型化数据流试点 |
| I83 | I88 | T7 终局残余审计干净轮 1 |
| I84 | I89 | 窄修复包 |
| I85 | I90 | T7 终局残余审计干净轮 2 |

行文内的依赖引用按同一方式改写：草案候选编号"I65"（ReplayEnvelope 生产者）现读作
I69，候选编号"I66"（T9 authority 默认值）现读作 I68；草案引用的其余已落地编号（I30、
I41、I44、I54、I55、I57、I58、I59、I61、I62、I63）在落地时未变。计划行之间的交叉引用
一律使用新编号。

## 1. 排期规则

1. 每个迭代只承担一个主要架构风险。仅当交付物本身就是显式依赖接缝时使用跨轨道标签
   （例如 T1 schema 机器服务 T10 证据面）。
2. 前置证据失败时，迭代以**带证据的 held** 关闭；不得强推迁移。
3. 除非对应行明确要求版本化或 opt-in 面，既有公开名称、JSON/配置形状、序列化值、
   retained 哈希与默认运行路径均保持不变。
4. 新防漂移门须进入维护 CI smoke 清单；若不进入，必须给出实测成本与另一自动化 owner。
5. T9 行为改动需要领域证据评审，仅有 parity 不足。
6. T7 最后执行，并在两个独立干净轮次上完成；两轮之间若有修复，干净轮计数重置。

## 2. 近期可执行队列

| 迭代 | 轨道 | 交付物 | 依赖 | 退出证据与红线 |
|---|---|---|---|---|
| I72（进行中） | T6 | T6 台账 §8.9/§9.3 的匹配器加固后续：I65 已用完整 `Path` 相等修复了两条 Windows 专属 `retained_pack/manifest.json` 断言，故本切片新增可复用的规范化路径组件匹配器，服务于测试无法构造完整期望路径的后缀检查，并补含跨边界后缀在内的 Windows/POSIX 负例；I65 的两处 Path 相等调用点保持不变。 | I57 台账；I65 §9.3 | 匹配器接受两种分隔符约定，并在 Windows 与 POSIX 分隔符下拒绝错误组件与跨边界路径；I65 修复的两条断言保持逐字节一致；组件脆性校准红继续独立登记。不改 retained writer、manifest 字节或哈希。 |
| I73（已落地） | T2/T3 | 类型化 `ScenarioLoader.sim` 接缝。普查该句柄上的全部维护方法，在中立 tasking/runtime-contract 层定义纯 stdlib 结构协议，证明 `_ScenarioLoaderRuntimeProxy` 实现它，并把 raw-kernel 注入限定为测试面。 | I62 死接口清理 | 精确调用清单、import 方向门、proxy 一致性测试、loader 行为不变。不建新枢纽，不引入 `gym_envs -> python.rl` 边。 |
| I76（进行中） | T8 | 用逐文件维护消费者分类器关闭 I63 的观测面逃逸口。把 raw-truth 扫描扩到 `reward_runtime` 之外，同时不把指令/动作/装载读取者误判为观测消费者。 | I63 | 每个维护观测/奖励消费者均被分类并登记；注入未登记消费者会变红。本切片不迁移生产读取。 |
| I77（进行中） | T9 | 裁定 I68 暴露的表示边界：层级权限（`CommandRelationship`/`AuthorityScope`）与动作接口权限（`AgentRole`/`AgentAuthorityScope`）。对相关 A2/A4-A6/A13 路径逐项给出有证据的映射或明确无映射结论。 | I68 | 双语裁定矩阵、源码指针、领域评审记录、可承载一致性门。零 C2 行为变更。 |
| I78（进行中） | T1/T10 | 让 C++ `ScenarioGenerationRequestMetadata` 与 Python `ScenarioGenerationRequest` 的谱系词汇共用一个 schema owner（T10 VA-6），生成两面并保持字段名、顺序、默认值与序列化。 | I69；T1 生成器 | 跨语言字节/数值 parity、freshness 门进入 smoke、无新运行时反向依赖；任何 codec escape hatch 都须明确 held。 |
| I79 | T10 | T10 切片 6A：经叠加式 opt-in/版本化路径填充 packet ancestry。parent 关联使用 facade trace allocator，`*_ref` 使用 I78 类型词汇；既有默认序列化值不变。 | I78；I54/I59/I69 | 真实 run 端到端 ancestry、replay 校验、retained/默认字节 parity、跨 facade 证据失败关闭。不得原地改默认路径。 |
| I74（进行中） | T11 | loader 表驱动束 4：`ship_platform` 与 `submarine_platform` 对象内部标量字段。对象存在旗标与 parse 相位仍手写；仅在原位置生成重复字段读取。 | I61；I55/I58 | 全字段 fixture parity、畸形输入 fail-first parity、27 定义数据库 parity、C++ 全量与 smoke。不吸收六个 held `has_*` 旗标、`default_loadout` 或 codec escape hatch。 |
| I75（进行中） | T5 | 加固类型化实验矩阵的三项 I30 残差：JSON 对象键转义、bool-vs-int 字面量相等、完整实验→场景映射漂移。 | I30/I44 | 三项可承载负例，24/24 生成配置逐字节不变。不改 CLI/配置路径或矩阵文件。 |

## 3. 依赖门控队列

| 迭代 | 轨道 | 交付物 | 启动门 | 退出证据与红线 |
|---|---|---|---|---|
| I80（进行中） | T4 | 在退役任何层级前关闭 exact-runtime 覆盖前置：经仍为 opt-in 的 `execution_episode_controller_mainline` 覆盖 post-launch 评估与全部维护 `flight_shaping_backend` 选项。 | I62 已落地；匹配的 C++/Python 构建 | 全选项格跨层 parity 与显式缺口矩阵。不翻默认，不删 Python 层。 |
| I81 | T1/T3 | 解决 I41(f) 中 `WorldExecutionEpisodeStepRequest` 借用 mission evaluation 类型的 contracts 边界。若可逐字节等价则用 T1 schema 所有权；否则冻结精确 held 结论。 | I80 证据 | 要么以 57 个绑定 parity 把 include allowlist 缩一，要么登记边仍 held 的理由。不得反转依赖。 |
| I82 | T3/T4 | 仅在 I80 证明覆盖后移动下一条 exact-runtime 所有权边界：让编译 episode controller 拥有已覆盖批切片，只退役被取代的私有 Python 编排。 | I80 通过；I81 已处置。代签处置（2026-07-27）：I80 缺口矩阵的 gpu_host 格保持 HELD（EF_ENABLE_CUDA_EXPERIMENTS 属实验性且默认关闭；mainline 的构造期拒绝维持不变）；post-launch 评估格约束红线——所有权搬迁的只减不增删除清单必须排除默认路径 post-launch 评估所需的每一条路径，且把该评估移植进 controller 登记为独立的未来工作项，不并入 I82。 | 默认路径前后 parity、热路径实测、公开面审计、只减不增的删除清单。任一维护选项需 Python fallback 即停止。 |
| I83 | T2 | 从实测共用 execution/observation seam 抽取 `WorldBatchCore` 第一切片，消费 I73 loader 协议与 I82 所有权边界。 | I73 与 I82 | 单向依赖图、single/leader/cooperative 兼容、无投机插件方法、重复量实测下降。 |
| I84 | T10 | T10 切片 7：以 opt-in 方式经维护 adapter 暴露 worldline/counterfactual 比较，消费 I69 envelope 与 I79 ancestry。 | I79 | 真实 run 比较证据、无真值晋升、确定性 replay ref、默认路径字节 parity。 |
| I85 | T11 | 在一个受限平台族上试点以内容能力束作为真源，位于 `typed_platform_request` 之后；`spawn_unit` 兼容路径保留为参照。 | I74 | 实体/物化 parity、版本化校验诊断、回退壳、不改 `examples/config/**`。 |
| I86 | T9 | 从 I77 认可映射中选择最小的首个行为 Agency 切片（优先 A13 谁可开火或 A2 默认分派 seam）。 | I77 映射获领域评审批准。I77 的代签签核已记录无映射（2026-07-27），该记录落地后 I86 预期以 held 关闭。 | 单一语义 owner、对抗式授权测试、无观测/奖励 ownership 泄漏、明确条令前后证据。若 I77 结论为无映射，I86 改以 held 关闭。 |
| I87 | T8 | 为一个受限 TL13 消费者族试点类型化观测数据流，消费 I76 分类与 T1 DTO 机器；让结构性 `ObservationViewSpec` 导出首次成为被消费的数据，而非仅元数据。 | I76；相关 T1 schema；I83 seam 稳定 | 类型化 view parity、试点内零 raw truth、无新跨层 import，并明确空 required/optional 字段清单的含义。 |

## 4. 收官队列

| 迭代 | 轨道 | 交付物 | 启动门 | 退出证据 |
|---|---|---|---|---|
| I88 | T7 | 终局残余审计干净轮 1，覆盖 T1-T11 代码、调用者、门禁、文档、held 项与工作树状态。 | I72-I87 已 accepted 或显式 held | 每个幸存项归类为 `intentional` / `held` / `uneconomic`；零未分类发现。 |
| I89 | T1-T11 | 仅修 I88 发现的窄修复包，不做顺手工作。 | I88 有发现 | 每个风险一提交、完整受影响门、独立评审。I88 若干净则跳过 I89。 |
| I90 | T7 | 在新 checkout 与匹配构建上做终局残余审计干净轮 2。 | 最后修复后无新改动 | 与第一轮分类一致、无新发现、台账哈希完整、连续两轮干净。 |

## 5. 明确不排期 / held

- 多速率时钟域与 barrier 调度继续等待 exact-runtime WP4/WP5 证据。
- I61 的六个存在/启用旗标在其配对对象块语义完成裁定前保持本地。
- `UnitDefinition::default_loadout` 与 `ExecutionBatchStepResult` 继续 held 于
  X-macro 逗号/类型 token 边界。
- T9 行为迭代不得按名称相似启动；I77 的表示裁定是硬前置。
- 不得提前执行 T7 来制造虚假的完成信号。

## 相关

- [统一架构计划](README.zh.md)
- [仓库整合计划](../repository_consolidation/README.zh.md)
- [Exact Runtime 重构计划](../exact_runtime/cpp_exact_runtime_refactor_plan.zh.md)
- [T6 残差台账](t6_residual_ledger.zh.md)
- [T8 G4 真值泄漏登记](t8_g4_truth_leak_inventory.zh.md)
- [T10 证据主干普查](t10_evidence_spine_census_20260721.zh.md)
- [T11 内容流水线普查](t11_content_pipeline_census_20260721.zh.md)