# Validation Benchmark Snapshot - Stage C Component Probability

状态：`generated_from_candidate_snapshot / non-authoritative / stage_c_component_probability_only`。

本文档记录当前候选包按 Stage C `component_failure_probability_authority` 候选路径
生成的第一版 component-specific snapshot。它来自
[damage_model_candidate_artifacts.py](../../../../../../tools/maintenance/damage_model_candidate_artifacts.py) `component-probability-snapshot`
对当前 runtime-aligned authority exercise 的 author-side 固定结果。

本文档不是独立 validation result，不创建 runtime descriptor，不授予
`component_failure_probability_authority`、`effect_scale_authority`、`pk_authority`
或 `deterministic_fuze_authority`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `snapshot_status` | `author_snapshot_complete_pending_independent_review` |
| `primary_release_scope` | `component_failure_probability_authority_only` |
| `scope_ref` | [narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md](../../narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md) |
| `runtime_aligned_ref` | [damage_model_candidate_artifacts.py](../../../../../../tools/maintenance/damage_model_candidate_artifacts.py) `runtime-authority-exercise` |
| `snapshot_artifact_ref` | [damage_model_candidate_artifacts.py](../../../../../../tools/maintenance/damage_model_candidate_artifacts.py) `component-probability-snapshot` |
| `stock_runtime_action` | `forbidden_pending_fragility_validation_and_residual_closeout` |

## 2. Current Candidate Snapshot

当前 author-side snapshot 固定的关键结论如下：

| 检查项 | 当前值 |
|---|---|
| primary projected component | `right_aileron_actuator` |
| primary component system | `flight_control` |
| primary redundancy group | `lateral_flight_control_actuators` |
| baseline runtime probability source | `synthetic_sigmoid` |
| descriptor `source_kind` | `validated_physics_surrogate` |
| descriptor `calibration_status` | `calibrated` |
| descriptor `component_failure_probability_authority` | `true` |
| descriptor `effect_scale_authority` | `false` |
| candidate row probability | `0.67` |
| surface probe fixed seeds | `20260526 / 20260527 / 20260528` |
| surface probe stock baseline source | all fixed probe points remain `synthetic_sigmoid` |
| component-specific row scope | only `right_aileron_actuator / flight_control / lateral_flight_control_actuators` |

当前 snapshot 结论：

- 当前 runtime-aligned candidate 已能把 component-specific probability row 绑定到
  `right_aileron_actuator`；
- 同一窄域当前还存在一份三点 surface probe / repeatability snapshot，可验证
  component-specific row 在 inner -> middle -> outer 探针上保持固定 seed、固定 probe 点和单调衰减；
- 该 row 仍只存在于 `test_local_authority_exercise_only` 的 descriptor candidate 内；
- 当前 baseline stock event 仍报告 `synthetic_sigmoid` 概率来源，因此该 snapshot
  不能被误读成 stock authority 已放行。

## 3. 当前解释边界

这份 snapshot 当前只允许支持以下结论：

- Stage C 已经有一张可执行、可追溯、可复跑的 component-specific candidate snapshot；
- projected component row、component provenance 字段以及六维 mechanism-load gate band
  （blast scaled distance / fragment density / fragment energy / penetration margin /
  blast impulse / surface incidence）已经可以由 maintenance tool 机器化检查；
- 同 scope 的 surface probe / repeatability snapshot 已经进入 author-side candidate
  artifact 链，但它仍只是 candidate fragility-surface 证据；
- Stage C 已不再只存在于 runtime test 断言里，也有 package-level candidate artifact。

这份 snapshot 当前**不能**支持以下结论：

- `component_failure_probability_authority` 已经 validated；
- `RES-009 component failure` 已关闭；
- 当前 fragility curve、failure residual 或 uncertainty 已完成独立审计；
- stock runtime authority 已经可以放行。

## 4. 对 residual 的推进含义

这份 snapshot 形成后，相关 residual 当前应解释为：

- `RES-009`：从“只有 test-local authority 演练”推进到“已有 author-side candidate snapshot”，但 fragility calibration、uncertainty 与独立 review 仍缺；
- `RES-010`：Stage C 还没有独立 criteria / result closeout，当前 snapshot 只是 Stage C kickoff artifact；
- `RES-012`：当前 snapshot 仍直接依赖 repo-authored runtime-aligned exercise，因此不能冒充独立 validation。

上述 residual 都**不关闭**。

## 5. 当前判定

当前判定为：

> `Stage C component-specific probability now has a first author-side candidate snapshot, but it remains test-local in origin, non-independent, and insufficient for stock component-probability authority release`.
