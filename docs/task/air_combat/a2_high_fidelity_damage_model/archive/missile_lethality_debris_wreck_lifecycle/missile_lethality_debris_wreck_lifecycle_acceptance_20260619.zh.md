# MLF-8 残骸和碎片生命周期 — 验收记录

状态：`2026-06-19` diagnostics-only MLF-8 lifecycle 切片 accepted / archived。
P0 边界、P1 盘点、P2 生命周期契约、P3 runtime 表达、P4 诊断/facade 暴露、
P5 聚焦验证、P6 broader smoke 和 P7 归档同步均已完成。

英文规范页：
[missile_lethality_debris_wreck_lifecycle_acceptance_20260619.md](missile_lethality_debris_wreck_lifecycle_acceptance_20260619.md)。

## 验收范围

本记录只验收有边界的 MLF-8 切片：在维护中的 engagement event stream 里记录
脱落结构部件和终端残骸的生命周期事实。它不创建一等碎片/残骸实体，不实现碎片物理，
不释放 reward 权威、校准杀伤权威或 Pk。

`[x]` = 已满足。`[~]` = 有意保留在 MLF-8 之外。

## MLF-8A：边界与索引

- [x] README、任务簇、当前状态、派发队列、盘点、生命周期契约、archive 占位和父级导航存在。
- [x] A2 父 README 和 archive registry 将 MLF-8 路由为 accepted archived
  diagnostics-only lifecycle evidence packet。
- [x] air-combat README 通过本地 A2 archive registry 读取 MLF-8，而不是 active planning path。
- [x] 禁止声明继续列出并保持拒绝。

## MLF-8B：生命周期契约

- [x] 基础 carrier 是 `LifecycleTransitionEvent`。
- [x] 脱落部件生命周期行是 diagnostics-only，并与上游结构事件链路关联。
- [x] 终端残骸生命周期行是 diagnostics-only，且要求存在链路关联的导弹结构/后果证据。
- [x] 普通非导弹地面坠毁仍不属于 MLF-8 权威。
- [x] accepted base slice 内 `wreck_entity` 保持为零。

## MLF-8C：Runtime 表达

- [x] engagement event recorder/store 可以记录和排序 lifecycle transition 行。
- [x] 结构断裂为每个 accepted structural event 写入一个有边界 detached-part lifecycle 行，
  包括 multi-axis aggregate 情形。
- [x] terminal wreck helper 仅在存在链路关联的上游 structural/consequence 证据时写行。
- [x] 后续 tick 不会重复发出已写入的 lifecycle 行。
- [x] 不创建一等 debris 或 wreck ECS 实体。

## MLF-8D：诊断与 Facade

- [x] Facade packet 会把 lifecycle 行追加并排序到 recent engagement evidence 中。
- [x] Python binding 和 contract tests 覆盖 lifecycle transition 字段。
- [x] Diagnostics probe rows 和 snapshot 暴露 lifecycle 行与摘要。
- [x] Diagnostic schema version 已随 lifecycle projection 更新。

## MLF-8E：Reward 与可见性边界

- [x] 已验收 MLF-8 lifecycle 行均为 diagnostics-only visibility。
- [x] Reward 忽略 diagnostics-only lifecycle 行，不创建新的 MLF-8 reward term。
- [x] 现有 terminal/reward 行为不会被 diagnostics-only lifecycle evidence 抵消。

## MLF-8F：验证证据

- [x] C++ structural lanes 覆盖 no-breakup、单脱落部件、multi-axis detached lifecycle、
  terminal wreck helper、真实 GroundContact-before-StructuralFailure 同 tick
  impact/breakup 顺序和无重复行。
- [x] Python runtime lanes 覆盖 facade、binding、engagement contract、diagnostics probe、
  continuous-rod integration 和 reward non-leakage。
- [x] MLF-8 分支修正 fuze expectation 后，geometry/edge-case smoke 仍然为绿。
- [x] 归档前 full CTest 与 broad air-combat/engagement pytest smoke 均已通过。

## MLF-8G：命令证据

- [x] `ctest --test-dir build-workshop --output-on-failure` -> 6 passed。
- [x] `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_geometry_and_edge_cases.py::GeometryAndEdgeCaseTests::test_live_controlled_geometry_varies_aspect_and_altitude_offset -vv`
  -> 1 passed。
- [x] `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_geometry_and_edge_cases.py`
  -> 11 passed。
- [x] `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat tests/runtime/engagement`
  -> 386 passed。
- [x] touched MLF-8/A2/air-combat docs 本地 Markdown 链接检查通过。
- [x] `git diff --check` 通过。

## MLF-8H：验收与归档

- [x] 当前状态已总结实现证据和残余。
- [x] 任务簇和派发队列已标记 P7 complete。
- [x] A2 父 README、A2 archive README、A2 archive registry 和 air-combat README 状态同步。
- [x] 物理归档已移动到 A2 本地 archive 下。
- [x] 原 active 路径只保留轻量指针。
- [x] MLF-9/MLF-10 residual 仍保持具名。

## 禁止声明

- [x] 没有真实世界 Pk 或统计杀伤趋势权威。
- [x] 没有校准碎片抛散、碎片射程、人员杀伤概率或 selected TP-21 output 权威。
- [x] 没有武器或飞机专用碎片校准。
- [x] accepted base slice 内没有一等 debris/wreck ECS entity model。
- [x] 没有碎片对其他目标的二次损伤交互。
- [x] MLF-8 diagnostics 不产生训练 reward 权威。
- [x] 没有海军、地面、可视化粒子或更广泛世界碎片生命周期权威。
