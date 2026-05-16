# `python/` 层职责

`python/` 不是杂项脚本目录，而是 C++ runtime 之上的 Python 支撑层。它承担场景编译与落地、训练回调、RL runtime 适配、world model 支持，以及测试运行时辅助。

主线依赖关系大致为：

```text
src/interfaces/python -> ef_py
  -> python/scenario_* + python/env_config + python/mission_obs_taxonomy
    -> gym_envs/
      -> python/rl/
        -> tools/ + tests/
```

## 允许

- 训练入口需要复用的 Python 运行时支持模块。
- 场景编译、world layout 落地、mission observation 维度约定。
- RL runtime、vec-env、policy algo、tasking glue。
- 训练时回调、benchmark helper、contract runner 支撑。
- world model / offline dataset 相关的纯 Python 组件。

## 禁止

- 把一次性人工诊断脚本直接堆到 `python/` 根目录。
- 在 `python/` 根目录里重复实现 `gym_envs/` 已经维护的环境职责。
- 为了兼容旧路径，继续新增扁平单文件入口而不进入已有子域。
- 在这里放置需要长期维护的 C++ binding 逻辑；那应留在 `src/interfaces/python/`。

## 子目录约定

- `rl/`
  - Python RL 主线，含 runtime、policy_algo、tasking、planning、profile、support。
- `training/`
  - `train.py` 主线入口复用的 CLI、bootstrap、实验目录与运行时 orchestration 支撑。
- `testing/`
  - 测试和 contract runner 运行时支撑。
- `world_model/`
  - Dreamer、replay、feature、network 等 world model 支撑。
- `models/`
  - Python 侧模型组件，目前主要是特征提取器等训练模型辅助。

## 当前阅读入口

- [rl/__init__.py](/home/void0312/Workshop/CMO/python/rl/__init__.py)
- [testing/runtime.py](/home/void0312/Workshop/CMO/python/testing/runtime.py)
- [testing/scenario_contract_runner.py](/home/void0312/Workshop/CMO/python/testing/scenario_contract_runner.py)
- [world_model/dreamer.py](/home/void0312/Workshop/CMO/python/world_model/dreamer.py)
- [models/transformer.py](/home/void0312/Workshop/CMO/python/models/transformer.py)

## 当前文件落点

- 根目录
  - [artifact_paths.py](/home/void0312/Workshop/CMO/python/artifact_paths.py)
    - artifact 路径解析和 contract / eval 路径归一化。
  - [env_config.py](/home/void0312/Workshop/CMO/python/env_config.py)
    - 训练配置到 env 设置的解析入口。
  - [mission_obs_taxonomy.py](/home/void0312/Workshop/CMO/python/mission_obs_taxonomy.py)
    - mission observation 维度、字段索引、模式枚举。
  - [scenario_compiler.py](/home/void0312/Workshop/CMO/python/scenario_compiler.py)
    - 场景 JSON 编译、prefab 合并、route / objective / layout 预处理。
  - [scenario_runtime.py](/home/void0312/Workshop/CMO/python/scenario_runtime.py)
    - compiled scenario 到 kernel/world-batch 的运行时落地与 roster 映射。
  - [training_callbacks.py](/home/void0312/Workshop/CMO/python/training_callbacks.py)
    - SB3 训练诊断、curriculum 与训练期统计回调。
- `rl/`
  - `control/`
    - scripted takeoff / landing / stable-flight 控制器与 wrapper。
  - `tasking/`
    - leader/tasking bridge、air/naval adapter、common-core profile glue。
  - `runtime/`
    - single-world、world-batch、leader-window、cooperative runtime 与 vec-env 适配。
  - `policy_algo/`
    - PPO adaptive KL、custom rollout buffer、policy、HMoE routing。
  - `planning/`
    - coarse route propagation 等规划辅助。
  - `profile/`
    - `common/air/naval` profile 默认值与推断。
  - `support/`
    - benchmark、nonfinite probe、SB3 vec-env 兼容支撑。
- `testing/`
  - `runtime.py`
    - repo/build 路径注入与测试期导入配置。
  - `scenario_contract_runner.py`
    - JSON contract 的统一执行入口。
- `training/`
  - `cli.py`
    - `train.py` 入口的 argparse 参数表。
  - `bootstrap.py`
    - 场景/配置校验、resume 目录约定、lock、seed、torch runtime bootstrap。
- `world_model/`
  - `dreamer.py`, `networks.py`, `features.py`, `replay.py`, `utils.py`
    - world model 训练、网络、特征和数据集支持。
- `models/`
  - `transformer.py`
    - 训练时可复用的 Transformer 特征提取器与观测预处理。

## 问题定位建议

如果你遇到的是：

- “训练配置为什么映射成这个 observation/action/env 设置”
  - 先看 [env_config.py](/home/void0312/Workshop/CMO/python/env_config.py)
- “场景为什么被编译成这种 route / objective / roster”
  - 先看 [scenario_compiler.py](/home/void0312/Workshop/CMO/python/scenario_compiler.py)
- “batch runtime 怎么把 compiled scenario 应用到 kernel”
  - 先看 [scenario_runtime.py](/home/void0312/Workshop/CMO/python/scenario_runtime.py)
- “leader/tasking/HMoE 训练逻辑在哪里”
  - 先看 `python/rl/tasking/` 与 `python/rl/policy_algo/`
- “train.py 为什么进入这个 run 目录、为什么自动 resume、torch 线程怎么定”
  - 先看 `python/training/`
- “训练日志、退化、termination 统计从哪来”
  - 先看 [training_callbacks.py](/home/void0312/Workshop/CMO/python/training_callbacks.py)
- “contract runner 或 eval 为什么解析不到 artifact”
  - 先看 [artifact_paths.py](/home/void0312/Workshop/CMO/python/artifact_paths.py)

## 迁移备注

- `python/rl/` 已经按子域收敛，新增 RL 相关逻辑应优先进入对应子包，不要恢复扁平文件布局。
- `scenario_compiler.py` 和 `scenario_runtime.py` 仍是根级主入口，因为它们被 `gym_envs/`、`tools/`、`tests/` 广泛复用。
- 如果后续 `world_model/` 或 `testing/` 继续膨胀，应优先在各自目录内再拆子包，而不是回退到根级兼容文件。
