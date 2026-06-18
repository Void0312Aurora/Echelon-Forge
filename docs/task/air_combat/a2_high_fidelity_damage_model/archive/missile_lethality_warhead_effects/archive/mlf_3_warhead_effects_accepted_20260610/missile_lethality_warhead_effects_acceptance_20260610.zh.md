# A2 MLF-3 收口验收记录

状态：`2026-06-10` closeout accepted / focused load-chain accepted。该记录验收 MLF-3A-G 的标准载荷事实链，不声明导弹杀伤模型整体高保真完成。

英文辅文：[missile_lethality_warhead_effects_acceptance_20260610.md](missile_lethality_warhead_effects_acceptance_20260610.md)

## 验收结论

通过：MLF-3 当前可以解释起爆后战斗部施加了什么载荷、覆盖到哪里、哪些部件承受了多少载荷。未起爆路径不会产生标准战斗部载荷事件。

保持未完成：真实弹种参数校准、连续杆、部件失效概率、结构解体、残骸对象、实体删除、Pk 和训练胜负投影。当前模型仍只使用通用、未校准、可替换的 research 数据。

## 已验收切片

| 切片 | 结论 | 证据 | 边界 |
| --- | --- | --- | --- |
| `MLF-3A` | accepted | 盘点记录确认现有 warhead / spatial / component 字段和 writer 缺口 | 不代表 runtime 完成 |
| `MLF-3B` | focused pass | event-store writer、真实起爆路径测试和 engagement capture 测试 | 不校准参数 |
| `MLF-3C` | focused pass | `test_warhead_blast_fragmentation_loads.py` 证明 range / direction / family 改变标准载荷事实 | 不引入真实 AIM-120C 参数 |
| `MLF-3D` | focused pass | Euclid 只读审计和 `test_warhead_spatial_component_projection.py` 证明空间覆盖/局部投影改变标准部件受载事实 | 不声明部件失效或坠毁 |
| `MLF-3E` | focused pass | process probe 优先读取标准 warhead / spatial / component 事件，同链路旧事件只作回退 | 不改变 reward 或胜负语义 |
| `MLF-3F` | focused pass | no-detonation gate 测试证明未起爆路径没有标准载荷事件 | 未来新增未起爆 outcome 时仍需保持 gate |
| `MLF-3G` | focused pass | 收口记录、README、状态、任务簇、派发队列和归档索引一致记录 accepted/held 边界 | 不关闭后续高保真阶段 |

## 复验命令

```bash
cmake --build build-workshop --target ef_py -j2
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest \
  tests/runtime/air_combat/test_warhead_spatial_component_projection.py \
  tests/runtime/air_combat/test_warhead_blast_fragmentation_loads.py \
  tests/runtime/air_combat/test_live_detonation_event_surface.py \
  tests/runtime/air_combat/test_fuze_no_detonation_event_gate.py \
  tests/runtime/engagement/test_live_engagement_event_capture.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
```

结果：`37 passed`。本次复验构建通过。

## 保持项

- 标准 `ComponentLoadEvent` 暂不显式暴露 per-component spatial weight；空间影响通过 `effect_scale` 和机制载荷读出。
- 默认常量缺少逐默认值 source category / scope / unit / uncertainty / replacement-rule runtime metadata。
- 结构解体、残骸、Pk、真实弹种参数、真实 AIM-120C/MQ-9 个案仍为后续阶段。

## 下一步

下一阶段应另建 MLF-4/5/6/8/9 等子项目处理连续杆、部件失效概率、结构解体、残骸和 Pk。MLF-3 输出只能作为这些阶段的标准载荷事实输入。
