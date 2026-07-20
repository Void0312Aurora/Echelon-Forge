# 统一架构计划

语言：
- 英文规范版：[README.md](README.md)
- 中文伴随版：`README.zh.md`

文档类型：`plan`
生命周期：`maintained`
规范路径：`docs/plan/unified_architecture_program/README.md`
所有者：`unified architecture program workline`
最近核验：`2026-07-20`

状态：`codex/redundancy-consolidation` 分支上的活跃计划，把已完成的文本级
整合阶段（I1-I19）与蓝图 W1-W2 波（I20-I24）延伸为剩余架构级统一工作的
单一冻结路线图。

## 目标

用有主的、生成的或组合式的系统替换剩余的手工平行基础设施，使新增一个
DTO 字段、一条训练线、一个探针或一个域切片的边际成本降为在唯一 owner
处修改一次。计划允许在证据支持下调整架构，但行为保持、字节/ABI parity
证据、公开面兼容与有界能力声明是绝对约束。

## 治理

- 迭代台账保留在
  [仓库整合计划](../repository_consolidation/README.zh.md)的登记表中。
  本计划的迭代延续同一 `I<n>` 编号与同一「分析/实现/验证/登记/提交」
  协议。本文档只承载路线图与轨道定义，不得成为第二本台账。
- 关键期（DTO 家族转换、基座提取、C++ target 拆分）按 W2 时所有者的
  决定在落地前接受一轮独立评审；其余迭代仅以 parity 门禁落地。
- 每个家族转换都随附再生成新鲜度门禁
  （`tools/maintenance/dto_schema/generate.py --check`），行为可能漂移
  之处按 I8/I19 范式提供内嵌参照的对拍测试。

## 设计原则

计划以长周期可维护性为优化目标，而非短期行数。具体而言：

1. **要体系不要补丁。** 能占有一整类变更的 schema、生成器、注册表或
   基座，优先于一次性去重——即使前期行数成本更高。以净增行数换单一
   owner 是可接受的（I18/I20 先例），但必须在台账如实记录。
2. **每次整合都交付扩展契约。** 轨道条目在「下一个消费者的接入路径」
   被文档化并入门禁之前不算完成：下一个 DTO 字段、域切片、训练线、
   探针或配置变体应通过注册的扩展点接入，而不是复制既有实现。
3. **域对称是扩展插座，不是死重。** naval/ground 薄切片对 air 的镜像
   是刻意的。T1 command 家族与 T3 loader 工作必须把按域注册形式化
   （schema 分组、profile 适配器、taxonomy 条目），使未来新域以注册
   方式挂接，而非修改 air 专有代码。
4. **为 C++ 接管而建，使 Python 越来越薄。** Python 基座不得固化
   exact-runtime 主线（WP4/WP5）计划接管的逻辑；生成的 builder 与
   插件必须能在对应家族的 C++ 所有权落地后按族退役。
5. **可逆性与可审计。** 生成产物入库并带新鲜度门禁；每次架构迁移都
   保留兼容壳，直至终局残余审计将其审慎退役。

## 性能边界

性能优化本身仍由 exact-runtime 主线
（[计划](../exact_runtime/cpp_exact_runtime_refactor_plan.zh.md)）与
架构/性能调研线拥有，刻意不设为本计划的轨道。本计划交付性能*使能项*
且不得堵死它们：DTO schema 层必须能从同一字段源生成替代布局（例如
未来 `ExactStateStore` 的 SoA 或 packed 设备视图）；基座统一必须使
热步进循环收敛为恰好一个可优化点；T3 的 target 拆分必须产出可供
剖析与后端工作独立迭代的链接单元。计划期间发现的实测性能工作项
一律路由到 exact-runtime 线，不扩宽本计划。

## 全局结构：承重不变量

没有声明全局结构的局部整合会制造枢纽耦合（人人依赖的"共享"owner）。
因此本计划由六条全局不变量治理；默认砍掉不服务于任何一条的局部工作项。

- **G1 两个世界，一个契约。** 系统恰为仿真世界（C++ 拥有真值与时间）
  与实验世界（Python 拥有组合：场景、训练、评估、诊断）。两界之间
  只存在一个边界契约（facade 加 schema 生成的 DTO 词汇）。跨界路径
  数是架构健康度指标，目标值为一。
- **G2 单向分层圈。** Python 侧：contracts → substrate → 域语义 →
  实验编排；C++ 侧：contracts → engine → mission → facade。共享需求
  一律下沉，绝不横向。反枢纽条款：中立层必须是依赖终端，基座必须
  阶段局部，owner 必须单一职责。
- **G3 状态所有权拓扑单调。** 每份状态恰有一个 owner，所有权只向
  内核方向迁移（exact-runtime 方向）。所有权地图是维护物（T0 普查
  产出），不是口头默契。
- **G4 信息状态分层是唯一跨界语义不变量。** 每个观测/奖励消费者
  声明其消费层（Truth/Sensed/Track/Picture/Observation/Belief）；
  强制手段从文档升格为门禁。
- **G5 扩展即注册。** 域、模式、探针、配置经声明的插座接入；需要
  修改共享代码的扩展按定义即设计缺陷。
- **G6 表示是描述的投影。** 跨界形状由 schema 生成。这是 G4 的富
  provenance 分层不塌缩为手写管道的前提。

## 基线批判与修订建议

SCAL 基线以明示批判的方式被采纳为目标本体。优点：信息状态分层、
带版本化反馈的因果-时序分离、能力组合。本计划记录并路由的缺陷：
（1）七图是无组合力学的分类学——只有时序 DAG 具有运行时实体；
（2）意图靠评审文化而非一小组构造性强制的内核不变量执行（G1-G6
即该压缩）；（3）线性 P0-P10 词汇与多速率、事件驱动子管线存在张力，
应改造为带声明子图的阶段契约；（4）Learning 面浅，而仓库的变更热区
恰在该处；（5）缺 Experiment 面——场景×配置×种子×课程×评估协议无
一等公民归宿，配置矩阵蔓延即其直接症状；（6）富认知本体缺配套表示
策略，由 G6 补足。修订候选（a：Experiment 面；b：带子图的阶段契约；
c：内核不变量清单；d：表示策略章节）提交给基线自身的治理流程，
本计划不越权直接改写。

## 系统性对齐：SCAL 一致性

下方的工程轨道是必要但不充分的。仓库已拥有一份概念架构基线——
[仿真系统架构设计](../architecture/simulation_system_architecture_design.zh.md)
（SCAL 四面、图之图、六层信息状态、`P0-P10` 规范语义生命周期、因果-时序
执行模型与能力组合式域扩展）——但维护中的代码尚未在结构上体现它。已知
一致性缺口包括：scenario loader 在单个对象里聚集了多个生命周期阶段；
观测模式分裂在 compiled-core 与 Python 适配器之间而无声明的
`ObservationViewSpec` 边界；`MissionCommand` 以五种表示存在而非单一
类型化契约词汇；`spawn_unit(type_name)` 尚未展开为类型化能力包。

因此本计划把该基线当作目标本体，而非仅背景阅读：

- **T0（新增）：语义生命周期与信息状态一致性。** 产出阶段一致性普查，
  把每个维护中的运行时函数映射到其 `P0-P10` 阶段与信息状态层，登记
  每处违例（跨阶段所有权、真值泄漏进策略路径、平行生命周期），并经
  其余轨道逐项消解缺口登记。
- **T2 重新定位：** `WorldBatchCore` 不只是去重容器，而是分阶段 tick
  管线在维护 Python 侧的投影。模式插件必须阶段局部（Agency 图适配
  器），基座的阶段边界必须与生命周期表对齐，使 WP4 能逐阶段迁往 C++。
- **T1 锚定：** command/tasking schema 家族实现 Semantic 面的类型化
  契约词汇；schema 分组应遵循基线的 packet 分类而非另造命名。
- **T3 锚定：** 域注册遵循能力组合模型（`PlatformFamily`/`SensorFamily`
  等扩展族），推动内容加载走向类型化能力包。

## 计划轨道

| 轨道 | 范围 | 主要目标 | 关键风险 |
| --- | --- | --- | --- |
| T0 SCAL 一致性与基线修订 | 对维护运行时（loader、vec-env、facade 消费者）做阶段一致性普查；信息状态层审计并交付消费者的 G4 声明机制；跨界旁路路径盘点（G1）；三条当下可强制的组合规则（语义→因果的内容编译降低、因果→时序的读写集调度、信息→机构的 view spec）；起草修订候选 (a)-(d) 并提交架构工作线治理 | 代码在结构上体现（修订后的）基线；批判变成力学而非评论 | 普查需要判断力；缺口必须路由到轨道而非引发临时重写 |
| T1 DTO 单源化收尾 | world-batch（约 211 字段）、engagement 余量（约 445 字段、29 类）、command/tasking 的 umbrella-slice-codec 家族、GPU packed 视图；engagement/command 的 schema 分组按修订 (b) 携带阶段契约与事件驱动子图元数据，不强塞线性阶段 | 把剩余约 2,400 条手工同步语句移入 schema 所有权；schema 词汇对齐 Semantic 面 packet 分类 | 成员顺序即 ABI；JSON codec 别名；部分暴露视图 |
| T2 运行时基座统一 | B-2 残余破环（包 init 懒化或派发依赖倒置，并修复 AST 门禁盲区）、`WorldBatchCore` 提取且阶段边界跟随修订后的阶段契约模型、execution/cooperative/leader 模式插件（阶段局部的 Agency 适配器）、adapter 与 single/leader 运行时收编；交付回填基线 Learning 面的学习运行时架构说明（修订候选 (e)） | 阶段接缝即 WP4 迁移接缝的单一批处理基座；消除约 1,400 行重复；分层单向 | monkeypatch 缝；shared-memory 与 leader 特殊路径；插件接口必须从实测重复提取而非投机 |
| T3 C++ 结构边界 | `ef_core` 拆分为 engine/mission/facade/content 链接单元并加 include 方向门禁；facade 结果投影去重；关闭 T0 盘点出的跨界旁路路径（G1：facade 成为唯一应用路径）；在 T1 验证 codec 逃生口后把 `unit_definition_loader` 表驱动化 | 强制层边界；跨界路径数收敛到一；loader 1,881 行手写映射入 schema 所有权 | 链接顺序与初始化；NaN 哨兵配置语义 |
| T4 exact-runtime 对齐 | 支撑 WP4 热路径切流到 `WorldBatchRuntime`；退役被 C++ 所有权替代的 Python 逐步 builder；重冻 exact-runtime 计划文档 | Python 步进层变薄而非固化 | 迁移期双所有权漂移 |
| T5 实验空间定义与声明式配置 | 冻结类型化 Experiment 定义（场景引用×配置组合×种子×评估协议），对齐 Experiment 面修订 (a)；run 配置由之派生（先对 24 文件空战矩阵做 bases+deltas 生成与新鲜度门禁）；opt-in 报告信封；第二批 argparse | 存在一等公民的实验对象，run 配置皆为其派生；配置矩阵以 delta 维护 | docs 钉住的配置路径必须稳定；实验类型不得先于修订固化 |
| T6 测试基建理性化 | 本机基线红修复（allowlist 路径分隔符匹配器、winsock harness 链接、GBK 探针解码、weapon-guidance 45 例环境失败）、权威表数据化重试、wrappers 契约簇 | 验证信噪比：本机预期红清零 | 基线修复不得掩盖真实回归 |
| T7 终局残余审计 | 对计划全表面连续两轮干净审计；每个幸存重复分类为 intentional/held/uneconomic | 按整合计划停止条件实现可审计的完成 | 文本上不存在不等于证明；需调用者/行为审计 |

以下适配轨道由认真对待 SCAL 各面推导而来：每条对应一张目前只有词汇
加零散片段而无 owner 的图。它们修改既有逻辑以适配本体，而不只是去重。

| 轨道 | 范围 | 主要目标 | 关键风险 |
| --- | --- | --- | --- |
| T8 信息状态架构 | 把 `ObservationViewSpec` 实现为真实的 facade 机制；将 G4 层声明机制（T0）应用于每个观测/奖励消费者；把 Python 侧观测适配器迁移到声明视图之上；盘点并关闭真值泄漏进策略路径 | 每个维护消费者声明其认知层并经声明视图读取；诊断之外的上帝视角在结构上不可能 | 视图管道必须搭乘 T1 schema 机器，否则重造手写 packet 体量 |
| T9 机构与条令架构 | 把授权模型（角色、范围、委派、仲裁）形式化为注册结构而非散落检查；条令/ROE 成为声明的 `DoctrineFamily`；把 tasking-contracts 层已起步的命令链 seam 收敛为 Agency 图的单一入口 | 「谁可指挥谁」成为带门禁的可检视数据，而非调用点里的口头传统 | C2 语义是本仓的研究对象；修改需域证据评审而不只是 parity |
| T10 证据与重放主干 | 把 trace id、packet 祖先、快照版本、重放门禁与 worldline/counterfactual 表面统一为由 T1 事件 schema 生成的单一证据架构 | 任何维护运行按构造可重放、可比较（兑现证据图承诺） | 证据表面被测试与 retained 产物 pin；扩展必须只增不改 |
| T11 内容编译管线 | 把场景/单位内容加载演化为分阶段 `P0 ContentCompile` 模型：类型化 setup packet、`spawn_unit` 兼容面之后的能力包展开、内容 schema 校验作为编译阶段；吸收并取代 T3 的 loader 条目 | 新内容与新域经编译且校验的能力组合进入 | 内容 JSON 兼容是硬外部面；必须逐包迁移并带 fixture parity |

登记但持有：多速率时钟域与屏障调度（Temporal 图的补全）继续以
exact-runtime WP4/WP5 进展为门，不由本计划排期。

## 顺序与依赖

0. T0 普查是本计划的开局调研动作（连同三项配套调研：C++ episode
   controller 与 Python 步进逻辑之间的 WP4 接口考古、共享路径中 air
   具体性泄漏的域不对称盘点、command/content 家族的 schema 逃生口
   普查）。其缺口登记在 T1-T4 关键期开始前重新冻结各期写集。T0 起草
   的基线修订必须经架构工作线治理、先于消费它们的各期落地：阶段契约
   修订 (b) 先于 T1 engagement 家族与 T2 插件提取；Experiment 面修订
   (a) 先于 T5 的实验类型冻结。
1. T2.B-2（残余破环）先于更深的基座提取落地，使插件化从单向层图出发。
2. T1 world-batch 家族先于 T3 的 facade 投影去重，后者消费生成的
   packet schema。
3. T1 command/tasking 家族先行验证 schema 逃生口（继承注册、JSON 别名、
   隐藏切片），T3 再据此把 `unit_definition_loader` 表驱动化。
4. T4 跟随其依赖的 T1 家族（episode 已完成；world-batch 其次），并与
   exact-runtime 计划协调而非由本文档指挥。
5. T6 基线修复可随时落地，越早越有利于门禁保真；T7 最后执行且跑两轮，
   覆盖面包含 T8-T11。
6. 适配轨道消费前序轨道的机器：T8 需要 T0 的 G4 机制并搭乘 T1 的
   观测/world-batch schema；T9 跟随 T1 command 家族与 T2 插件接缝；
   T10 搭乘 T1 engagement schema；T11 跟随 T1 逃生口验证并在启动时
   取代 T3 的 loader 条目。

## 非目标

- 文档压缩与归档规范化（P7）按所有者决定不在范围内；evidence 包保持
  不可变。
- 不建运行时反射层，不引入新第三方依赖，生成器不参与常规 CMake 构建。
- 未提供显式兼容壳与迁移说明前，不改任何公开 Python 名、CLI 旗标、
  配置键或 JSON schema。

## 相关权威

- [仓库整合计划](../repository_consolidation/README.zh.md)（迭代台账与协议）
- [exact runtime 重构计划](../exact_runtime/cpp_exact_runtime_refactor_plan.zh.md)
- [文档生命周期政策](../../standards/governance/document_lifecycle_policy.zh.md)
- [Agent 文档权威地图](../../agent/rules/document_authority_map.zh.md)
- [SCAL 一致性普查（2026-07-20）](scal_conformance_census_20260720.zh.md)（T0 产出；违例登记与修订依据）
- [T6 残差台账（2026-07-20）](t6_residual_ledger.zh.md)（T6 产出；索引迭代台账中以自然语言散落登记的 I28/I31/I33 本机红与 DTO 迁移残差）
