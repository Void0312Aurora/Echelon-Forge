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

## 已有数据与仍缺准入

子项目下的数据与 payload 已经存在，本 backlog 不把 `RES-005/006` 表述为“没有数据”：

| 数据面 | 已保留内容 | 仍不能关闭的原因 |
|---|---|---|
| source payload | `source_payload_pack_20260531/payloads/TP-21.pdf`、`BEC-O-V1.xlsx`、`TP-20.pdf` 已由 manifest 记录 sha256 | payload acquired 只证明源文件存在；不自动允许复制原文、表格、原始数值或把输出消费为 release evidence |
| TP-21 / `RES-005` | `selected_debris_output_anchor_set.json` 已存在，但当前 `selected_debris_output_hash_count=0` | 仍缺 reviewer-selected case locator、redacted selected-output preimage sha256、hash-only selected debris output anchor set、independent reviewer signoff 和 allowed-output signoff |
| BEC-O / `RES-006` | `beco_recalculated_hash_anchor_set.json` 已保留 9/9 recalculated hash anchors；`mechanism_comparison_hashes.json` 已保留 9 个 cached anchors | cached-vs-recalculated 为 0 match / 9 mismatch；仍缺 independent lineage review、allowed-output signoff、numeric tolerance policy 或 replacement-anchor signoff |
| rights / output policy | `source_rights_output_policy_gate.json` 已冻结 policy | 当前 policy 仍 fail-closed，`release_grade_satisfied=false`，不能把 selected comparison outputs 当作 release-consumed evidence |

因此，下一步不是重新“找数据”，而是把已有数据的 selected-case / replacement path
补成可审阅、hash-only、rights-safe、signoff 完整的 retained admission evidence。

| residual | retained gate result | backlog interpretation |
|---|---|---|
| `RES-005` TP-21 fragment mechanism | `blocked_fail_closed_tp21_debris_admission_gate` / `blocked_fail_closed_tp21_selected_debris_outputs_missing` | 下一轮只补 selection/provenance/hash/signoff 证据链；当前不 admit TP-21 debris outputs |
| `RES-006` BEC-O blast mechanism | `res006_remains_blocked_fail_closed` / `blocked_fail_closed_beco_recalculation_not_admitted` | 下一轮只处理 recalculation lineage、allowed-output、tolerance/replacement signoff；当前不 admit BEC-O hashes |

2026-06-01 retained review packet 已把上述两个 blocker 机器化为新的 fail-closed
review inputs，但没有关闭 residual：

| residual | retained review packet | 当前结论 |
|---|---|---|
| `RES-005` | `retained_artifacts/res005_tp21_selected_case_admission_20260601/res005_tp21_selected_case_admission_review_gate.json` | `blocked_fail_closed_tp21_selected_case_admission_review_packet`；仍缺 reviewer-selected case locator、selected output preimage sha256、selected debris output anchor set、independent reviewer signoff、allowed-output signoff 和 authority-boundary signoff |
| `RES-006` | `retained_artifacts/res006_beco_replacement_tolerance_admission_20260601/res006_beco_replacement_tolerance_admission_gate.json` | `blocked_fail_closed_res006_beco_replacement_tolerance_admission_review`；仍缺 independent lineage review、allowed-output signoff、numeric tolerance policy signoff 和 replacement-anchor signoff |

同轮还生成了三个 request / candidate 层 retained packet。它们只把已有数据的准入缺口继续机器化，
不代表 signoff 已经完成：

| packet | retained artifact | 当前结论 |
|---|---|---|
| TP-21 selected-case candidate | `retained_artifacts/res005_tp21_selected_case_candidate_20260601/res005_tp21_selected_case_candidate_packet.json` | `blocked_fail_closed_tp21_selected_case_candidate_packet`；已有 TP-21 payload，但仍无 retained selected case locator、preimage sha256 或 selected output hash anchors |
| BEC-O lineage/tolerance candidate | `retained_artifacts/res006_beco_lineage_tolerance_review_20260601/res006_beco_lineage_tolerance_review_candidate_packet.json` | cached/recalculated topology 已可审计，仍是 0/9 match 且无 independent lineage、tolerance 或 replacement signoff |
| source-rights signoff request | `retained_artifacts/source_rights_signoff_request_20260601/source_rights_signoff_request_packet.json` | 只生成 review request/checklist；`approval_granted=false`、`release_grade_satisfied=false`，policy 继续 fail-closed |
| signoff intake contract | `retained_artifacts/signoff_intake_contract_20260601/signoff_intake_contract.json` | 只定义未来外部 reviewer/signoff packet 的 hash-only 输入形状和 checker；当前无外部 signoff packet supplied，`approval_granted=false`、`admission_granted=false` |
| external signoff template | `retained_artifacts/external_signoff_packet_template_20260601/external_signoff_packet_template.json` | reviewer-fillable template；placeholder decisions 刻意不是合法 reviewer decision，填充前会被 intake contract 拒绝 |
| signoff admission preflight | `retained_artifacts/signoff_admission_preflight_20260601/signoff_admission_preflight_packet.json` | 只把 shape-valid 外部 signoff packet 转成后续 admission gate 的 ready flag；默认无外部 packet supplied，`ready_for_admission_gate=false` |

2026-06-01 第 2 轮只读 evidence sweep 已确认：下一步不是重新获取数据，而是等待或生成外部
reviewer/signoff 输入。RES005 未找到可复用的 selected-case locator、selected-output
preimage sha256、非空 selected-output anchor set、independent reviewer signoff、
allowed-output signoff 或 RES005-specific authority-boundary signoff；RES001 的通用
authority-boundary signoff 不能替代 RES005 selected-case signoff。RES006 未找到可复用的
independent lineage、allowed-output、numeric tolerance 或 replacement-anchor signoff；
`9/9` recalculated anchors retained 和 `0/9` cached-vs-recalculated match 仍只表示
hash-only topology，不构成 tolerance 或 replacement admission。

新增 signoff intake contract 后，后续若收到外部 reviewer/signoff packet，应先按该 contract
做 shape check：必须 pin 到当前 source-rights signoff request packet，包含七个必需 signoff id，
只保留 reviewer/decision/input 的 sha256 引用，所有 raw-content absence 与 authority guard
字段保持 false。shape check 通过也只是进入后续 admission gate 的前置条件，不是 approval。
本轮新增的 external template 和 preflight 把这条路径补成可操作流程：reviewer 可从 template
复制后替换 placeholder 决策与 hash refs；fixture 测试保证 raw key 或 authority true 会被拒绝；
preflight 只报告是否可以尝试 RES005/RES006 admission gate，不消费 reviewer 决策。

## Backlog Item: `TC-A2-BF-003-RES005-TP21`

目标：把 `RES-005` 从“TP-21 payload 已保留但 selected debris comparison outputs 缺失”推进到可复审的
selected-case admission artifact；在签收前保持 fail-closed。

| 字段 | 内容 |
|---|---|
| owner | Mechanism admission evidence owner + independent reviewer；source-rights reviewer 必须单独签收 allowed-output 边界 |
| 输入 | `retained_artifacts/res005_tp21_debris_admission_20260531/res005_tp21_debris_admission_gate.json`；`selected_debris_output_anchor_set.json`；`retained_artifacts/source_payload_pack_20260531/payloads/TP-21.pdf` 的 payload hash；`source_rights_output_policy_20260531/source_rights_output_policy_gate.json`；`validation_res005_tp21_debris_admission_gate_20260531.zh.md`；`residual_register.zh.md` 中 `RES-005` 状态 |
| 输出 | 新的 retained selected-case admission artifact，至少包含 stable reviewer case id、page/section 或 figure/table locator label、redacted selected output preimage sha256、hash-only selected debris output anchor set、independent reviewer signoff、allowed-output signoff；同时保留 authority guards 全 false 和 `benchmark_consumed_for_release=false` |
| 禁止越界项 | 不复制 TP-21 prose、tables、figures 或 raw numeric values；不把 controlled criteria vocabulary 当成 concrete benchmark case；不把 selected hash output 当 release benchmark consumption；不修改 retained gate JSON 或 source ledger；不授予 `fragment_mechanism_authority`、`component_failure_probability_authority`、stock/runtime/Pk/fuze authority |
| 验收命令或验收证据 | 运行 `python3 tools/maintenance/damage_model_benchmark_evidence.py debris-admission`、`python3 tools/maintenance/damage_model_benchmark_evidence.py selected-debris-case-admission`、对应 architecture tests 和 retained manifest integrity；另外提交 independent reviewer signoff 与 allowed-output signoff 的 retained evidence。只有新的 gate 明确 `closed_residual_ids_by_this_gate` 或 narrow closeout，才能更新 residual register；否则继续 fail-closed |

当前 blocker 精确清单：

- 缺 reviewer-selected concrete TP-21 debris comparison case 的 page/section provenance labels；
- 缺 reviewer-selected case 的 selected output preimage hash；
- 缺 selected debris output hash anchor set；
- 缺 independent reviewer signoff；
- source-rights allowed-output policy 尚未 admit current comparison output hashes；
- 缺 authority-boundary signoff，确认 fragment/component/effect/stock/runtime/Pk/fuze authority 仍 false。

## Backlog Item: `TC-A2-BF-003-RES006-BECO`

目标：把 `RES-006` 从“BEC-O headless recalculation 已执行但 9/9 selected output hashes 与 cached anchors 不一致”
推进到可复审的 replacement/tolerance admission path；在签收前保持 fail-closed。

| 字段 | 内容 |
|---|---|
| owner | Blast mechanism admission owner + spreadsheet execution reviewer + source-rights/tolerance reviewer；replacement promotion 必须由独立 reviewer 签收 |
| 输入 | `retained_artifacts/res006_beco_recalculation_admission_20260531/res006_beco_recalculation_admission_gate.json`；`beco_recalculated_hash_anchor_set.json`；`retained_artifacts/mechanism_comparison_hashes_20260531/mechanism_comparison_hashes.json`；`source_rights_output_policy_20260531/source_rights_output_policy_gate.json`；`validation_res006_beco_recalculation_admission_gate_20260531.zh.md`；`residual_register.zh.md` 中 `RES-006` 状态 |
| 输出 | 单独 retained replacement/tolerance admission artifact，至少说明 cached-anchor lineage、headless recalculation runtime/version lineage、9 个 selected comparison id 的 hash-only replacement set、allowed-output signoff、exact-hash replacement 或 numeric tolerance policy signoff、independent reviewer decision；同时保留 authority guards 全 false 和 `benchmark_consumed_for_release=false` |
| 禁止越界项 | 不原地修改 `mechanism_comparison_hashes` cached anchors；不保留 spreadsheet raw selected values、formula text、temporary workbook copy、stdout/stderr 或 raw output tables；不把 LibreOffice headless execution 当 independent spreadsheet review；不把 replacement anchor set 当 admitted evidence；不修改 retained gate JSON 或 source ledger；不授予 `blast_mechanism_authority`、`effect_scale_authority`、`component_failure_probability_authority`、stock/runtime/Pk/fuze authority |
| 验收命令或验收证据 | 运行 `python3 tools/maintenance/damage_model_benchmark_evidence.py spreadsheet-recalculation-admission`、`python3 tools/maintenance/damage_model_benchmark_evidence.py spreadsheet-replacement-tolerance`、对应 architecture tests 和 retained manifest integrity；另外提交 independent lineage review、allowed-output signoff、tolerance 或 replacement-anchor signoff 的 retained evidence。只有新的 gate 明确 admit replacement/tolerance path，才能考虑 residual register 的窄域状态更新；否则继续 fail-closed |

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

- `RES-005` TP-21 对 research profile 已闭合为可替换 mechanism-load envelope 路线，
  对 authority 保持 `research_closed_mechanism_load_envelope_authority_fail_closed_tp21_selected_debris_outputs_missing`；
- `RES-006` BEC-O 对 research profile 已闭合为可替换 blast envelope 路线，
  对 authority 保持 `research_closed_mechanism_load_envelope_authority_fail_closed_beco_recalculation_not_admitted`；
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
