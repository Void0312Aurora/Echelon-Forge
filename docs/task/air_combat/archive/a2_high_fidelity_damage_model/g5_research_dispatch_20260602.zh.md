# A2 G5 Research Dispatch - 2026-06-02

状态：`2026-06-02 / G5 research_packet_accepted / research_only / replaceable_data`。

本文是 A2 `G5-R` 的中央分发包。它只启动 Pk / fuze proxy 的研究级任务线，不启动
工业级 / release-grade 准入，不授予 `pk_authority` 或 `deterministic_fuze_authority`，
不创建 runtime descriptor，不替换现有 RNG-compatible fallback。

父入口：

- [G4/G5 research continuation](g4_g5_research_continuation_20260601.zh.md)
- [G4 research integration acceptance](g4_research_integration_acceptance_20260601.zh.md)
- [research candidate data policy](research_candidate_data_policy_20260601.zh.md)
- [G3 residual closeout status](g3_residual_closeout_status_20260601.zh.md)
- [residual register](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)

## Boundary Decision

`G5-R` 本轮只按 research lane 分发：

- `G5-R-A`：Pk / fuze proxy method source scan；
- `G5-R-B`：Pk / fuze proxy boundary design；
- `G5-R-C`：kill-chain event-chain map；
- `G5-R-D`：uncertainty / independence audit；
- `G5-R-INTEGRATION`：串行整合与 guard validation。

本轮不得写成：

- Pk authority or Pk calibration claim；
- deterministic fuze authority or release claim；
- mission-kill probability；
- stock descriptor created；
- runtime RNG / fallback path removed；
- training reward or combat win accepted as kill-chain truth。

## Dispatch Matrix

| Task | Grain | Owner | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
|---|---|---|---|---|---|---|---|---|---:|---|
| `G5-R-DISPATCH` | `G5 research` | main-thread dispatch owner | 拆出 G5 research proxy 工作包 | `g5_research_dispatch_20260602.zh.md` | 不做 G5 authority；不修改 runtime/test | 分发包存在且每个子任务有 write set、non-goals、validation、closure gate | 中央入口说明 G5 已按 research 分发 | 依赖 G4 integration accepted | 1 | `pass` |
| `G5-R-A-SOURCE-SCAN` | `G5 research` | source / method scan worker | 整理 Pk / fuze proxy 可用方法输入、拒绝项和 replacement rule | [data_collection/kill_chain_proxy_methods/README.zh.md](data_collection/kill_chain_proxy_methods/README.zh.md)、[g5_r_source_scan_20260602.zh.md](data_collection/kill_chain_proxy_methods/g5_r_source_scan_20260602.zh.md) | 不写 Pk 曲线；不抽游戏/论坛参数；不复制受限 raw output | source rows 均有 class、scope、rights、uncertainty/confidence、replacement rule | source scan 已落盘，可作为 proxy boundary design 输入 | 可先行 | 1 | `pass` |
| `G5-R-B-PROXY-BOUNDARY` | `G5 research` | proxy design worker | 定义 Pk / fuze proxy event variables、allowed output 和 forbidden claims | [g5_research_pk_fuze_proxy_boundary_design_20260602.zh.md](g5_research_pk_fuze_proxy_boundary_design_20260602.zh.md) | 不输出概率真值；不替换 RNG hit gate；不创建 descriptor | 每个 proxy variable 绑定 source ids、scope、uncertainty、replacement rule；明确 non-authoritative | boundary design 已落盘，可进入 event-chain map | 依赖 `G5-R-A` | 1 | `pass` |
| `G5-R-C-EVENT-CHAIN-MAP` | `G5 research` | event-chain worker | 把 guidance / fuze proxy / G4 mechanism / G4 fragility / consequence 串成 research event chain | [g5_research_event_chain_map_20260602.zh.md](g5_research_event_chain_map_20260602.zh.md) | 不做 runtime 实现；不写 Pk；不消费 combat reward | guard grep；event rows 不包含 authority true 或 calibrated claim | event chain map 明确每个 stage 的输入、输出和不确定性 | 依赖 `G5-R-B` | 1 | `pass` |
| `G5-R-D-UNCERTAINTY-AUDIT` | `G5 research` | uncertainty / independence reviewer | 审查 proxy chain 的 source/model/result independence 与 uncertainty coverage | [g5_research_uncertainty_independence_audit_20260602.zh.md](g5_research_uncertainty_independence_audit_20260602.zh.md) | 不把 proxy score 写成 reviewer-accepted truth | audit 覆盖 epistemic/aleatory/source/scope/model-form uncertainty | G5 proxy packet 可进入 integration | 依赖 `G5-R-C` | 1 | `pass` |
| `G5-R-INTEGRATION` | `G5 research` | main thread | 同步 README、dispatch、execution status 和 validation list | [g5_research_integration_acceptance_20260602.zh.md](g5_research_integration_acceptance_20260602.zh.md)、README/status/dispatch | 不启动 authority backlog；不修改 retained artifacts | retained manifest integrity、source audit、candidate bundle、guard grep、diff check | G5-R research packet 完成并保持 guards false | 依赖 `G5-R-C/D` | 1 | `pass` |

## Worker Packet Requirements

每个 G5 research worker 返回：

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
research boundary confirmation:
```

`status=pass` 只表示被分配的 research slice 完成；不得解读为 `Pk`、deterministic fuze
或 mission-kill authority。

## Validation Plan

```bash
python tools/maintenance/a2_retained_manifest_integrity.py
python tools/maintenance/a2_source_admission_audit.py --strict
python tools/maintenance/a2_candidate_vps_bundle.py
rg -n "pk_authorit[y].*true|deterministic_fuze_authorit[y].*true|stock_descriptor_create[d].*true|replacement_allowe[d].*false" docs/task/air_combat/archive/a2_high_fidelity_damage_model/g5_research_*.zh.md docs/task/air_combat/archive/a2_high_fidelity_damage_model/data_collection/kill_chain_proxy_methods
git diff --check
```

## Acceptance Criteria

`G5-R` 可以继续从 dispatch 进入 research packet execution，仅当：

- `G5-R-A` 和 `G5-R-B` 不写概率真值或引信真值；
- `G4-R-B` / `G4-R-C` 只作为 research input，不被上卷成 kill-chain truth；
- `RES-013/014` 仍明确为 research proxy lane 的边界，不关闭 authority；
- candidate bundle 仍输出 `candidate_non_authoritative_bundle`；
- stock/effect/component/Pk/fuze machine guards 全 false。

## Residual Boundary

- `RES-013`：G5-R 可以设计 Pk proxy chain，但不得声称 Pk calibration 或 single-shot kill probability。
- `RES-014`：G5-R 可以设计 fuze proxy branch 与 fallback-compatible event shape，但不得声称 deterministic fuze authority。
- `RES-005/006`、`RES-009..012`：只作为 G4 research input dependency，不在 G5-R 中重新关闭。
