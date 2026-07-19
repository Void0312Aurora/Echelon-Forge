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

## 计划轨道

| 轨道 | 范围 | 主要目标 | 关键风险 |
| --- | --- | --- | --- |
| T1 DTO 单源化收尾 | world-batch（约 211 字段）、engagement 余量（约 445 字段、29 类）、command/tasking 的 umbrella-slice-codec 家族、GPU packed 视图 | 把剩余约 2,400 条手工同步语句移入 schema 所有权 | 成员顺序即 ABI；JSON codec 别名；部分暴露视图 |
| T2 运行时基座统一 | B-2 残余破环（包 init 懒化或派发依赖倒置，并修复 AST 门禁盲区）、`WorldBatchCore` 提取、execution/cooperative/leader 模式插件、adapter 与 single/leader 运行时收编 | 单一批处理基座，消除约 1,400 行重复，分层单向 | monkeypatch 缝；shared-memory 与 leader 特殊路径 |
| T3 C++ 结构边界 | `ef_core` 拆分为 engine/mission/facade/content 链接单元并加 include 方向门禁；facade 结果投影去重；在 T1 验证 codec 逃生口后把 `unit_definition_loader` 表驱动化 | 强制层边界；loader 1,881 行手写映射入 schema 所有权 | 链接顺序与初始化；NaN 哨兵配置语义 |
| T4 exact-runtime 对齐 | 支撑 WP4 热路径切流到 `WorldBatchRuntime`；退役被 C++ 所有权替代的 Python 逐步 builder；重冻 exact-runtime 计划文档 | Python 步进层变薄而非固化 | 迁移期双所有权漂移 |
| T5 声明式配置收尾 | 训练配置 bases+deltas 生成器与新鲜度门禁（先做 24 文件空战矩阵）、opt-in 报告信封、第二批 argparse | 配置矩阵以 delta 维护而非拷贝 | docs 钉住的配置路径必须稳定 |
| T6 测试基建理性化 | 本机基线红修复（allowlist 路径分隔符匹配器、winsock harness 链接、GBK 探针解码、weapon-guidance 45 例环境失败）、权威表数据化重试、wrappers 契约簇 | 验证信噪比：本机预期红清零 | 基线修复不得掩盖真实回归 |
| T7 终局残余审计 | 对计划全表面连续两轮干净审计；每个幸存重复分类为 intentional/held/uneconomic | 按整合计划停止条件实现可审计的完成 | 文本上不存在不等于证明；需调用者/行为审计 |

## 顺序与依赖

1. T2.B-2（残余破环）先于更深的基座提取落地，使插件化从单向层图出发。
2. T1 world-batch 家族先于 T3 的 facade 投影去重，后者消费生成的
   packet schema。
3. T1 command/tasking 家族先行验证 schema 逃生口（继承注册、JSON 别名、
   隐藏切片），T3 再据此把 `unit_definition_loader` 表驱动化。
4. T4 跟随其依赖的 T1 家族（episode 已完成；world-batch 其次），并与
   exact-runtime 计划协调而非由本文档指挥。
5. T6 基线修复可随时落地，越早越有利于门禁保真；T7 最后执行且跑两轮。

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
