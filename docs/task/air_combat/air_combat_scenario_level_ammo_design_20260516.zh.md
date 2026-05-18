# 空战场景级 Ammo 设计与落地

状态：`2026-05-16` 已实现并完成聚焦验证。

关联文档：

- [空战 1v1 冻结计划](air_combat_1v1_freeze_plan_20260516.zh.md)
- [空战 1v1 武器链进展](air_combat_1v1_weapon_chain_progress_20260516.zh.md)
- [空战 1v1 武器链回归测试](../../../tests/runtime/test_air_combat_1v1_fire_missile.py)

## 一、问题背景

在当前仓库中，`Ammo` 的真实运行时来源原先主要是：

1. 单位数据库定义；
2. `UnitDefinition -> DefaultUnitFactory -> Ammo` 这条平台默认链；
3. `fire_missile()` / `missiles_remaining` / `can_fire` 也都直接读实体上的 `Ammo` 组件。

这导致一个实际问题：

1. 从设计上，任务级弹药配置更适合放在场景层；
2. 但在实现上，场景 `entities[]` 之前并不能稳定覆盖实体 `Ammo`；
3. 于是 `1v1`/`2v2` 任务合同会被平台默认值绑定，而不是由场景明确控制。

## 二、本轮冻结的设计

本轮把“平台默认 ammo”和“场景级 ammo 覆盖”收敛成以下维护型语义：

1. 平台数据库仍然负责提供默认 `Ammo` / `WeaponCooldown`。
2. 场景层可以在 `entities[]` 中显式写 `ammo` 与 `weapon_cooldown`。
3. 若场景未写，则保持平台默认值不变。
4. 若场景显式写了，则场景覆盖优先于平台默认值。

推荐场景字段：

```json
{
  "name": "Blue_Fighter",
  "type": "F-16C_Block50",
  "side": "Blue",
  "is_agent": true,
  "pos": [0.0, 0.0, 1200.0],
  "vel": [0.0, 180.0, 0.0],
  "heading": 0.0,
  "ammo": {
    "missiles_remaining": 2,
    "max_missiles": 6
  },
  "weapon_cooldown": {
    "cooldown_s": 0.75,
    "last_fire_time": -1.0
  }
}
```

## 三、当前支持的字段范围

本轮只把最小维护型字段接通为：

1. `ammo.missiles_remaining`
2. `ammo.max_missiles`
3. `weapon_cooldown.cooldown_s`
4. `weapon_cooldown.last_fire_time`

当前不在本轮范围内的仍包括：

1. 站位级 / 类型级细分武器库存；
2. `default_loadout` 到 runtime ammo 的自动映射；
3. `weapon_select_id` 与具体弹种绑定；
4. 场景层按挂点声明真实载荷后自动生成 runtime 通用弹药。

## 四、落地路径

本轮打通了两条维护路径：

1. 单 world：
   - `ScenarioLoader`
   - `apply_world_layout_to_kernel(...)`
   - `SimulationKernel.set_unit_ammo(...)`
   - `SimulationKernel.set_weapon_cooldown(...)`
2. batch world：
   - `CompiledWorldLayoutTemplate`
   - `WorldSpawnRequest`
   - `WorldBatchRuntime.spawn_units_batch(...)`
   - `WorldBatchRuntime.apply_world_setup_batch(...)`

这意味着：

1. 同一个场景定义在单 world 与 batch world 下具有一致的 ammo 覆盖语义。
2. 后续 `execution` / `world_batch_vec_env` / `cooperative_world_batch_vec_env` 都可以复用同一场景级配置面。

## 五、对 1v1 的直接意义

这次落地后，`1v1` 工作可以更自然地推进：

1. 可以把 `F-16C_Block50` 留作平台真实机体；
2. 再通过场景层显式补 `ammo`，而不是为了弹药链路退回通用 `Aircraft`；
3. 后续 `1v1` 和 `2v2` 的任务合同也可以更明确地写“本任务双方初始弹药各是多少”。

## 六、验证

本轮已验证：

1. 场景级 `ammo` 覆盖会在 `ScenarioLoader` 路径生效；
2. 相同场景在 compiled + batch runtime 路径也会生效；
3. 覆盖后的 `missiles_remaining` 可被观测面稳定读到。

聚焦命令：

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/runtime/test_air_combat_1v1_fire_missile.py
cmo_python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k 'load_compiled_scenario_batch or scenario_loader_and_batch_runtime_share_setup_semantics'
```

当前结果：

```text
4 passed
3 passed, 15 deselected
```

## 七、建议下一步

在这条设计已经落地后，下一步最自然的是：

1. 把 `1v1` 夹具从通用 `Aircraft` 切换到 `F-16C_Block50`；
2. 通过场景层显式声明双方 `ammo`；
3. 再继续冻结 `1v1` 的终止 / 奖励合同。
