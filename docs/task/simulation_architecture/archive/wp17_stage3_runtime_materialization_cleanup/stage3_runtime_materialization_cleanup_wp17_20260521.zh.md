# WP17 Stage 3 Runtime Materialization And Cleanup

状态：`2026-05-21` complete / accepted selected-slice
runtime-materialization closure；full counterfactual/worldline orchestration
仍不在本阶段完成范围内。

语言版本：

- 英文主文：[stage3_runtime_materialization_cleanup_wp17_20260521.md](stage3_runtime_materialization_cleanup_wp17_20260521.md)
- 中文辅文：`stage3_runtime_materialization_cleanup_wp17_20260521.zh.md`

输入：

- [Stage 3 platform expansion mainline plan](../../review/stage3_platform_expansion_mainline_plan_20260521.md)
- [WP16 runtime spine consolidation](../wp16_runtime_spine_consolidation/runtime_spine_consolidation_wp16_20260521.zh.md)
- [WP16 验收审查](../../review/wp16_runtime_spine_consolidation_acceptance_review_20260521.zh.md)
- [WP17 验收审查](../../review/wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.zh.md)

## 1. 目标

`WP16` 已经验收 selected runtime-spine slice。`WP17` 是 Stage 3 的最后一组重构任务：把剩余契约面转成 runtime 行为，并清理仍然让业务路径依赖旧入口的地方。

这不是新的纯文档阶段。每个子阶段都必须迁移一个维护中 consumer、物化一个 runtime path、收紧一个 legacy boundary，或者诚实记录 blocked residual。

## 2. 当前代码事实

| 方向 | 当前事实 | 对计划的影响 |
|------|----------|--------------|
| Runtime capabilities | `RuntimeFacade::capabilities()` 已经返回保守 baseline/candidate metadata。 | 现在缺口不是“空 capabilities”，而是 profile request/admission 与 provider dispatch。 |
| Model providers | 仍没有 `ModelProvider` 调度抽象，也没有 stage node 按 fidelity profile 选择 provider。 | 先做一个 provider family 和一个 stage-node slice。 |
| Capability composition | `CapabilityBundle`、bindings 与 `DefaultUnitFactory` 内部 bundle/resolved-plan helper 已存在；public `spawn_platform` 仍被刻意禁止。 | 先晋级内部 resolution chain，不直接替换 public setup schema。 |
| Counterfactual runtime | replay/branch/request gate 对 full restore 仍保持 metadata/fail-closed；`RuntimeFacade::run_counterfactual_branch()` 已支持 explicit setup baseline 的 selected-entity branch/compare。 | 可以引用 selected-slice facade runtime 证据，但仍不能声明 arbitrary live-world clone、full restore 或 full worldline orchestration。 |
| Multi-rate scheduler | `ActionHoldPolicy` 是 DTO；`kWp10ClockDomainAdvisoryOnly = true` 仍为真。 | 先让架构 §8 的 10Hz/20Hz/60Hz 示例跑起来。 |
| Training/batch business path | `RuntimeFacadeAdapter` 已有 facade-shaped 方法，但 `batch_runtime` 仍是 compatibility view，部分测试/调用仍读它。 | 第一批 cleanup 应迁移 maintained reads，保留兼容测试。 |

## 3. 子阶段

| 子阶段 | 状态 | 核心目标 |
|--------|------|----------|
| `WP17-A Fact Ledger And Boundary Freeze` | recovered / pass | 锁定当前代码事实、residual 与非目标。 |
| `WP17-B Facade Business Migration And Compatibility Cleanup` | implemented / focused pass | 维护中的 batch/training read 暴露 facade-shaped adapter/env 方法，`batch_runtime` 保持 compatibility-only。 |
| `WP17-C Multi-Rate Runtime Example` | implemented / focused pass | §8 selected policy/control/physics cadence 已有 hold/expiry/barrier runtime evidence。 |
| `WP17-D Fidelity Provider Runtime` | implemented / focused pass | facade-owned request/admission/provider selection 接受 reference CPU baseline，并对未维护 provider fail closed。 |
| `WP17-E Capability Spawn Runtime Promotion` | implemented / focused pass | capability resolution 已进入 maintained spawn materialization，同时保留 type-name 兼容。 |
| `WP17-F Counterfactual Runtime Slice And Closure` | narrowed selected-slice implemented / focused pass | explicit baseline setup 可产生 parent/branch snapshot 与 selected entity causal deltas。 |

## 4. 派发规则

- `WP17-A` 是轻量事实锁定任务：mini model，xhigh。
- `WP17-B` 是中等集成重构：`gpt-5.4`，high。
- `WP17-C` 是复杂 scheduler seam：`gpt-5.4`，xhigh。
- `WP17-D` 是复杂 backend/fidelity seam：`gpt-5.4`，high 或 xhigh。
- `WP17-E` 是复杂 spawn/content seam：`gpt-5.4`，high。
- `WP17-F` 是复杂 replay/runtime seam：`gpt-5.4`，xhigh；当前已释放并完成
  explicit-setup selected-entity branch/compare 窄切片，不代表 full worldline。

## 5. 非目标

- 第一批 cleanup 不删除 `WorldBatchRuntime` 或 `RuntimeFacade.runtime()`。
- 不做 global scheduler rewrite。
- 不直接晋级 exact GPU、resident-state 或 adaptive multi-fidelity。
- 不在 compatibility/content 证据前强推 public `spawn_platform` schema。
- 不声明 full counterfactual orchestration。
- 不声明 arbitrary live-world reflection/clone 可作为 counterfactual branch baseline。
