# A2 Research Candidate Data Policy - 2026-06-01

状态：`2026-06-01 / research_profile_active / non-authoritative / authority_opt_in_only`。

本文记录 A2 当前的务实决策：默认目标保留为 research / candidate model，不追求工业级、
型号级或 release-grade 数据来源。底层数据必须可替换、可扩展、可追溯，并显式标注可信等级。

本文不创建 runtime descriptor，不授予 `effect_scale_authority`、
`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。
未来若要做 `G4/G5`，必须另启 authority 任务线。

## Decision

当前 A2 默认完成口径改为：

- 做出可运行、可审阅、可复现的 research-grade blast-fragmentation damage candidate；
- 允许公开、第三方、社区、开源配置和工程近似数据进入候选池；
- 所有底层数据都必须能被后续更好来源替换；
- 所有参数、row、benchmark 和 retained artifact 必须保留 provenance、source tier、
  uncertainty / confidence、scope 和 residual；
- 不把 research data 写成 calibrated stock authority。

这意味着 `G1 runtime`、`G2 candidate package` 和 `G3 residual accounting` 可以作为当前
research profile 的完成面。`G4/G5` 从默认后续目标降级为 explicit opt-in backlog。

## Data classes

| class | 可用作 | 必填标注 | 不可声称 |
|---|---|---|---|
| `tier_a_method_reference` | 公开公式、教材模型、论文方法、validation criteria | source ref、scope、适用假设、单位 | 型号级真值 |
| `tier_b_public_engineering_candidate` | 几何量级、武器/目标公开参数、工程近似范围 | 发布方、版本、rights、confidence、交叉验证 | 单独校准 authority |
| `tier_c_community_sanity_check` | 社区数据、开源仿真配置、民间数据库、论坛汇编的 sanity envelope | 社区/二手标签、合理性评估、冲突记录 | calibrated row 或 release evidence |
| `derived_research_estimate` | 多源融合后的研究级参数区间 | 输入 source ids、算法/脚本、uncertainty、替换策略 | 官方或工业级数据 |
| `hash_only_restricted_reference` | 有版权或再分发限制材料的定位、hash、审阅记录 | locator、hash、不得保留 raw content 的说明 | 复制原文、表格、图或 raw selected values |

## Replaceability rule

每个 research 数据项都应能被更好来源替换。最小字段：

- stable `source_id` 或 artifact id；
- `source_ref`、DOI、URL、ISBN、报告编号、代码 commit 或 retained hash；
- source tier 和 data class；
- rights / redistribution note；
- scope：target、weapon family、aspect、closure、miss-distance、mechanism、component；
- value type：point estimate、range、distribution、qualitative label 或 hash-only locator；
- uncertainty / confidence；
- cross-check notes；
- residual ids affected；
- replacement rule：什么条件下可以 supersede。

## RES interpretation under research profile

`RES-*` 不再被理解为“当前项目必须拿到工业级权威数据才能完成”。在当前
research / candidate profile 下，`RES-001..014` 已闭合为 `research_closed_authority_retained`：
没有 residual 继续阻塞当前研究级候选模型。它们现在分为两种：

| residual role | 含义 |
|---|---|
| research blocker | 阻塞当前 research model 的可运行、可解释、可替换数据面；当前为 none |
| authority blocker | 只阻塞未来 `G4/G5`；不阻塞当前 research profile |

当前 `RES-005/006` 对 authority 仍 fail-closed，但在 research profile 下已闭合为
hash-only / third-party / community / derived estimate 的非权威 mechanism-load envelope 路线。
当前 `RES-009..012` 对 release-grade component probability 仍 blocked，但在 research
profile 下已闭合为 Stage C candidate probability surface 和 uncertainty notes 路线。
`RES-013/014` 仍只属于未来 Pk / deterministic fuze 任务线。

## Rights boundary

个人、非商业或学术用途不自动清除版权或再分发限制。当前仓库的安全做法是：

- 不复制受版权保护来源的长段正文、表格、图片或 raw selected values；
- 记录 source ref、locator、hash、短摘要和派生参数；
- 对不能确认再分发权的输入使用 `hash_only_restricted_reference`；
- 在 source ledger 中说明引用源、处理方式和不能支持的结论；
- 公开仓库内只保留 research estimates、参数区间、脚本、manifest 和 hash。

## Acceptance

research profile 可视为完成时，需要：

- runtime 和 candidate package 仍通过当前 G1/G2/G3 守卫；
- source ledger 可区分 Tier A/B/C、derived estimate 和 hash-only restricted reference；
- 关键参数有 uncertainty / confidence 和 replacement rule；
- candidate bundle 输出仍为 non-authoritative；
- authority guards 全 false；
- 文档明确 G4/G5 为 opt-in，不是当前完成标准。

当前工作区复核：

- retained manifest integrity：`manifest_count=29`、`missing_total=0`、`sha_mismatch_total=0`、`guard_true_total=0`；
- source admission strict：`9 ledgers, 29 candidate docs, 51 calibration docs`；
- candidate bundle CLI：exit 0，仍保持 `candidate_non_authoritative` 和 authority guards 全 false；
- A2 candidate/source/manifest/descriptor suite：`17 passed`；
- fail-closed signoff / residual packet focused suite：`44 passed`。

## Next work

后续工作优先级：

1. 按 [G4/G5 research continuation](g4_g5_research_continuation_20260601.zh.md)
   启动 `G4-R-B` research mechanism-load envelope，而不是等待 release-grade signoff；
2. 启动 `G4-R-C` research component fragility surface 和 uncertainty ledger；
3. 评估 `G5-R` Pk / fuze proxy design，但保持 out-of-scope / non-authoritative；
4. 把公开/社区/第三方来源写入可替换 source ledger；
5. 只在用户明确要求时启动 `G4/G5 authority`。
