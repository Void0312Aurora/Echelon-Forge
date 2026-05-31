# A2 Candidate 验收状态

状态：`2026-06-01 / G2 candidate acceptance entry / TC-A2-BF-001-HASH accepted / non-authoritative`。

本文承接当前 blast-fragmentation 候选包验收。当前批次名称固定为：

`A2 blastfrag candidate evidence package acceptance`

它不是 stock release，不创建 runtime descriptor，不授予 `effect_scale_authority`、
`component_failure_probability_authority`、`pk_authority` 或
`deterministic_fuze_authority`。

本文的验收层级是 `G2 candidate acceptance`。`TC-A2-BF-001..004` 只属于本层级。
文中涉及 `RES-*` 的内容只读取 `G3 residual` 状态，不把局部 residual closeout
上卷为当前批次完成条件。`G4/G5` 继续 deferred。

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
- 当前验收输出为 `manifest_count=21`、`missing_total=0`、`sha_mismatch_total=0`、
  `guard_true_total=0`；
- 该验收只证明 retained manifest 引用和 hash 自洽，不授予任何 `G4/G5` authority。

## G4/G5 deferred

`TC-A2-AUTH-B`、`TC-A2-AUTH-C` 和 `TC-A2-KILLCHAIN` 不由本文关闭；不得从
`TC-A2-BF-001..004` 推导 stock runtime authority、Pk 或 deterministic fuze。

## G3 residual 读取规则

事实源是 [residual_register.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)
和 retained artifact manifests。叙事文档不得覆盖 retained gate JSON 的结论。

| residual | 当前 candidate 口径 |
|---|---|
| `RES-001` | 窄域 internal signoff evidence 已关闭；仍不构成外部发布权或 benchmark consumption authority |
| `RES-002` | scoped package identity 已关闭；仍不构成 global clean release identity |
| `RES-003/004` | Stage B witness geometry / family scope 子范围关闭；真实几何和具体战斗部 truth 继续 open |
| `RES-005/006` | mechanism execution evidence 已保留但 fail-closed；不得消费为 release evidence |
| `RES-007/008` | Stage B scope/bucket review 通过；不得扩展成 validated near-miss 或 closure physics authority |
| `RES-009` | Stage C component fragility truth 继续 open |
| `RES-010/011/012` | Stage B closeout 已有 retained evidence；Stage C release-grade closeout 继续 blocked |
| `RES-013/014` | Pk 与 deterministic fuze 是 boundary deferred，不在本候选包关闭 |

## 活跃证据入口

- [candidate package README](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/README.zh.md)
- [residual register](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)
- `calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/**/manifest.json`
- [tools/maintenance/a2_candidate_vps_bundle.py](../../../../tools/maintenance/a2_candidate_vps_bundle.py)
- [tools/maintenance/a2_blastfrag_runtime_aligned_authority_pack.py](../../../../tools/maintenance/a2_blastfrag_runtime_aligned_authority_pack.py)
- [mechanism admission fail-closed backlog](mechanism_admission_failclosed_backlog_20260601.zh.md)

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
