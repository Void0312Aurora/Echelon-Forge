# Ground Bootstrap 计划验收

状态：`2026-06-05` 已接受并归档
`ground_domain_bootstrap_plan_20260521`。

## 已接受范围

本次接受的是 bootstrap planning lane，不接受 route movement 或完整 ground runtime
behavior。该计划的成功标准已经满足，因为当前 ground 记录已经能稳定回答：

- 第三域位置：`services/army` 保持 service-profile 边界，`ground/` 是执行特化线；
- 第一批 maintained scope：G0/G1 tasking、static status、static command
  metadata 与 native schema identity；
- 必须一起补的横向面：standards、task profile dispatch、content seed、
  contracts、scenario smoke fixtures、native schema evidence、owner-slice DTO、
  Python bindings，以及没有新增 private ground runtime path 的证据；
- 必须延后的边界：route movement、terrain、sensing、fires、damage、combat、
  observation export 与完整 ground runtime behavior；
- G1 前必须坚持的 G0 承诺：命名、别名、platoon-centered starter scope、第一任务族、
  capability-composition 方向、cadence 假设与 information-state 边界。

## 证据

- [Ground 当前进展](../ground_current_progress_20260524.zh.md) 记录已接受的
  G0-G6-E 状态，以及 `2026-06-05` static command-authoring 更新。
- [Ground dispatch queue](../ground_subagent_dispatch_queue_20260521.zh.md) 记录
  G0-G6-E 已接受包，并继续将 route movement 保留到后续 release vote。
- progress tracker 记录的聚焦验证包括 `ef_py` build、domain-shell guard tests、
  mission-command round-trip、native ground schema tests、ground scenario tests、
  profile semantics 与 lifecycle bridge tests。
- `2026-06-05` 收口验证：

```bash
cmake --build build-workshop --target ef_py -j2
# [100%] Built target ef_py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/command_tasking/test_dto_domain_shell_guard.py tests/runtime/mission/test_mission_command_ground_fields_roundtrip.py tests/runtime/ground/test_ground_native_platform_schema.py tests/runtime/ground/test_ground_mvp_scenario.py tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py tests/leader/test_tasking_profile_contracts.py tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
# 40 passed

git diff --check
# clean
```

## 残余

- `G2 route move implementation` 仍保持 held，直到后续 G6-D3/G6-F
  route-move release vote 消费已接受的 G6-E2/E3 native schema evidence，并命名
  movement evidence gates。
- 本次验收不释放 terrain-aware movement、sensing、fires、damage、combat、
  observation export、learned ground policy、ground action space、reward、
  curriculum 或 evaluation suite。

## 索引同步

- bootstrap plan 已移入
  [ground_domain_bootstrap_plan_20260521.zh.md](ground_domain_bootstrap_plan_20260521.zh.md)。
- `docs/task/ground/` 下不保留 active-path 副本。
- ground 父级 README 与 progress tracker 已指向 archived accepted baseline。
- 新工作必须另开 fresh follow-on package，不在 archived bootstrap plan 内继续追加。
