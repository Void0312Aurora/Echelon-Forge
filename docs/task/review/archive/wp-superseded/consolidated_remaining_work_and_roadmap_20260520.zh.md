<!-- Machine-translated draft generated on 2026-05-20 from docs/task/review/consolidated_remaining_work_and_roadmap_20260520.md. Review before treating this file as authoritative. -->

# 剩余工作与前瞻路线图（综合版）

状态：`2026-05-20` 路线图审查；WP9 已验收。
范围：WP0–WP8 审查文档中识别的所有延期、后续及已规划但未分配架构工作。

输入：

- [WP3 验收审查](archive/wp-acceptance/wp3_engagement_pilot_acceptance_review_20260519.md)
- [WP4 第一波 / 第二波 / 最终验收审查](archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP5 第一波 / 信息-信念 / 最终验收审查](archive/wp-acceptance/wp5_validation_harness_acceptance_review_20260519.md)
- [WP6 验收审查](archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md)
- [WP7.5 验收审查](archive/wp-acceptance/wp75_training_path_facade_bridge_acceptance_review_20260520.md)
- [WP8 验收审查](archive/wp-acceptance/wp8_learning_face_acceptance_review_20260520.md)
- [架构计划审查](architecture_plan_review_20260519.md)
- [temp-02 SCAL 审查](temp-02_review_20260519.md)
- [WP4 外观对齐计划审查](archive/wp-superseded/wp4_facade_alignment_plan_review_20260519.md)

## 1. 目的

WP0 至 WP8 已验收。在所有验收审查中，积累了一组一致的延期项——大部分规模较小、理解充分，仅因优先级而非设计不确定性而阻塞。

本文档将这些延期项合并为一个压缩工作包（`WP9 合同与基础设施收尾`），然后阐述其后的剩余架构路线图。

## 2. 合并的 WP9——合同与基础设施收尾

验收：

- [WP9 验收审查](wp9_contract_infrastructure_closure_acceptance_review_20260520.zh.md)

残余：

- `INF-6` real missile terminal effects capture 仍是已跟踪 follow-up，因为当前
  damage system 缺少窄的 maintained recorder seam。该残余已记录在 WP3 与
  WP9 验收审查中。

以下所有项均直接提取自 WP3–WP7.5 验收审查的“残余风险”或“延期后续”部分。无需新的架构发现。每项都有已知的解决方案和明确的责任文档。

### 2.1 DTO / 合同提升

| ID | 项 | 来源 | 当前状态 | 要求输出 |
|----|------|--------|---------------|-----------------|
| DTO-1 | `RewardReport`：类型化事实/形塑归因 | WP4 最终 §4.3, WP5 最终 §4.3 | `reward_breakdown_json` 为非结构化字符串；事实/形塑划分在架构 §6 中有定义但未类型化 | C++ `RewardReport` 结构体，包含 `fact_terms`、`shaping_terms`、`fact_snapshot_version`、`term_owner` |
| DTO-2 | `TerminationSpec`：类型化原因来源归因 | WP4 最终 §4.3, WP5 最终 §4.3 | `terminated` / `truncated` 为并行向量；原因来源未类型化 | C++ `TerminationSpec` 结构体，包含 `reason`、`reason_source`（仿真/策略/编排）、`snapshot_version` |
| DTO-3 | `ObservationBatchPacket` 元数据：快照版本、屏障 ID、源时间 | WP4 最终 §4.1, WP5 最终 §4.2 | `ObservationBatchPacket` 缺少 WP2.5 溯源字段 | 向现有结构体添加 `snapshot_version`、`barrier_id`、`source_time_s` |
| DTO-4 | `ObservationViewSpec`：<主版本>.<次版本>、必需/可选字段、检查点兼容性规则 | WP4 第一波 §4.5, WP4 计划审查 §2.2 | 架构 §6 定义了规则；不存在类型化表面 | C++ `ObservationViewSpec` 结构体或带有版本协商的文档化模式 |
| DTO-5 | `ActionIntentPacket`：effective_time、valid_until、merge_policy、action family | WP4 第一波 §2, WP4 表面映射 | 在 WP4 表面清单中列为延期缺口 | C++ `ActionIntentPacket` 结构体，与架构 §6 字段对齐 |
| DTO-6 | `CoordinationIntentPacket`：source type/id、roster、merge_policy | WP4 第一波 §2, WP4 表面映射 | 列为延期缺口 | C++ `CoordinationIntentPacket` 结构体 |
| DTO-7 | `AgentRole`：角色 + 权限 + 信息状态来源 + 决策模型 + 动作接口 | WP4 第二波 §4, temp-02 审查 §2.4 | Python `agent_shim.py` 包含被动标签；无 C++ 类型 | 从 Python 垫片提升为 C++ `AgentRole` 结构体 |
| DTO-8 | `DecisionBelief`：与 `ObservationPacket` 的形式化边界 | WP5-D §4, temp-02 审查 §2.3 | Python 垫片标签存在；无类型化强制 | C++ `DecisionBelief` 结构体或文档化边界契约 |

### 2.2 基础设施收尾

| ID | 项 | 来源 | 要求输出 |
|----|------|--------|-----------------|
| INF-1 | `merge_policy` 命名冲突：WP2.5 时钟合并 vs 架构 §6 跨层合并 | WP2.5 审查 | 将 WP2.5 §6 重命名为 `clock_merge_policy`；添加交叉引用说明 |
| INF-2 | `DiagnosticsTrace` 独立外观表面 | WP4 计划审查 §2.3, WP4 最终 §4.4 | 专用外观查询端点；与 engagement 导出带带分离 |
| INF-3 | `RuntimeCapabilities` 填充触发条件 | WP6 审查 §3 | 记录触发条件：“当至少维护一个非参考后端配置文件时” |
| INF-4 | StageNodeManifest 注册表补全 | WP2.5 审查 §3 | 添加 P0–P6、P8–P10 示例清单（当前仅存在 P7） |
| INF-5 | 外观拆分阈值规则 | WP4 计划审查 §3.4 | 记录：`RuntimeFacade` 在约40个方法时拆分为 Session/Setup/Execution/Observation/Diagnostics/Engagement/Capability 组 |
| INF-6 | WP3遗留: 真实导弹终端效果捕获 | WP3 任务文档 §9 | 从调试的接近命中路径迁移到维护的引导/效果事件捕获 |
| INF-7 | WP3遗留: 近期事件存储策略 | WP3 任务文档 §9 | 从有界缓冲区（`kMaxRecentEngagementEvents=64`）迁移到与 WP2.5 事件排序对齐的正式事件队列 |

### 2.3 延期守卫强制

| ID | 项 | 来源 | 要求输出 |
|----|------|--------|-----------------|
| GUA-1 | 全局 `sim.*` AST 守卫及允许列表 | WP5 最终 §4.5 | 溯源标签 + 兼容性/诊断允许列表，在广泛禁止之前 |
| GUA-2 | 绑定表面冒烟测试提升 | WP5 最终 §4.1 | 修复 `test_bindings_engagement_surface.py` 中空 packet-shell 世界索引情况 |

### 2.4 WP9 工作包

| 工作包 | 范围 | 退出产物 |
|--------------|-------|---------------|
| `WP9-A DTO 提升批次 1` | DTO-1 至 DTO-4：`RewardReport`、`TerminationSpec`、`ObservationBatchPacket` 元数据、`ObservationViewSpec` | C++ 头文件 + 外观表面 + Python 绑定 + 聚焦测试 |
| `WP9-B DTO 提升批次 2` | DTO-5 至 DTO-8：`ActionIntentPacket`、`CoordinationIntentPacket`、`AgentRole`、`DecisionBelief` | C++ 头文件 + 外观表面 + Python 绑定 + 聚焦测试 |
| `WP9-C 基础设施收尾` | INF-1 至 INF-7：命名修复、诊断表面、能力触发条件、清单注册表、外观拆分规则、WP3遗留 | 文档补丁 + 注册表条目 + 1 个新外观方法 |
| `WP9-D 守卫强制` | GUA-1、GUA-2：允许列表、绑定冒烟测试提升 | 允许列表文档 + 测试修复 |
| `WP9-E 集成与索引同步` | 交叉引用、README 更新、中英文对齐 | 更新的索引 |

### 2.5 WP9 依赖图

```
WP9-A ──┐
WP9-B ──┼── WP9-E
WP9-C ──┤
WP9-D ──┘
```

所有四个子包彼此独立，可并行运行。WP9-E 为串行。

## 3. WP8——SCAL 学习面（已验收）

WP8 现在是已验收的 documentation-only Learning-face 任务族。其三个实质性门控
已有已检查产物：

| 门控 | 最小已检查产物 |
|------|--------------------------|
| WP8-A 课程与场景生成 | 版本化的 `CurriculumRequest` / `ScenarioGenerationSpec` 模式，包含种子策略、阶段和请求字段 |
| WP8-B 评估与能力分析 | `BenchmarkProtocol` + `CapabilityProfile` 模式，包含分数归因、证据规则以及“无隐藏真相”验证 |
| WP8-C 世界模型接口与学习证据 | `ObservationPacket` / `DecisionBelief` / `World Truth` 边界契约，包含溯源及重放/诊断血统规则 |

WP8 仅包含文档，无需 RL 训练或新代码。

## 4. 前瞻路线图

```
                        WP8              WP9                 WP10+
                   SCAL 学习面      合同与基础设施         架构扩展
                       Face           Closure             Expansion
                   ─────────────   ─────────────────    ─────────────
状态：             已验收          已验收                未排期

交付：             课程            类型化 DTO（8 个）      调度器实现
                   评估            命名修复                多保真度
                   世界模型         外观表面                能力图
                   边界            清单注册表              世界线
                                   守卫允许列表            实验生成
```

### WP9 后的架构扩展（未排期，未排序）

以下是在 temp-02 及更早审查中识别的较大架构项。均无硬编码工作包编号。优先级应在 WP9 完成后根据当时项目需求决定。

| 方向 | 先决条件 | 性质 |
|-----------|--------------|--------|
| 调度器语义实现 | WP2.5（规约已完成） | C++ 代码：运行时中的 StateStore、EventQueue、ClockDomain、Barrier |
| 多保真度架构 + ModelProvider | WP6 + WP7（后端配置文件 + 多保真度进入条件） | 文档 + 代码：保真度配置文件、ModelProvider 抽象、相同场景 → 不同保真度 |
| 能力图迁移 | WP2（契约本体论） + WP9（AgentRole DTO） | 文档 + 代码：`spawn_unit(type_name)` → `spawn_platform({capabilities...})` |
| 世界线 / 反事实架构 | WP2.5（确定性重放） + 状态快照/恢复 | 文档 + 代码：分支点、反事实 rollout、因果差异 |
| 实验生成架构 | WP8（课程 + 评估） | 文档 + 代码：场景生成器、对手生成器、能力分析器、泛化测试器 |

## 5. 立即后续行动

1. **评估 WP9 后优先级**——根据项目需求从未排期的 WP10+ 方向中选择下一项。
2. **保持 `INF-6` 可见**——在后续 owner 添加 maintained recorder seam 之前，
   不把 terminal effects capture 静默视为已关闭。

## 6. 结束说明

本文档不重新打开任何已验收的工作包。WP9 中的所有项均来自现有验收审查的延期/后续部分。WP9 后的路线图仅为建议性，不带有硬编码工作包编号——其目的是防止这些方向被丢失，而非规定其执行顺序。
