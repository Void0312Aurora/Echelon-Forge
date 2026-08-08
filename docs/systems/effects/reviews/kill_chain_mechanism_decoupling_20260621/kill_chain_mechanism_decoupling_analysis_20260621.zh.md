# 杀伤链机制抽象与解耦分析

日期：`2026-06-21`

状态：完成版研究记录 / 解耦诊断已闭环，P2 runtime facade、P3 旧倍率入口删除、
P4 runtime named load factors 和 P5 runtime response owner 迁移已落地。本文不做杀伤参数重调，不声明真实
AIM-120C、F-16C、Pk 或确定性杀伤权威；它把当前仓库的工程代理链路拆成可校准的
阶段，并给出后续重构顺序。P6 engineering-proxy admission gate 已落地并开放单层
proxy calibration plan；P5 load-row response 字段已从 ABI 删除，真实世界权威声明仍保持关闭。

## 结论

当前 8 km / 30 度偏置场景的表象是“像没打中、近炸杀伤偏低”，但前一份诊断记录
已经显示：导弹实际进入了近炸/引信窗口，主要问题是近炸后的有效载荷、部件响应
和后果投影被多层弱化。

更深一层看，问题很可能不是单个参数太小，而是机制耦合过重：

- 同一个距离/几何事实在引信质量、战斗部空间投影、机制载荷、易损性缩放、
  部件失效概率和状态传播里多次参与缩放。
- `effect_scale` 同时像“空间覆盖”“战斗部作用强度”“部件受载权重”“后果强度”
  几种东西，导致很难判断 8-12 m 区间到底是战斗部没覆盖、载荷太低、
  目标阈值太高，还是后果投影太保守。
- 如果在这种状态下直接校准数据，容易得到一组能过单个场景、但不可解释且互相抵消
  的参数。

因此后续应先做抽象和解耦，再做数据校准。

## 本文完成范围与证据

本文的完成对象是机制抽象、耦合边界、迁移顺序和可执行诊断证据，不是调高近炸杀伤、
改 C++ 事件合同或发布真实弹种/目标校准数据。

已闭环内容：

- 当前链路分析：本文已把引信、空间投影、机制载荷、目标易损性、部件响应和后果投影
  的重复缩放关系拆开说明。
- 阶段抽象：`approach -> fuze_decision -> warhead_load_field -> component_response -> consequence_projection`
  已落到只读 probe 输出，见
  [kill_chain_decoupling_stage_abstraction_slice_20260621.zh.md](kill_chain_decoupling_stage_abstraction_slice_20260621.zh.md)。
- 基线复现：8 km / 30 度 AIM-120C 左右镜像和近炸距离 sweep 已由同一工具生成，
  见 [kill_chain_decoupling_probe_results_20260621.zh.md](kill_chain_decoupling_probe_results_20260621.zh.md)。
- P0 标量账本：`fuze_quality`、`effect_scale`、`spatial_effect_scale`、
  `component_failure_probability` 等 producer / owner / consumer 关系已机器可读，
  见 [kill_chain_scalar_coupling_ledger_20260621.zh.md](kill_chain_scalar_coupling_ledger_20260621.zh.md)。
- P1/P4 `effect_scale` 拆分：effects-event 级 spatial、armor/exposure、
  threshold 和 vulnerability 因子已进入摘要和账本，runtime component load rows
  已暴露 named load factors，见
  [kill_chain_effect_scale_decomposition_probe_20260621.zh.md](kill_chain_effect_scale_decomposition_probe_20260621.zh.md)。
- P1-b 逐部件视图：每个 component row 的 `effect_scale`、failure probability、
  case aggregate factors 和 residual proxy 已并排输出，见
  [kill_chain_component_load_factor_view_20260621.zh.md](kill_chain_component_load_factor_view_20260621.zh.md)。
- P3 清理：`fuze_quality -> effective.damage` 旧隐式倍率已从 runtime surface 删除，见
  [kill_chain_fuze_damage_policy_slice_20260621.zh.md](kill_chain_fuze_damage_policy_slice_20260621.zh.md)。
- P2/P5 runtime facade：`EffectsEvent` 已能转换到
  `a2.kill_chain_runtime_facade.v1`，并把 response-owner 形状暴露给 diagnostics，
  见 [kill_chain_runtime_facade_slice_20260621.zh.md](kill_chain_runtime_facade_slice_20260621.zh.md)。
- P6 admission：`a2.kill_chain_calibration_admission.v1` 已进入 probe 顶层输出，
  当前通过 repository engineering proxy 打开 guarded 单层校准计划，见
  [kill_chain_calibration_admission_gate_20260621.zh.md](kill_chain_calibration_admission_gate_20260621.zh.md)。

当前 baseline artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json`

P6 external evidence preflight artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_preflight_20260621.json`

P6 external evidence template artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_template_20260621.json`

P6 external evidence template check artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_template_check_20260621.json`

P6 external evidence supplemental contract artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_supplemental_contract_20260621.json`

P6 external evidence supplemental contract check artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_supplemental_contract_check_20260621.json`

P6 current manifest readiness check artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_current_manifest_readiness_check_20260621.json`

P0~P6 completion audit artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_completion_audit_20260621.json`

当前关键事实：

- artifact 大小 `1186180` bytes。
- guidance cases：`4`；proximity cases：`7`。
- scalar ledger rows：`646`。
- component factor rows：`33`。
- rows with response fields on load row：`0`。
- component response facade rows：`33`。
- runtime facade cases：`11`。
- `component_load_named_factor_available=63`。
- `runtime_dto_authority=true`，`component_response_rows_available=true`。
- P3：`legacy_fuze_quality_damage_multiplier_removed=true`。
- P6 admission：`admission_granted=true`，`admission_mode=engineering_proxy_single_layer_guarded`。
- P6 engineering proxy evidence：读取 MLF-10 retained report，真实 authority
  `admitted_record_count=0`，但 `engineering_proxy_record_count=2`，
  `engineering_proxy_layer_ids=[fuze_data, warhead_data, target_response_data, consequence_data]`。
- P6 evidence gap：缺
  `component_failure_probability_authority`、`deterministic_fuze_authority`、
  `effect_scale_authority` 和 `pk_authority`；`warhead_data` 已能追踪到相关 blocked
  evidence ids 与 blocking reason counts，`target_response_data` 也已能追踪到
  `MLF10-CURRENT-STAGE-C-COMPONENT-PROBABILITY` 和
  `MLF10-CURRENT-TP21-SELECTED-DEBRIS` 这两条 blocked evidence。
- P6 evidence unblock queue：`evidence_unblock_queue_count=4`，按 open item
  count 排序为 `MLF10-CURRENT-BECO-RECALCULATED-BLAST`、
  `MLF10-CURRENT-STAGE-B-EFFECT-SCALE`、
  `MLF10-CURRENT-STAGE-C-COMPONENT-PROBABILITY`、
  `MLF10-CURRENT-TP21-SELECTED-DEBRIS`。
- P6 external evidence preflight：schema
  `a2.kill_chain_calibration_evidence_preflight.v1`，artifact 大小 `18822` bytes，
  不跑仿真即可复核 engineering-proxy admission、MLF-10 authority gap 与 unblock queue。
- P6 external evidence template：schema
  `a2.kill_chain_calibration_evidence_template.v1`，artifact 大小 `14863` bytes；
  MLF-10 v1 可接收 `effect_scale_authority` 与
  `component_failure_probability_authority` 的 manifest record 模板，
  `deterministic_fuze_authority` 与 `pk_authority` 已指向 supplemental evidence
  contract 模板。
- P6 external evidence template check：schema
  `a2.kill_chain_calibration_evidence_template_check.v1`，artifact 大小 `3894`
  bytes，当前 template `ready_for_mlf10_audit=false`，blocker 为
  `placeholder_values_present` 和 `population_fields_invalid`。
- P6 external evidence supplemental contract：schema
  `a2.kill_chain_calibration_supplemental_evidence_contract.v1`，artifact 大小
  `7249` bytes；覆盖 `deterministic_fuze_authority` 和 `pk_authority`，并为
  `fuze_decision` / `consequence_projection` 绑定 stage delta guard 要求。
- P6 external evidence supplemental contract check：schema
  `a2.kill_chain_calibration_supplemental_evidence_contract_check.v1`，artifact 大小
  `3357` bytes，当前 `ready_for_authority_admission=false`，blocker 为
  `placeholder_values_present` 和 `population_fields_invalid`。
- P6 current manifest readiness check：artifact 大小 `6599` bytes；当前 MLF-10
  manifest 有 `7` 条 records，其中 `4` 条 authority candidates 全部 blocked，
  `ready_record_count=0`，`blocked_record_count=4`。
- P0~P6 completion audit：schema `a2.kill_chain_completion_audit.v1`，artifact
  大小 `4562` bytes，`closed_item_count=7/7`，`blocked_item_ids=[]`，
  `goal_complete=true`，`contract_surface_closed=true`。
- P6 single-layer plan：`plan_available=true`，`dry_run_only=true`，
  `admitted_layer_count=4`；每个 plan 仍要求单层 mutation 和 delta guard。
- P6 delta guard：plan 绑定 `a2.kill_chain_calibration_delta_guard.v1`，要求
  before/after report 中目标 stage 有变化、冻结 stage 无变化；CLI 可直接读取两个
  report JSON 并输出 guard JSON。
- `aim120_8km_left_30deg` 最近距 `10.963446 m`，最大部件失效概率 `0.006350`，
  component factor rows `3`。
- `aim120_8km_right_30deg` 最近距 `10.963479 m`，最大部件失效概率 `0.006356`，
  component factor rows `4`。

验证：

```bash
python -m pytest \
  tests/tools/test_kill_chain_decoupling_probe.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_summary.py \
  -q
```

结果：`36 passed`。

补充 runtime facade / 合同 / 绑定验证：

```bash
./.venv/bin/python -m pytest -q \
  tests/runtime/engagement/test_launch_adapter_static_shape.py \
  tests/runtime/engagement/test_engagement_contract_shape.py \
  tests/runtime/engagement/test_diagnostics_trace_contract.py \
  tests/runtime/engagement/test_munition_damage_adapter.py \
  tests/runtime/bindings/test_bindings_engagement_surface.py \
  tests/tools/test_kill_chain_decoupling_probe.py
```

结果：`42 passed`。

## 当前耦合链路

### 1. 引信层同时承担决策和强度缩放

`src/systems/combat/damage_system_common.h` 中，引信评估会计算 sensor opportunity、
mechanism range quality、目标探测、终端制导支持和起爆概率：

- `damage_fuze_surrogate_evidence(...)` 生成 `sensor_opportunity_score`、
  `target_detection_confidence` 和 `mechanism_coverage_score`。
- `damage_fuze_detonation_probability(...)` 负责给出是否起爆的概率。
- 历史兼容路径曾在近炸成立后用 `m[i].fuze_quality = quality`，随后进入 effects 前
  执行 `effective.damage = effective.damage * (0.6 + 0.4 * m[i].fuze_quality)`。
  当前这条 runtime 路径已删除。

这条历史路径意味着同一个“离得远/近炸质量一般”的事实，既影响是否起爆，又影响战斗部输入强度。
合理边界应是：引信决定是否起爆、何时何处起爆、决策置信度；它不应再暗中改变
战斗部装药本身的强度。

### 2. 空间投影层把多种因素压成一个 `effect_scale`

`src/models/weapons/detail/default_effects_warhead_detail.inc` 中：

- `resolve_spatial_projection_radius_m(...)` 用 `lethal_radius * projection.radius_fraction`
  得到空间投影半径。
- `projected_spatial_effect_scale(...)` 根据距离和半径给出基础空间衰减。
- `make_default_effects_spatial_projection_candidate(...)` 又把基础空间衰减、near-field
  floor、axis weight、orientation weight、armor scale、exposure scale 和 sampling scale
  全部乘到 `candidate.effect_scale`。

这个 `effect_scale` 信息量太大：它既包含几何交会，也包含方向、装甲、暴露和采样。
之后它还被当作 system severity、component mechanism scale、load event 字段和
后果传播强度继续使用。

### 3. 机制载荷层再次使用距离和几何

`estimate_warhead_mechanism_load(...)` 又重新计算 `radius_quality = 1 - distance / radius`，
并结合 exposure、axis/orientation pattern、closure、spatial sample 去生成破片能量、
面密度、爆风超压/冲量、连续杆切割裕度等载荷事实。

这一步本来很适合作为“战斗部载荷场”的唯一出口，但当前它和 `effect_scale` 并行存在，
并且两者都被后续部件概率消费。结果是：同一个 miss distance 既降低空间强度，也降低
机制载荷，还可能继续降低部件概率尾部。

### 4. 易损性和部件响应仍在重复缩放

`make_vulnerability_adjustment(...)` 会按 family、aspect、closure、direct/near-miss
scale 生成目标易损性缩放；非直击时还继续乘入 `0.85 + 0.15 * spatial_effect_scale`。

`component_failure_probability(...)` 再把 severity、mechanism scale、component scale、
mechanism load scale、系统脆弱性、依赖复杂度和已有损伤状态相乘。非直击路径还额外有
subthreshold tail、projection response、load response、component response 和 pre-damage
response。

这说明“近炸未直接命中”在这里不是一次惩罚，而是经过了多次门控和尾部函数。
对于 8-12 m 这种边缘区间，多个平滑函数叠加后会形成很陡的实际落差。

### 5. 状态和后果层继续消费 `effect_scale`

`apply_component_damage_state(...)` 用 `failure_probability` 和 `effect_scale` 一起减少
component integrity；`apply_component_dependency_damage(...)` 又用 failure probability
和 `effect_scale` 推导依赖损伤。

空域后果里，`default_effects_air_domain.h` 还把 severity、`scratch.spatial_effect_scale`、
`scratch.sampled_mechanism_scale` 和 vulnerability adjustment 再相乘，得到平台/机体
后果强度。

这使得一个低 `effect_scale` 会在载荷、概率、完整性和平台后果中连续变小。

## 重复变量归属表

| 变量/事实 | 当前出现位置 | 风险 | 建议唯一归属 |
| --- | --- | --- | --- |
| 最近距、相对姿态、closure | 引信质量、空间投影、机制载荷、易损性、概率尾部 | 同一几何事实被多次折损 | `ApproachFact`，只作为几何输入 |
| 引信可靠性、sensor opportunity | 起爆概率、effects confidence、damage 缩放 | 可靠性和毁伤强度混在一起 | `FuzeDecision`，只决定起爆/不起爆 |
| 空间覆盖/方向/暴露/装甲/采样 | `effect_scale` 一个复合标量 | 无法知道弱杀伤来自哪一项 | `WarheadLoadField` 的命名因子 |
| 破片/爆风/连续杆载荷 | mechanism load rows、probability channel | 载荷事实和失效概率互相掺杂 | `WarheadLoadField`，只给载荷 |
| 目标脆弱性、冗余、阈值 | vulnerability scale、component scale、probability、状态传播 | 目标数据和后果政策混合 | `TargetSusceptibility` + `ComponentResponse` |
| 平台 kill/loss/reward | component state、platform consequence、Pk trend | 容易把局部损伤直接解释为 Pk | `ConsequenceProjection`，只消费响应结果 |

## 建议的抽象边界

### `ApproachFact`

来源：制导/运动学/最近接近计算。

字段示例：

- `closest_distance_m`
- `closest_point_local_forward/right/up_m`
- `closure_mps`
- `relative_velocity_mps`
- `aspect_bucket`
- `terminal_track_valid`
- `approach_confidence`

边界：不包含 damage、probability of kill、component failure，也不包含战斗部强度。

### `FuzeDecision`

来源：引信模型。

字段示例：

- `can_detonate`
- `detonation_probability`
- `detonation_sample`
- `detonation_time_s`
- `detonation_point_source`
- `fuze_reliability`
- `sensor_opportunity_score`
- `target_detection_confidence`
- `reason`

边界：只决定是否起爆，以及起爆事件的置信度。`fuze_quality` 不应再作为
warhead damage multiplier。

### `WarheadLoadField`

来源：战斗部作用模型。

字段示例：

- `spatial_intersection_fraction`
- `pattern_weight`
- `orientation_weight`
- `receiver_exposure_fraction`
- `armor_transmission`
- `sampling_confidence`
- `fragment_energy_j`
- `fragment_areal_density_per_m2`
- `blast_overpressure_kpa`
- `blast_impulse_kpa_ms`
- `rod_cut_margin`
- `load_source`

边界：它描述“目标/部件受到了什么载荷”，不输出 component failure probability。
当前 `ComponentLoadEvent` 和 `KillChainComponentLoadFact` 已暴露上述 named load factors；
`effect_scale` 仍作为兼容复合字段保留，后续消费者应逐步从复合字段迁移到命名因子。

### `TargetSusceptibility`

来源：目标数据和校准数据。

字段示例：

- component identity / system / redundancy group
- armor / shielding / exposed area
- component criticality
- failure thresholds by mechanism
- vulnerability evidence row / calibration status
- synthetic-vs-admitted authority flags

边界：它是目标被打后的响应参数，不回写引信和战斗部载荷。

### `ComponentResponse`

来源：部件响应模型。

字段示例：

- `failure_probability`
- `failure_sample`
- `integrity_loss`
- `failure_mode`
- `response_source`
- `calibrated`
- `evidence_row_id`

边界：这是唯一生成部件失效概率的地方。非直击 tail、阈值、概率上限、已有损伤增敏
都应收敛到这里，不再分散在空间投影、易损性缩放和后果传播里。

### `ConsequenceProjection`

来源：部件状态到系统/平台/训练信号的投影。

字段示例：

- system availability deltas
- aircraft structural/sensor/propulsion/fire consequences
- platform loss state
- reward/probe projection

边界：只消费 component response 和已有系统状态，不再改变战斗部载荷或部件概率。

## 解耦规则

1. 一个事实只有一个主人：最近距归 `ApproachFact`，引信可靠性归 `FuzeDecision`，
   战斗部载荷归 `WarheadLoadField`，目标阈值归 `TargetSusceptibility`。
2. 引信质量不能作为战斗部威力缩放。它可以作为起爆决策、事件 confidence 或诊断字段。
3. `effect_scale` 必须拆成命名因子。至少区分空间交会、方向图、暴露、装甲传递、
   采样置信度和载荷强度。
4. 载荷事实不直接等同杀伤概率。破片面密度、爆风冲量和 rod cut margin 是输入；
   failure probability 是响应层输出。
5. 非直击概率尾部只能在 `ComponentResponse` 中出现一次，避免投影层、易损性层和
   状态层各自再做一套“近炸修正”。
6. 诊断按层报告，不只报告最终 target active 或 failure count。8 km / 30 度场景
   至少要同时输出 approach、fuze、load、response、consequence 五段。

## 迁移路线与当前状态

下面路线保留为后续工作分解。本文已经完成 P0/P1 的只读诊断闭环，完成 P4 的
diagnostic factor view 和 runtime named load factor 合同，把 P3 的隐式倍率改成默认关闭的 runtime policy 和诊断字段，完成
P2 兼容 runtime facade，并把 P5 response-owner rows 与模型内部写入路径迁移到
`ComponentResponseRow`。P6 admission gate 已机器化，并在 repository engineering proxy
模式下开放 guarded 单层校准计划；真实世界 Pk / 确定性引信权威仍保持关闭。

### P0：建立耦合账本

先不改行为，把所有用于缩放的标量列出来：`fuze_quality`、`effect_scale`、
`spatial_effect_scale`、`sampled_mechanism_scale`、`vulnerability_effect_scale`、
`component_scale`、`mechanism_load_scale`、`near_miss_scale`、probability tail 系数。

验收：每个标量标注当前生产者、消费者、物理/工程含义和是否可校准。

当前状态：诊断层已完成。`kill_chain_scalar_coupling_ledger_20260621.zh.md` 和
`kill_chain_decoupling_probe_20260621.json` 已给出 `646` 条 scalar ledger rows。

### P1：新增分层诊断，不改变结果

给 8 km / 30 度和 0.5/2/4/8/10.96/12 m 近炸 sweep 增加同一套 stage report：

- approach：最近距、local point、closure、terminal track。
- fuze：起爆概率、sample、sensor opportunity、target detection。
- load：projection radius、spatial intersection、pattern/exposure/armor/sampling、
  fragment/blast/rod load。
- response：component threshold、mechanism load scale、failure probability、failure mode。
- consequence：component integrity、system health、platform/loss-state delta。

验收：报告能解释“8 km / 30 度到底弱在哪一层”，而不是只显示最终无失效。

当前状态：诊断层已完成。stage abstractions、baseline sweep、effects-event factor view
和 per-component factor rows 已分别记录在本目录的四份 follow-on 文档中。当前解释是：
8 km / 30 度场景已进入 fuze/effects，弱化主要集中在 load/response/consequence 边界，
不是单纯没有近炸事件。

### P2：引入 runtime DTO / facade

先在内部或诊断 facade 中引入 `ApproachFact`、`FuzeDecision`、`WarheadLoadField`、
`TargetSusceptibility`、`ComponentResponse`、`ConsequenceProjection` 概念结构。
当前实现已让 Python bindings、事件存储和测试读取 runtime DTO 与
`ComponentResponseRow`。

验收：旧测试通过；新诊断可以从新结构读取。

当前状态：runtime DTO / facade 已完成。当前合同新增
`a2.kill_chain_runtime_facade.v1`，并通过 `make_kill_chain_runtime_facade(const EffectsEvent&)`
把 `EffectsEvent` 转换成 ApproachFact、FuzeDecision、WarheadLoadField、
TargetSusceptibility、ComponentResponse 和 ConsequenceProjection 结构。Python binding
和 `kill_chain_decoupling_probe.py` 已能读取该结构。

边界：这不是参数重调。`ComponentResponse` 现在读取
`EffectsEvent.component_response_rows`。`ComponentMechanismLoadRow` 上的 response 字段已从
ABI 删除；差异诊断现在以
`rows_with_response_fields_on_load_row=0` 作为 P5 owner 清理证据。

### P3：移除引信到伤害的隐式缩放

将 `effective.damage *= 0.6 + 0.4 * fuze_quality` 改为可控开关或诊断字段，
并默认关闭。关闭时，起爆与否仍由 `FuzeDecision` 决定；战斗部载荷由战斗部数据
和起爆几何决定。

验收：固定 `WarheadLoadField` 时，改变 fuze reliability 只影响起爆发生率/置信度，
不改变已经起爆样本的载荷大小。

当前状态：旧倍率 runtime policy 与诊断字段已删除。已验证已经起爆样本不再被
`fuze_quality` 改写；后续只能通过单层 engineering-proxy evidence/admission 路径进入校准。

### P4：拆分 `effect_scale`

扩展 `ComponentLoadEvent` 或新增 load-factor row，至少显式保留：

- `spatial_intersection_fraction`
- `pattern_weight`
- `orientation_weight`
- `receiver_exposure_fraction`
- `armor_transmission`
- `sampling_confidence`
- `load_intensity_scale`

`effect_scale` 是当前 load 侧聚合量，但不能再作为唯一权威解释字段。

验收：近/远、左右镜像、不同局部命中点能看到具体哪个因子变化，而不是只看到
一个 `effect_scale` 变小。

当前状态：diagnostic + runtime 合同切片已完成。当前 probe 已输出 effects-event 级
spatial / armor / exposure / threshold / vulnerability 因子，并输出逐部件
`component_load_factor_rows` 与 residual proxy。`ComponentLoadEvent` 和
`KillChainComponentLoadFact` 现已包含 `spatial_intersection_fraction`、
`pattern_weight`、`orientation_weight`、`receiver_exposure_fraction`、
`armor_transmission`、`sampling_confidence` 和 `load_intensity_scale`；
`effect_scale` 继续作为当前 load 侧聚合量，而不再是唯一解释字段。

### P5：收敛部件响应模型

把非直击 tail、threshold、probability ceiling、pre-damage amplification 统一到
`ComponentResponse`。此阶段才适合校准部件失败曲线。

验收：固定 load facts 时，响应层的概率曲线可单独绘制；改变 target vulnerability
只改变 response，不改变 approach/fuze/load。

当前状态：response-owner facade / DTO 形状、event-level runtime owner rows 和模型内部
scratch 写入路径均已完成迁移。P1-b 已证明 `effect_scale` 最大的部件不一定产生最大
failure probability；P5 边界切片进一步证明当前 `33` 条 component factor rows 上
`response_fields=[]`，`response_owner_violation_field_counts={}`。新增
`ComponentResponseRow` / `KillChainComponentResponseFact` 已把 probability、sample、
failure mode 和 integrity before/after 写入并投影到 `ComponentResponse` owner，并在
diagnostics 中作为 runtime DTO-backed rows 读取。

剩余边界：有效 response owner 已迁移到 `ComponentResponseRow`；后续只处理消费者迁移。

### P6：再做数据校准

校准拆成四类，不混用：

- 引信数据：可靠性、探测窗口、delay、detonation probability。
- 战斗部数据：投影半径、破片数量/质量/速度、爆风衰减、方向图。
- 目标响应数据：部件阈值、装甲/遮蔽、冗余、失效模式概率。
- 后果数据：部件失效到平台 loss/reward 的映射。

验收：每次校准只改变一个层级的参数，并能用 stage report 证明影响没有跨层泄漏。

当前状态：admission gate 已完成，工程代理校准入口已打开。`calibration_admission`
顶层报告把 P6 拆成 `fuze_data`、`warhead_data`、`target_response_data` 和
`consequence_data` 四个互斥 layer admission，并要求每次校准只改变一个 layer、
带 before/after stage report。当前 `admission_granted=true`，模式为
`engineering_proxy_single_layer_guarded`；probe 会读取 MLF-10 retained admission report，
其中 `engineering_proxy_record_count=2`，用于工程代理校准入口。真实 authority 的
`admitted_record_count=0` 仍只表示不能声明真实 Pk、确定性引信或真实弹种/目标权威。
`single_layer_calibration_plan` 已输出 P6 dry-run 合同，并绑定
`calibration_delta_guard`；当前 `plan_available=true`，四个 layer 均可按
engineering-proxy scope 单独开放，冻结其他 stage，并要求 before/after
report 通过 delta guard；该 guard 已暴露为 `kill_chain_decoupling_probe.py`
CLI。`external_evidence.layer_gap_summary` 还会列出每个 layer 缺失的 authority field、
相关 evidence id 和 blocking reason counts。P6 contract surface 已把 MLF-10 v1 可接收的
`effect_scale_authority` / `component_failure_probability_authority` 与 supplemental
contract 覆盖的 `deterministic_fuze_authority` / `pk_authority` 分开；后两者当前也只是
模板和 readiness check，不是 admitted evidence。P5 load-row response owner 已清理。本文和相关 probe 继续明确拒绝
calibration authority、real-world Pk 和 deterministic fuze authority。

## P0~P6 完成性审计

| 项 | 当前结论 | 证据 | 剩余边界 |
| --- | --- | --- | --- |
| P0 | 已闭合 | `scalar_coupling_summary.scalar_count=646`，账本标注 producer / owner / consumer / calibration-ready | 仍是诊断账本，不释放调参权威 |
| P1 | 已闭合 | `4` 个 guidance case、`7` 个 proximity case 均有 stage abstractions | 不改变默认杀伤结果 |
| P2 | 已闭合 | `a2.kill_chain_runtime_facade.v1`，`runtime_dto_authority=true`，`runtime_facade_case_count=11` | 不改变默认杀伤参数 |
| P3 | 已闭合 | 旧引信质量伤害倍率 surface 已删除 | 不声明真实引信可靠性 |
| P4 | 已闭合 | `component_load_named_factor_available=63`，`ComponentLoadEvent` / `KillChainComponentLoadFact` 暴露 7 个 named load factors | 聚合 `effect_scale` 仍是当前 load scalar，后续可继续拆分消费者 |
| P5 | 已闭合 | `rows_with_response_fields_on_load_row=0`，`component_response_row_count=33`，`component_response_rows_available=true` | 后续只处理消费者迁移 |
| P6 | 已闭合工程代理校准入口；admission/evidence intake、evidence-gap summary、evidence-unblock queue、evidence template/check、supplemental contract/check、preflight、completion audit、dry-run plan 和 delta guard surface 已闭合 | `calibration_admission.admission_granted=true`，`admission_mode=engineering_proxy_single_layer_guarded`，MLF-10 retained report `engineering_proxy_record_count=2`，`admitted_record_count=0`，`engineering_proxy_layer_ids=[fuze_data, warhead_data, target_response_data, consequence_data]`，`completion_audit.items[P6].status=closed`，`single_layer_calibration_plan.plan_available=true`，`admitted_layer_count=4`，`delta_guard_schema_version=a2.kill_chain_calibration_delta_guard.v1` | 仅限工程代理校准；真实 Pk / deterministic fuze / stock weapon-target authority 仍为 false |

## 针对 8 km / 30 度的验收建议

短期不要把验收写成“必须击毁真实 F-16C”或“真实 AIM-120C Pk 达到某值”。更合适的
工程门是：

1. 制导门：数据库 AIM-120C、8 km / 30 度、左右镜像、匀速目标，报告最近距并给出
   更严格但仍属工程代理的上限，例如从当前 `<15 m` 收紧到 `<9 m` 或 `<8 m`。
2. 引信门：该场景在固定 truth track 下必须明确进入 `FuzeDecision=detonated` 或给出
   no-detonation 原因；不能只靠最终 damage event 推断。
3. 载荷门：10-12 m 区间的 blast-frag load facts 不应突然归零；如果归零，stage report
   必须说明是投影半径、空间交会、方向图还是装甲/暴露导致。
4. 响应门：固定载荷下，component response 曲线应连续、可解释，并能单独校准。
5. 后果门：component failure / integrity / platform consequence 分开报告，不把
   component failure count 直接当成 Pk。

## 当前可执行判断

本文已完成“把杀伤链拆成可以单独观察和单独校准的五段”的分析与只读诊断闭环：

`approach -> fuze decision -> warhead load field -> component response -> consequence`

当前证据已经足以说明：8 km / 30 度偏置场景不是“完全没有近炸”，而是在
warhead load field、component response 和 consequence projection 边界上出现多重弱化。
下一步仍不应直接把 warhead radius、failure threshold 或总 `effect_scale` 调到命中；
更合适的继续方向是：

1. P2/P4：兼容 facade / DTO 与 component-load named factors 已引入；继续保持旧字段
   兼容映射，直到 downstream 从复合 `effect_scale` 迁移完。
2. P5：runtime owner 迁移已完成；后续仅剩 ABI 字段物理删除/下游兼容迁移问题。
3. P3 已默认关闭旧倍率；P6 admission gate 已在 engineering-proxy scope 下开放，
   真实世界 Pk / deterministic fuze / stock weapon-target authority 继续关闭。

因此本文可以作为后续 runtime 解耦和校准 admission 的入口文档，但不能被用作
真实 AIM-120C、真实 F-16C、Pk 或确定性杀伤结论。
