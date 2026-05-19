# WP4 Facade 对齐 — 计划审查

状态：`2026-05-19` 计划审查完成。
范围：WP4 facade 对齐计划 — surface map 覆盖度、架构文档对齐、缺口识别、结构性评估。

关联文档：

- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.md) — 第 3、6、7、9、11 节
- [WP3 交战试点验收审查](wp3_engagement_pilot_acceptance_review_20260519.zh.md)
- [WP4 facade 对齐计划](../../task/simulation_architecture/facade_alignment_wp4_20260519.md)
- [架构计划审查](architecture_plan_review_20260519.md)

## 1. 审查范围

本次审查评估 WP4 facade 对齐计划对架构设计文档中 facade 层和跨层契约要求的覆盖程度。架构文档在四个章节中定义了相关要求：

- **第 3 节**（目标分层模型）：Facade 作为前端/适配器与仿真引擎之间的稳定 request/result API。
- **第 6 节**（系统层耦合模型）：八个跨层契约，含具体所有权、字段要求和治理规则。
- **第 7 节**（契约分类法）：十六个契约族，含定义目的和长期所有者。
- **第 9 节**（后端与性能策略）：设备端状态须通过契约暴露，后端能力通过 facade 接入。
- **第 11 节**（验证闸门）：十个架构验证闸门。

## 2. 覆盖矩阵

### 2.1 完全覆盖

| 架构要求 | WP4 对应 | 评估 |
|---------|---------|------|
| Facade 作为稳定 request/result API（第 3 节） | Section 3 Facade Surface Map——11 个 surface，含 maintained shape 和 validation gate | 匹配架构文档目标分层模型。Surface map 格式清晰可操作。 |
| `ObservationPacket`（第 6 节） | `ObservationBatchRequest` / `ObservationBatchPacket` → "Keep as the maintained observation surface"，含 snapshot version、source time、include flags | 已存在且所有权正确归 facade。 |
| `ActionIntentPacket` / `ActionHoldPolicy`（第 6 节） | 明确标记为缺口 → WP4-D，minimum shape 含 effective time、validity window、hold/expiry policy、merge policy、action family | 范围正确。Minimum shape 字段匹配架构文档的跨层请求字段。 |
| `CoordinationIntentPacket`（第 6 节） | 明确标记为缺口 → WP4-D，minimum shape 含 source type/id、roster、target refs、update clock、merge policy、produced tasking fields | 范围正确。匹配架构文档对脚本化/学习型/人类指挥员的要求。 |
| `RewardSpec` / `RewardReport`（第 6 节：fact/shaping 分离） | "Align the maintained result shape with explicit fact/shaping attribution"——fact snapshot version、fact terms、shaping terms、term owner/source | 匹配架构文档的 fact boundary 标准。 |
| `TerminationSpec` / `EpisodeStatus`（第 6 节：terminated/truncated 分离） | "Align the maintained result shape with explicit reason-source attribution"——reason、reason source、snapshot version、mirrored phase | 匹配架构文档："Simulation owns semantic termination; policy/test/orchestration may request truncation." |
| `EpisodeLifecycleContract`（第 6 节） | "Keep the compiled/facade state authoritative and the adapters mirrored"——phase、step count、reset transition id、authoritative source | 匹配架构文档："Adapters never advance a private authoritative phase machine." |
| `merge_policy`（第 6 节：5 个 enum 值） | 列于 ActionIntentPacket minimum shape | 在 facade surface 词汇表中存在。 |
| 架构法则 #1（前端依赖 facade） | Gate 2: "Maintained policy/test paths do not depend on `RuntimeFacade::runtime()` or raw `WorldBatchRuntime`" | 对法则 #1 的直接强制执行。 |
| 架构法则 #7（facade 不复制 kernel） | Section 2 Non-Goals: "Collapsing compatibility adapters into implicit calls" | 防止逐方法 kernel 镜像。 |
| Engagement export world-safety（第 10 节） | WP4-B: "Keep engagement export world-safe and make the packet shell explicit" | 维持 WP3 试点的 world-safety 属性。 |
| Python 绑定镜像 | WP4-E: "Keep Python bindings and helper layers aligned with the maintained facade surface" | 确保 `ef_py` 跟踪 C++ facade surface。 |
| 兼容性逃逸口治理 | `RuntimeFacade::runtime()` / raw `WorldBatchRuntime` 显式列为 "compatibility-only" | 架构测试已强制执行。 |

### 2.2 部分覆盖

| 架构要求 | WP4 状态 | 缺口 |
|---------|---------|------|
| `ObservationViewSpec`（第 6 节：schema versioning、required/optional fields、checkpoint compatibility） | 未列为独立 surface。`ObservationBatchRequest` 仅有 `include_*` 布尔标志。 | 架构文档定义了 `<major>.<minor>` 版本格式、required/optional field 声明、以及 minor-compatible vs major-incompatible 变更规则。WP4 surface map 中缺失。 |
| 跨层请求字段（第 6 节：`source_layer`、`source_id`、`input_snapshot_version`） | 部分出现在 ActionIntentPacket minimum shape | `source_layer` 和 `source_id` 未显式列出，`input_snapshot_version` 通过 observation snapshot version 隐式关联。 |
| `RuntimeCapabilities`（第 7 节隐含：后端能力暴露） | `RuntimeCapabilities` struct 存在但 `capabilities()` 返回空结构 | WP4 未规划实现 `capabilities()` 查询。该 struct 是占位符。 |

### 2.3 未覆盖

| 架构要求 | 缺口描述 | 严重程度 |
|---------|---------|---------|
| `DiagnosticsTrace` 作为独立 facade surface（第 7 节） | 架构文档将 `DiagnosticsTrace` 列为契约族，owner 为 `core/engine` 和 facade contracts。WP3 实现了数据结构。WP4 surface map 无专用 diagnostics/trace endpoint。 | 中等。诊断当前依附于 `EngagementEventPacket`。独立 surface 可将可解释性关注点与交战数据分离。 |
| `BackendCapabilityFacade`（第 9 节） | 架构文档要求设备端状态路径通过 facade contracts 暴露能力。WP4 surface map 无后端能力 surface。 | 低。GPU 代码受 `EF_ENABLE_CUDA_EXPERIMENTS` 保护。可推迟至后端 profile 工作包。 |
| 观察 schema 兼容性规则（第 6 节：minor vs major 版本变更） | 架构文档规定 checkpoint 加载必须拒绝 major-version 不匹配，minor-version 差异可加载但缺失 optional field 需 default-fill。WP4 未体现这些规则。 | 中等。当策略 checkpoint 需要在观察 schema 演进中存活时，这些规则变得关键。应加入 `ObservationViewSpec` 设计。 |
| Facade endpoint 治理（temp-01 建议：consumer group、request DTO、result DTO、snapshot/version semantics、compatibility adapter、deprecation rule、mainline/diagnostic/experimental 分类） | WP4 surface map 每个 surface 定义了 "Minimum maintained shape" 和 "Validation gate"，但未强制 per-endpoint 元数据。 | 低。Endpoint 治理可增量添加。Surface map 格式是合理的起点。 |

## 3. 结构性评估

### 3.1 工作包分解质量

WP4 分解为 6 个子包（WP4-A 至 WP4-F），具有清晰的 write scope、并行规则和 exit artifact。依赖图（A → B/C/D/E → F）简单且避免循环依赖。结构良好。

值得注意：WP4-A（Facade Surface Inventory）正确放置为第一个工作包——在任何实现工作开始前定义共享词汇表。这正是使 WP3-A（Contract DTO Scaffold）有效的相同模式。

### 3.2 Write-scope 规则

Write-scope 规则（Section 7）具体且可执行：
- "facade worker owns `src/runtime/facade/*`"
- "binding worker owns `src/interfaces/python/bindings_runtime.cpp`"
- "policy/adapter worker owns `python/rl/runtime/*`, `python/rl/control/*`, `gym_envs/*`"
- 规则 6 显式禁止对 `simulation_kernel_weapon_api.cpp` 的并行编辑

这是从 WP3 的 write-scope 规则中学到的直接教训——该规则曾防止空中和海军适配器 worker 之间的共享内核文件冲突。

### 3.3 与调度器语义缺口的关系

WP4 正确地将自身范围限定为 facade surface 对齐，未尝试定义调度器语义。然而，两个 WP4 surface 对未冻结的调度器概念有隐式依赖：

- `ActionHoldPolicy` 需要跨 control-rate 和 physics-rate tick 的 hold-last/interpolation/expiry 语义——这依赖于尚不存在的 clock domain 定义。
- `ObservationViewSpec` 需要 snapshot version 语义——这依赖于尚不存在的 state shard versioning 规则。

WP4 可以通过定义契约形状（字段布局、enum 值）同时将运行时执行留给调度器语义冻结来推进这些 surface。WP4 文档应显式标注此依赖。

### 3.4 Facade 单体外貌风险

WP4 选择了"narrowing and naming existing surfaces"的路径，而非将 `RuntimeFacade` 拆分为多个 facade 类。对于当前项目规模（约 30 个 public 方法），这是正确的选择。然而，WP4 surface map 已识别出 11 个不同的 surface。随着新 surface 的添加（ActionIntentPacket、CoordinationIntentPacket），单体外貌类风险增加。

建议：在 WP4-A 输出中添加拆分阈值规则——当 `RuntimeFacade` 超过 40 个 public 方法时，拆分为 `RuntimeSessionFacade`、`WorldSetupFacade`、`ExecutionStepFacade`、`ObservationFacade`、`DiagnosticsFacade`、`EngagementFacade` 和 `BackendCapabilityFacade`。

## 4. 建议

### 加入 WP4-A（Facade Surface Inventory）

| 项目 | 理由 |
|------|------|
| `ObservationViewSpec` 作为独立 surface | 架构第 6 节将其定义为 policy/test 拥有，含 schema version、required/optional fields 和 checkpoint compatibility 规则。当前 surface map 中缺失。 |
| `DiagnosticsTrace` 作为独立 facade surface | 架构第 7 节将其列为契约族。WP3 已实现数据结构。应拥有独立于 engagement export 的专用查询 endpoint。 |
| Facade 拆分阈值规则 | 推迟拆分至约 40 个方法，但现在记录目标拆分架构。 |
| 每个 surface 对调度器语义的依赖声明 | 依赖于 clock domain 或 state versioning 的 surface 应显式标注。 |

### 加入 WP4-C（Step And Lifecycle Alignment）

| 项目 | 理由 |
|------|------|
| 观察 schema 兼容性规则 | 架构第 6 节定义了 `<major>.<minor>` 版本格式和 checkpoint compatibility 行为。应文档化于 `ObservationViewSpec` 设计中。 |

### 推迟至后端 profile 工作包

| 项目 | 理由 |
|------|------|
| `BackendCapabilityFacade` | 架构第 9 节要求，但 GPU 代码为实验性。推迟至 WP5 后。 |

## 5. 验收闸门覆盖

WP4 定义了 8 个验收闸门。与架构文档的 10 个验证闸门（第 11 节）交叉对照：

| 架构闸门 | WP4 闸门 | 状态 |
|---------|---------|------|
| 1. 文档命名 stage、owner、packet | 隐式包含于 surface map | 已覆盖 |
| 2. 文档命名 read/write set、clock、latency、sync | 不在 WP4 范围（属调度器语义） | 正确排除 |
| 3. 公共访问通过 facade | Gate 1、Gate 2 | 已覆盖 |
| 4. 架构测试防止原始 runtime 访问 | Gate 2 | 已覆盖 |
| 5. Include/build 边界 | WP4-E binding alignment | 已覆盖 |
| 6. CPU 语义基线 | Section 2 Non-Goals | 已覆盖 |
| 7. 跨领域烟雾测试 | Gate 7（本地验证） | 已覆盖 |
| 8. 诊断可解释性 | Gate 8 | 已覆盖 |
| 9. 跨层契约所有权 | Gates 3-5 | 已覆盖 |
| 10. Policy/test 适配器使用 facade API | Gates 2、5 | 已覆盖 |

全部 10 个架构闸门均已处理，或由 WP4 闸门直接覆盖，或正确排除在 WP4 范围外。

## 6. 结论

WP4 的 facade 对齐计划范围恰当、结构良好。覆盖了约 80% 的架构文档 facade 和跨层契约要求。三项主要缺口：

1. **`ObservationViewSpec` 缺失为独立 surface**——架构文档的 schema versioning 和 checkpoint compatibility 规则需要一个归属。
2. **`DiagnosticsTrace` 缺失为独立 facade surface**——当前依附于 engagement export，但应有自己的 endpoint。
3. **对未冻结调度器语义的隐式依赖**——`ActionHoldPolicy` 和 `ObservationViewSpec` 的 snapshot 语义需要尚不存在的 clock domain 和 state versioning 定义。

这些可通过在 WP4-A surface inventory 中添加三项来解决，无需重组工作包分解。WP4 计划在补充这些项目后即可推进。
