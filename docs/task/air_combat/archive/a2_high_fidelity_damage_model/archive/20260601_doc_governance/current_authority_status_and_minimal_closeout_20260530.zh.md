# A2 当前 Authority 状态与最小收口集

状态：`2026-05-30 / status_audit / non-authoritative`。

本文档用于回答两个问题：

1. 当前 A2 高保真空战杀伤模型到底已经实现到哪一层；
2. 按当前梯度真实性和公开来源准入守则，下一步应该如何收口，而不是继续发散。

本文档不创建 runtime descriptor，不授予 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。

## 1. 当前总判断

当前 A2 更准确的状态不是“高保真杀伤模型已完成”，而是：

> structured-aircraft damage/effects runtime 主链已经进入维护路径；窄域 candidate 包、validation scaffold 和 test-local authority exercise 已经成形；但 stock runtime authority 仍未放开。

按 [梯度真实性原则](../../../../../standards/foundation/gradient_realism_principles.zh.md)，当前最稳妥的真实性声明应停留在：

- 已有可信的结构化飞机毁伤 runtime contract；
- 已有窄域 `AIM-120C-class blast_fragmentation -> F-16C_Block50` 的 authority 演练路径；
- 尚不能把该进展上卷成 stock authority、full `G6`、单发 `Pk` 或确定性引信真实性。

## 2. 当前实现分层

### 2.1 Runtime 机制层：已落地

当前 runtime 侧已经完成并进入维护路径的部分包括：

- structured aircraft 不再默认走 HP-first kill authority，结构化目标会进入几何/组件/overlay 路径；
- `AircraftDamageState`、`PlatformDamageState`、`ComponentDamageState` 已能承接局部命中后的后果传播；
- `blast_fragmentation` near-miss 已能通过 hitbox 投影形成 broad spatial effects，并在 broad near-miss 下导出 projected component rows；
- `EffectsEvent` 已能导出 vulnerability profile、evidence descriptor 元数据、effect-scale 来源、component probability 来源和 mechanism-load 证据字段；
- row-backed `effect_scale` 与 row-backed `component_failure_probability` 都已经有运行时消费路径，但当前只在 test-local exercise 中演练。

相关实现入口：

- [default_effects_model.cpp](../../../../../../src/models/weapons/default_effects_model.cpp)
- [unit_definition_loader.cpp](../../../../../../src/content/unit_definition_loader.cpp)
- [damage.h](../../../../../../src/components/combat/damage.h)

### 2.2 Candidate / scaffold 层：已成形

当前窄域 candidate 包已经不再只是模板集合，而是具备 package-level 审阅形状：

- package source ledger、surrogate model card、validation report draft 已真实落文；
- `BFM-BM-001..006` 已全部进入可执行 scaffold 层；
- `a2_candidate_vps_bundle.py` 可以汇总文档、validation scaffold 和 runtime-aligned authority exercise；
- `a2_blastfrag_runtime_aligned_authority_pack.py` 可以导出 baseline event summary、projected component rows，以及 test-local descriptor candidate；
- 对应 architecture/runtime tests 已固定这些边界，防止 candidate、test-local、stock 三层混淆。

相关入口：

- [候选包 README](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/README.zh.md)
- [validation manifest 草案](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_manifest_draft_blastfrag_20260528.zh.md)
- [residual register](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)
- [a2_candidate_vps_bundle.py](../../../../../../tools/maintenance/a2_candidate_vps_bundle.py)
- [a2_blastfrag_runtime_aligned_authority_pack.py](../../../../../../tools/maintenance/a2_blastfrag_runtime_aligned_authority_pack.py)

### 2.3 Stock authority 层：仍未放开

当前仍然不能放开 stock runtime authority，原因不是“代码里完全没有 authority 通路”，而是以下 gate 仍未关闭：

- stock 数据库里没有经过正式放行的 authoritative descriptor；
- candidate bundle 仍保持 `candidate_non_authoritative_bundle`；
- validation manifest 仍是 `validation_status=not_run`；
- effect-scale 与 component probability 虽有 test-local positive path，但没有被 candidate residual closeout 和正式 acceptance criteria 支撑；
- loader 当前只要复制进来至少一条通过 gate 的 evidence row，就可能把 profile 级 authority 置为 `true`；这足以支持 test-local exercise，但还不足以自动证明该 profile 对当前 scope 的 row 覆盖已经“完整可发布”；
- `pk_authority` 与 `deterministic_fuze_authority` 继续显式保持 `false / deferred`。

当前 bundle 工具给出的机器可读快照也一致：

- `stock_database_authority_granted = false`
- `effect_scale_authority_in_stock = false`
- `component_failure_probability_authority_in_stock = false`
- `pk_authority = false`
- `deterministic_fuze_authority = false`

## 3. 当前已经做到的“最远一步”

如果只讨论“实现程度”，当前最远已经到达：

1. `effect_scale_authority`：
   - 已有完整 runtime 消费路径；
   - 已有 scope 对齐、manifest 完整、仅放行 effect-scale 的 test-local descriptor 演练；
   - 但它仍只属于 `test_local_authority_exercise_only`。
2. `component_failure_probability_authority`：
   - 已有 broad near-miss -> projected component row -> component-specific probability row 的消费路径；
   - 已能在 `right_aileron_actuator` 这一窄组件上做 test-local authority 演练；
   - 但它仍不具备 stock descriptor 放行资格。

换句话说，当前不是“还没做到 authority”，而是“authority 的技术通路已经打通，但还没有证据链资格进入 stock 语义”。

## 4. 为什么当前不能直接宣称窄域 authority 已完成

当前最容易混淆的地方是：runtime 已能消费 row，并不等于项目已经获得可宣称的 authority。

按 [窄域任务定义](../../narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md) 与 [A2 数据来源准入规则](../../data_collection/source_admission_rules_20260528.zh.md)，当前至少还缺三类东西：

### 4.1 验证冻结还没完成

当前仍缺：

- benchmark 结果对应的 artifact hash；
- 独立 reviewer signoff；
- 可附着到结果表的 metrics / threshold 执行记录；
- 可以审计 benchmark 是否独立于模型输入与调参来源的完整记录。

当前已经新增并冻结了一个 Stage B `effect_scale` 用的独立 artifact：

- [validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md)

这意味着 `RES-010` 已经从“指标和门槛未定义”推进到了“criteria 已冻结，但 run/review/closeout 未完成”。

本轮又补入了两类 author-side closeout artifacts：

- [validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md)
- [validation_review_readiness_record_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_review_readiness_record_stage_b_effect_scale_20260530.zh.md)

它们把 Stage B frozen hard gates 的第一版 fixed-seed candidate snapshot 与 author-side review inputs 固化下来，
但仍不构成独立 review 或 stock authority。

本轮还补入了一个统一结果包：

- [validation_result_pack_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_result_pack_stage_b_effect_scale_20260530.zh.md)

它把 scaffold、scope probe 与 Stage B snapshot 汇总为带 content hash 与 independence 语义的统一 candidate result pack，
进一步减少“结果分散在多份 author-side artifact 中”的问题，但仍不构成 retained validation artifact。

本轮还补入了一个 release-readiness gate：

- [validation_release_readiness_gate_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_release_readiness_gate_stage_b_effect_scale_20260530.zh.md)

它的作用是把“当前为什么 blocked”机器化固定下来，防止当前 author-side hard-gate pass 被误读成
`ready to release`。

本轮还把 Stage B author-side retained evidence chain 固化到 repo 内：

- [validation_retained_artifact_pack_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_retained_artifact_pack_stage_b_effect_scale_20260530.zh.md)

这意味着 `RES-002` 当前更准确的状态已经不是“完全没有 retained chain”，而是“canonical author-side
retained pack 已存在，但 release-grade surrogate identity 仍未闭合”。

本轮还补入了一个 package-level shared provenance / surrogate identity gate：

- [validation_provenance_and_identity_gate_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_provenance_and_identity_gate_20260530.zh.md)

它把 `RES-001` 与 `RES-002` 的共享阻塞面单独机器化收口，避免 Stage B / Stage C 各自重复解释
同一套 provenance / identity blocker。

当前还新增了一个 Stage B `effect_scale` 用的 scope / independence manifest：

- [validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md)

并且已经补入第一版 boundary result report：

- [validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md)

这意味着：

- `RES-007` 已从“near-miss 子桶未定义”推进到“anchor、boundary probes 和第一版结果表已存在”；
- `RES-008` 已从“beam/high 轴未固化”推进到“轴定义、rejection rules、第一版结果表和 candidate closure-sensitive response 已存在”；
- `RES-012` 已从“independence 边界未写清”推进到“benchmark/input separation 与初版结果表都已成文，但尚未独立审计”。

这直接阻塞：

- `RES-010 validation criteria`
- `RES-011 uncertainty`
- `RES-012 independence`

### 4.2 候选包的 provenance 还没从“评审就绪”走到“可授权”

当前 package-level 文档已经可审，但还不等于可放权。仍缺：

- external artifact checksum / version pin 的最终冻结；
- surrogate 自身的 model/version/run manifest 冻结；
- geometry / warhead / mechanism 方法与 runtime row 之间更严格的可追溯映射。

这直接阻塞：

- `RES-001 source provenance`
- `RES-002 surrogate identity`
- `RES-003 target geometry`
- `RES-004 warhead scope`

本轮又补入了四份把这些 residual 从“口头边界”推进成“显式 artifact”的文档：

- [artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md)
- [surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md)
- [target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md)
- [warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md)

它们的作用是把 provenance / surrogate identity / geometry / warhead boundary 说清楚，
不是把 `RES-001..004` 直接关闭。

### 4.3 窄域 bucket 与 mechanism residual 还没有真正收口

当前 `beam / high / near_miss_0_35m` 已经不只是纯 scope bookkeeping：`high` closure 上已出现第一版 candidate closure-sensitive response；但它仍远不是验证完成的 authority bucket。并且 `blast_fragmentation` 的 row gate 仍依赖 mechanism-load residual 关闭。

这直接阻塞：

- `RES-005 fragment mechanism`
- `RES-006 blast mechanism`
- `RES-007 near-miss bucket`
- `RES-008 beam/high closure`

## 5. effect-scale 放行前的最小收口集

若下一步目标是“先推进 `effect_scale_authority`，而不是同步推进 component probability / Pk / fuze”，那么按当前 residual register 的正式阻塞关系，最小必须收口的 residual 子集应为：

| residual | 是否属于 effect-scale 最小集 | 原因 |
|---|---|---|
| `RES-001` | 是 | effect-scale row 的来源、rights、source pin 不冻结，就不能进入 authority。 |
| `RES-002` | 是 | surrogate/model/version/run manifest 不冻结，就不能形成可复审 descriptor。 |
| `RES-003` | 是 | effect-scale 仍受 target geometry 与 spatial projection 影响，不能把工程 hitbox 误当真值。 |
| `RES-004` | 是 | 当前是 `AIM-120C-class blast_fragmentation` family 候选，不先明确 warhead scope，就会把 family 假设误写成型号真值。 |
| `RES-006` | 是 | 当前 effect-scale row gate 已消费 blast scaled-distance / overpressure / impulse 轴，blast residual 不能悬空。 |
| `RES-007` | 是 | 当前 scope 明写 `near_miss_0_35m`，bucket 边界与采样密度不冻结就不能发布 row-backed authority。 |
| `RES-008` | 是 | `beam` 与 `high` 只是候选标签，若定义不冻结，scope 会泄漏。 |
| `RES-010` | 是 | 没有运行前冻结的 acceptance criteria，就无法判定通过与否。 |
| `RES-011` | 是 | effect-scale 至少要说明不确定性覆盖或暂不覆盖到什么程度。 |
| `RES-012` | 是 | benchmark 若与模型输入循环引用，就不能称为 validation。 |
| `RES-005` | 否，形式上可后置，但实务上常会被追问 | register 当前把它主要挂到 component probability；但若 effect-scale row 明确依赖 fragment areal-density / fragment-energy gate，评审时通常仍会要求说明该 residual。 |
| `RES-009` | 否，建议留到下一阶段 | 它主要阻塞的是 component-specific probability authority，而不是 effect-scale-only authority。 |
| `RES-013` | 否，边界项 | 明确保持 `pk_authority=false`。 |
| `RES-014` | 否，边界项 | 明确保持 `deterministic_fuze_authority=false`。 |

结论：

> 若只想先放行 effect-scale，正确做法不是“一口气全关 14 个 residual”，而是先收口 `RES-001/002/003/004/006/007/008/010/011/012`，同时把 `RES-009`、`RES-013`、`RES-014` 保持在下一层或边界层；`RES-005` 则按 row gate 的实际依赖程度决定是否跟随本轮一并收口。

## 6. component probability 放行需要额外补的东西

当 effect-scale-only 已经具备 release 条件后，若继续推进 `component_failure_probability_authority`，还需要额外收口：

- `RES-009 component failure`

当前这一层也不再只存在于 runtime test 断言里。本轮已经补入第一版 Stage C author-side snapshot：

- [validation_benchmark_snapshot_stage_c_component_probability_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_benchmark_snapshot_stage_c_component_probability_20260530.zh.md)

它把 `right_aileron_actuator` 的 component-specific probability candidate、component provenance
字段以及 mechanism-load gate band 固化成 package-level artifact，但仍明确保持
`test_local_authority_exercise_only` 来源，不构成 stock authority。

本轮还进一步补入了多类 Stage C 收口 artifact：

- [validation_metrics_and_acceptance_criteria_stage_c_component_probability_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_metrics_and_acceptance_criteria_stage_c_component_probability_20260530.zh.md)
- [validation_result_pack_stage_c_component_probability_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_result_pack_stage_c_component_probability_20260530.zh.md)
- [validation_retained_artifact_pack_stage_c_component_probability_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_retained_artifact_pack_stage_c_component_probability_20260530.zh.md)
- [validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md)
- `tools/maintenance/a2_blastfrag_stage_c_component_probability_surface_probe.py` 对应的 retained
  surface probe / repeatability snapshot 已进入 Stage C canonical artifact 链。

这意味着 Stage C 当前更准确的状态已经不是“只有 snapshot”，而是“已有 pre-run candidate
criteria、snapshot、surface probe、unified candidate result pack、canonical retained
pack 和 blocked review gate，但 fragility validation / uncertainty / independent review
仍未闭合”。

这一项不是简单“补一条 row”就能算完成，而至少要明确：

- component-specific row 与 global row 的优先级是否固定；
- fragility benchmark 与 component identity / redundancy group 的对应关系是否固定；
- failure probability residual、calibration curve 或 uncertainty 口径是否冻结；
- component-specific provenance 是否足够解释“为什么是这个组件，而不是整机统一概率”。

因此，`component_failure_probability_authority` 适合作为 effect-scale 之后的第二个 release step，而不是和 effect-scale 混成同一轮验收。

## 7. 明确不应在本轮关闭的边界项

下列 residual 当前应保留为边界，不应在本 candidate 包内尝试“顺手做完”：

| residual | 当前处理方式 |
|---|---|
| `RES-013 Pk boundary` | 保持 open，等待独立 kill-chain / mission-kill 概率证据链。 |
| `RES-014 deterministic fuze boundary` | 保持 open，等待独立 fuze trigger / signature / reliability / replay admission 证据链。 |

原因很简单：

- 当前窄域主线只做到 mechanism-load -> effect-scale / component consequence；
- 一旦把 `Pk` 或 deterministic fuze 混进来，scope 会立刻从“局部 authority”膨胀成“完整 kill-chain authority”，不符合当前梯度真实性守则。

## 8. 推荐的下一步切口

按当前状态，最合理的下一步不是继续扩面，而是沿 effect-scale-only 收口：

1. 审阅并保持当前 Stage B metrics / acceptance criteria artifact 冻结，不再在 benchmark 结果出来后改写门槛。
2. 为 candidate 依赖的 external artifacts 补 version/hash/rights pin，优先收紧 `RES-001`。
3. 把 surrogate 的 model/version/run-manifest 固定到单独 artifact，优先收紧 `RES-002`。
4. 把 `beam`、`high`、`near_miss_0_35m` 的 bucket 定义、边界点和 out-of-scope rejection 写成显式文档或 executable manifest，优先收紧 `RES-007/008/012`。
5. 生成与 frozen criteria 对齐的 benchmark result table 和独立 review record，再讨论把 effect-scale-only descriptor 从 test-local exercise 提升为候选 stock release 审查对象。
6. `component_failure_probability_authority` 留在下一阶段，避免 effect-scale 与 fragility calibration 混验收。

## 9. 当前统一口径

当前对 A2 主线应统一使用以下口径：

> A2 已经具备 structured-aircraft damage/effects runtime 主链，以及 `AIM-120C-class blast_fragmentation -> F-16C_Block50` 的 test-local authority exercise；但这仍属于 candidate / scaffold / test-local 层，不等于 stock runtime authority 已放行。下一步应优先收口 effect-scale-only 的最小 residual 集，再考虑 component-specific probability authority；`Pk` 与 `deterministic_fuze` 继续保持边界关闭。
