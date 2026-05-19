# WP8 学习面验收审查

状态：`2026-05-20` 已收紧验收规则；尚未授予验收通过。

语言版本：

- 英文主文：[wp8_learning_face_acceptance_review_20260520.md](wp8_learning_face_acceptance_review_20260520.md)
- 中文辅文：`wp8_learning_face_acceptance_review_20260520.zh.md`

审查输入：

- [WP8 SCAL 学习面](../simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.zh.md)
- [WP7.5 训练路径 facade 桥接](../simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)

## 1. 必需验收产物

下列产物若不齐全或不同步，`WP8` 验收包即视为不完整：

- `docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.md`
- `docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.zh.md`
- `docs/task/review/wp8_learning_face_acceptance_review_20260520.md`
- `docs/task/review/wp8_learning_face_acceptance_review_20260520.zh.md`

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
| `WP8-A Curriculum And Scenario Generation` | 受检的 curriculum / scenario-generation 文档、任务线要求的 request/versioning 字段，以及用于确认这些请求保持显式且可版本化的精确验证命令或文档检查。 | 只有存在显式 request/versioning 证据，且没有隐藏 simulation authority 时，才能 `pass`。 |
| `WP8-B Evaluation And Capability Profiling` | 受检的 benchmark / profile artifact、score attribution 与 capability evidence 的表达方式，以及用于证明 profile 仍是元数据而不是隐藏 support claim 的精确验证命令或审查检查。 | 只有存在证据化的 profile 纪律，且不会从 helper / probe 存在性推出 support claim 时，才能 `pass`。 |
| `WP8-C World-Model Interface And Learning Evidence` | 受检的 observation/evidence 边界文档、区分 `ObservationPacket` / `DecisionBelief` / `World Truth` 的规则，以及用于验证 provenance 与 replay/diagnostics ancestry 的精确命令或文档检查。 | 只有边界与溯源证据明确，且 learning 不会变成 truth source 时，才能 `pass`。 |
| `WP8-D Integration And Index Sync` | 必需产物存在性确认、`WP7.5` 仍是 maintained training-path bridge 的引用确认，以及中英双文保持对齐的确认。 | 只有发布、交叉引用与 bridge ownership 三者自洽时，才能 `pass`。 |

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
| `WP8-A Curriculum And Scenario Generation` | `fail` | 当前任务文档只定义了该流与 gate 规则，但本审查尚未记录除规划文档之外的具体 curriculum / scenario-generation request 字段或已核对 artifact。 | 尚未记录 gate 级验证命令或已核对 artifact。 |
| `WP8-B Evaluation And Capability Profiling` | `fail` | 当前任务文档只定义了 benchmark / profile scope 与 gate 规则，但本审查尚未记录已核对的 benchmark / profile artifact、score attribution 证据或 profile 验证命令。 | 尚未记录 gate 级验证命令或已核对 artifact。 |
| `WP8-C World-Model Interface And Learning Evidence` | `fail` | 当前任务文档只定义了 `ObservationPacket` / `DecisionBelief` / `World Truth` 的目标边界，但本审查尚未记录已核对的 evidence-boundary artifact 或 provenance 验证命令。 | 尚未记录 gate 级验证命令或已核对 artifact。 |
| `WP8-D Integration And Index Sync` | `pass` | 必需产物现已齐全，`WP8` 明确把 `WP7.5` 作为 maintained training-path bridge 引用，中英双文也已作为本次验收包的一部分建立。 | 当前工作树已完成文档存在性与交叉引用检查；该 gate 不受额外运行时阻塞。 |

整体结论：`fail`。

原因：

- 验收标准已经显式化，review 产物也已齐全。
- `WP8-A/B/C` 仍缺少必需的已核对 artifact 与 gate 级证据，因此当前不能报告为已验收。
