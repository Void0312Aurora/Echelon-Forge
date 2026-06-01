# A2 Candidate 验收状态

状态：`2026-06-01 / G2 candidate acceptance closeout / accepted_non_authoritative / non-authoritative`。

本文承接当前 blast-fragmentation 候选包验收。当前批次名称固定为：

`A2 blastfrag candidate evidence package acceptance`

它不是 stock release，不创建 runtime descriptor，不授予 `effect_scale_authority`、
`component_failure_probability_authority`、`pk_authority` 或
`deterministic_fuze_authority`。

本文的验收层级是 `G2 candidate acceptance`。`TC-A2-BF-001..004` 已按本层级收尾为
`accepted_non_authoritative`。
文中涉及 `RES-*` 的内容只读取 `G3 residual` 状态，不把局部 residual closeout
上卷为当前批次完成条件。`G4/G5` 继续 deferred。

当前项目默认保留 research / candidate profile，见
[research_candidate_data_policy_20260601.zh.md](research_candidate_data_policy_20260601.zh.md)。
因此 `accepted_non_authoritative` 是当前务实完成口径，不再默认等待工业级或 release-grade
数据来源。底层数据后续按可替换、可扩展、可追溯原则继续完善。

## G2 closeout verdict

当前批次可关闭为：

| 项 | 收尾结论 | 边界 |
|---|---|---|
| `TC-A2-BF-001` source / identity / retained evidence | accepted | source payload、rights/output policy、scoped identity、retained manifest integrity 与 authority guard 可审阅 |
| `TC-A2-BF-002` scope / geometry / warhead evidence | accepted with deferred truth residuals | Stage B witness geometry / family scope 子范围可审计；真实 F-16 geometry 和 AIM-120C warhead truth 继续 open |
| `TC-A2-BF-003` mechanism admission evidence | accepted as retained/fail-closed package evidence | TP-21 / BEC-O retained packets、signoff intake、template 和 preflight 存在；`RES-005/006` 不关闭、不消费为 release evidence |
| `TC-A2-BF-004` candidate bundle / regression | accepted | bundle、source admission、manifest integrity 和 runtime/contract regression 提供当前机器入口 |

该 verdict 只表示 `candidate package accepted`。它不创建 stock runtime descriptor，不授予
`effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或
`deterministic_fuze_authority`。

## Scope

| 轴 | 当前值 |
|---|---|
| target | `F-16C_Block50` |
| weapon class | `AIM-120C-class` |
| weapon family | `blast_fragmentation` |
| aspect bucket | `beam` |
| closure bucket | `high` |
| miss-distance bucket | `near_miss_0_35m` |
| authority state | candidate / non-authoritative / fail-closed by default |

## G2 candidate acceptance 任务簇

| 任务簇 | 粒度 | 验收标准 | 不属于本簇 |
|---|---|---|---|
| `TC-A2-BF-001` source / identity / retained evidence | `G2 candidate acceptance` | source payload、rights/output policy、scoped surrogate identity 可读取；bundle 可机器读取；retained manifest integrity checker 通过；authority guards 全 false | 法律意见、外部发布权、global clean release identity、stock runtime authority |
| `TC-A2-BF-002` scope / geometry / warhead evidence | `G2 candidate acceptance`；只读 `G3 residual` 状态 | 固定 `F-16C_Block50 x AIM-120C-class/blast_fragmentation x beam/high/near_miss_0_35m`；Stage B witness geometry、family-scope、bucket/axis gate retained；truth gaps 明确留在 residual | 真实 F-16 内部几何/材料/遮挡真值、具体 AIM-120C 战斗部真值、多目标/多武器扩面 |
| `TC-A2-BF-003` mechanism admission evidence | `G2 candidate acceptance`；只读 `G3 residual` 状态 | TP-21 / BEC-O 执行、hash、admit 或 fail-closed 原因由 retained gate 固化；accepted as retained/fail-closed package evidence, not admitted as release-consumed evidence | 把 TP-21/BEC-O 输出消费为 release evidence；授予 fragment/blast row authority |
| `TC-A2-BF-004` candidate bundle / regression | `G2 candidate acceptance` | [a2_candidate_vps_bundle.py](../../../../tools/maintenance/a2_candidate_vps_bundle.py) 和 A2 regression 只作为机器入口与回归入口；它们能汇总 source、validation scaffold、runtime-aligned exercise 和 residual 状态；stock/effect/component/Pk/fuze authority 全 false | release-grade authority promotion、stock DB release、Pk/fuze/kill-chain 验收 |

## Retained manifest integrity

`TC-A2-BF-001-HASH` 已作为当前 candidate 包的 retained manifest 强验收项通过：

- [a2_retained_manifest_integrity.py](../../../../tools/maintenance/a2_retained_manifest_integrity.py)
  默认扫描 candidate package 的 `retained_artifacts/**/manifest.json`；
- 当前验收输出为 `manifest_count=29`、`missing_total=0`、`sha_mismatch_total=0`、
  `guard_true_total=0`；
- 该验收只证明 retained manifest 引用和 hash 自洽，不授予任何 `G4/G5` authority。

## G4/G5 deferred

`TC-A2-AUTH-B`、`TC-A2-AUTH-C` 和 `TC-A2-KILLCHAIN` 不由本文关闭；不得从
`TC-A2-BF-001..004` 推导 stock runtime authority、Pk 或 deterministic fuze。

若下一步只是继续研究级高保真，应使用
[G4/G5 research continuation](g4_g5_research_continuation_20260601.zh.md)，并保持
non-authoritative / replaceable data 口径。

## 当前工作区复核

本轮按 `docs/agent` 的能力声明门槛，在当前工作区重新核验了代码/测试/工具表面：

```bash
python -m pytest -q tests/architecture/test_a2_retained_manifest_integrity.py tests/architecture/test_a2_candidate_vps_bundle.py tests/architecture/test_a2_source_admission_audit.py tests/runtime/air_combat/test_vulnerability_evidence_dataset_descriptor.py
python -m pytest -q tests/runtime/engagement/test_engagement_contract_shape.py tests/runtime/engagement/test_launch_adapter_static_shape.py tests/runtime/engagement/test_live_engagement_event_capture.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/architecture/test_a2_blastfrag_signoff_admission_preflight.py tests/architecture/test_a2_blastfrag_res006_beco_recalculation_admission_gate.py tests/architecture/test_a2_blastfrag_res005_tp21_selected_case_candidate_packet.py tests/architecture/test_a2_blastfrag_signoff_intake_fixture_contract.py tests/architecture/test_a2_blastfrag_signoff_intake_contract.py tests/architecture/test_a2_blastfrag_source_rights_signoff_request_packet.py tests/architecture/test_a2_blastfrag_res006_beco_lineage_tolerance_review_packet.py tests/architecture/test_a2_blastfrag_res005_tp21_selected_case_admission_gate.py tests/architecture/test_a2_blastfrag_external_signoff_packet_template.py tests/architecture/test_a2_blastfrag_res006_beco_replacement_tolerance_admission_gate.py
python tools/maintenance/a2_retained_manifest_integrity.py
python tools/maintenance/a2_source_admission_audit.py --strict
python tools/maintenance/a2_candidate_vps_bundle.py
```

结果：

- A2 candidate/source/manifest/descriptor：`17 passed`；
- engagement contract / launch adapter / live capture shape：`16 passed`；
- weapon guidance realism guards：`150 passed`；
- G2 fail-closed signoff / residual packet focused suite：`44 passed`；
- retained manifest integrity：`manifest_count=29`、`missing_total=0`、
  `sha_mismatch_total=0`、`guard_true_total=0`；
- source admission strict：`9 ledgers, 29 candidate docs, 51 calibration docs`；
- candidate bundle CLI：exit 0，输出仍为 `candidate_non_authoritative_bundle`，
  stock/effect/component/Pk/fuze authority guard 全 false。

## G3 residual 读取规则

事实源是 [residual_register.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)
和 retained artifact manifests。G3 台账收尾记录是
[g3_residual_closeout_status_20260601.zh.md](g3_residual_closeout_status_20260601.zh.md)。
叙事文档不得覆盖 retained gate JSON 的结论。

G3 当前只能写成 `research_closed_authority_retained`：`RES-001..014` 对当前 research
profile 不再形成阻塞，且均有明确状态和证据入口，但不是 `all authority residuals closed`。

在 research profile 下，旧 open / fail-closed residual 已重标为 research-closed 或
research-out-of-scope；它们保留为 future authority blocker 或后续 research data replacement target。

| residual | 当前 candidate 口径 |
|---|---|
| `RES-001` | 窄域 internal signoff evidence 已关闭；仍不构成外部发布权或 benchmark consumption authority |
| `RES-002` | scoped package identity 已关闭；仍不构成 global clean release identity |
| `RES-003/004` | Stage B witness geometry / family scope 子范围关闭；真实几何和具体战斗部 truth 只阻塞 future authority |
| `RES-005/006` | mechanism execution evidence、2026-06-01 retained review packet、candidate/signoff request packet 已保留；research profile 可走可替换 envelope，authority 仍 fail-closed，不得消费为 release evidence |
| `RES-007/008` | Stage B scope/bucket review 通过；不得扩展成 validated near-miss 或 closure physics authority |
| `RES-009` | Stage C research surface 可保留；component fragility truth 只阻塞 future authority |
| `RES-010/011/012` | Stage B closeout 已有 retained evidence；Stage C release-grade closeout 继续只阻塞 future authority |
| `RES-013/014` | Pk 与 deterministic fuze 是 research out-of-scope / authority boundary deferred，不在本候选包关闭 |

2026-06-01 第 2 轮只读 evidence sweep 已确认：子项目数据和 retained packets 已存在，
但 `RES-005/006` 的具体 selected-case / replacement-tolerance signoff 链未闭合；本候选
包仍停在 `G2 candidate acceptance`，不产生 `G4/G5` authority。
随后新增的 signoff intake contract 只定义未来外部 reviewer/signoff packet 的 hash-only
输入形状和 fail-closed checker；默认无外部签收输入，不关闭 residual。
本轮继续新增 external signoff packet template 和 signoff admission preflight，只把后续
reviewer 输入的填写形状与入 gate 前预检机器化；仍不消费 reviewer 决策，不关闭
`RES-005/006`。

## 活跃证据入口

- [candidate package README](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/README.zh.md)
- [residual register](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)
- `calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/**/manifest.json`
- [tools/maintenance/a2_candidate_vps_bundle.py](../../../../tools/maintenance/a2_candidate_vps_bundle.py)
- [tools/maintenance/a2_blastfrag_runtime_aligned_authority_pack.py](../../../../tools/maintenance/a2_blastfrag_runtime_aligned_authority_pack.py)
- [mechanism admission fail-closed backlog](mechanism_admission_failclosed_backlog_20260601.zh.md)
- `retained_artifacts/res005_tp21_selected_case_admission_20260601/res005_tp21_selected_case_admission_review_gate.json`
- `retained_artifacts/res006_beco_replacement_tolerance_admission_20260601/res006_beco_replacement_tolerance_admission_gate.json`
- `retained_artifacts/res005_tp21_selected_case_candidate_20260601/res005_tp21_selected_case_candidate_packet.json`
- `retained_artifacts/res006_beco_lineage_tolerance_review_20260601/res006_beco_lineage_tolerance_review_candidate_packet.json`
- `retained_artifacts/source_rights_signoff_request_20260601/source_rights_signoff_request_packet.json`
- `retained_artifacts/signoff_intake_contract_20260601/signoff_intake_contract.json`
- `retained_artifacts/external_signoff_packet_template_20260601/external_signoff_packet_template.json`
- `retained_artifacts/signoff_admission_preflight_20260601/signoff_admission_preflight_packet.json`

## 验收命令

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\test_a2_source_admission_audit.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python tools\maintenance\a2_source_admission_audit.py --strict
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\test_a2_retained_manifest_integrity.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python tools\maintenance\a2_retained_manifest_integrity.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\test_a2_candidate_vps_bundle.py
```

如果本簇声明 `A2 regression 通过`，同时按 [runtime 状态](runtime_status.zh.md) 的
验证锚点运行 runtime / binding regression。
