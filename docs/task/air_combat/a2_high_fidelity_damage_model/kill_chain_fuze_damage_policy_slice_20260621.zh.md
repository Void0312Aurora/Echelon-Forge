# P3 引信质量伤害倍率清理切片

日期：`2026-06-21`

状态：旧的 `fuze_quality -> effective.damage` 隐式倍率已经从 runtime、DTO、
Python binding 和诊断导出中物理删除。当前默认链路不再提供旧倍率入口。

## 当前实现

已清理的运行面：

- missile tuning 中不再存在引信质量伤害倍率 policy。
- missile runtime state 中不再暴露引信质量伤害倍率开关。
- effects/fuze facade 中不再暴露倍率应用前后 scalar。
- launch adapter、damage adapter、process probe 和 decoupling probe 不再从该倍率生成
  杀伤输入。

`fuze_quality` 现在只保留在引信/起爆诊断语义中，不再改写 warhead damage scalar。

## 验证

关键负向测试：

```bash
CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py \
  -k legacy_fuze_quality
```

结果：`1 passed, 45 deselected`。

补充回归已覆盖：

- `tests/runtime/engagement/test_launch_adapter_static_shape.py`
- `tests/runtime/engagement/test_engagement_contract_shape.py`
- `tests/runtime/engagement/test_diagnostics_trace_contract.py`
- `tests/runtime/engagement/test_munition_damage_adapter.py`
- `tests/runtime/bindings/test_bindings_engagement_surface.py`
- `tests/tools/test_kill_chain_decoupling_probe.py`

## 边界

这不是 P6 数据校准，也不是 Pk 或真实弹种杀伤声明。它只关闭旧耦合入口，
让后续工程代理数据校准只能通过显式的单层 evidence/admission 路径进入。
