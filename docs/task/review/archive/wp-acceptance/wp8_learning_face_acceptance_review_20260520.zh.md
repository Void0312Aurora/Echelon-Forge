# WP8 学习面验收审查

状态：`2026-05-20` 已验收的 documentation-only Learning-face 任务族。

语言版本：

- 英文主文：[wp8_learning_face_acceptance_review_20260520.md](wp8_learning_face_acceptance_review_20260520.md)
- 中文辅文：`wp8_learning_face_acceptance_review_20260520.zh.md`

审查输入：

- [WP8 SCAL 学习面](../simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.zh.md)
- [WP8-A 课程与场景生成](../simulation_architecture/wp8_learning_face/wp8_curriculum_scenario_generation_cluster_20260520.zh.md)
- [WP8-B Evaluation 与 Capability Profiling](../simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.zh.md)
- [WP8-C World-Model 接口与学习证据](../simulation_architecture/wp8_learning_face/wp8_world_model_interface_and_learning_evidence_cluster_20260520.zh.md)
- [WP7.5 训练路径 facade 桥接](../simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)

## 1. 必需验收产物

下列产物若不齐全或不同步，`WP8` 验收包即视为不完整：

- `docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.md`
- `docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.zh.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_curriculum_scenario_generation_cluster_20260520.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_curriculum_scenario_generation_cluster_20260520.zh.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.zh.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_world_model_interface_and_learning_evidence_cluster_20260520.md`
- `docs/task/simulation_architecture/wp8_learning_face/wp8_world_model_interface_and_learning_evidence_cluster_20260520.zh.md`
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
| `WP8-A Curriculum And Scenario Generation` | `pass` | 已检查 `wp8_curriculum_scenario_generation_cluster_20260520.md` 与 `.zh.md`。契约列出 `request_id`、`request_version`、`contract_version`、`scenario_set_id`、`scenario_family_id`、`selection_policy_id`、`selection_constraints`、`seed_policy_id`、`seed_mode`、`seed_source`、`seed_scope`、`curriculum_phase_id`、`phase_order`、`entry_condition`、`exit_condition`、`generation_request_version`、`requested_output_shape`、`input_refs`、`result_id`、`result_version`、`status`、`generated_scenario_set_id` 与 `result_refs`。该切片明确 generation request 是显式请求，不是隐藏仿真 authority。 | `git diff --check` 通过。`rg -n "WP8-A|curriculum|scenario selection|scenario-set|seed policy|curriculum phase|generation request|request/result|version" docs/task/simulation_architecture/wp8_learning_face docs/task/simulation_architecture/wp75_training_path_facade_bridge docs/task/review` 通过。 |
| `WP8-B Evaluation And Capability Profiling` | `pass` | 已检查 `wp8_evaluation_capability_profiling_cluster_20260520.md` 与 `.zh.md`。契约定义 benchmark protocol 字段，区分 metadata、profile claims 与 hidden support claims，分解 score attribution，并声明 helper/probe presence 最多解释 observability 或 deployment state，不能证明 support。 | `git diff --check` 通过。`rg -n "WP8-B|benchmark protocol|profile schema|score attribution|capability evidence|hidden support|helper|probe|support claim|WP7.5" docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520*.md docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520*.md docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520*.md` 通过。 |
| `WP8-C World-Model Interface And Learning Evidence` | `pass` | 已检查 `wp8_world_model_interface_and_learning_evidence_cluster_20260520.md` 与 `.zh.md`。契约保持 `ObservationPacket`、`DecisionBelief`、`World Truth` 与 `LearningEvidenceBundle` 分离，要求 observation / belief / replay / diagnostics ancestry，并声明 evidence bundle 不修改状态，也不能绕过相关 `WP8-B` gate 变成 support claim。 | `git diff --check` 通过。`rg -n "WP8-C|world-model|World Truth|ObservationPacket|DecisionBelief|learning evidence|provenance|replay|diagnostics ancestry|WP7.5" docs/task/simulation_architecture/wp8_learning_face/wp8_world_model_interface_and_learning_evidence_cluster_20260520*.md docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520*.md docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520*.md docs/task/review` 通过。 |
| `WP8-D Integration And Index Sync` | `pass` | 必需产物已齐全，`WP8` 明确把 `WP7.5` 作为 maintained training-path bridge 引用，WP8 任务族已链接 A/B/C 子切片，`docs/task/simulation_architecture/README.md` 与 `.zh.md` 已列出已验收 WP8 输出，本 review 双文也已记录 gate 级证据。 | `git diff --check` 通过。`rg -n "WP8|Learning face|curriculum|evaluation|capability profiling|scenario generation|world-model|learning evidence" docs/plan/architecture docs/task/simulation_architecture docs/task/review` 通过。 |

整体结论：`pass`。

原因：

- `WP8-A/B/C` 已具备已检查的双语任务切片，且写明显式 contract 字段与
  doc-only 验证证据。
- `WP8-D` 发布 / 索引同步已完成，并且 `WP8` 继续把 maintained training-path
  bridge 指向 `WP7.5`。
- WP8 保持 documentation-only；本次验收不要求本机 RL 训练、benchmark run 或
  world-model 实现。
