# WP4-D + WP4-E 分发表：Policy、AgentRole 与 Python Mirror

状态：`2026-05-19` 分发表；在 WP4-A 为 action、coordination、observation、belief 与 agent role 发布稳定 surface 名称后启动。

语言版本：

- 英文主文：[wp4_policy_binding_cluster_20260519.md](wp4_policy_binding_cluster_20260519.md)
- 中文辅文：`wp4_policy_binding_cluster_20260519.zh.md`

输入：

- [WP4 facade 对齐](facade_alignment_wp4_20260519.zh.md)
- [WP4-A surface inventory 任务簇](wp4_surface_inventory_cluster_20260519.zh.md)
- [Temp-02 SCAL 架构愿景审查](../review/temp-02_review_20260519.zh.md)
- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- 当前 `python/rl/runtime/*`、`python/rl/control/*`、`gym_envs/*` 与
  `src/interfaces/python/bindings_runtime.cpp`

## 一、目的

本表把触及 policy/orchestration adapter 与 Python exposure 的 WP4 工作归为一组：

- `WP4-D Policy And Coordination Bridge`
- `WP4-E Python Mirror And Cleanup`

本任务簇的核心规则是：**RL policy 不是 agent。** Learned、scripted、human、LLM、MCTS 或 rule-based decision model 都挂接到声明 role、authority、information state、decision model 与 action interface 的 `AgentRole` 上。

## 二、分发交付物

| 流 | 必需输出 | 主要写入范围 | 思考预算 |
|----|----------|--------------|----------|
| `WP4-D1 AgentRole Contract Sketch` | 五元素 `AgentRole` schema，以及到当前 policy/coordination adapter 的映射。 | docs 与 policy adapter notes；surface 稳定后才改代码。 | 高。 |
| `WP4-D2 ActionIntent Adapter Path` | 记录或实现显式 facade-compatible action intent path，包含 `effective_time`、`valid_until` 与 `merge_policy`。 | `python/rl/runtime/*`、`python/rl/control/*`、`gym_envs/*`；避免 facade signature churn。 | 高。 |
| `WP4-D3 CoordinationIntent Adapter Path` | 记录或实现 scripted、learned 与 human producer 的显式 coordination path。 | `python/rl/runtime/*`、`gym_envs/*`。 | 中高。 |
| `WP4-D4 Observation/Belief Leakage Review` | 识别 maintained observation/belief path，并把 truth-derived oracle path 标记为 diagnostics-only。 | Python adapter docs/tests。 | 高。 |
| `WP4-E1 Binding Surface Mirror` | 确保 Python bindings 镜像稳定的维护中 facade DTO，且不暴露新的 raw-runtime path。 | `src/interfaces/python/bindings_runtime.cpp`、binding tests。 | 中。 |
| `WP4-E2 Helper Cleanup Notes` | 记录仍为 compatibility-only 的 helper-layer path 及其 deprecation 条件。 | Python helper docs/tests。 | 中。 |

## 三、写入范围规则

1. Policy/adapter worker 拥有 `python/rl/runtime/*`、`python/rl/control/*` 与 `gym_envs/*`。
2. Binding worker 拥有 `src/interfaces/python/bindings_runtime.cpp` 与 binding tests。
3. 本任务簇不得新增 raw `WorldBatchRuntime` 维护路径。
4. 添加 public C++ binding surface 前，应等待 WP4-A 名称稳定。若名称不稳定，应写 compatibility note 或 pending test。
5. 本任务簇必须把 diagnostics-only oracle data 视为非维护中 policy input。
6. 若必须改变 facade DTO，应与 WP4-B/C owner 协调，并串行处理签名变更。

## 四、AgentRole 最小形态

`AgentRole` 必须包含：

| 字段 | 规则 |
|------|------|
| `role_id` | 用于 replay、diagnostics 与 policy/binding reference 的稳定 id。 |
| `role_type` | 示例值：`flight_lead`、`wingman`、`autopilot`、`fire_control`、`coordinator`、`human_operator`、`diagnostic_oracle`。 |
| `authority_scope` | 该 role 可影响的 entity、roster、command family 或 tasking scope。 |
| `information_state_source` | `ObservationPacket`、`DecisionBelief`、shared tactical picture 或 diagnostics-only oracle。 |
| `decision_model_ref` | Scripted doctrine、learned policy checkpoint、human source、search planner、LLM planner 或 compatibility helper。 |
| `action_interface` | `ActionIntentPacket`、`CoordinationIntentPacket`、tasking/command adapter 或 diagnostics-only output。 |
| `maintained_status` | `maintained`、`compatibility_adapter` 或 `diagnostics_only`。 |

## 五、Action 与 Coordination 规则

维护中的 policy/orchestration output 必须声明：

1. `source_layer`，
2. `source_id`，
3. `input_snapshot_version` 或 consumed observation/belief version，
4. `effective_time`，
5. `valid_until`，
6. `merge_policy`，
7. action 或 coordination family，
8. target entity、roster 或 scope，
9. 关联的 `AgentRole`。

如果当前 adapter 不能携带全部字段，WP4-D 应记录缺口，并创建 compatibility shim 或 pending WP5 validation gate，而不是静默写 raw runtime state。

## 六、Python Mirror 规则

WP4-E 必须让 Python exposure 与维护中的 C++ surface 对齐：

1. Binding 镜像稳定 DTO 名称与字段语义。
2. Binding test 覆盖维护中 DTO 的字段存在性。
3. Compatibility-only helper 保持标记，不成为文档化维护路径。
4. Diagnostics-only oracle/belief material 不得作为 maintained observation data 暴露。
5. 如果 C++ surface 名称不稳定，WP4-E 应等待或记录 pending mirror gap，而不是过早锁定 binding。

## 七、验证目标

签名稳定后的推荐聚焦命令：

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings tests\architecture\test_runtime_facade_layering.py
```

若本地缺少 RL training dependency，adapter-specific test 可以收窄。

## 八、退出标准

本任务簇退出条件：

1. `AgentRole` 有连接到当前 adapter 的五元素 contract sketch。
2. Action 与 coordination path 是 facade-compatible，或明确标记为 compatibility gap。
3. 维护中的 adapter path 不把 `World Truth` 当作 observation 消费。
4. Python bindings 镜像稳定的维护中 facade DTO。
5. Compatibility-only helper path 有 deprecation 或 promotion 条件。
