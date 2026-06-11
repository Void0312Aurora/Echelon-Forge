# A2 MLF-4 连续杆切割机制验收

状态：`2026-06-11` accepted / archived。

英文辅文：[missile_lethality_continuous_rod_acceptance_20260611.md](missile_lethality_continuous_rod_acceptance_20260611.md)

## 验收结论

MLF-4 可以按“连续杆/切割曝光事实链”验收。它完成了从起爆后机制事实到切割曝光诊断的闭合：

- `continuous_rod` 起爆能产生同一链路下的正 rod/cut 事实。
- 非连续杆战斗部不会产生正 rod/cut 事实。
- 未起爆路径不会被诊断补出虚假的战斗部、空间覆盖或部件切割行。
- 切割事实会随距离、侧向/方位、方向轴和部件投影变化。
- 部件受载行能暴露切割曝光，但不声明部件失效、机体解体、坠毁或实体删除。
- 诊断快照能携带战斗部层和部件层的 `rod_cut_margin`，方便后续阶段消费。

## 已验收证据

- 盘点证据：[missile_lethality_continuous_rod_inventory_20260610.zh.md](missile_lethality_continuous_rod_inventory_20260610.zh.md)
- 当前状态：[missile_lethality_continuous_rod_current_status_20260610.zh.md](missile_lethality_continuous_rod_current_status_20260610.zh.md)
- 派发记录：[missile_lethality_continuous_rod_dispatch_queue_20260610.zh.md](missile_lethality_continuous_rod_dispatch_queue_20260610.zh.md)
- 任务簇边界：[missile_lethality_continuous_rod_task_clusters_20260610.zh.md](missile_lethality_continuous_rod_task_clusters_20260610.zh.md)
- 主 README 证据包：[README.zh.md](README.zh.md)

## 测试证据

- [test_continuous_rod_event_surface.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_event_surface.py)：标准 rod/cut 事件面。
- [test_continuous_rod_geometry_response.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_geometry_response.py)：距离、侧向/方位和方向轴响应。
- [test_continuous_rod_component_cut_projection.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_component_cut_projection.py)：部件切割曝光投影。
- [test_continuous_rod_diagnostic_projection.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_diagnostic_projection.py)：诊断解释、非连续杆零切割、未起爆不合成虚假 rod 行。
- [test_diagnostics_probe_contracts.py](../../../../../../../tests/runtime/air_combat/test_diagnostics_probe_contracts.py)：诊断字段合同回归。

本轮收口复验命令：

```bash
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_continuous_rod_diagnostic_projection.py tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat -q -k "mlf4 or continuous_rod or rod_cut"
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_continuous_rod tools/diagnostics/air_combat_weapon_employment_process_probe.py tests/runtime/air_combat/test_continuous_rod_diagnostic_projection.py
```

## 明确未验收

- 不验收部件失效概率。后续应进入 MLF-5。
- 不验收结构解体、机体被切断或空中碎裂。后续应进入 MLF-6。
- 不验收残骸/wreck 对象生命周期。后续应进入 MLF-8。
- 不验收 Pk 或统计杀伤概率。后续应进入 MLF-9。
- 不验收真实 AIM-120C/MQ-9 或任何具体弹种/目标组合的杀伤结论。

## 后续入口

MLF-4 已关闭，不再派发。后续若要让“切割曝光”产生实际损伤，应按 `docs/agent` 标准新建 MLF-5，
让部件失效模型消费本包输出的 rod/cut 事实，而不是在 MLF-4 内继续追加规则。
