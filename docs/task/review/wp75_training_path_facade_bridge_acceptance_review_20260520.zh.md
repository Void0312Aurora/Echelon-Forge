# WP7.5 训练路径 facade 桥接验收审查

状态：`2026-05-20` 已收紧验收规则；尚未授予验收通过。

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
| `WP7.5-A Step Execution Mainline` | `blocked` | 维护中的 mainline 代码已通过 `RuntimeFacade.step_execution_batch()` 路由 batch step 请求，且聚焦回归测试已改为在 `tests/world_batch/test_world_batch_vec_env.py` 上记录外层 batch request 标志。静态检查显示维护主线会消费 `ExecutionBatchStepResult.observation_packet`。 | `python -m pytest tests/world_batch/test_world_batch_vec_env.py -k mainline_step_prefers_batch_step_observation_packet -q` 在本机被阻塞：普通 shell 无法导入 `ef_py`，而 `.\tools\maintenance\cmo_env.ps1 python -m pytest ...` 又被 `ModuleNotFoundError: No module named 'torch'` 阻塞。 |
| `WP7.5-B Observation Packet Mainline` | `blocked` | 静态检查显示 `python/rl/runtime/world_batch/adapter.py`、`python/rl/runtime/world_batch_vec_env.py` 与 `python/rl/runtime/cooperative_world_batch_vec_env.py` 的维护中 observation read 已走 `ObservationBatchRequest` / `ObservationBatchPacket`；维护中 vec-env 回归测试也会拒绝 direct observation getter。 | `python -m pytest tests/world_batch/test_world_batch_vec_env.py -k reset_uses_runtime_facade_compatibly -q` 被同一环境分裂阻塞：普通 shell 缺 `ef_py`，maintenance shell 缺 `torch`。 |
| `WP7.5-C Compatibility Escape Hatch Reduction` | `fail` | `python/rl/runtime/world_batch/adapter.py` 中仍存在 `self._compat_runtime = self.facade.runtime()` 这一维护中 adapter seam 根部；本审查也尚未把所有剩余可接受 escape hatch 按 compatibility-only / diagnostics-only 逐项列全。 | 已使用静态审计命令：`rg -n "\\.runtime\\(\\)|RuntimeFacade\\.runtime|WorldBatchRuntime" python/rl/runtime tests/architecture tests/runtime`。必需的 allowlist 仍不完整。 |
| `WP7.5-D Validation And Integration Sync` | `pass` | `WP7.5` 必需产物现已齐全，regression guard 已落到任务文档与测试文件里，且 `WP8` 明确通过引用 `WP7.5` 获得 maintained training-path bridge，而不是重写迁移。 | 当前工作树已完成文档存在性与交叉引用检查；该 gate 不再受额外运行时阻塞。 |

整体结论：`blocked`。

原因：

- 验收标准已经显式化，review 产物也已齐全。
- `WP7.5-A/B` 的运行验证仍被环境分裂阻塞。
- `WP7.5-C` 在剩余 escape-hatch allowlist 补齐前仍为 `fail`。
