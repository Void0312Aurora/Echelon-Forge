# WP14-F Compatibility Validation And Acceptance Handoff

状态：`2026-05-21` planned / serial closure lane。此时不要创建 acceptance
review；WP14 first slice 仍 open/planned。

语言版本：

- 英文主文：[wp14_compatibility_validation_acceptance_cluster_20260521.md](wp14_compatibility_validation_acceptance_cluster_20260521.md)
- 中文辅文：`wp14_compatibility_validation_acceptance_cluster_20260521.zh.md`

输入：

- [WP14 capability composition](capability_composition_wp14_20260521.zh.md)
- [WP14-A capability bundle contract](wp14_capability_bundle_contract_cluster_20260521.zh.md)
- [WP14-B content definition lowering](wp14_content_definition_lowering_cluster_20260521.zh.md)
- [WP14-C spawn resolution bridge](wp14_spawn_resolution_bridge_cluster_20260521.zh.md)
- [WP14-D additive facade setup DTO](wp14_additive_facade_setup_dto_cluster_20260521.zh.md)
- [WP14-E capability effects materialization](wp14_capability_effects_materialization_cluster_20260521.zh.md)
- [Post-WP9 architecture route plan](../post_wp9_architecture_route_plan_20260520.zh.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.zh.md)

## 1. 目的

`WP14-F` 是串行 compatibility 与 acceptance handoff lane。它整合 A-E，验证
`type_name` compatibility 是否在 capability composition 后仍成立，记录 validation
outcomes，发布 residuals，并准备 acceptance review。

它不应阻塞 A-E 达到 `Mergeable`，而是在 implementation evidence 已存在后运行。

并行规则：

- 这个 lane 是串行的，只能由主线程负责。
- 不要让 subagents 在同一规范性表格上与 A-E 实现 worker 同时写 acceptance text。

## 2. 范围

范围内：

- 验证 A-E touched files、commands、blockers 与 residuals；
- 执行或记录最终 validation commands；
- 证明 `spawn_unit(type_name)`、`WorldSpawnRequest` 与 facade setup 的兼容性；
- 更新 simulation architecture README/index entries；
- 只有在 implementation evidence 支撑时，才把 post-WP9 route status 从 Phase 5
  opened 更新为 accepted；
- gates 通过后发布英文和中文 acceptance review；
- 确保最终 commit messages 使用 capability/result language，避免 internal WP labels。

范围外：

- 隐藏 failed 或 blocked validation；
- 把 documentation-only output 当作 implementation closure；
- 声称 full spawn-platform migration、backend/fidelity promotion、scenario schema
  replacement 或新战术行为。

## 3. 验收包清单

最终 handoff 必须包含：

| Item | Required content |
|------|------------------|
| Gate verdict table | A-E pass/fail/blocked 与一行证据。 |
| Validation commands | 精确 command、status 与短 outcome。 |
| Compatibility statement | 明确说明 `spawn_unit(type_name)` 与 `WorldSpawnRequest.type_name` 仍为 maintained compatibility surfaces。 |
| Runtime surface summary | 新 contracts、lowering helpers、bridge points、DTOs 与 evidence fields。 |
| Residual register | 具名 residuals，含 owner、reason 与 next-phase recommendation。 |
| Index sync | README、route plan、review index 与 bilingual companions 已检查。 |
| Commit-message note | 最终建议 commit title 避免 internal work-package labels。 |

## 4. 验证命令

预期最终 validation set：

```powershell
git diff --check
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp14_*.py
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup or capabilities or observation_packet"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\test_gpu_runtime_bindings.py -k "runtime_capabilities"
python tools\maintenance\wp_doc_closure_audit.py --wp WP14
```

此 lane 的最低 acceptance gates：

- A-E implementation gates 已经 mergeable；
- `git diff --check` 与上面的 validation commands 都有精确 outcome；
- README、route 与 review indices 已同步；
- `spawn_unit(type_name)` 与 `WorldSpawnRequest.type_name` 的 compatibility 被明确写出；
- 在 A-E 真正 mergeable 前不写 acceptance review。

若命令被环境阻塞，应记录 blocker 和最窄替代证据。不得在未运行测试且无理由时标记 gate
accepted。

## 5. Review 草稿要求

仅在 gates 通过后创建：

- `docs/task/review/wp14_capability_composition_acceptance_review_20260521.md`
- `docs/task/review/wp14_capability_composition_acceptance_review_20260521.zh.md`

review 必须说明：

- accepted scope 与 non-scope；
- A-E gate verdicts；
- validation outcomes；
- 哪些 compatibility guarantees 仍然 maintained；
- future public `spawn_platform`、scenario schema migration、deeper capability effects
  与 full platform-family expansion 的 residuals；
- 推荐下一阶段：只有 capability composition gates 通过后才进入 counterfactual and
  experiment generation。

## 6. 交接契约

返回：

- A-F final status；
- integration/closure touched files；
- 精确 commands 与 outcomes；
- 若已创建，提供 acceptance review links；
- residuals 与 recommended next action；
- 不含 `WP14` 的 capability/result-oriented commit message 建议。
