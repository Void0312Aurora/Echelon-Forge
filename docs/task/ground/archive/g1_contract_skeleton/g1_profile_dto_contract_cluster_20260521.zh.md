<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g1_contract_skeleton/g1_profile_dto_contract_cluster_20260521.md. Review before treating this file as authoritative. -->

# G1 配置文件与 DTO 合约集群

状态：`2026-05-21` G1-A 预先检查与 G1-B Python 配置文件实现已接受。

输入：

- [G1 自述文件](README.md)
- [G1 配置文件与 DTO 预先检查](g1_profile_dto_preflight_20260521.md)
- [地面标准概述](../../../standards/ground/README.md)
- [地面最小任务结构](../../../standards/ground/minimal_task_structure.md)
- [子代理使用策略](../../../standards/governance/subagent_usage_policy.md)

## 目的

添加第一个地面合约框架，同时保留现有的 `通用 + 专用 + 配置文件桥接` 模式。

## 任务项

| 标识 | 项目 | 验收标准 |
|------|------|----------|
| `G1-A1` | 配置文件解析器 | `tasking_profile` 接受 `army`、`ground` 和 `land`，并将其标准化为 `ground`。 |
| `G1-A2` | 地面配置文件壳 | 一个 `ground_profile` 和适配器应暴露任务桥接所需的相同窄接口。 |
| `G1-A3` | 起始任务默认值 | `TASK_MOVE`、`TASK_OCCUPY` 和 `TASK_SUPPORT` 映射到通用核心字段，无空中/海军词汇泄露。 |
| `G1-A4` | DTO 放置决策 | 决定 G1 是否需要空/最小化 `components/tasking/ground` 和 `components/command/ground` 头文件，还是仅保留 Python 配置文件。 |
| `G1-A5` | 聚焦测试 | 测试证明配置文件解析和起始默认值，同时保持现有空中/海军测试通过。 |

## 写入范围

可能在 G0 关闭后允许：

- `python/rl/tasking/bridge.py`
- `python/rl/tasking/common_core_profile.py`
- `python/rl/tasking/ground_adapter.py`
- `python/rl/profile/ground_profile.py`
- 聚焦的 `tests/leader` 或 `tests/runtime/mission` 配置文件测试
- 可选的 `src/components/tasking/ground/**` 和 `src/components/command/ground/**`

请勿编辑：

- 移动、物理、传感器、武器、伤害或外观运行时行为
- 空中/海军配置文件语义，除非是兼容性保留的解析器钩子
- 广泛的场景加载器行为

## 建议验证

```bash
git diff --check
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/runtime/mission/test_naval_mission_command_mapping.py
```

实现开始后，添加一个聚焦的地面配置文件测试。

## 交接

返回：

- 修改的文件
- 已接受的配置文件别名
- 任务默认映射表
- 运行的测试
- G2/G3 的遗留项

预先检查结果：

- [G1 配置文件与 DTO 预先检查](g1_profile_dto_preflight_20260521.md) 建议采用窄的仅 Python 配置文件实现发布，并将 DTO 决策记录为 `G1 中不需要`。

实现结果：

- `G1-B` 仅编辑了 Python 解析器/配置文件/适配器文件以及聚焦的 `tests/leader` 覆盖。
- `army`、`ground`、`land` 和 `ServiceProfile.Army` 现已标准化为 `ground`。
- DTO 壳决策仍为 `G1 中不需要`。
- C++ DTO 壳、绑定、运行时行为、命令传递、场景加载以及 G2/G3/G4 范围保持不变。
