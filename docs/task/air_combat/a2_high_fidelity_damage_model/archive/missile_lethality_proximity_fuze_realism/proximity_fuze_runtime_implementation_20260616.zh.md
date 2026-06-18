# 近炸引信运行时实现结果

状态：`2026-06-16`，PF-R4 通过；聚焦运行时实现完成。

英文对应文件：
[proximity_fuze_runtime_implementation_20260616.md](proximity_fuze_runtime_implementation_20260616.md)。

## 已实现范围

本次 PF-R4 只实现非权威 surrogate 合同里的运行时解释性，不声明真实武器校准。

已实现：

- 新增终止负例原因：
  - `outside_sensor_window`
  - `target_not_detected`
- 在 `FuzeEvaluationEvent`、`EffectsEvent`、导弹 debug runtime state、
  Python 绑定和诊断链路行里暴露近炸传感/探测证据。
- 在触发抽样前新增近炸 surrogate evidence 步骤：
  - 传感窗口来源和分数；
  - 末端航迹是否有效；
  - 目标探测来源、置信度和阈值；
  - 是否探测到目标；
  - 起爆点来源；
  - 机制覆盖分数。
- 对未起爆、无末端航迹、传感窗口外、目标未探测到等结果保持 no-load
  不变量。
- 保留触发引信和定时引信的显式路径。
- 探测成功之后尽量保持既有起爆概率面兼容；新增探测证据是门控和诊断解释，
  不是校准后的 Pk 模型。
- 将诊断行 schema 提升到 `7`，便于后续 CSV/JSON 消费者读取新的近炸证据列。

## 涉及文件

- [../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../src/runtime/contracts/engagement_contracts.h)
- [../../../../../src/components/combat/common/weapon_common.h](../../../../../../src/components/combat/common/weapon_common.h)
- [../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp](../../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp)
- [../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp](../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp)
- [../../../../../src/core/engine/weapon_launch_adapter.h](../../../../../../src/core/engine/weapon_launch_adapter.h)
- [../../../../../src/interfaces/python/bindings_runtime.cpp](../../../../../../src/interfaces/python/bindings_runtime.cpp)
- [../../../../../src/interfaces/python/bindings_core.cpp](../../../../../../src/interfaces/python/bindings_core.cpp)
- [../../../../../src/systems/combat/damage_system_common.h](../../../../../../src/systems/combat/damage_system_common.h)
- [../../../../../tools/diagnostics/lethality_chain_contract.py](../../../../../../tools/diagnostics/lethality_chain_contract.py)
- [../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py](../../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py)
- [../../../../../tests/runtime/air_combat/weapon_guidance_realism/fuze.py](../../../../../../tests/runtime/air_combat/weapon_guidance_realism/fuze.py)
- [../../../../../tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py](../../../../../../tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py)
- [../../../../../tests/runtime/bindings/test_bindings_engagement_surface.py](../../../../../../tests/runtime/bindings/test_bindings_engagement_surface.py)

## 验证

所有 Python 测试都通过项目虚拟环境包装器执行：
`.\tools\maintenance\cmo_env.ps1`。

通过：

```powershell
cmake --build build-local-win --target ef_py -j2
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/test_continuous_rod_surface.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/test_fuze_no_detonation_event_gate.py tests/runtime/air_combat/test_live_detonation_event_surface.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py tests/runtime/air_combat/test_diagnostics_process_probe_summary.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/training/test_fire_timing_fault_localization_contracts.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/engagement/test_engagement_contract_shape.py
```

通过计数：

- 构建：通过，仅有既有 unused-variable 警告；
- launch/guidance/fuze：`36 passed, 4 subtests passed`；
- continuous rod surface：`14 passed`；
- fuze no-detonation 与 live detonation 事件门：`2 passed`；
- diagnostics process probe：`34 passed`；
- training fault-localization contracts：`19 passed`；
- binding 与 engagement contract shape：`23 passed`。

## 残留问题

- PF-R4 不声明真实引信阈值、真实 Pk、武器特定杀伤概率或确定性引信权威。
- 抽样运行过更大的 `test_warhead_and_component_damage.py`，其失败主要集中在当前
  部件几何身份和 primary component 旧断言上。该失败不作为 PF-R4 接受证据，
  应该在几何/测试基线 follow-up 中处理，而不是塞进近炸 surrogate 切片。
- PF-R5 矩阵验证已作为聚焦 surrogate 检查完成；其残余是 live guidance
  会把实际最近距离压在较窄区间，所以初始发射偏置不是纯起爆点对称性测试。

## 决策

PF-R4 作为聚焦实现和诊断导出切片已经完成。运行时接受范围限于已测试的
surrogate evidence 合同。PF-R5 已作为带残余的 surrogate 矩阵验证关闭，
不是对真实引信校准或 Pk authority 的接受。
