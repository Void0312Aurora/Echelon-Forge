# python/rl control 子域入箱收敛记录

状态：`2026-05-16` 第一轮已完成
范围：`mission_defs`、`scripted_*` 控制器、`wrappers`

## 1. 目标

在 `tasking` 子域完成入箱后，继续处理 `python/rl` 根目录中另一组明显成体系的控制语义模块：

- `mission_defs.py`
- `scripted_takeoff.py`
- `scripted_stable_flight.py`
- `scripted_landing.py`
- `wrappers.py`

这组文件共同承担：

- 命令码与阶段语义定义
- 起飞 / 巡航 / 着陆脚本控制器
- 多时间尺度动作包装与 scripted residual 混控

因此更适合作为独立 `control` 子域，而不是继续平铺在根目录。

## 2. 本轮结果

已迁移到：

- `python/rl/control/mission_defs.py`
- `python/rl/control/scripted_takeoff.py`
- `python/rl/control/scripted_stable_flight.py`
- `python/rl/control/scripted_landing.py`
- `python/rl/control/wrappers.py`
- `python/rl/control/__init__.py`

## 3. 兼容策略（历史）

与 `tasking` 子域一致，本轮曾短期保留根级 shim：

- `python/rl/mission_defs.py`
- `python/rl/scripted_takeoff.py`
- `python/rl/scripted_stable_flight.py`
- `python/rl/scripted_landing.py`
- `python/rl/wrappers.py`

在 `2026-05-16` 主链、测试与工具链切换完成后，这些 shim 已删除。

## 4. 已切换到新路径的主链模块

本轮已将以下核心模块改为优先使用 `python.rl.control.*`：

- `gym_envs/leader_env.py`
- `gym_envs/scenario_loader.py`
- `python/rl/world_batch_vec_env.py`
- `python/rl/cooperative_world_batch_vec_env.py`
- `python/rl/runtime/single_world_batch_runtime.py`
- `python/rl/runtime/leader_world_batch_runtime.py`
- `python/rl/policy_algo/hmoe_routing.py`
- `python/rl/profile/air_profile.py`
- `python/rl/tasking/leader_tasking.py`
- `game/backend/app.py`

## 5. 当前边界

本轮没有继续处理：

1. `control` 内部再拆分，例如将 `wrappers.py` 拆为更细粒度组件。
2. 工具链 / 诊断脚本 / 历史测试的所有旧路径导入。
3. `runtime`、`policy_algo`、`planning`、`support` 子域的进一步入箱。

## 6. 后续建议

下一阶段优先级建议：

1. `runtime` 子域收纳。
2. `policy_algo` 子域收纳。
3. 保持 `python.rl.control.*` 作为唯一稳定导入面，不再恢复根级兼容层。
