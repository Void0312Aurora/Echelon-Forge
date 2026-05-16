# `python/training/` 层职责

`python/training/` 保存主线训练入口的 bootstrap 和 orchestration 支撑。

它的定位不是替代 `python/rl/` 中的算法、policy 或 vec-env 逻辑，而是把
顶层脚本里与“入口协调”强相关的职责收口起来，例如：

- CLI 参数表与默认值
- 训练配置和场景路径校验
- 实验目录、resume / init-from 目录约定
- seed 与 PyTorch runtime bootstrap
- 训练开始前的统一运行时摘要打印

## 当前文件

- [cli.py](/home/void0312/Workshop/CMO/python/training/cli.py)
  - `train.py` 复用的 argparse 定义。
- [bootstrap.py](/home/void0312/Workshop/CMO/python/training/bootstrap.py)
  - 路径校验、配置装载、实验目录准备、锁文件、seed / torch runtime 初始化。

## 边界

- 这里可以放训练入口的参数解析、实验目录管理、运行时 bootstrap。
- 不要把 SB3 算法、policy 结构、vec-env 细节重新搬进来。
- `world_model_train.py` 的后续拆分不在这个子域当前阶段的范围内。
