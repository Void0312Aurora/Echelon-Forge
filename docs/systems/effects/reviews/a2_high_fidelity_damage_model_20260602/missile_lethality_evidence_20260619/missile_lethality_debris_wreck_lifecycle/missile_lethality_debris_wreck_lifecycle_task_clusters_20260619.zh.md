# MLF-8 残骸和碎片生命周期任务簇

状态：`2026-06-19` accepted / archived，用于 [README.zh.md](README.zh.md)
的有限任务簇记录。MLF-8 所有任务簇均已按有边界 diagnostics-only lifecycle
切片完成。

父子项目链接：

- 英文规范页：[missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.md](missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.md)
- 中文辅文：`missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.zh.md`

## 边界决策

MLF-8 可以为终端残骸和脱落部件添加有边界生命周期表达。它不得添加 Pk 权威、
校准碎片抛散、weapon-specific lethality 或默认 reward 权威。第一版实现输出应保持
diagnostics-only，除非后续已验收契约明确改变该 visibility。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-8-P0` | main thread | n/a | 创建子项目入口、状态、契约表面、派发队列、archive 占位和父级导航。 | `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_debris_wreck_lifecycle/**`；父 A2 和 air-combat README | runtime 修改、测试、reward 修改 | Markdown link、`git diff --check` | 子项目可导航且范围受限 | first, serial | 1 | complete / link-pass |
| `MLF-8-P1` | read-only diagnostics worker | n/a | 盘点结构断裂输出、生命周期字段、实体 active 语义、event store、facade、bindings、diagnostics 和 reward consumers。 | 本子项目 inventory/status docs | code change、authority change | 引用源码/测试盘点；本地链接检查 | inventory 命名可复用字段和缺口 | P0 后；只读阶段可与 P2 草案审阅并行 | 1 | complete / inventory-pass |
| `MLF-8-P2` | contract worker | n/a | 定义原机体、残骸事实、脱落部件碎片事实和未来可选碎片实体的生命周期契约。 | contract/status docs | runtime edit、selected TP-21 output authority、Pk | 契约表检查；与 MLF-7 residual 一致 | 契约说明 producer、consumer、visibility 和验收门 | P1 后 | 1 | complete / contract-pass |
| `MLF-8-P3` | integration worker | n/a | 按已验收契约实现有边界生命周期状态/事件写入。 | `src/components/**`、`src/systems/**`、`src/core/engine/**`、聚焦 C++ 测试 | 碎片物理抛散、可视化粒子、reward shaping | `cmake --build build-workshop --target ef_test -j 2`；聚焦 CTest | runtime 只发出已验收生命周期事实并保持 active-state 语义 | P2 后，串行 | 2 | complete / focused-pass |
| `MLF-8-P4` | diagnostics/facade worker | n/a | 通过 bindings、facade packet 和 diagnostics probe 暴露 lifecycle facts。 | `src/interfaces/**`、`src/runtime/facade/**`、`tools/diagnostics/**`、tests | reward authority、Pk、calibration claim | 聚焦 Python 和 facade/binding tests | MLF-8 lifecycle 行可检查且链路关联 | P3 后 | 2 | complete / focused-pass |
| `MLF-8-P5` | validation worker | n/a | 覆盖 no-breakup、单脱落部件、多部件断裂、终端残骸和 diagnostics-only reward non-leakage。 | `src/tests/**`、`tests/runtime/**`、status docs | 新模型范围、宽泛重构 | focused CTest、targeted pytest lanes | 测试证明已验收生命周期行为和零误报 | P3/P4 后 | 2 | complete / focused-pass |
| `MLF-8-P6` | main thread | n/a | 运行更广 smoke 并更新证据。 | status/acceptance docs | scope expansion | `ctest --test-dir build-workshop --output-on-failure`；targeted air-combat pytest | 回归 smoke 全绿或 residual 明确保留 | P5 后，串行 | 1 | complete / smoke-pass |
| `MLF-8-P7` | main thread | n/a | 验收或保留 MLF-8，同步父级导航，并在 accepted 后归档。 | README/status/acceptance/archive files；parent indexes | runtime edits | docs link check、`git diff --check` | 验收说明精确声明和后置项 | P6 后，串行 | 1 | complete / archived |

## 派发规则

- 每个 worker packet 必须精确对应上表一个 cluster。
- 除主线程明确要求修断链或上游事实 bug 外，不得修改已归档 MLF-1 到 MLF-8 包。
- 不允许两个 worker 同时编辑同一规范表、生命周期契约、event binding 或 status line。
- runtime 实现必须遵循已接受的 P2 lifecycle contract。
- P2 必须先解决 lifecycle event 的 reward filtering 缺口，P3 才能发出
  diagnostics-only lifecycle 行。
- 验收和 archive 修改保留给主线程串行处理。
- 若 cluster 超过 round cap，必须先停下重新划分范围，不能继续叠加修复 wave。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 验证计划

```bash
git diff --check
cmake --build build-workshop --target ef_test -j 2
ctest --test-dir build-workshop --output-on-failure
PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/runtime/engagement/
```

实现簇内使用更窄命令；只有 P6 或高影响范围修改才跑更广 smoke。

## 验收标准

- 生命周期输出与结构/后果证据链路关联。
- 终端原实体退役和残骸/碎片事实不混淆。
- diagnostics-only lifecycle facts 不进入 reward shaping。
- 不引入 Pk、selected debris-output、真实碎片抛散或 weapon-specific authority。
- 父级导航和 residual map 保持最新。

## 残余地图

| Residual | Destination | Notes |
| --- | --- | --- |
| Pk / 统计趋势投影 | MLF-9 | 需要独立趋势契约和验证数据。 |
| 校准碎片抛散或真实碎片损伤 | MLF-10 或后续证据门 | 现有 debris 证据在 selected outputs 被准入前保持 fail-closed。 |
| 碎片对其他目标的二次损伤 | 基础生命周期验收后的未来 MLF-8 扩展 | 不得并入 P3 基础表达。 |
| 可视化碎片渲染 | 未来 visual/runtime task | 不属于杀伤权威。 |
