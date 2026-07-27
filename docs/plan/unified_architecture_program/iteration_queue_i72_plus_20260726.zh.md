# 统一架构 I72+ 迭代队列（2026-07-26）

语言：
- 英文正本：[iteration_queue_i72_plus_20260726.md](iteration_queue_i72_plus_20260726.md)
- 中文伴随：`iteration_queue_i72_plus_20260726.zh.md`

文档种类：`plan`
生命周期：`maintained`
正本：`docs/plan/unified_architecture_program/iteration_queue_i72_plus_20260726.md`
所有者：`unified architecture program workline`
最后核验：`2026-07-27`
基线与源落地 head：`93f1214c`

状态：未落地的 2026-07-23 草案（`iteration_queue_i67_plus_20260723.md`）的重编号后继版，
本文取代该草案。草案按 I61-I66 候选编号设计；该编号在 I61-I71 落地波登记时发生了变化。
I72-I85 现均 accepted/landed；I86 以带证据 held 收口；I87 为 accepted/landed。I88
已作为第一轮终局审计执行并返回 findings；I89 现为活动中的窄修复包，I90 保持最后。后续 I96-I98 PR-bot 修复只登记入台账，
不属于 I72-I90 编号映射；`727193b2` 是谱系 CI gate 的前置/核验修复，不是新迭代编号。

## 0. 编号说明

2026-07-23 草案按当时的候选台账把计划行编号为 I67-I85。落地台账实际把 I63（T8 门网）、
I65（T6 第三包）、I66（T11 航空束）、I67（T2 learning-runtime 说明）、I68（T9 A3
authority-default 命名；草案中的"I66"）、I69（T10 维护 run ReplayEnvelope 生产者；草案
中的"I65"）、I70（build-infra nanobind 回移）与 I71（本迭代队列文档）分配给了落地波，
因此草案的计划行按下表重编号。这是历史编号映射；当前状态见第 2-4 节（内容与顺序均不变；I72 除外，已按其行内说明调整）：

| 草案编号（2026-07-23） | 本队列编号 | 内容 |
|---|---|---|
| I67 | I72 | T6 路径后缀匹配器加固（accepted/landed；已调整——I65 已落地原两断言修复） |
| I68 | I73 | T2/T3 `ScenarioLoader.sim` 接缝（已落地） |
| I69 | I76 | T8 维护消费者分类器 |
| I70 | I77 | T9 表示边界裁定 |
| I71 | I78 | T1/T10 谱系词汇 |
| I72 | I79 | T10 切片 6A ancestry |
| I73 | I74 | T11 舰船/潜艇束（accepted/landed；为束 4，修正草案的"束 3"——航空束才是束 3） |
| I74 | I75 | T5 实验矩阵加固（accepted/landed） |
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
| I72（accepted/landed） | T6 | T6 台账 §8.9/§9.3 的匹配器加固后续。 | I57 台账；I65 §9.3 | Windows/POSIX 分隔符与跨边界负例受测；I65 两处断言不变。 |
| I73（accepted/landed） | T2/T3 | 类型化 `ScenarioLoader.sim` 接缝。 | I62 死接口清理 | 调用清单、import 方向、proxy 一致性及 loader 行为均受门约束。 |
| I76（accepted/landed） | T8 | 逐文件维护消费者分类器。 | I63 | 维护观测/奖励消费者均分类登记；未登记注入变红。 |
| I77（accepted/landed） | T9 | I68 表示边界裁定。 | I68 | 双语裁定矩阵、源码证据与可承载一致性门；零 C2 行为变更。 |
| I78（accepted/landed） | T1/T10 | 跨 C++/Python 谱系词汇 shared schema owner。 | I69；T1 生成器 | 跨语言 parity、smoke freshness 门与 codec held 判定。 |
| I79（accepted/landed） | T10 | packet ancestry 的 opt-in/versioned 路径。 | I78（已落地）；I54/I59/I69 | 真实 run、replay、默认字节 parity 与外 facade fail-closed。 |
| I74（accepted/landed） | T11 | ship/submarine loader 表驱动束。 | I61；I55/I58 | fixture、fail-first、27 定义库、C++ 与 smoke 证据。 |
| I75（accepted/landed） | T5 | 实验矩阵三项 I30 残差加固。 | I30/I44 | 三项可承载负例和 24/24 字节不变。 |

## 3. 依赖门控队列

| 迭代 | 轨道 | 交付物 | 启动门 | 退出证据与红线 |
|---|---|---|---|---|
| I80（accepted/landed） | T4 | exact-runtime 覆盖前置，保持 opt-in。 | I62 已落地；匹配 C++/Python 构建 | 选项格 parity 与缺口矩阵；不翻默认、不删 Python 层。 |
| I81（accepted/landed） | T1/T3 | I41(f) contracts 边界处置。 | I80 证据 | 边有带证据的处置；不反转依赖。 |
| I82（accepted/landed） | T3/T4 | 覆盖格 controller 默认解析，以去武装状态落地等待性能证据。 | I80、I81 已落地；gpu_host/post-launch 约束仍按记录 held。 | 去武装时零行为变更；删除清单保持只减不增。 |
| I83（accepted/landed） | T2 | 已度量 execution/observation seam 的 `WorldBatchCore` 第一切片。 | I73、I82 已落地。 | 单向图、single/leader/cooperative 兼容、无投机 plugin 方法与重复量下降。 |
| I84（accepted/landed） | T10 | opt-in 的维护 worldline/counterfactual 对比。 | I79 已落地。 | 真实 run、无真值晋升、确定性 replay ref、默认字节 parity。 |
| I85（accepted/landed） | T11 | `typed_platform_request` 后的能力束真源试点。 | I74 已落地。 | 实体/物化 parity、版本化诊断、回退壳、`examples/config/**` 零编辑。 |
| I86（held） | T9 | 首个行为 Agency 切片。 | I77/I91 no-mapping 证据链及本行显式 held 分支。 | 已 held 收口；重开须新领域证据切片引入显式注册映射。 |
| I87（accepted/landed） | T8 | 有界 TL13 消费者族的类型化观测数据流试点。 | I76、相关 T1 schema 与 I83 稳定 seam 均已落地。 | 类型化 view parity、试点无 raw truth read、无新跨层 import、空清单语义已记录。 |

## 4. 收官队列

| 迭代 | 轨道 | 交付物 | 启动门 | 退出证据 |
|---|---|---|---|---|
| I88（发现；clean 计数为 0） | T7 | 覆盖 T1-T11 代码、调用者、门、文档、held 项与工作树状态的终局审计第一轮。 | I72-I85 accepted/landed；I86 带证据 held；I87 accepted/landed。 | findings 已记入 [I89 残留裁定](t7_i89_residual_disposition_20260727.zh.md)；不计 clean。 |
| I89（进行中） | T1-T11 | 仅修 I88 findings：有界 sensor-loader 平价、T8/T9 维护文档更正与残余分类。 | I88 有发现 | 将独立评审的风险切片组装为一个一致落地提交；完整受影响门与独立评审。 |
| I90（最后；待执行） | T7 | 新 checkout 与匹配构建上的终局审计，并在修复后取得两轮 clean。 | I89 评审后无新改动 | 与 I89 裁定分类一致、无新发现、台账哈希完整、连续两轮干净。 |

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
- [I89 残留裁定](t7_i89_residual_disposition_20260727.zh.md)
- [T8 G4 真值泄漏登记](t8_g4_truth_leak_inventory.zh.md)
- [T10 证据主干普查](t10_evidence_spine_census_20260721.zh.md)
- [T11 内容流水线普查](t11_content_pipeline_census_20260721.zh.md)
