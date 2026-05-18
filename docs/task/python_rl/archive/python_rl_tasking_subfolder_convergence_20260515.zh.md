# python/rl tasking 子域入箱收敛记录

状态：`2026-05-16` 已完成入箱与根级 shim 清理
范围：`python/rl` 下 `tasking` 相关实现文件与其兼容入口

## 1. 背景

此前 `python/rl` 根目录存在明显扁平化倾向：

- `common_core_profile.py`
- `leader_tasking.py`
- `tasking_air_adapter.py`
- `tasking_bridge.py`

这几类文件都属于同一条 `tasking` 语义链，但长期平铺在根目录，会带来两个问题：

1. 根目录语义密度过高，难以从目录结构上识别子域。
2. 新文件容易继续往根目录堆积，导致“桥接层 / 适配层 / 具体实现”边界越来越模糊。

## 2. 本轮冻结目标

本轮只解决结构问题，不做大规模行为改写：

1. 将 `tasking` 相关实现迁入真实子文件夹。
2. 让项目内部优先使用子包路径。
3. 完成主链与测试切换后删除旧路径 shim。

## 3. 结果

已落位到：

- `python/rl/tasking/common_core_profile.py`
- `python/rl/tasking/leader_tasking.py`
- `python/rl/tasking/air_adapter.py`
- `python/rl/tasking/bridge.py`
- `python/rl/tasking/__init__.py`

根目录对应实现文件已删除，不再作为真实实现驻留在 `python/rl/` 根层。

## 4. 兼容策略（历史）

为避免一次性修改全部旧调用，第一阶段曾短期保留根级 shim：

- `python/rl/common_core_profile.py`
- `python/rl/leader_tasking.py`
- `python/rl/tasking_air_adapter.py`
- `python/rl/tasking_bridge.py`

这些 shim 当时是“模块对象级”兼容，不只是普通符号 re-export，因此能继续支持：

- 旧式 `from python.rl.leader_tasking import ...`
- 旧式 `import python.rl.tasking_bridge as ...`
- 测试中的 `mock.patch("python.rl.leader_tasking.ef_py", ...)`

在 `2026-05-16` 完成主链、测试与工具链切换后，上述 shim 已删除。

## 5. 已同步到新路径的内部调用

本轮已将以下内部使用迁移到子包路径：

- `python/rl/world_batch_vec_env.py`
- `python/rl/cooperative_world_batch_vec_env.py`
- `game/backend/app.py`
- `python/testing/scenario_contract_runner.py`

说明：

- 项目主链现已统一引用 `python.rl.tasking.*`。
- 根级 `python/rl/*.py` tasking 兼容入口已不再保留。

## 6. 当前边界

本轮没有进一步处理：

1. `leader_tasking.py` 内部职责再拆分。
2. `common_core_profile.py` 与 `profile/` 的语义进一步下沉。
3. `ScenarioLoader` / runtime 侧的全部旧路径替换。
4. 非 `tasking` 子域的整体收纳。

## 7. 后续建议

下一阶段可以继续做两件事：

1. 在 `tasking` 子包内部继续拆分：
   - `phase_manager`
   - `scripted_c2_manager`
   - `mission_command_builder`
   - `common_core_facade`

2. 保持 `python.rl.tasking.*` 作为唯一稳定导入面，避免重新引入根级兼容层。

这样可以避免“虽然进了子文件夹，但子文件仍然过胖”的第二层堆积问题。
