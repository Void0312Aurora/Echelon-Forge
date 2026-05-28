# replay / admission matrix

状态：`2026-05-28` 计划/标准文档。本文定义 P4 deterministic fuze 的 replay / admission matrix 草案；它不是当前 admission 结果，不代表 deterministic fuze 已放行。

## Admission 状态枚举

建议使用下列状态：

- `not_admitted`：未申请或缺少 manifest。
- `candidate`：manifest 和证据包存在，但 replay matrix 未通过。
- `admitted_limited_scope`：仅对声明 scope 放行。
- `rejected`：证据或 replay 明确失败。
- `revoked`：曾放行，但代码、数据、模型或 scope 变化后撤销。

当前 A2 P4 状态：`not_admitted` / `deferred`。

## Matrix 轴

每次 admission 至少覆盖这些轴：

- fuze type：`radar_proximity`、`laser_proximity`、`contact` / `impact`、`timed`；
- weapon id / family；
- target type / family；
- aspect：head-on、tail-chase、beam、high-off-boresight；
- closure：low、nominal、high；
- miss distance：direct hit、near miss in trigger radius、near miss outside trigger radius、far miss；
- environment：nominal、declared degraded、out-of-scope；
- backend：固定 simulation backend profile；
- dt：固定 time-step policy；
- replay mode：single run, repeated deterministic replay, branch replay, serialization roundtrip replay。

scope 可以窄化，但不能缺少对 scope 边界和 out-of-scope 回退的测试。

## Required cases

| Case id | fuze type | 几何 | 期望 | Admission 判据 |
|----|----|----|----|----|
| `RDR-HO-IN` | radar proximity | head-on / in radius | 触发或按证据模型给出 no-trigger | event 字段完整，signature evidence ref 匹配，replay 稳定 |
| `RDR-BEAM-EDGE` | radar proximity | beam / trigger edge | 边界行为稳定 | false/missed trigger 在门槛内 |
| `RDR-LOW-SIG` | radar proximity | low signature aspect | 按阈值降低触发可能或 no-trigger | 不得用默认 1.0 proxy 放行 |
| `RDR-OOS` | radar proximity | out-of-scope target/environment | 回退 non-authoritative path | 不得标记 deterministic authority |
| `LSR-SIDE-IN` | laser proximity | side aspect / in radius | 投影/反射证据驱动触发 | event 记录校准 signature source |
| `LSR-NOSE-LOW` | laser proximity | small projection | 低签名边界稳定 | missed trigger 判据满足 |
| `LSR-GRAZE` | laser proximity | hitbox edge graze | 起爆点和目标局部坐标稳定 | replay 误差在容差内 |
| `CNT-DIRECT` | contact / impact | direct structure hit | contact trigger | surface / penetration / inside-hitbox 完整 |
| `CNT-NEAR-MISS` | contact / impact | old radius 内但未接触 | no-trigger | 不得借 proximity radius 起爆 |
| `CNT-GRAZE` | contact / impact | graze angle | 按接触证据触发或 dud | 入射角 / surface normal 可审计 |
| `TMD-ON-TIME` | timed | expected intercept delay | timed detonation | commanded/actual delay 在门槛内 |
| `TMD-NO-TARGET` | timed | delay 到时无目标 footprint | detonated_no_effect 或限定效果 | 不得伪造命中 |
| `TMD-SAFE` | timed | safe separation 未满足 | no detonation 或 safed | safety evidence 完整 |
| `ALL-REPLAY` | all admitted types | fixed seed repeated replay | event 序列一致 | 事件数量、顺序、字段 hash 一致或在容差内 |
| `ALL-BRANCH` | all admitted types | branch replay at pre-terminal tick | child worldline 稳定 | branch point 后 fuze decision 可复现 |
| `ALL-SERIAL` | all admitted types | snapshot serialize/restore | 结果一致 | runtime fuze state 完整保存 |

## 字段完整性门槛

每个 replay event 至少校验：

- `trigger_type`
- `fuze_type`
- `fuze_trigger_radius_m`
- `fuze_delay_s`
- `fuze_reliability`
- `fuze_profile_synthetic`
- `fuze_signature_source`
- `fuze_target_signature`
- `fuze_signature_scale`
- `fuze_effective_reliability`
- `fuze_contact_surface_distance_m`
- `fuze_contact_penetration_depth_m`
- `fuze_contact_surface_tolerance_m`
- `fuze_contact_inside_hitbox`
- `nearest_approach_time_s`
- `detonation_time_s`
- `miss_distance_m`
- target local detonation point
- missile axis
- detonation attitude
- authority manifest id
- evidence refs consumed
- admission state

缺少 authority manifest id 或 evidence refs 时，事件只能标记 diagnostics-only。

## Determinism 门槛

建议 admission 门槛：

- 固定 seed / backend / dt 下，fuze decision event 序列一致；
- `detonation_time_s`、`nearest_approach_time_s`、`miss_distance_m`、target local detonation point 在声明容差内；
- delayed detonation queue 在 serialize / restore 后一致；
- branch replay 从同一 branch point 得到同一 fuze decision；
- out-of-scope case 必须回退为 non-authoritative path；
- schema fixture、synthetic data、engineering proxy 不能让 admission state 变为 admitted。

## Admission 输出

每次 admission 应输出：

- `admission_id`
- `manifest_id`
- `schema_version`
- `admission_status`
- `scope_hash`
- `backend_profile_ref`
- `time_step_policy_ref`
- `code_revision_ref`
- `data_revision_ref`
- `replay_matrix_ref`
- `event_hashes`
- `failed_cases`
- `waivers`
- `residual_risk_ref`
- `revocation_policy_ref`

没有上述输出的测试通过，不构成 deterministic fuze admission。

## 当前结论

当前没有 P4 replay/admission matrix 通过记录。P4 继续 deferred。
