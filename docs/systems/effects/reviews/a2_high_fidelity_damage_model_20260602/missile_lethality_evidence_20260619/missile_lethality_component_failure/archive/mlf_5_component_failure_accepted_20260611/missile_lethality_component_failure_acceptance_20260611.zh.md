# A2 MLF-5 目标部件脆弱性与失效验收

状态：`2026-06-11` accepted / archived。

英文辅文：[missile_lethality_component_failure_acceptance_20260611.md](missile_lethality_component_failure_acceptance_20260611.md)

## 验收结论

MLF-5 可以按“目标部件脆弱性与失效事实链”验收。它完成了从起爆后的部件受载/切割曝光到部件损伤事实的闭合：

- 同一链路下的部件受载或切割曝光可以产生标准部件损伤事实。
- 部件损伤事实包含部件名、系统、冗余组、失效概率、随机样本、失效模式、严重度和完整度前后值。
- 正概率不等于已经失效；只有样本触发并写入状态后，才导出部件损伤事件。
- 未起爆、无部件载荷、无正载荷或未触发样本不会被补成虚假的部件失效。
- 部件状态变化写入已有损伤状态，由已有飞行动力学、推进、传感器和系统模型继续传播后果。
- 诊断链路能解释部件损伤，但不把部件损伤提升为坠毁、结构解体、残骸、Pk 或训练胜负。

## 已验收证据

- 主证据包：[README.zh.md](README.zh.md)
- 只读盘点：[missile_lethality_component_failure_inventory_20260611.zh.md](missile_lethality_component_failure_inventory_20260611.zh.md)
- 当前状态：[missile_lethality_component_failure_current_status_20260611.zh.md](missile_lethality_component_failure_current_status_20260611.zh.md)
- 任务簇边界：[missile_lethality_component_failure_task_clusters_20260611.zh.md](missile_lethality_component_failure_task_clusters_20260611.zh.md)
- 派发记录：[missile_lethality_component_failure_dispatch_queue_20260611.zh.md](missile_lethality_component_failure_dispatch_queue_20260611.zh.md)
- 扩大方位/距离矩阵：[missile_lethality_component_failure_expanded_matrix_20260611.zh.md](missile_lethality_component_failure_expanded_matrix_20260611.zh.md)

## 测试证据

- `test_component_damage_event_surface.py`：标准部件损伤事件面、样本触发 gate、完整度前后值和 Python 绑定。
- [test_component_failure_probability_surface.py](../../../../../../../../tests/runtime/air_combat/test_component_failure_probability_surface.py)：通用失效概率随载荷、切割曝光、近炸破片/爆压、冗余、已有损伤和授权证据行变化。
- `test_warhead_spatial_component_projection.py`：上游战斗部/空间/部件受载事实投影。
- [test_live_detonation_event_surface.py](../../../../../../../../tests/runtime/air_combat/test_live_detonation_event_surface.py)：live 起爆事件面回归。
- `test_diagnostics_probe_contracts.py`：诊断链路 schema v2、`component_damage` 阶段、标准事件优先和未触发样本保护。

本轮收口复验命令：

```bash
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py tests/runtime/air_combat/test_component_damage_event_surface.py tests/runtime/air_combat/test_component_failure_probability_surface.py tests/runtime/air_combat/test_warhead_spatial_component_projection.py tests/runtime/air_combat/test_live_detonation_event_surface.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat -q -k "component_damage or vulnerability or component_failure"
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.md docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.zh.md docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_continuous_rod/README.md docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_continuous_rod/README.zh.md tools/diagnostics/air_combat_weapon_employment_process_probe.py tests/runtime/air_combat/test_diagnostics_probe_contracts.py
```

清理绑定默认值、重标定通用近炸概率并修复调试命中抽样种子后的最新记录结果：诊断 `26 passed`；组合回归 `42 passed`；宽筛选 `41 passed, 282 deselected, 7 subtests passed`。补充距离/方位探测确认 35 m 配置下爆破/破片约 15.75 m 后退出投影，连续杆约 11 m 后退出投影；良好侧向暴露时连续杆 y=6 m 理论概率为 `0.347818`，256 种子实际任意部件触发率为 `0.527344`，y=12 m 边缘触发率降到 `0.015625`，y=16 m 无投影。扩大矩阵还覆盖鼻向、尾向、上下方和斜向，确认不同方位存在明显差异。先前的 nanobind 退出泄漏提示已定位到绑定/测试 helper 的默认对象；收集阶段和实际运行阶段的收口复测均不再出现该提示。

## 明确未验收

- 不验收结构解体、机体断裂或空中碎裂。后续应进入 MLF-6。
- 不验收残骸/wreck 或碎片对象生命周期。后续应进入 MLF-8。
- 不验收 Pk、训练胜负、实体删除或任务周期结束规则。
- 不验收真实 AIM-120C/MQ-9 或任何具体弹种/目标组合的杀伤结论。
- 不写“某个部件坏了就直接坠毁”的捷径规则。

## 后续入口

MLF-5 已关闭，不再派发。后续若要把部件失效发展成机体断裂、残骸生命周期、Pk 或具体弹种校准，应按 `docs/agent` 标准另建子项目，让后续阶段消费本包输出的部件损伤事实，而不是在 MLF-5 内继续追加规则。
