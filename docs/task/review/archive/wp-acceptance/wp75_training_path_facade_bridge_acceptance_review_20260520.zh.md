# WP7.5 训练路径 facade 桥接验收审查

状态：`2026-05-20` 已验收通过。

语言版本：

- 英文主文：[wp75_training_path_facade_bridge_acceptance_review_20260520.md](wp75_training_path_facade_bridge_acceptance_review_20260520.md)
- 中文辅文：`wp75_training_path_facade_bridge_acceptance_review_20260520.zh.md`

审查输入：

- [WP7.5 训练路径 facade 桥接](../simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)
- [WP8 SCAL 学习面](../simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.zh.md)

## 1. 必需验收产物

下列产物若不齐全或不同步，`WP7.5` 验收包即视为不完整：

- `docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md`
- `docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md`
- `docs/task/review/wp75_training_path_facade_bridge_acceptance_review_20260520.md`
- `docs/task/review/wp75_training_path_facade_bridge_acceptance_review_20260520.zh.md`

缺失规则：

- 任一产物缺失，整体结果必须为 `fail`。
- 产物存在但未记录 gate verdict 与 required evidence，也必须为 `fail`。

## 2. 审查判定词汇

每个 gate 以及整体任务线只能以以下状态收束：

- `pass`：required evidence 全部到位，且没有被反证。
- `fail`：required evidence 缺失、被反证，或被意图性表述替代。
- `blocked`：环境或机器限制阻止了必须执行的检查。此状态保持 gate 未决，
  不能算作验收通过。

阻塞表述规则：

- 写成 blocked 的 gate 必须写出精确命令、精确阻塞点和下一环境。
- `Blocked` 不能被重写成“ready”、“accepted pending tests”或其他软通过表述。

## 3. Gate 检查清单

| Gate | 本审查中必须出现的 required evidence | 判定规则 |
|------|--------------------------------------|----------|
| `WP7.5-A Step Execution Mainline` | 受检的维护中训练 step 文件、所消费的维护中 facade batch-stepping surface，以及用于证明维护主线不再依赖 raw runtime episode stepping 的精确验证命令或测试。 | 只有存在具体维护路径证据时才能 `pass`。 |
| `WP7.5-B Observation Packet Mainline` | 受检的维护中 observation bridge 文件、所消费的 observation request/result surface，以及用于证明维护路径消费 facade observation packet 流的精确验证命令或测试。 | 只有存在 packet-flow 证据，且没有回退到批准 seam 之外的 direct observation getter 时，才能 `pass`。 |
| `WP7.5-C Compatibility Escape Hatch Reduction` | 迁移后仍可接受的每一处 `RuntimeFacade.runtime()` 或 raw `WorldBatchRuntime` 用法清单，并逐项标注为 compatibility-only 或 diagnostics-only。 | 只有当剩余 escape hatch 全部被显式记录，且没有被抬升成维护中的 training / learning API 时，才能 `pass`。 |
| `WP7.5-D Validation And Integration Sync` | 必需产物存在性确认、narrow regression guard 仍然存在的确认，以及 `WP8` 通过引用 `WP7.5` 获得 maintained training-path migration 的确认。 | 只有当发布、验证与 `WP8` 桥接引用三者自洽时，才能 `pass`。 |

## 4. 审查记录规则

本审查对每个 gate 都应记录：

1. 判定结果：`pass`、`fail` 或 `blocked`。
2. 实际观察到的 required evidence。
3. 如果运行了命令，记录精确命令。
4. 如果被阻塞，记录精确阻塞点与下一环境。

缺省规则：

- 如果本审查没有明确写出某个 gate 的 verdict 与 required evidence，则该 gate
  必须记为 `fail`。

## 5. 当前状态

截至 `2026-05-20` 的 gate 快照：

| Gate | 判定 | 本审查已观察到的证据 | 命令 / 阻塞点 |
|------|------|----------------------|---------------|
| `WP7.5-A Step Execution Mainline` | `pass` | 维护中的 mainline 代码已通过 `RuntimeFacade.step_execution_batch()` 路由 batch step 请求，且聚焦回归测试已改为在 `tests/world_batch/test_world_batch_vec_env.py` 上记录外层 batch request 标志。静态检查显示维护主线会消费 `ExecutionBatchStepResult.observation_packet`。 | 已在本机通过：`python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "mainline_step_prefers_batch_step_observation_packet or reset_uses_runtime_facade_compatibly"` 和 `python -m pytest tests/world_batch/test_world_batch_vec_env.py -q`。此前的 blocked 结果属于另一台设备，原因是缺少 RL 依赖（`torch`、`gymnasium`、`stable-baselines3`）或那台设备上的 `ef_py` 构建产物。 |
| `WP7.5-B Observation Packet Mainline` | `pass` | 静态检查显示 `python/rl/runtime/world_batch/adapter.py`、`python/rl/runtime/world_batch_vec_env.py` 与 `python/rl/runtime/cooperative_world_batch_vec_env.py` 的维护中 observation read 已走 `ObservationBatchRequest` / `ObservationBatchPacket`；维护中 vec-env 回归测试也会拒绝 direct observation getter。 | 已在本机通过：`python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "mainline_step_prefers_batch_step_observation_packet or reset_uses_runtime_facade_compatibly"` 和 `python -m pytest tests/world_batch/test_world_batch_vec_env.py -q`。另一台 blocked 设备应先通过 `cmake --build build-workshop --target ef_core ef_py -j4` 恢复 `ef_py`，并安装 `.[rl]` extra 或等价直接依赖后再复测。 |
| `WP7.5-C Compatibility Escape Hatch Reduction` | `pass` | 剩余维护中 seam 已被显式列为 `compatibility-only`：`python/rl/runtime/world_batch/adapter.py` 的 `RuntimeFacadeAdapter.__init__` 中，`self.facade.runtime()` 或 fallback `ef_py.WorldBatchRuntime(...)` 创建集中 compatibility adapter 根部。`tests/runtime/facade/test_runtime_facade.py` 中的 raw `WorldBatchRuntime` 构造属于 `compatibility-only` fixture 覆盖。engagement 测试中用 `facade.runtime().world(...)` 构造 live evidence fixture 的用法属于 `diagnostics-only`、`test-only`，不是维护中训练输入。 | 已使用静态审计命令：`rg -n "RuntimeFacade\\.runtime\\(|\\.runtime\\(\\)|WorldBatchRuntime" python/rl/runtime tests/architecture tests/runtime tests/world_batch --glob "*.py"`。guard 证据已通过：`python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_wp5_design_boundary_gates.py`。 |
| `WP7.5-D Validation And Integration Sync` | `pass` | `WP7.5` 必需产物现已齐全，regression guard 已落到任务文档与测试文件里，且 `WP8` 明确通过引用 `WP7.5` 获得 maintained training-path bridge，而不是重写迁移。 | 当前工作树已完成文档存在性与交叉引用检查；该 gate 不再受额外运行时阻塞。 |

整体结论：`pass`。

原因：

- 验收标准已经显式化，review 产物也已齐全。
- `WP7.5-A/B` 的运行验证已在本机通过；剩余环境分裂仅限另一台设备，应通过安装
  已声明的 `.[rl]` 依赖集并在那台设备上构建 `ef_py` 来处理。
- `WP7.5-C` 已具备显式 allowlist 与 guard 覆盖，且没有把任何剩余 escape hatch
  抬升为维护中的 policy、training 或 learning API。
