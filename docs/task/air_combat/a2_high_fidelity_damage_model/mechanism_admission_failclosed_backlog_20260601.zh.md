# Mechanism Admission Fail-Closed Backlog - 2026-06-01

状态：`TC-A2-BF-003-FAILCLOSED / G2 candidate acceptance blocker backlog / G3 residual read-only / non-authoritative`。

本文把 `TC-A2-BF-003` 的 mechanism admission fail-closed blockers 拆成下一轮可执行任务。它只承接
[candidate_acceptance_status.zh.md](candidate_acceptance_status.zh.md) 中 `G2 candidate acceptance`
对 `RES-005/006` 的口径，并只读取
[residual_register.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)
和 retained gate 的 `G3 residual` 状态。

本文不是 release evidence，不关闭 residual，不启动 `G4/G5`，不授予 fragment/blast row authority，
不把 TP-21 或 BEC-O comparison outputs 消费为 release evidence。`G4` authority promotion 和
`G5` Pk / deterministic fuze 继续 deferred。

## 当前固定口径

| 项 | 当前值 |
|---|---|
| candidate package | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| target / weapon / bucket | `F-16C_Block50` x `AIM-120C-class/blast_fragmentation` x `beam/high/near_miss_0_35m` |
| task cluster | `TC-A2-BF-003` / mechanism admission evidence |
| acceptance layer | `G2 candidate acceptance` |
| residual layer | `G3 residual` read-only status |
| release consumption | `false` |
| authority state | candidate / non-authoritative / fail-closed by default |

事实源固定为 retained gate 与 residual register；叙事文档不得覆盖 retained gate JSON 的结论。

| residual | retained gate result | backlog interpretation |
|---|---|---|
| `RES-005` TP-21 fragment mechanism | `blocked_fail_closed_tp21_debris_admission_gate` / `blocked_fail_closed_tp21_selected_debris_outputs_missing` | 下一轮只补 selection/provenance/hash/signoff 证据链；当前不 admit TP-21 debris outputs |
| `RES-006` BEC-O blast mechanism | `res006_remains_blocked_fail_closed` / `blocked_fail_closed_beco_recalculation_not_admitted` | 下一轮只处理 recalculation lineage、allowed-output、tolerance/replacement signoff；当前不 admit BEC-O hashes |

## Backlog Item: `TC-A2-BF-003-RES005-TP21`

目标：把 `RES-005` 从“TP-21 payload 已保留但 selected debris comparison outputs 缺失”推进到可复审的
selected-case admission artifact；在签收前保持 fail-closed。

| 字段 | 内容 |
|---|---|
| owner | Mechanism admission evidence owner + independent reviewer；source-rights reviewer 必须单独签收 allowed-output 边界 |
| 输入 | `retained_artifacts/res005_tp21_debris_admission_20260531/res005_tp21_debris_admission_gate.json`；`selected_debris_output_anchor_set.json`；`retained_artifacts/source_payload_pack_20260531/payloads/TP-21.pdf` 的 payload hash；`source_rights_output_policy_20260531/source_rights_output_policy_gate.json`；`validation_res005_tp21_debris_admission_gate_20260531.zh.md`；`residual_register.zh.md` 中 `RES-005` 状态 |
| 输出 | 新的 retained selected-case admission artifact，至少包含 stable reviewer case id、page/section 或 figure/table locator label、redacted selected output preimage sha256、hash-only selected debris output anchor set、independent reviewer signoff、allowed-output signoff；同时保留 authority guards 全 false 和 `benchmark_consumed_for_release=false` |
| 禁止越界项 | 不复制 TP-21 prose、tables、figures 或 raw numeric values；不把 controlled criteria vocabulary 当成 concrete benchmark case；不把 selected hash output 当 release benchmark consumption；不修改 retained gate JSON 或 source ledger；不授予 `fragment_mechanism_authority`、`component_failure_probability_authority`、stock/runtime/Pk/fuze authority |
| 验收命令或验收证据 | 运行 `python3 tools/maintenance/a2_blastfrag_res005_tp21_debris_admission_gate.py` 和 `pytest -q tests/architecture/test_a2_blastfrag_res005_tp21_debris_admission_gate.py`；另外提交 independent reviewer signoff 与 allowed-output signoff 的 retained evidence。只有新的 gate 明确 `closed_residual_ids_by_this_gate` 或 narrow closeout，才能更新 residual register；否则继续 fail-closed |

当前 blocker 精确清单：

- 缺 reviewer-selected concrete TP-21 debris comparison case 的 page/section provenance labels；
- 缺 reviewer-selected case 的 selected output preimage hash；
- 缺 independent reviewer signoff；
- source-rights allowed-output policy 尚未 admit current comparison output hashes。

## Backlog Item: `TC-A2-BF-003-RES006-BECO`

目标：把 `RES-006` 从“BEC-O headless recalculation 已执行但 9/9 selected output hashes 与 cached anchors 不一致”
推进到可复审的 replacement/tolerance admission path；在签收前保持 fail-closed。

| 字段 | 内容 |
|---|---|
| owner | Blast mechanism admission owner + spreadsheet execution reviewer + source-rights/tolerance reviewer；replacement promotion 必须由独立 reviewer 签收 |
| 输入 | `retained_artifacts/res006_beco_recalculation_admission_20260531/res006_beco_recalculation_admission_gate.json`；`beco_recalculated_hash_anchor_set.json`；`retained_artifacts/mechanism_comparison_hashes_20260531/mechanism_comparison_hashes.json`；`source_rights_output_policy_20260531/source_rights_output_policy_gate.json`；`validation_res006_beco_recalculation_admission_gate_20260531.zh.md`；`residual_register.zh.md` 中 `RES-006` 状态 |
| 输出 | 单独 retained replacement/tolerance admission artifact，至少说明 cached-anchor lineage、headless recalculation runtime/version lineage、9 个 selected comparison id 的 hash-only replacement set、allowed-output signoff、exact-hash replacement 或 numeric tolerance policy signoff、independent reviewer decision；同时保留 authority guards 全 false 和 `benchmark_consumed_for_release=false` |
| 禁止越界项 | 不原地修改 `mechanism_comparison_hashes` cached anchors；不保留 spreadsheet raw selected values、formula text、temporary workbook copy、stdout/stderr 或 raw output tables；不把 LibreOffice headless execution 当 independent spreadsheet review；不把 replacement anchor set 当 admitted evidence；不修改 retained gate JSON 或 source ledger；不授予 `blast_mechanism_authority`、`effect_scale_authority`、`component_failure_probability_authority`、stock/runtime/Pk/fuze authority |
| 验收命令或验收证据 | 运行 `python3 tools/maintenance/a2_blastfrag_res006_beco_recalculation_admission_gate.py` 和 `pytest -q tests/architecture/test_a2_blastfrag_res006_beco_recalculation_admission_gate.py`；另外提交 independent lineage review、allowed-output signoff、tolerance 或 replacement-anchor signoff 的 retained evidence。只有新的 gate 明确 admit replacement/tolerance path，才能考虑 residual register 的窄域状态更新；否则继续 fail-closed |

当前 blocker 精确清单：

- headless spreadsheet execution completed，但 `BEC-O-METRIC-DEFAULT-001..009` 的 recalculated selected output hashes 全部不同于 cached anchors；
- cached-vs-recalculated selected hashes 不满足 exact-hash admission；
- source rights allowed-output policy 仍对 selected comparison outputs fail-closed；
- release-grade tolerance 或 replacement-anchor signoff 不存在；
- candidate recalculated hash anchor set 已保留，但未 admitted。

## G2/G3 边界

本 backlog 的完成标准只允许形成下一轮 `TC-A2-BF-003` mechanism admission 的 retained review inputs。
它不构成 `G4` authority promotion，也不构成 `G5` kill-chain authority。

在 `RES-005/006` 新 gate 明确通过前，以下结论必须保持不变：

- `RES-005` TP-21 保持 `open_fail_closed_tp21_selected_debris_outputs_missing`；
- `RES-006` BEC-O 保持 `open_fail_closed_beco_recalculation_not_admitted`；
- TP-21 / BEC-O comparison outputs 不消费为 release evidence；
- fragment/blast row authority 不授予；
- stock descriptor、runtime authority、effect-scale、component probability、Pk、deterministic fuze authority 全 false。

## 下一轮交付包格式

下一轮 worker 若执行任一 blocker，应返回：

- touched retained artifact path / manifest path；
- retained gate decision；
- `closed_residual_ids_by_this_gate` 和 authority guard diff；
- source-rights / allowed-output / independent reviewer signoff 引用；
- 验收命令输出；
- 明确说明是否仍 fail-closed。
