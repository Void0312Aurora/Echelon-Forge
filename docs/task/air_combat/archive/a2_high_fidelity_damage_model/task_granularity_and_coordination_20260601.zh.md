# A2 高保真空战毁伤模型任务粒度与协调总账

状态：`2026-06-02 / coordination_index / G5 research accepted / non-authoritative`。

本文只整理任务粒度、命名和当前执行边界，不创建 runtime descriptor，不授予
`effect_scale_authority`、`component_failure_probability_authority`、`pk_authority`
或 `deterministic_fuze_authority`。

当前默认目标是 research / candidate profile：保留可运行、可审阅、可复现、数据可替换的
非权威毁伤模型。`G4/G5` authority 不再作为默认后续完成标准，只在用户明确要求时另启。

## 1. 为什么需要这份总账

当前 A2 子项目已经同时包含 runtime 工程、candidate evidence package、source admission、
residual closeout、validation scaffold、独立 review gate 和 stock authority promotion 等材料。
这些材料都必要，但它们不属于同一粒度。

目前最容易混淆的是：

- 把 `Phase 1/2/3/5` 当成 release 任务簇；
- 把 `TC-A2-BF-*` candidate acceptance 当成 authority promotion；
- 把 `RES-*` residual 的局部关闭当成全局关闭；
- 把 test-local descriptor 正向路径当成 stock runtime authority；
- 把 `DamageReport` / `EffectsEvent` runtime 闭环当成 Pk 或 deterministic fuze 闭环。

后续 A2 工作必须先说明自己在下面哪一层移动。

## 2. 标准粒度

| 层级 | 名称 | 用途 | 可说“完成”的条件 | 不得越界为 |
|---|---|---|---|---|
| `G0` | 项目方向 | A2 高保真空战毁伤模型总体方向 | 不作为单次验收对象 | 不能说整个高保真 kill-chain 完成 |
| `G1` | runtime 工程阶段 | Phase 1/2/3/5 的代码、事件面、测试和维护路径 | 相关 runtime 行为、contract、binding、回归通过 | 不等于 calibrated authority |
| `G2` | 候选证据包验收 | `TC-A2-BF-*` 当前执行批次 | retained artifacts、bundle、source admission 和边界守卫通过 | 不等于 stock release |
| `G3` | residual 状态 | `RES-001..014` 的阻塞项、局部关闭项和边界项 | residual register 有稳定 artifact 引用和明确状态 | 不等于上层任务簇完成 |
| `G4 research` | 研究级机制载荷 / 脆弱性延续 | non-authoritative mechanism-load envelope、component fragility surface、uncertainty ledger | 数据可追溯、可替换、带 uncertainty / confidence / replacement rule，authority guards 全 false | 不等于 `G4 authority` 或 stock release |
| `G4 authority` | authority promotion | `effect_scale_authority` / `component_failure_probability_authority` 进入可发布 runtime authority | descriptor、source、validation、scope、rows 和 residual gate 全部满足 | 不等于 Pk 或 fuze |
| `G5 research` | 研究级 kill-chain proxy | Pk / fuze proxy boundary、event-chain map、uncertainty audit | proxy 数据可追溯、可替换，且明确不是 Pk / deterministic fuze authority | 不等于 `G5 authority`、Pk 或 fuze release |
| `G5 authority` | kill-chain authority | Pk、deterministic fuze、mission-kill 概率 | 独立证据链存在并另行验收 | 不得由本 candidate 包或 research proxy 顺手关闭 |

在当前 research profile 下，`G1/G2/G3` 是基础完成面；`G4/G5 research` 可以作为
非权威、可替换数据的延续工作被验收。`G4/G5 authority` 才是 opt-in backlog，
不是当前项目必须拿工业级数据才能继续的阻塞项。

推荐用语：

- `runtime sub-loop closed`：只表示某段工程链路从状态到事件/消费面闭合。
- `candidate package accepted`：只表示候选包非权威验收通过。
- `residual locally closed`：只表示某个 residual 的某个子范围有 retained gate。
- `authority promoted`：只用于 stock/runtime authority 真正放行。
- `boundary deferred`：用于 Pk、deterministic fuze 等本批次不关闭的边界。

禁止用语：

- 不单独说“闭合了 A2 毁伤模型”，除非同时指明 `G1..G5` 中哪一层。
- 不把“Stage B passed”写成“effect-scale authority released”。
- 不把“Stage C test-local positive path”写成“`component_failure_probability` calibrated”。
- 不把“DamageReport 终局/非终局消费可用”写成“Pk 已校准”。

## 3. 当前执行批次

当前批次名称固定为：

`A2 blastfrag candidate evidence package acceptance`

当前批次不是：

- `release-grade authority promotion`
- `stock runtime authority release`
- `Pk calibration`
- `deterministic fuze release`
- `full A2 high-fidelity kill-chain completion`

当前批次的验收目标只到 `G2`。`G3` 在本批次中只表示 residual 状态读取、
局部 closeout 记录和台账闭合，不上卷为批次验收层级或 authority release：

1. 候选包可以被审计、复现和 fail-closed；
2. source / identity / retained artifacts 有稳定 manifest；
3. scope / bucket / mechanism admission 的 admit 或 fail-closed 原因可机器读取；
4. `authority` guard 全程保持 false；
5. A2 runtime 和 architecture regression 不回归。

2026-06-01 后，`G3` 可以写成
`research_closed_authority_retained`，含义仅限 `RES-001..014` 对当前 research profile
不再形成阻塞，且均有明确状态、稳定证据入口和不得上卷边界。完整清点见
[g3_residual_closeout_status_20260601.zh.md](g3_residual_closeout_status_20260601.zh.md)。
这不表示所有 authority residual substantive closeout，也不自动要求 `G4/G5 authority`。
后续 `G4/G5 research` 已按独立 research packet 收口。

同日确认 research-only 决策：当前不再等待工业级或 release-grade 数据作为默认完成条件。
`RES-*` 中阻塞 authority 的部分继续保留为 authority blocker；阻塞 research data surface 的部分
应按 [research_candidate_data_policy_20260601.zh.md](research_candidate_data_policy_20260601.zh.md)
转为可替换、可扩展、非权威数据路线。

## 4. 任务簇归并

| 任务簇 | 粒度 | 当前口径 | 主要证据入口 |
|---|---|---|---|
| `TC-A2-RUNTIME` | `G1` | structured aircraft damage/effects runtime 主链进入维护路径；仍非校准权威 | `runtime_status.zh.md`、runtime tests、`EffectsEvent` / `DamageReport` contract |
| `TC-A2-BF-001` source / identity / retained evidence | `G2` | accepted non-authoritative；不授予外部发布权或 stock authority | [candidate status](candidate_acceptance_status.zh.md)、candidate package README、source payload pack、source rights policy、identity gates |
| `TC-A2-BF-002` scope / geometry / warhead evidence | `G2` + `G3` 状态读取 | Stage B scope/witness/family bookkeeping 可接受；真实 geometry/warhead truth 继续 residual | [candidate status](candidate_acceptance_status.zh.md)、[RES-003/004/007/008](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) |
| `TC-A2-BF-003` mechanism admission evidence | `G2` + `G3` 状态读取 | accepted as retained/fail-closed package evidence；TP-21/BEC-O 不作为 release-consumed evidence | [candidate status](candidate_acceptance_status.zh.md)、[RES-005/006](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) |
| `TC-A2-BF-004` candidate bundle / regression | `G2` | candidate bundle 可审计，authority guard false | [candidate status](candidate_acceptance_status.zh.md)、[damage_model.py](../../../../tools/maintenance/damage_model.py) `candidate-artifacts package-bundle`、runtime-aligned authority pack |
| `G4-R-B` mechanism-load envelope | `G4 research` | 已完成 research packet；只形成 non-authoritative fragment / blast envelope | [G4 research dispatch](g4_research_dispatch_20260601.zh.md)、[mechanism-load envelope dispatch](g4_research_mechanism_load_envelope_dispatch_20260601.zh.md) |
| `G4-R-C` component fragility surface | `G4 research` | 已完成 research packet；只形成 non-authoritative component fragility surface / uncertainty ledger | [G4 research dispatch](g4_research_dispatch_20260601.zh.md)、[component fragility dispatch](g4_research_component_fragility_dispatch_20260601.zh.md) |
| `TC-A2-AUTH-B` effect-scale promotion | `G4 authority` | 尚未启动为 release-grade promotion；不得和当前批次混验收 | [authority backlog](authority_promotion_backlog.zh.md) |
| `TC-A2-AUTH-C` component_failure_probability promotion | `G4 authority` | Stage C test-local 演练存在，release-grade truth 仍 blocked | [authority backlog](authority_promotion_backlog.zh.md)、[RES-009/010/011/012](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) |
| `G5-R` Pk / fuze proxy | `G5 research` | 已完成 research packet；只形成 non-authoritative proxy source scan / boundary / event-chain / audit | [G5 research dispatch](g5_research_dispatch_20260602.zh.md)、[G5 integration acceptance](g5_research_integration_acceptance_20260602.zh.md) |
| `TC-A2-KILLCHAIN` Pk / deterministic fuze | `G5 authority` | boundary deferred | [authority backlog](authority_promotion_backlog.zh.md)、[RES-013/014](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) |

## 5. 当前 residual 状态如何读

`residual_register.zh.md` 是 residual 状态源，但它不是任务计划总表。

读取规则：

1. `closed_*_non_authoritative` 只关闭该 residual 的 candidate / internal / scoped 子范围；
2. `research_closed_*_authority_blocked_*` 表示当前 research profile 不再被阻塞，但全局 truth、Stage C 或 release-grade authority 仍未放行；
3. `research_closed_*_authority_fail_closed_*` 表示证据执行或保留有效，research profile 可走可替换估计，但 authority admit gate 仍失败，不能消费为 release evidence；
4. `research_out_of_scope_authority_boundary_deferred_*` 表示本批次 research scope 明确不覆盖，也不应作为当前批次未完成项反复分发；
5. 只要进入 `G4` authority promotion，就必须重新逐项声明哪些 residual 对该 promotion 仍阻塞。

## 6. 单一入口职责

后续维护时，各文件职责固定如下：

| 文件 | 职责 |
|---|---|
| `README.zh.md` | 活跃薄入口，只给当前口径、阅读路径和证据源 |
| `task_granularity_and_coordination_20260601.zh.md` | 本文件，定义粒度、当前批次和任务簇归并 |
| `runtime_status.zh.md` | `TC-A2-RUNTIME` / `G1` 工程状态、回归面和非目标 |
| `candidate_acceptance_status.zh.md` | 当前 `TC-A2-BF-001..004` / `G2` candidate 验收状态，并读取 `G3` residual |
| `g3_residual_closeout_status_20260601.zh.md` | `G3` 台账收尾记录；说明哪些 residual 窄域关闭、fail-closed、Stage C blocked 或 boundary deferred |
| `research_candidate_data_policy_20260601.zh.md` | 当前默认 research / candidate 数据策略；定义可替换数据、第三方/社区来源和 authority opt-in 边界 |
| `g4_g5_research_continuation_20260601.zh.md` | `G4/G5` 的研究级延续入口；允许启动 non-authoritative envelope / fragility / proxy 工作，不启动 authority promotion |
| `g4_research_dispatch_20260601.zh.md` | 当前 `G4 research` 中央分发包；串行整合 `G4-R-B` 与 `G4-R-C` 分发结果 |
| `g5_research_dispatch_20260602.zh.md` | 当前 `G5 research` 中央分发包；分发 Pk / fuze proxy source scan、boundary design、event-chain map 和 audit |
| `g5_research_integration_acceptance_20260602.zh.md` | `G5 research` 串行整合结论；确认 proxy packet accepted 且 guards false |
| `authority_promotion_backlog.zh.md` | 未来 `TC-A2-AUTH-B/C` 和 `TC-A2-KILLCHAIN`，只登记不混入当前验收 |
| `narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md` | 窄域 scope 和 authority boundary |
| `calibration/.../residual_register.zh.md` | residual 状态源 |
| `calibration/.../retained_artifacts/**/manifest.json` | retained artifact 机器证据 |
| `archive/20260601_doc_governance/**` | 历史叙事、审计快照和旧 review note，不作为任务分发入口 |

如果这些文件冲突，优先级为：

1. retained artifact manifest / gate JSON；
2. residual register；
3. task granularity 总账；
4. narrow-scope boundary；
5. runtime / candidate / backlog 活跃状态文件；
6. README 薄入口；
7. 旧的中间 review note。

## 7. 下一步建议

短期不要继续新增横向任务簇。当前已完成第一轮文档治理：

- `README.zh.md` 已降级为薄入口；
- `runtime_status.zh.md` 承接 `G1 runtime`；
- `candidate_acceptance_status.zh.md` 承接当前 `G2 candidate`，并读取 `G3 residual`；
- `authority_promotion_backlog.zh.md` 承接未来 `G4/G5 authority`；
- 旧长叙事、Phase 0 审计和历史状态审计已归档到 `archive/20260601_doc_governance/`。

下一轮治理不应先移动 calibration narrative。`damage_model.py candidate-artifacts package-bundle`、release-readiness
gate 和 source-admission audit 仍硬引用多份 calibration / update 文档；若要归档这些文件，
必须先改工具和测试引用，或保留 redirect stub。

任何新任务描述仍必须先标注粒度：`G1 runtime`、`G2 candidate`、`G3 residual`、
`G4 research`、`G5 research`、`G4 authority` 或 `G5 kill-chain`。
