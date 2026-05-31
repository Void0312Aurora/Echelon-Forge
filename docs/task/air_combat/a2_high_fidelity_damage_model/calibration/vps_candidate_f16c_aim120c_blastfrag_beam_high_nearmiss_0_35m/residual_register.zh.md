# Residual Register

状态：非权威 candidate 残差登记表。所有初始条目默认 open；任何 open residual 都阻止本候选包被描述为已校准或 authoritative。本文档不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

候选 scope 固定为：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。

## 当前残差

| `residual_id` | 区域 | 残差描述 | 对 scope 的影响 | 阻塞的 authority | close 条件 | 状态 |
|---|---|---|---|---|---|---|
| `RES-001` | source provenance | source payload pack 已保留 3/3 payload 并校验 sha256；rights / allowed-output policy 已冻结为 fail-closed；benchmark 输出显式不作为 release-consumed evidence | 不再阻塞本包“内部发布签收证据”这一窄域 closeout；仍不构成法律意见、外部发布权或 benchmark consumption authority | 全部 | source ledger 完整并经审阅 | closed_narrow_internal_signoff_non_authoritative |
| `RES-002` | surrogate identity | 候选 surrogate 的 model card、identity manifest、canonical retained artifact pack 与 scoped identity gate 已成形；当前相关文件以 sha256 绑定，未要求全仓 clean | 不再阻塞 scoped package identity freeze；仍不能宣称 global clean release identity 或 validation status promotion | 全部 | model card、retained identity surface 与复现说明经独立审阅闭合 | closed_scoped_identity_non_authoritative |
| `RES-003` | target geometry | F-16C Block 50 组件几何、材料、遮挡和暴露面积来源未审计 | 可能把工程 hitbox 当成真实 vulnerability | effect scale / component probability | geometry 来源、假设和误差界限可追溯 | open |
| `RES-004` | warhead scope | AIM-120C-class blast-fragmentation 候选参数未与可公开、可审计来源绑定 | 可能过拟合或暗示未知具体弹药参数 | effect scale / mechanism load | warhead class 假设、范围和敏感性分析完成 | open |
| `RES-005` | fragment mechanism | TP-21 source payload 已保留，但 reviewer-selected debris comparison case artifacts 与 hash-only selected debris outputs 仍缺 | 破片载荷 row 门槛不可作为权威 | component probability | benchmark 覆盖 fragment-energy / areal-density residual | open_fail_closed_tp21_selected_debris_outputs_missing |
| `RES-006` | blast mechanism | BEC-O headless recalculation 已执行，但 9/9 selected output hashes 与 cached anchors 不一致，且 release-grade tolerance / allowed-output signoff 仍缺 | 爆轰载荷 row 门槛不可作为权威 | effect scale / component probability | benchmark 覆盖 blast residual 与适用区间 | open_fail_closed_beco_recalculation_not_admitted |
| `RES-007` | near-miss bucket | `near_miss_0_35m` 的 anchor、0.25/0.35/0.45 m boundary probes、结果表和独立 review gate 已通过 Stage B scope-only 验收 | 对 Stage B scope/bucket 证据面不再形成独立阻塞；不得扩展为 validated near-miss authority | 全部 | bucket 内多点覆盖和边界敏感性报告完成 | closed_stage_b_scope_review_only_release_blocked |
| `RES-008` | beam/high closure | `beam` / `high` 的轴定义、out-of-scope rejection、700/900/1100 mps closure probe 与独立 review gate 已通过 Stage B scope-only 验收 | 对 Stage B scope/bucket 证据面不再形成独立阻塞；不得扩展为 closure physics authority | 全部 | scope 轴定义和 out-of-scope 检查通过 | closed_stage_b_scope_review_only_release_blocked |
| `RES-009` | component failure | 组件失效概率与机制载荷之间的映射仍未由独立 benchmark 验证；Stage C artifacts 仍来自 test-local authority exercise / author-side candidate review | synthetic probability 或局部 candidate row 可能被误提升 | component probability | 概率 residual、校准曲线和 uncertainty 通过预设门槛 | open_stage_c_fragility_truth_missing |
| `RES-010` | validation criteria | Stage B effect-scale criteria、snapshot、result pack 与独立 review gate 已通过；Stage C component probability 仍缺 formal result promotion 与 release-grade closeout | 仍不能放行 Stage C 或 stock authority | 全部 | pre-run criteria 冻结、独立 review record、benchmark result table 与适用 scope 的 residual closeout 完整 | open_stage_b_review_passed_stage_c_release_blocked |
| `RES-011` | uncertainty | Stage B seed-window CV 与独立 review closeout 已通过；Stage C probability uncertainty coverage、result-level 审计和 release-grade bounds 仍缺 | 无法把 Stage C 当前波动范围叙述成已验证的不确定性边界 | effect scale / component probability | uncertainty coverage 指标通过预设门槛 | open_stage_b_closed_stage_c_blocked |
| `RES-012` | independence | Stage B benchmark/input separation audit 已通过；Stage C result-level benchmark/input independence 仍缺，且 independent fragility truth 不存在 | 验证仍可能在 Stage C 发生循环引用 | 全部 | benchmark/input 分离审计完成 | open_stage_b_closed_stage_c_blocked |
| `RES-013` | Pk boundary | 本候选包未覆盖 kill-chain Pk 校准 | 任何 Pk 声称都越界 | Pk | 不在本包关闭；需独立 Pk 证据链 | open_boundary_deferred |
| `RES-014` | deterministic fuze boundary | 本候选包未覆盖 live fuze trigger、target signature、reliability 或 miss-distance/fuze 联合验证 | 不能替换 RNG hit gate | deterministic fuze | 不在本包关闭；需独立 fuze/kill-chain 证据链 | open_boundary_deferred |

## 2026-05-31 验收固化

本轮验收接受以下 retained gate 作为残余状态更新依据，但不放行任何 runtime、stock、Pk 或 deterministic-fuze authority：

- `RES-001`：`retained_artifacts/res001_release_signoff_20260531/res001_release_signoff_gate.json` 窄域关闭，结论限定为 project-internal signoff evidence；source payload 3/3 retained/hash match，allowed-output policy fail-closed，benchmark explicit non-consumption。
- `RES-002`：`retained_artifacts/res002_scoped_release_identity_20260531/res002_scoped_release_identity_gate.json` 窄域 scoped package identity pass；不要求全仓 clean，不声明 global release identity。
- `RES-005/006`：`retained_artifacts/res005006_benchmark_execution_admission_20260531/benchmark_execution_admission_gate.json` 已执行但 fail-closed；TP-21 selected debris outputs 缺失，BEC-O 9 个 selected recalculation hashes 与 cached anchors 不一致。
- `RES-007/008`：`retained_artifacts/scope_bucket_independent_review_20260531/scope_bucket_independent_review_gate.json` Stage B scope/bucket review passed；仅关闭 Stage B scope-only 阻塞，不授予 validated near-miss 或 closure physics authority。
- `RES-011/012`：`retained_artifacts/res011012_independent_review_closeout_20260531/res011012_independent_review_closeout_gate.json` Stage B effect-scale closeout passed；Stage C component probability 因 independent fragility truth、probability uncertainty coverage 与 result-level independence 缺失继续 open。

## Closeout 规则

- 关闭 residual 必须引用 source ledger、model card 或 validation report 中的稳定 artifact，不接受口头结论。
- `RES-013` 和 `RES-014` 是本候选包的 scope boundary，不应在本目录内关闭为已授权；只能在独立证据链存在后标注为外部处理。
- 任何 residual 关闭后仍需检查是否引入新的 out-of-scope 声称。
- 在所有适用 residual 关闭前，`calibration_status` 必须保持 `unvalidated`，所有 authority 字段必须保持 `false`。
