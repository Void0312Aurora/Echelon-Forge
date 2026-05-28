# 独立 fuze authority schema / manifest 草案

状态：`2026-05-28` 计划/标准文档。本文定义独立 fuze authority schema / manifest 草案，用于未来 P4 admission；它不是实现记录，不代表 deterministic fuze 已放行。

## 核心原则

fuze authority 必须独立于 vulnerability descriptor：

- 不复用 `a2.vulnerability_evidence.v1`；
- 不把 vulnerability row、effect scale、component failure probability 或 Pk authority 当作 fuze authority；
- 不允许 aircraft JSON 自声明 deterministic fuze authority；
- 不允许 synthetic fixture、schema fixture 或 engineering surrogate 直接授权；
- 每个 manifest 只对声明的 weapon / fuze type / target family / aspect / closure / miss-distance / environment scope 生效。

建议 schema id：`a2.fuze_authority.v1`。

建议 manifest 文件职责：描述某一窄域引信模型可被 deterministic admission 使用的证据、验证包、回放结果和限制条件。

## Manifest 顶层字段草案

必需字段：

- `manifest_id`：全局唯一 manifest 标识。
- `schema_version`：必须为 `a2.fuze_authority.v1`。
- `status`：`draft`、`candidate`、`admitted`、`rejected`、`revoked`。
- `authority_scope`：授权适用域，必须窄化到 weapon、fuze、target、几何和环境。
- `source_kind`：`external_test_dataset`、`instrumented_range_dataset`、`validated_fuze_surrogate`、`manufacturer_or_public_technical_source`、`engineering_proxy` 等。
- `source_ref`：非空、稳定、可审计来源引用。
- `provenance`：来源、版本、适用范围和限制说明。
- `validation_manifest`：验证包引用和摘要。
- `evidence_refs`：按 fuze type 绑定的证据条目。
- `replay_admission_ref`：回放准入报告引用。
- `deterministic_fuze_authority`：只有 manifest status 为 `admitted` 且所有 gate 通过时才允许为 true。
- `authority_limits`：授权不能覆盖的条件。
- `revocation_policy`：何种代码、数据或模型变更必须撤销或重跑 admission。

禁止字段：

- `vulnerability_rows`
- `effect_scale_authority`
- `component_failure_probability_authority`
- `pk_authority`
- `vulnerability_evidence_dataset_ref`

如果需要引用 vulnerability 或 warhead 证据，只能通过 `dependency_refs` 声明外部依赖和版本，不得把这些依赖提升为 fuze authority。

## authority_scope 草案

`authority_scope` 必须包含：

- `weapon_id` 或 `weapon_family`
- `fuze_type`
- `fuze_profile_ref`
- `warhead_profile_ref`
- `target_type` 或 `target_family`
- `target_signature_scope`
- `aspect_bucket`
- `closure_bucket`
- `miss_distance_bucket`
- `altitude_band`
- `environment_scope`
- `simulation_backend_profile_ref`
- `time_step_policy_ref`
- `geometry_model_ref`

scope 不允许使用过宽的 `all` 默认值。缺少任一关键轴时，manifest 只能保持 `draft` 或 `candidate`，不能 `admitted`。

## validation_manifest 草案

`validation_manifest` 必须包含：

- `schema_version`：建议为 `a2.fuze_validation.v1`。
- `validation_status`：`passed` 或 `validated`。
- `validation_artifact_ref`
- `validation_artifact_sha256`
- `validated_model_ref`
- `validation_dataset_ref`
- `validation_benchmark_ref`
- `validation_metrics_ref`
- `acceptance_criteria_ref`
- `validation_scope`
- `toolchain_ref`
- `reviewer_ref`
- `review_date`

`validation_scope` 必须逐项匹配 `authority_scope`。只给出一个 validation artifact 名称不能构成授权。

## evidence_refs 草案

每条 evidence ref 建议包含：

- `evidence_id`
- `fuze_type`
- `evidence_kind`
- `source_ref`
- `provenance`
- `sample_count`
- `coverage_scope`
- `measurement_units`
- `uncertainty_model_ref`
- `acceptance_criteria_ref`
- `event_fields_required`
- `replay_cases_required`

`evidence_kind` 可包括：

- `trigger_threshold`
- `signature_response`
- `false_trigger_rate`
- `missed_trigger_rate`
- `delay_distribution`
- `arming_safety_logic`
- `contact_surface_response`
- `timed_setting_accuracy`
- `environment_sensitivity`
- `detonation_point_error`

所有 evidence 必须有非空 `source_ref` 和 `provenance`。缺少来源的 evidence 不进入 admission 计算。

## authority gate 草案

建议 admission gate：

1. schema gate：`schema_version == a2.fuze_authority.v1`。
2. status gate：manifest `status == admitted`。
3. scope gate：当前事件的 weapon / fuze / target / aspect / closure / miss-distance / environment 全部落入 `authority_scope`。
4. source gate：`source_kind` 为可授权来源；`engineering_proxy`、`synthetic_fixture`、`schema_fixture` 不可授权。
5. validation gate：`validation_manifest.validation_status` 通过，artifact sha256 非空，scope 与 authority scope 匹配。
6. evidence gate：当前 fuze type 所需证据条目全部存在且通过最小样本量、误差、漏触发、误触发和 delay 门槛。
7. replay gate：replay/admission matrix 全部 required case 通过，且 deterministic replay bitwise 或字段容差满足要求。
8. dependency gate：依赖的 warhead、geometry、target signature、backend profile 和 time-step policy 与 admission 使用版本一致。
9. revocation gate：自 admission 后没有触发 revocation policy 的代码、数据或参数变更。

只有所有 gate 通过，runtime 才可在该窄 scope 内把 deterministic fuze admission 标记为 true。任何 gate 失败时必须回退为 deferred / RNG-compatible path。

## Manifest 样例骨架

```json
{
  "manifest_id": "a2.fuze_authority.example.v1",
  "schema_version": "a2.fuze_authority.v1",
  "status": "draft",
  "deterministic_fuze_authority": false,
  "authority_scope": {
    "weapon_id": "aim_120c",
    "fuze_type": "radar_proximity",
    "fuze_profile_ref": "examples/config/database/weapons/air_to_air/aim_120c.json#fuze",
    "warhead_profile_ref": "examples/config/database/weapons/air_to_air/aim_120c.json#warhead",
    "target_type": "F-16C_Block50",
    "target_signature_scope": "rcs_aspect_calibrated",
    "aspect_bucket": "head_on",
    "closure_bucket": "high_closure",
    "miss_distance_bucket": "near_miss_0_35m",
    "altitude_band": "medium_altitude",
    "environment_scope": "clear_air_nominal",
    "simulation_backend_profile_ref": "a2.backend_profile.locked",
    "time_step_policy_ref": "a2.fixed_step.policy",
    "geometry_model_ref": "a2.aircraft_hitbox_geometry.v1"
  },
  "source_kind": "validated_fuze_surrogate",
  "source_ref": "TBD",
  "provenance": "Draft placeholder only; not authority.",
  "validation_manifest": {
    "schema_version": "a2.fuze_validation.v1",
    "validation_status": "not_validated",
    "validation_artifact_ref": "",
    "validation_artifact_sha256": "",
    "validated_model_ref": "",
    "validation_dataset_ref": "",
    "validation_benchmark_ref": "",
    "validation_metrics_ref": "",
    "acceptance_criteria_ref": "",
    "validation_scope": {}
  },
  "evidence_refs": [],
  "replay_admission_ref": "",
  "authority_limits": [
    "No deterministic fuze authority is granted by this draft."
  ],
  "revocation_policy": {
    "rerun_on_code_paths": [
      "fuze trigger logic",
      "missile guidance integration",
      "damage/effects event recording",
      "hitbox geometry",
      "time-step scheduling"
    ],
    "rerun_on_data_paths": [
      "weapon fuze profile",
      "target signature model",
      "warhead profile",
      "aircraft geometry"
    ]
  }
}
```

## 当前结论

当前项目没有 admitted `a2.fuze_authority.v1` manifest。P4 保持 deferred。
