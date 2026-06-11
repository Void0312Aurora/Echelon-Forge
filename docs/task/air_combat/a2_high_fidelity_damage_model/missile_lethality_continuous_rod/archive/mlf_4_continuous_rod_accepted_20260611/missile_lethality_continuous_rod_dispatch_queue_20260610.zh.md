# A2 MLF-4 派发队列

状态：`2026-06-11` dispatch queue。`MLF-4A-X1`、`MLF-4B-W1-R2`、`MLF-4C-W1`、`MLF-4D-W1` 与 `MLF-4E-W1` 已验收；`MLF-4F-C1` 可进入收口/归档准备。

英文辅文：[missile_lethality_continuous_rod_dispatch_queue_20260610.md](missile_lethality_continuous_rod_dispatch_queue_20260610.md)

父任务簇：[missile_lethality_continuous_rod_task_clusters_20260610.zh.md](missile_lethality_continuous_rod_task_clusters_20260610.zh.md)

## 队列

| Packet | Cluster | Suggested owner | Write set | Goal | Status |
| --- | --- | --- | --- | --- | --- |
| `MLF-4A-X1` | `MLF-4A Boundary And Inventory` | read-only worker | 仅 docs inventory packet | 盘点 rod 字段、continuous_rod 分支、历史测试和缺口。 | accepted |
| `MLF-4B-W1` | `MLF-4B Standard Rod Event Surface` | current-session worker | event contracts/export/store/tests | 稳定标准 rod/cut 事实。 | accepted via R2 |
| `MLF-4C-W1` | `MLF-4C Generic Rod Geometry` | current-session worker | default effects rod geometry/tests | 验证通用切割带/方向行为。 | accepted |
| `MLF-4D-W1` | `MLF-4D Component Cut Projection` | current-session worker `019eb268-2e2d-7bf2-bb1b-3fb048a192ee` / Carver | spatial/component projection/tests | 将 rod 切割曝光投影到部件。 | accepted |
| `MLF-4E-W1` | `MLF-4E Diagnostics And Gates` | main thread | diagnostics + guard tests | 解释 rod/cut 事实并阻止虚假 rod 行。 | accepted |
| `MLF-4F-C1` | `MLF-4F Acceptance And Archive Prep` | main thread | docs/index/archive | 汇总 accepted/held 状态和残余。 | ready |

## 最近派发

| Packet | Worker | Model / reasoning | Started | Expected packet |
| --- | --- | --- | --- | --- |
| `MLF-4A-X1` | 当前会话内受控 explorer `019eb210-9e5e-7b80-bc77-335b98d5796c`，后由主线程异常恢复复核 | `gpt-5.4-mini` / `xhigh` | `2026-06-10` | [accepted inventory packet](missile_lethality_continuous_rod_inventory_20260610.zh.md)。 |
| `MLF-4B-W1` | 当前会话内受控 worker `019eb24d-db2b-7161-be3f-b02566339d3d` / Goodall | inherited model / `high` | `2026-06-11` | failed / closed before packet：尝试大范围越界 `src/` formatting 改动；主线程已丢弃这些改动。 |
| `MLF-4B-W1-R2` | 当前会话内受控 worker `019eb255-383b-7851-a721-e33bdfbda459` / Kepler | inherited model / `high` | `2026-06-11` | returned pass；主线程本地复验后验收。新增 [test_continuous_rod_event_surface.py](../../../../../tests/runtime/air_combat/test_continuous_rod_event_surface.py)。 |
| `MLF-4C-W1` | 当前会话内受控 worker `019eb268-2e2d-7bf2-bb1b-3fb048a192ee` / Carver | inherited model / `high` | `2026-06-11` | returned pass；主线程本地复验后验收。新增 [test_continuous_rod_geometry_response.py](../../../../../tests/runtime/air_combat/test_continuous_rod_geometry_response.py)。 |
| `MLF-4D-W1` | 当前会话内受控 worker `019eb268-2e2d-7bf2-bb1b-3fb048a192ee` / Carver | inherited model / `high` | `2026-06-11` | returned pass；主线程本地复验后验收。新增 [test_continuous_rod_component_cut_projection.py](../../../../../tests/runtime/air_combat/test_continuous_rod_component_cut_projection.py)。 |
| `MLF-4E-W1` | 主线程本地实现与复验 | n/a | `2026-06-11` | accepted。新增 [test_continuous_rod_diagnostic_projection.py](../../../../../tests/runtime/air_combat/test_continuous_rod_diagnostic_projection.py)，并更新诊断 probe 的 rod/cut 快照与未起爆 fallback gate。 |

## 派发说明

- `MLF-4E-W1` 已 accepted；下一步从 `MLF-4F-C1` acceptance/archive prep 开始。
- 事件面决定被验收前，不并行派发 4C/4D。
- MLF-4 仍处于 planning 时，不进入 MLF-5 部件失效或 MLF-6 结构解体。
- 返回包必须保持通用 research 数据规则，并说明触及的默认常量。

## Worker Packet 清单

- status
- touched files
- commands/outcomes
- remaining paths
- behavior risks
- integration notes
- 未起爆/非 rod gate 状态
- 已避免的禁止声明
