# 空战 1v1 武器链进展

状态：`2026-05-16` 当前轮已验证版。

关联文档：

- [空战 1v1 切入分析](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_entry_analysis_20260516.zh.md)
- [空战 1v1 冻结计划](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_freeze_plan_20260516.zh.md)
- [空战 1v1 传感器烟雾夹具](/home/void0312/Workshop/CMO/scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)
- [空战 1v1 武器链回归测试](/home/void0312/Workshop/CMO/tests/runtime/test_air_combat_1v1_fire_missile.py)

## 一、文档定位

本文档记录本轮围绕 `1v1` 空战第一阶段补下来的真实进展。

本轮目标不是接通完整训练入口，而是先回答一个更基础的问题：

1. 当前内核里的 `fire_missile()` 到底能不能作为 `1v1` 的真实交战链起点。
2. 当前导弹链是否存在会直接阻断 `1v1` 的基础异常。
3. `1v1` 后续合同应该把什么视为“已经成立”，又把什么继续视为 blocker。

## 二、本轮新确认的事实

### 2.1 `fire_missile()` 的基础发射合同已可回归验证

当前已经有 focused runtime tests 证明：

1. 没有有效敌方 track 时，`fire_missile(attacker_id, target_id)` 不会发射。
2. 有效敌方 track 存在时，`fire_missile()` 会成功生成导弹实体。
3. 发射后会扣减 `missiles_remaining`。
4. 发射后会进入 `WeaponCooldown`，冷却未过时不能连续发射。

对应测试文件：

- [test_air_combat_1v1_fire_missile.py](/home/void0312/Workshop/CMO/tests/runtime/test_air_combat_1v1_fire_missile.py)

### 2.2 本轮修掉了两个直接阻断 `1v1` 的武器链问题

本轮在内核层确认并修复了两个关键问题：

1. 导弹 seeker / guidance 候选目标没有排除发射机与同阵营目标。
2. `fire_missile()` 生成的导弹实体没有挂上平移积分所需的 `Mass` / `ForceAccumulator`，而仓库主线又已停用旧的 `UpdatePosition`，导致导弹几乎不进入真实平移链。

修复后：

1. 导弹不再把发射机重新当成 guidance 锁定目标。
2. 导弹 seeker 原始探测层也不再纳入同阵营目标。
3. 导弹会进入当前维护中的 leapfrog 平移积分链，而不是只改 `Velocity` 却几乎不前进。

对应代码：

- [default_guidance_model.cpp](/home/void0312/Workshop/CMO/src/models/weapons/default_guidance_model.cpp)
- [default_sensor_model.cpp](/home/void0312/Workshop/CMO/src/models/systems/default_sensor_model.cpp)
- [simulation_kernel_weapon_api.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_weapon_api.cpp)

### 2.3 当前 `head-on` 夹具下已经形成真实 kill chain

在当前维护夹具：

- [air_combat_1v1_headon_sensor_smoke_v1.json](/home/void0312/Workshop/CMO/scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)

中，修复后的 `fire_missile()` 已经可以形成：

1. 蓝机保持存活；
2. 红机被击毁；
3. `red_active == false`；
4. `red_health == [0.0, 0.0]`；
5. 当前观测样本下，击毁出现在发射后约 `141` 个 tick。

这意味着：

1. `1v1` 第一阶段不再只是“传感器烟雾测试”。
2. 当前仓库已经具备最小真实交战内核闭环。

## 三、当前可冻结的 1v1 第一阶段合同

基于本轮结果，可以把 `1v1` 第一阶段的武器链合同冻结为：

1. 第一阶段允许直接以 `SimulationKernel.fire_missile()` 作为真实发射主链。
2. 第一阶段的 kill / splash 判定可以基于：
   - `is_unit_active(target_id) == false`
   - 或目标 `health <= 0`
3. 第一阶段可以把“蓝机存活且红机击毁”作为最小胜利样本。
4. 第一阶段仍然以 `execution` 主线承载训练任务更稳妥，不需要现在就跳到 `cooperative_execution`。

## 四、当前仍未接通的部分

虽然武器链已经比上一轮前进很多，但以下部分仍然没有被这轮工作接通：

1. `PilotAction.fire_weapon / master_arm / weapon_select_id` 仍未直接接到维护型导弹发射主链。
2. `ScenarioLoader` / `execution` 主线仍没有维护型 `1v1` 终止理由与奖励合同。
3. 当前 `1v1` 仍没有独立的 eval JSON 结果口径。
4. 当前仍没有维护型脚本红方 / 冻结对手挂接面。

因此，本轮结论不是“`1v1` 训练已完成”，而是：

1. `1v1` 的真实武器内核闭环已经成立。
2. 后续可以进入 reward / termination / eval 合同冻结，而不是继续停留在“是否真的能打起来”的不确定阶段。

## 五、建议的下一步

当前最合适的下一步已经比上一轮更明确：

1. 先新增 `1v1` 明确终止合同：
   - 蓝胜
   - 红胜
   - 双亡
   - 超时
   - 弹尽未决
2. 再把该合同接到 `execution` 主线的 reward / done / info 输出。
3. 再补一个最小 `1v1` eval 口径，至少输出胜负、超时、终止原因、交战步数。
4. 最后再考虑脚本红方或冻结对手，不要反过来。

## 六、验证命令

本轮聚焦验证命令：

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/runtime/test_air_combat_1v1_fixture.py tests/runtime/test_air_combat_1v1_fire_missile.py
```

当前结果：

```text
5 passed
```
