# 内核绑定、测试与可视化层

> ARCHIVED NOTE (2026-03-23): 该文档属于旧的架构拆分说明，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/Workshop/CMO/docs/standards/README.md)。

## 1. 职责

这一层负责：

- 将内核对象暴露给 Python
- 通过合同测试和诊断脚本验证链路
- 提供可视化与回放入口

## 2. 当前代码落点

### 2.1 Python 绑定

- [`src/interfaces/python/python_module.cpp`](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp)

负责暴露：

- `MissionCommand`
- `TaskOrder`
- `LeaderIntent`
- `PilotReport`
- `SimulationKernel`

### 2.2 合同与测试

- [`python/testing/scenario_contract_runner.py`](/home/void0312/Workshop/CMO/python/testing/scenario_contract_runner.py)
- [`tests/contracts/`](/home/void0312/Workshop/CMO/tests/contracts)
- [`tests/diagnostics/`](/home/void0312/Workshop/CMO/tests/diagnostics)

负责：

- 任务链合同
- 长机层 generalization 合同
- 轨迹、跑道、性能诊断

### 2.3 可视化

- [`examples/viz/viz_runner.py`](/home/void0312/Workshop/CMO/examples/viz/viz_runner.py)

负责：

- 执行层模型可视化
- 长机层 batched decision 可视化
- 通过 `train_config` 推断是 execution 还是 leader 模式

## 3. 当前最该关注的接口

如果要改绑定、测试或可视化，优先看：

1. [`src/interfaces/python/python_module.cpp`](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp)
2. [`python/testing/scenario_contract_runner.py`](/home/void0312/Workshop/CMO/python/testing/scenario_contract_runner.py)
3. [`examples/viz/viz_runner.py`](/home/void0312/Workshop/CMO/examples/viz/viz_runner.py)

## 4. 当前结构风险

- 绑定层字段名直接暴露底层结构，一旦 `action.h` 改字段，Python 训练和测试都会一起受影响。
- 合同测试目前更擅长卡高层任务链，对“真实着陆成功”这类终端行为的覆盖需要继续加强。
- 可视化脚本既支持 execution，又支持 leader，后续接口变化时容易出现“合同通过但 viz 错”的分叉。

## 5. 后续修改建议

若要改这一层，建议顺序是：

1. 先改 `python_module.cpp`
2. 再改 `scenario_contract_runner.py`
3. 最后改 `viz_runner.py`

这样可以先保住自动验证，再修可视化入口。
