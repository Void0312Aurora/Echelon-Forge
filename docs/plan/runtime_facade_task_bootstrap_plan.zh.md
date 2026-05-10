# Runtime Facade 任务启动筹备方案

文档导航：

- [README.md](/home/void0312/Workshop/CMO/docs/plan/README.md)
- [system_layering_and_engine_encapsulation_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/system_layering_and_engine_encapsulation_plan.zh.md)
- [architecture_and_performance_research_followup.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture_and_performance_research_followup.zh.md)
- [runtime_facade_contract_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_contract_plan.zh.md)
- [runtime_facade_layering_cleanup_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_layering_cleanup_freeze.zh.md)

状态：`2026-05-10` 冻结执行记录（第一批 `WP1-WP6` 已完成）。  
文档定位：

- 本文档曾用于冻结 runtime facade 第一批启动任务，现作为执行记录保留。
- 本文档只覆盖 `WP1-WP6` 的冻结范围、完成状态、回归结果与 benchmark 产物。
- 后续若继续推进 facade contract deepening、device-view、resident-state、exact backend 等工作，必须新建或更新单独的冻结执行文档。
- 下一批候选分层清理工作已收敛到
  [runtime_facade_layering_cleanup_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_layering_cleanup_freeze.zh.md)。

本文档用于把
[runtime_facade_contract_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_contract_plan.zh.md)
转化为可执行的第一批任务；当前这批任务已全部完成。

实现进展：

- 已新增 `src/runtime/facade/runtime_facade_types.h`
- 已新增 `src/runtime/facade/runtime_facade.h`
- 已新增 `src/runtime/facade/runtime_facade.cpp`
- 已在 [python_module.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp) 暴露 `RuntimeFacade` 与首批 facade 类型
- 已新增 [test_runtime_facade.py](/home/void0312/Workshop/CMO/tests/runtime/test_runtime_facade.py) 作为最小回归入口

当前阶段说明：

- 当前文档只冻结第一批任务，即 `WP1` 到 `WP6`
- `WP4` 的主线路径接入已完成
- facade 仍直接包装 `WorldBatchRuntime`
- `WorldBatchVecEnv.reset()` 主路径已优先接入 facade
- `WorldBatchVecEnv.step_wait()` 主路径、execution episode controller mainline / shadow compare 子路径，以及批量动作下发 / 命令链同步 / 状态读回已切到 facade-first
- 单 world autoreset 仍保留局部 world apply 逻辑，但后续读回与 command-chain 同步已与 facade-first 主路径对齐
- 当前不再允许继续扩展未冻结的 facade contract deepening 范围；任何 `observation / reward / info` 合同深化、device-view、resident-state、exact backend 等后续工作，必须单独立项并重新冻结后才能启动

相关文档：

- [system_layering_and_engine_encapsulation_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/system_layering_and_engine_encapsulation_plan.zh.md)
- [architecture_and_performance_research_followup.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture_and_performance_research_followup.zh.md)
- [runtime_facade_contract_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_contract_plan.zh.md)
- [runtime_facade_layering_cleanup_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_layering_cleanup_freeze.zh.md)

## 零、冻结执行边界

本轮只允许执行以下冻结范围：

1. `WP1` facade 契约对象定义
2. `WP2` facade 原型层实现
3. `WP3` Python 绑定入口
4. `WP4` `WorldBatchVecEnv` 主线路径接入
5. `WP5` 回归测试补齐与核对
6. `WP6` 基准验证

本轮不允许执行以下未冻结内容：

- 新增 `WP` 之外的 contract deepening 工作
- 把 `ExecutionBatchStepResult` 扩展为新的高层 DTO 族
- 推进 facade 级 `device_view`、resident-state、exact backend 切换位
- `ScenarioLoader` 大拆分或 ownership 再下沉
- 任何未在本文档中明确写入的“顺手继续优化”

执行规则：

1. 如果某项工作不直接服务 `WP1` 到 `WP6` 的验收标准，则不得启动。
2. 如果某项工作需要新增范围，必须先修改本文档并完成冻结，再进入实现。
3. 当前代码中已经存在、但未写入本文档冻结目标的增量，不作为继续扩展的依据。

## 零点一、当前 WP 状态

- `WP1`：已完成
- `WP2`：已完成
- `WP3`：已完成
- `WP4`：已完成
- `WP5`：已完成
- `WP6`：已完成

第一批冻结任务已全部完成。

基准结果与测试结果记录：

1. `WP5` 冻结测试集合：
   `tests/world_batch/test_world_batch_vec_env.py`
   `tests/runtime/test_execution_episode_controller.py`
   `tests/runtime/test_execution_episode_state.py`
   `tests/runtime/test_execution_episode_batch_prepare.py`
   `tests/runtime/test_runtime_facade.py`
   结果：`41 passed`
2. `WP6` `benchmark_world_batch_vec_env_phase4.py`
   输出文件：
   [wp6_benchmark_world_batch_vec_env_phase4.json](/home/void0312/Workshop/CMO/docs/plan/results/wp6_benchmark_world_batch_vec_env_phase4.json)
3. `WP6` `benchmark_policy_observation_bridge_phase4.py`
   当前 `build-facade-local` 缺少该脚本要求的 CUDA runtime bridge 绑定，脚本按预期返回
   `CUDA runtime is not available for the bridge benchmark.`

## 一、目标

第一批任务不追求一步完成完整架构切换，而是完成以下三个启动目标：

1. 先冻结一版维护中的 facade 契约和最小对象集。
2. 搭出一个不改变行为的 facade 原型层。
3. 让 `WorldBatchVecEnv` 的一部分主线路径开始依赖 facade，而不是直接拼底层 runtime 细节。

## 二、启动原则

### 原则 1：先改依赖方向，再改语义所有权

也就是说，第一阶段允许 facade 内部仍调用：

- `WorldBatchRuntime`
- `ScenarioLoader` 辅助逻辑
- 当前 observation build 路径

但前端依赖方向要先改过来。

### 原则 2：先切 reset / step 主路径，不先统一所有 probe

第一阶段只服务维护中的 execution rollout 主路径。

不要求第一批就统一：

- exact-state probe
- experimental GPU backend switch
- 所有 diagnostics helper

### 原则 3：所有改动必须可回归验证

第一批任务必须以现有测试与 benchmark 可验证为前提。

## 三、第一批交付范围

### In Scope

- facade 契约对象定义
- facade 原型实现骨架
- `WorldBatchVecEnv` reset/step 路径初步接入
- capability 协商对象
- observation packet 外壳
- 最小回归测试

### Out Of Scope

- `ScenarioLoader` 全量拆分
- exact GPU backend 主线切换
- resident-state 主线接入
- RPC / service 部署
- 目录大迁移
- 未单独冻结的 facade contract deepening

## 四、建议的工作包拆分

### WP1：定义 facade 契约对象

目标：

- 在代码层建立 facade 级 request / response / capability 类型

建议文件落点：

- `src/runtime/facade/runtime_facade_types.h`
- 后续如需要：`src/runtime/facade/runtime_facade_types.cpp`

建议首批类型：

- `RuntimeCapabilities`
- `RuntimeBatchConfig`
- `BatchResetRequest`
- `ExecutionBatchStepRequest`
- `ExecutionBatchStepResult`
- `ObservationBatchPacket`

验收标准：

- 类型命名和字段语义与文档一致
- 不要求首批字段完美，但必须稳定描述主线 reset / step 用例

### WP2：实现最小 facade 原型层

目标：

- 新增一个 facade 类，把 `WorldBatchRuntime` 包进去

建议文件落点：

- `src/runtime/facade/runtime_facade.h`
- `src/runtime/facade/runtime_facade.cpp`

建议首批接口：

- `create_session` 或构造函数
- `capabilities()`
- `reset_execution_batch(...)`
- `step_execution_batch(...)`
- `export_runtime_state(...)`

实现策略：

- 第一阶段可直接转调现有 `WorldBatchRuntime`
- 必要时允许临时调用 loader 辅助逻辑

验收标准：

- 不改变当前维护语义
- facade 能独立承载 reset / step 主用例

### WP3：增加 Python 绑定入口

目标：

- 让 Python 前端能调用新的 facade 原型

建议文件落点：

- [python_module.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp)

建议新增绑定对象：

- `RuntimeFacade`
- `RuntimeCapabilities`
- facade 级 request / result 类型

验收标准：

- Python 侧可实例化 facade
- 可从 Python 调用 reset / step

### WP4：接入 `WorldBatchVecEnv`

目标：

- 让 `WorldBatchVecEnv` 的一条主线路径开始依赖 facade

建议范围：

- 先切 `reset()`
- 再切 `step_wait()` 主路径

注意：

- 第一阶段不要求删除所有旧逻辑
- 可以先保留 fallback path
- 当前已落地的增量策略是：`reset()` 先切主路径，随后把 `step_wait()` 的 runtime 编排职责分阶段切到 facade-first

验收标准：

- 现有主线测试不退化
- 观测、奖励、终止语义保持一致

### WP5：补回归测试

目标：

- 用现有 runtime 测试和 world-batch 测试保护第一批切换

重点测试文件：

- [tests/world_batch/test_world_batch_vec_env.py](/home/void0312/Workshop/CMO/tests/world_batch/test_world_batch_vec_env.py)
- [tests/runtime/test_execution_episode_controller.py](/home/void0312/Workshop/CMO/tests/runtime/test_execution_episode_controller.py)
- [tests/runtime/test_execution_episode_state.py](/home/void0312/Workshop/CMO/tests/runtime/test_execution_episode_state.py)
- [tests/runtime/test_execution_episode_batch_prepare.py](/home/void0312/Workshop/CMO/tests/runtime/test_execution_episode_batch_prepare.py)

建议新增测试方向：

- facade reset 与现有 reset 行为一致
- facade step 与现有主线路径输出一致
- capability 协商结果稳定

冻结完成标准补充：

- 至少完成本文档列出的 runtime / world-batch 重点测试核对
- 不以零散的针对性子集通过替代 `WP5` 完成声明

执行结果：

- 已完成文档列出的冻结测试集合核对
- 固定运行环境：
  `CMO_BUILD_DIR=build-facade-local`
  `LD_LIBRARY_PATH=/home/void0312/Workshop/CMO/build-facade-local/_deps/flecs-build:/home/void0312/Workshop/CMO/build-facade-local`
- 结果：`41 passed`

### WP6：补基准验证

目标：

- 确认 facade 引入没有把主线性能拉坏

建议基准文件：

- [tools/diagnostics/benchmark_world_batch_vec_env_phase4.py](/home/void0312/Workshop/CMO/tools/diagnostics/benchmark_world_batch_vec_env_phase4.py)
- [tools/diagnostics/benchmark_policy_observation_bridge_phase4.py](/home/void0312/Workshop/CMO/tools/diagnostics/benchmark_policy_observation_bridge_phase4.py)

验收标准：

- facade 引入不应显著降低当前主线吞吐
- 如有小幅额外开销，必须换来后续 ownership 与 contract 稳定性的明显收益

冻结完成标准补充：

- 至少运行本文档列出的 benchmark 脚本并记录结果
- 在 `WP6` 完成前，不宣布第一批任务整体收口

执行结果：

- 已运行 `benchmark_world_batch_vec_env_phase4.py`
  记录文件：
  [wp6_benchmark_world_batch_vec_env_phase4.json](/home/void0312/Workshop/CMO/docs/plan/results/wp6_benchmark_world_batch_vec_env_phase4.json)
  摘要：
  `n_envs=8`
  `dummy_reset_ms=10.051270`
  `world_batch_reset_ms=11.891172`
  `reset_speedup=0.85x`
  `dummy_ms_per_env_step=0.392506`
  `world_batch_ms_per_env_step=0.292365`
  `step_speedup=1.34x`
- 已运行 `benchmark_policy_observation_bridge_phase4.py`
  当前结果不是性能数值，而是前置条件失败记录：
  当前 `build-facade-local` 的 `ef_py` 不包含该脚本要求的 CUDA runtime bridge 绑定，因此脚本返回
  `CUDA runtime is not available for the bridge benchmark.`
  该结果已记录为本轮冻结执行结果的一部分，而不是继续扩展范围去补新的构建线

## 五、建议的实施顺序

建议顺序如下：

1. `WP1` 类型冻结
2. `WP2` C++ facade 原型
3. `WP3` Python 绑定
4. `WP5` 最小回归测试
5. `WP4` `WorldBatchVecEnv.reset()` 接入
6. `WP4` `WorldBatchVecEnv.step_wait()` 接入
7. `WP6` 基准复核

原因：

- 先把契约和类型立起来
- 再让前端逐步切流量
- 避免先在 Python 里发明一层“假 facade”

## 六、建议的最小代码骨架

第一阶段可以采用非常保守的结构：

```text
src/runtime/facade/
  runtime_facade_types.h
  runtime_facade.h
  runtime_facade.cpp
```

`runtime_facade.h` 中建议最小类形态：

- `class RuntimeFacade`
- 内部持有 `WorldBatchRuntime`
- 提供 facade 级 reset / step / export_state / capabilities

这里的关键不是第一次就做得很通用，而是先把依赖边界抽出来。

## 七、前置条件检查

开始实施前，需要确认以下前置条件：

1. 当前 `WorldBatchRuntime` 作为底座已足够稳定。
2. `ExecutionEpisodeState` / `ExecutionEpisodeController` 的现有测试是绿的。
3. `WorldBatchVecEnv` 主线 benchmark 脚本可用，便于做切换前后比对。
4. 不在同一轮里同时做大规模 `ScenarioLoader` 语义重构。

## 八、风险清单

### 风险 1：Facade 只是多包了一层，却没有改变依赖方向

规避：

- 第一阶段就让 `WorldBatchVecEnv` 至少有一条主线改走 facade

### 风险 2：Facade 设计过于贴近当前实现细节

规避：

- request / response 用高层用例命名
- 避免直接把所有 `WorldBatchRuntime::*_batch` 方法一比一搬出去

### 风险 3：Facade 一期范围过大

规避：

- 只服务维护中的 reset / step 主线
- probe / diagnostics 继续作为二级接口保留

### 风险 4：切换时语义漂移

规避：

- 用现有 shadow compare、episode state roundtrip、world-batch 测试保护

### 风险 5：把 `ScenarioLoader` 一起大改导致任务爆炸

规避：

- facade 第一期允许内部临时依赖 loader 辅助逻辑
- `ScenarioLoader` 拆分单列为后续任务

## 九、后续候选事项（需另行冻结）

如果第一批完成，下一批最自然的延续任务是：

1. `ScenarioLoader` 的 execution-state adapter 拆分
2. facade 级 observation packet 中引入 `device_view`
3. facade 级 capability 协商接入 GPU helper 能力
4. facade 级 backend mode 预留 resident-state / exact backend 切换位

注意：

- 本节仅是候选方向，不构成当前冻结执行范围
- 本节任何条目都必须在第一批 `WP1` 到 `WP6` 完成后，另行形成新文档或新版本冻结，才能进入实现

## 十、历史启动里程碑（已完成）

### M1：契约落地

完成标准：

- facade 类型定义完成
- 文档和代码命名一致

### M2：原型可调用

完成标准：

- Python 侧可实例化 facade
- 可完成一次 reset / step 主调用

### M3：前端开始切流量

完成标准：

- `WorldBatchVecEnv` 至少一条主线路径接入 facade

### M4：回归与基准通过

完成标准：

- 现有核心测试通过
- benchmark 无显著退化

## 十一、最终建议

这一轮启动不应追求“看起来像一次大重构”，而应追求：

1. 把维护中的前端依赖边界先冻结下来。
2. 用最小代价把 facade 原型插入主线。
3. 为后续的 C++ ownership 下沉、CUDA resident-state、device-view 观察路径建立稳定入口。

因此，最建议的执行方式是：

- 先完成 `WP1 + WP2 + WP3`
- 然后切 `WorldBatchVecEnv.reset()`
- 再切 `step_wait()`
- 最后用测试和 benchmark 收口

这样启动成本最低，同时也最符合当前仓库的演进节奏。
