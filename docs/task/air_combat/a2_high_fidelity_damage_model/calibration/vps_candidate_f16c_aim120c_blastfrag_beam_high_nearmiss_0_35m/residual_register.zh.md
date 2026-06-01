# Residual Register

状态：`2026-06-01 / G3 residual accounting closeout / research_closed_authority_retained / non_authoritative`。当前默认完成口径为 research / candidate profile；`RES-001..014` 不再阻塞当前研究级候选模型闭合。任何 `authority_blocked`、`authority_fail_closed` 或 `authority_boundary_deferred` residual 都继续阻止本候选包被描述为已校准或 authoritative。本文档不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

候选 scope 固定为：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。

## 当前残差

| `residual_id` | 区域 | 残差描述 | 对 scope 的影响 | 阻塞的 authority | close 条件 | 状态 |
|---|---|---|---|---|---|---|
| `RES-001` | source provenance | source payload pack 已保留 3/3 payload 并校验 sha256；rights / allowed-output policy 已冻结为 fail-closed；benchmark 输出显式不作为 release-consumed evidence | 不再阻塞本包“内部发布签收证据”这一窄域 closeout；仍不构成法律意见、外部发布权或 benchmark consumption authority | 全部 | source ledger 完整并经审阅 | closed_narrow_internal_signoff_non_authoritative |
| `RES-002` | surrogate identity | 候选 surrogate 的 model card、identity manifest、canonical retained artifact pack 与 scoped identity gate 已成形；当前相关文件以 sha256 绑定，未要求全仓 clean | 不再阻塞 scoped package identity freeze；仍不能宣称 global clean release identity 或 validation status promotion | 全部 | model card、retained identity surface 与复现说明经独立审阅闭合 | closed_scoped_identity_non_authoritative |
| `RES-003` | target geometry | Stage B witness-geometry bookkeeping 已窄域 closeout；真实 F-16C Block 50 组件几何、材料、遮挡和暴露面积来源仍未审计 | Stage B 采样 bookkeeping 不再阻塞 research profile；仍可能把工程 hitbox 当成真实 vulnerability | effect scale / component probability | G4 前补充 geometry 来源、假设和误差界限 | research_closed_stage_b_witness_geometry_bookkeeping_authority_blocked_global_geometry |
| `RES-004` | warhead scope | Stage B AIM-120C-class blast-fragmentation family scope 已窄域 closeout；具体 AIM-120C 战斗部真值、质量、破片形态和 fuze 证据仍未关闭 | Stage B family-scope 标签不再阻塞 research profile；仍可能过拟合或暗示未知具体弹药参数 | effect scale / mechanism load | G4 前补充 warhead class 假设、范围和敏感性分析 | research_closed_stage_b_family_scope_authority_blocked_specific_warhead_truth |
| `RES-005` | fragment mechanism | TP-21 source payload 已保留；release-grade reviewer-selected debris comparison case artifacts 与 hash-only selected debris outputs 仍缺 | 可作为 non-authoritative research mechanism-load envelope 的替换目标；破片载荷 row 门槛不可作为权威 | component probability | G4 前重跑 selected-case admission gate；research profile 只保留可替换估计 | research_closed_mechanism_load_envelope_authority_fail_closed_tp21_selected_debris_outputs_missing |
| `RES-006` | blast mechanism | BEC-O headless recalculation 已执行，但 9/9 selected output hashes 与 cached anchors 不一致，且 release-grade tolerance / allowed-output signoff 仍缺 | 可作为 non-authoritative research blast envelope 的替换目标；爆轰载荷 row 门槛不可作为权威 | effect scale / component probability | G4 前完成 lineage / allowed-output / tolerance 或 replacement signoff；research profile 只保留可替换估计 | research_closed_mechanism_load_envelope_authority_fail_closed_beco_recalculation_not_admitted |
| `RES-007` | near-miss bucket | `near_miss_0_35m` 的 anchor、0.25/0.35/0.45 m boundary probes、结果表和独立 review gate 已通过 Stage B scope-only 验收 | 对 Stage B scope/bucket 证据面不再形成独立阻塞；不得扩展为 validated near-miss authority | 全部 | bucket 内多点覆盖和边界敏感性报告完成 | closed_stage_b_scope_review_only_release_blocked |
| `RES-008` | beam/high closure | `beam` / `high` 的轴定义、out-of-scope rejection、700/900/1100 mps closure probe 与独立 review gate 已通过 Stage B scope-only 验收 | 对 Stage B scope/bucket 证据面不再形成独立阻塞；不得扩展为 closure physics authority | 全部 | scope 轴定义和 out-of-scope 检查通过 | closed_stage_b_scope_review_only_release_blocked |
| `RES-009` | component failure | 组件失效概率与机制载荷之间的映射仍未由独立 benchmark 验证；Stage C artifacts 仍来自 test-local authority exercise / author-side candidate review | 可保留为 research component fragility surface；synthetic probability 或局部 candidate row 不得误提升 | component probability | G4 前补概率 residual、校准曲线和 uncertainty 门槛 | research_closed_stage_c_candidate_surface_authority_blocked_fragility_truth |
| `RES-010` | validation criteria | Stage B effect-scale criteria、snapshot、result pack 与独立 review gate 已通过；Stage C component probability 仍缺 formal result promotion 与 release-grade closeout | research profile 下可视为候选验证面已闭合；仍不能放行 Stage C 或 stock authority | 全部 | G4 前完成 formal result promotion 与适用 scope 的 residual closeout | research_closed_stage_b_review_authority_blocked_stage_c_release |
| `RES-011` | uncertainty | Stage B seed-window CV 与独立 review closeout 已通过；Stage C probability uncertainty coverage、result-level 审计和 release-grade bounds 仍缺 | research profile 下保留 uncertainty note；不得叙述成 release-grade uncertainty boundary | effect scale / component probability | G4 前补 reviewer-accepted uncertainty coverage 指标 | research_closed_stage_b_uncertainty_authority_blocked_stage_c_probability |
| `RES-012` | independence | Stage B benchmark/input separation audit 已通过；Stage C result-level benchmark/input independence 仍缺，且 independent fragility truth 不存在 | research profile 下保留 candidate independence note；不得叙述成 release-grade independent validation | 全部 | G4 前补 Stage C result-level independence 和 independent fragility truth | research_closed_stage_b_independence_authority_blocked_stage_c_probability |
| `RES-013` | Pk boundary | 本候选包未覆盖 kill-chain Pk 校准 | research profile 下明确 out-of-scope；任何 Pk 声称都越界 | Pk | 不在本包关闭；需独立 Pk 证据链 | research_out_of_scope_authority_boundary_deferred_pk |
| `RES-014` | deterministic fuze boundary | 本候选包未覆盖 live fuze trigger、target signature、reliability 或 miss-distance/fuze 联合验证 | research profile 下明确 out-of-scope；不能替换 RNG hit gate | deterministic fuze | 不在本包关闭；需独立 fuze/kill-chain 证据链 | research_out_of_scope_authority_boundary_deferred_deterministic_fuze |

## 2026-06-01 G3 台账收尾

G3 已按 research profile 收尾为 `research_closed_authority_retained`：`RES-001..014`
均有当前状态、稳定 retained artifact 或活跃 backlog 入口，以及明确的不得上卷边界。
这表示当前研究级候选模型不再被 RES 阻塞；它不是 `all authority residuals closed`，
也不是 `G4/G5` authority closeout。

完整清点见
[g3_residual_closeout_status_20260601.zh.md](../../g3_residual_closeout_status_20260601.zh.md)。
当前项目默认保留 research / candidate profile，见
[research_candidate_data_policy_20260601.zh.md](../../research_candidate_data_policy_20260601.zh.md)。
因此原先 open / fail-closed residual 已被重标为 research-closed 或 research-out-of-scope；
它们保留为 future authority blocker 或后续可替换 research data target。
当前归类如下：

| 归类 | residuals | 台账结论 |
|---|---|---|
| narrow/scoped non-authoritative closeout | `RES-001/002` | 已有 retained gate；不构成外部发布权、global release identity 或 authority |
| Stage B local review/subscope closeout | `RES-003/004/007/008/010/011/012` | research profile 不再缺证据；真实 geometry/warhead、release-grade validation 或 Stage C 只阻塞 future authority |
| mechanism research envelope / authority fail-closed | `RES-005/006` | retained packets、template 和 preflight 已存在；research profile 走可替换估计，future authority 无外部 reviewer/signoff packet 时不得 admit |
| Stage C candidate surface / authority blocker | `RES-009` | component fragility research surface 可保留；independent fragility truth 只在未来 `TC-A2-AUTH-C` 中处理 |
| kill-chain boundary deferred | `RES-013/014` | Pk 与 deterministic fuze 不在本候选包内关闭；research profile 明确 out-of-scope |

research profile 下的实际后续工作是：为 `RES-005/006` 建立非权威 mechanism-load
envelope，为 `RES-009..012` 建立 research component fragility surface 和 uncertainty ledger。
这些工作可以使用公开、第三方、社区或 derived estimate，但必须保留 source tier、
uncertainty、confidence、scope 和 replacement rule。

## 2026-05-31 验收固化

本轮验收接受以下 retained gate 作为残余状态更新依据，但不放行任何 runtime、stock、Pk 或 deterministic-fuze authority：

- `RES-001`：`retained_artifacts/res001_release_signoff_20260531/res001_release_signoff_gate.json` 窄域关闭，结论限定为 project-internal signoff evidence；source payload 3/3 retained/hash match，allowed-output policy fail-closed，benchmark explicit non-consumption。
- `RES-002`：`retained_artifacts/res002_scoped_release_identity_20260531/res002_scoped_release_identity_gate.json` 窄域 scoped package identity pass；不要求全仓 clean，不声明 global release identity。
- `RES-003`：`retained_artifacts/res003_target_geometry_closeout_20260531/res003_target_geometry_closeout_gate.json` 仅关闭 Stage B effect-scale witness-geometry bookkeeping；真实 F-16 component geometry、material、occlusion、exposed area 与 Stage C component probability 依赖继续 open。
- `RES-004`：`retained_artifacts/res004_warhead_scope_closeout_20260531/res004_warhead_scope_closeout_gate.json` 仅关闭 Stage B AIM-120C-class blast-fragmentation family-scope 子范围；missile-specific warhead truth、toy numeric authority、fuze、Pk 与 component probability 继续 blocked。
- `RES-005`：`retained_artifacts/res005_tp21_debris_admission_20260531/res005_tp21_debris_admission_gate.json` 远端执行有效但 fail-closed；仍缺 reviewer-selected TP-21 case page/section provenance、selected output preimage hash、independent reviewer signoff 与 allowed-output signoff。
- `RES-006`：`retained_artifacts/res006_beco_recalculation_admission_20260531/res006_beco_recalculation_admission_gate.json` 远端执行有效但 fail-closed；9/9 recalculated hash anchors 已保留为 candidate replacement set，cached-vs-recalculated 为 0 match / 9 mismatch，仍缺 independent lineage、allowed-output、tolerance/replacement signoff。
- `RES-005/006`：`retained_artifacts/res005006_benchmark_execution_admission_20260531/benchmark_execution_admission_gate.json` 已执行但 fail-closed；TP-21 selected debris outputs 缺失，BEC-O 9 个 selected recalculation hashes 与 cached anchors 不一致。
- `RES-007/008`：`retained_artifacts/scope_bucket_independent_review_20260531/scope_bucket_independent_review_gate.json` Stage B scope/bucket review passed；仅关闭 Stage B scope-only 阻塞，不授予 validated near-miss 或 closure physics authority。
- `RES-011/012`：`retained_artifacts/res011012_independent_review_closeout_20260531/res011012_independent_review_closeout_gate.json` Stage B effect-scale closeout passed；Stage C component probability 因 independent fragility truth、probability uncertainty coverage 与 result-level independence 缺失继续 open。

## 2026-06-01 机制准入补充

本轮新增 retained review packet、external signoff template 和 admission preflight，只把
`RES-005/006` 的下一步准入流程机器化。它们不消费 reviewer 决策，不关闭 residual，
不授予 fragment/blast row authority。

- `RES-005`：`retained_artifacts/res005_tp21_selected_case_admission_20260601/res005_tp21_selected_case_admission_review_gate.json` 和 `retained_artifacts/res005_tp21_selected_case_candidate_20260601/res005_tp21_selected_case_candidate_packet.json` 继续 fail-closed；仍缺 reviewer-selected case locator、selected-output preimage sha256、selected output hash anchors、independent reviewer signoff、allowed-output signoff 和 authority-boundary signoff。
- `RES-006`：`retained_artifacts/res006_beco_replacement_tolerance_admission_20260601/res006_beco_replacement_tolerance_admission_gate.json` 和 `retained_artifacts/res006_beco_lineage_tolerance_review_20260601/res006_beco_lineage_tolerance_review_candidate_packet.json` 继续 fail-closed；仍缺 independent lineage review、allowed-output signoff、numeric tolerance policy signoff 和 replacement-anchor signoff。
- `RES-005/006` 共用流程：`retained_artifacts/signoff_intake_contract_20260601/signoff_intake_contract.json`、`retained_artifacts/external_signoff_packet_template_20260601/external_signoff_packet_template.json` 和 `retained_artifacts/signoff_admission_preflight_20260601/signoff_admission_preflight_packet.json` 只定义 future reviewer packet 的 shape / template / ready flag。默认无外部 packet supplied，`approval_granted=false`，`admission_granted=false`，`ready_for_admission_gate=false`。

## Closeout 规则

- 关闭 residual 必须引用 source ledger、model card 或 validation report 中的稳定 artifact，不接受口头结论。
- `RES-013` 和 `RES-014` 是本候选包的 scope boundary，不应在本目录内关闭为已授权；只能在独立证据链存在后标注为外部处理。
- 任何 residual 关闭后仍需检查是否引入新的 out-of-scope 声称。
- 在所有适用 residual 关闭前，`calibration_status` 必须保持 `unvalidated`，所有 authority 字段必须保持 `false`。
