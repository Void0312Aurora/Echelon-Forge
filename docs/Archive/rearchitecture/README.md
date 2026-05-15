# [ARCHIVED] 全面性能重构总纲

本目录已于 2026-03-22 归档。

这组文档只保留历史设计、阶段记录和 benchmark 背景，不再作为当前执行计划。考虑到提速收益未稳定跨过门槛，后续工作默认转回任务学习与训练主线，而不是继续沿本重构路线推进。

注意：

- 文中出现的“目标”“下一步”“后续”“推进”等表述均为归档前语境。
- Phase 1-6 的实现记录仍有参考价值，但不再代表当前优先级。
- 如需确认当前热路径结论与终止口径，以 `docs/speed_rearchitecture/` 的归档说明为准。

## 1. 当前判断

当前项目已经具备：

- 可运行的 C++ 内核与 Python 训练入口
- 执行层连续任务链
- 长机层 / C2 任务链
- 合同测试与诊断脚本

但当前吞吐上限主要不是由单个算子决定，而是由下面几类结构事实共同决定：

### 1.1 环境套环境

当前长机层训练并不是“在一个统一 runtime 上跑多速率控制”，而是：

`LeaderTrainingEnv -> UniversalEnv -> SimulationKernel`

这意味着每个 leader step 都会在 Python 中驱动一段完整的执行层循环，训练成本天然被执行层成本放大。

### 1.2 热路径仍在 Python

当前这些高频逻辑仍主要在 Python 中完成：

- observation 拼装
- mission / waypoint / ILS 几何推导
- reward / termination
- `TaskOrder / LeaderIntent / PilotReport / MissionCommand` 同步
- leader teacher / C2 / guard / baseline 逻辑

这使系统实际吞吐更接近“Python 编排上限”，而不是“内核仿真上限”。

### 1.3 Python/C++ 边界过碎

当前绑定主要以单对象 `get_* / set_*` 为主，缺少：

- batch observation 获取
- batch action 写入
- batch reset / step
- 编译后的场景运行时对象

因此 Python 需要在热路径中频繁跨边界取状态、组对象、再回写状态。

### 1.4 并行方式仍以多进程复制为主

当前主流训练并行方式仍是：

- 多个 Python 进程
- 每个进程一套 `SimulationKernel`
- 每个 leader env 一套执行环境
- 每个 env 各自持有冻结执行策略

这种模式可以扩容，但上限受制于：

- 进程间通信
- 重资源复制
- Python 调度
- 无法对 world stepping 做真正 batch 化

### 1.5 reset 缺少“场景编译层”

当前 reset 仍包含：

- 读 JSON
- 处理 imports
- 重建 zones
- spawn entities
- 深拷贝 mission / waypoint / transition 数据

这说明“场景描述”和“运行时实例”还没有明确分层。

## 2. 重构总目标

本轮重构的最终目标是把主链改造成：

`ScenarioCompiler -> CompiledScenarioRuntime -> WorldBatchRuntime -> Multi-rate Control Runtime -> Thin Python Training Adapter`

即：

1. 场景先编译，再实例化
2. world stepping 在 C++ 侧批量执行
3. 高热度 mission/geometry/reward 逻辑下沉到 C++
4. leader / execution 在同一 runtime 中以不同频率运行
5. Python 退化成训练编排层，而不是热路径控制层

## 3. 目标架构

### 3.1 ScenarioCompiler

新增“场景编译”层，把 JSON / prefab / 几何预处理转换成不可变运行时描述。

职责：

- 解析 JSON / imports / prefab
- 校验配置
- 生成稳定的 runway / waypoint / ILS / route / recovery 编号
- 预编译静态几何
- 产出可复用的 `CompiledScenario`

效果：

- reset 不再重新解释大部分静态数据
- 后续 spatial query / route logic 有统一输入

### 3.2 Spatial / Mission Runtime

将当前散落在 `ScenarioLoader` 中的几何与任务派生逻辑下沉为编译后运行时服务。

职责：

- runway local frame
- ILS / recovery 几何采样
- route leg 投影与进度
- waypoint 切换判定
- mission observation 基础特征

效果：

- Python 不再手工重复做几何计算
- reward / termination / guidance 可共享同一套几何口径

### 3.3 WorldBatchRuntime

在 C++ 中直接维护一批 worlds，而不是让 Python 多进程各自维护单 world。

职责：

- `reset_batch`
- `step_batch`
- `get_obs_batch`
- `set_action_batch`
- 统一生命周期管理

效果：

- world stepping 真正 batch 化
- 降低 Python 调度与边界调用次数
- 为后续共享推理和 GPU/CPU pipeline 留接口

### 3.4 Multi-rate Control Runtime

将 leader / execution 改造成同一 runtime 中的两级控制，而不是 env 套 env。

职责：

- execution 以 low-level tick 运行
- leader 以 decision interval 运行
- runtime 内部决定何时采样 leader action、何时复用 execution action

效果：

- 去掉 `LeaderTrainingEnv -> UniversalEnv` 的结构性套娃
- 训练链路更接近真实控制层级

### 3.5 Event-driven Command Chain

把命令链从“每 tick Python clone + sync”改成 runtime 内事件/状态机。

职责：

- task/order/intention/report 的生命周期管理
- 命令变更事件
- kernel 内缓存与读写

效果：

- 降低对象搬运成本
- 降低跨层错配风险
- 提升 leader / C2 重构空间

### 3.6 Thin Python Adapter

Python 环境层最终只保留：

- 训练框架适配
- 配置装配
- 实验脚本
- 非热路径日志与诊断

不再承担高频 mission / reward / geometry / stepping 逻辑。

## 4. 分阶段路线

### Phase 1

先拆 `ScenarioLoader` 中最重的几何热路径，建立编译后 spatial query 层。

对应文档：

- [phase1_spatial_query.md](./phase1_spatial_query.md)

状态：

- 已完成，冻结日期为 2026-03-20
- 已建立 `CompiledScenarioGeometry` 与 Python 绑定
- 已把 runway / ILS / route 的主几何热路径从 `ScenarioLoader` 手写逻辑切到 compiled query
- 已补行为合同与性能 benchmark，作为 Phase 1 结束口径

### Phase 2

引入 `ScenarioCompiler / CompiledScenario`，把静态场景解释与 reset 分离。

对应文档：

- [phase2_scenario_compiler.md](./phase2_scenario_compiler.md)

状态：

- 已完成，冻结日期为 2026-03-20
- 已落地 `ScenarioCompiler`、`CompiledScenario`、路径级缓存与 `load_compiled_scenario()` 分层入口
- 已把 runtime instantiate 从通用 `deepcopy` 切到专用 scenario materializer
- 真实 combined 场景下，`instantiate()` 已从 `0.3440 ms` 降到 `0.0976 ms`
- 当前 reset 主成本已转移到 loader runtime 与 kernel 装配，后续进入 Phase 3

### Phase 3

将 mission observation、reward、termination 逐步迁移到 C++ runtime。

对应文档：

- [phase3_mission_runtime.md](./phase3_mission_runtime.md)

状态：

- 已完成，冻结日期为 2026-03-21
- 已新增 `mission_runtime`、`reward_runtime`、`objective_runtime`、`termination_runtime` C++ helper 与 Python 绑定
- 已把 `nav_v1/nav_v2` mission-nav、waypoint reward、approach reward、conditional objective success、fail-fast / runway safety termination 组合器切到 runtime helper
- `ScenarioLoader` 现已在 load 时预编译 conditional objectives，并通过 runtime 输出收口 `termination_reason`
- 当前 benchmark 显示 nav helper `14.69x`，waypoint reward helper `9.01x`，approach reward helper `13.95x`，objective helper `48.91x`，safety helper `21.35x`

### Phase 4

引入 `WorldBatchRuntime` 和 batch Python 绑定。

对应文档：

- [phase4_world_batch_runtime.md](./phase4_world_batch_runtime.md)

状态：

- 已归档，最后记录日期为 2026-03-22
- 已新增 `WorldBatchRuntime`、batch setup/state 结构、batch Python 绑定、共享 `scenario_runtime` apply helper、以及单 world / batch world 一致性回归
- 已新增 execution-layer `WorldBatchVecEnv`，并把 `train.py` 接上 `runtime.world_batch_vec_env` opt-in backend
- `WorldBatchVecEnv` 已进一步改成 batch initial-state 读取、batch command-chain sync、以及 cached `route_ref_id`
- `CompiledScenario` 已补 runtime-only instantiate 路径，reset 不再为只读 scenario branches 付整份 clone 成本
- 已新增 `worker_threads` 控制，并把 `train.py` / benchmark 接上 `runtime.world_batch_threads`
- 已新增 reusable `BatchWorldApplyBuffer`，`WorldBatchVecEnv.reset()` 不再重复分配整批 batch apply descriptor
- 已重排 `ScenarioLoader._finalize_loaded_world()` / command-chain sync 顺序，把 reset 中的 `update_behaviors(0.0)` 和重复 geometry rebuild 从热路径里移掉
- 已补齐 `WorldBatchVecEnv -> ScenarioLoader.load_prepared_world()` 的 compiled runtime metadata ownership，batch reset 不再回退到 `_compile_conditional_objectives()` / `_extract_ils_beacons()` 的 legacy 分支
- 已去掉 `ScenarioLoader._randomize_mission()` 里的重复 `normalize/materialize/_build_lnav_runtime_config`，reset 只在 `_finalize_loaded_world()` 做一次
- 已把 `waypoint_templates` 编译进 runtime metadata，并让 world-yaw 同步旋转 `_normalized_waypoints`；waypoint cache fast-path 不再默认整段重建
- 已把 route template 的 `route_ref_id` 固定为逻辑身份，不再因为 world yaw 在 reset 中反复清零重算
- compiler 已补实验性 `layout_template` metadata，并增加 direct `layout build` benchmark；当前语义已打通，但 benchmark 仍显示 template materializer 慢于 legacy build，因此默认未挂主链
- 当前 benchmark 显示 `worker_threads = 1` 时低层 `kernel apply 1.02x`、`step/read 1.03x`，训练 adapter 已到 `reset 1.03x / ms/env-step 1.15x`
- 最新 profile 下 batch reset 主链继续缩短到了约 `0.058 s`，但更长口径 benchmark 仍显示 reset 处于 `0.96x` 到 `0.97x` 的噪声区；这也正是该路线随后被归档的原因之一
- 定向 `load_compiled_scenario_batch` 口径下，reusable apply buffer 约 `1.02x`
- 最新 direct 口径下，`legacy layout build = 4.455673 ms`，`compiled layout build = 4.831221 ms`，`layout build speedup = 0.92x`
- 同时 benchmark 也表明这条链路现在不适合默认开大线程：`worker_threads = 4` 和 `auto(16)` 都比 `1` 更慢，因此新增 CPU 目前更适合先换成更高 `n_envs`
- 说明 Phase 4 已经从“只有 runtime 边界收口”推进到“真实 rollout 主链可用”，但 world lifecycle 和更粗粒度 batch 仍是当时未解决的主瓶颈
- 最新一轮 slim runtime-context 进一步把 batch direct path 的 `environment.zones` / 完整 `entities` clone 从 reset 主链里拿掉，并保留 route-generator 所需的显式 spawn context
- 这轮行为验证通过，但 benchmark 结果仍然显示 `reset 0.93x / step 1.14x`；因此 Phase 4 在这里停止继续微调，后续也未再作为独立主线继续推进

### Phase 5

拆掉 `LeaderTrainingEnv` 对 `UniversalEnv` 的嵌套依赖，改成统一多速率 runtime。

对应文档：

- [phase5_multirate_runtime.md](./phase5_multirate_runtime.md)

状态：

- 已归档，最后记录日期为 2026-03-22
- `LeaderTrainingEnv` 已新增外部 `execution_runtime` 注入口，不再强制自己构造并拥有一个 `UniversalEnv`
- 现有单环境路径继续通过 `_SingleExecutionRuntime(UniversalEnv(...))` 工作，行为保持兼容
- 已新增 `LeaderWorldBatchExecutionRuntimeGroup`，并让 `LeaderBatchedVecEnv` 可选注入 shared low-level `WorldBatchRuntime`
- leader observation 现在已复用 shared runtime 的 `inst/truth` 缓存，减少单 env kernel 状态回读
- leader command-chain 现在在 shared runtime 路径下支持 deferred sync：teacher/C2/leader 更新先改 loader，真正的 kernel 写回在 batch step 前统一执行
- `ScenarioLoader.get_mission_observation()` 与 `ScriptedC2TaskManager` 的关键 helpers 现在也能直接消费缓存 `truth/inst`；测试会显式阻止 shared-runtime 路径回退到 `sim.get_*`
- 当时的 `leader_perf_probe.py` 用于 Phase 5 对照；脚本现位于 [tools/diagnostics/leader_perf_probe.py](/home/void0312/CMO/tools/diagnostics/leader_perf_probe.py)，当前维护中的 CLI 已移除那批实验性参数
- 这轮已经把 visual execution obs 和 `MultiTimescaleActionWrapper` 接到了 shared runtime 主链上，`p5/p6/p7` 这类主力 execution config 现在能真正激活 `leader_world_batch_runtime`
- 真实 `p7` smoke 口径下，`4 env / 64 step` 已从 batched baseline 的 `15.5317 leader_fps` 提到 `16.5035 leader_fps`，约 `1.06x`
- 但同口径 `SubprocVecEnv` 仍约 `30.2315 leader_fps`，所以 Phase 5 只拿到了第一段真实收益，未达到替代多进程 leader 训练的门槛

### Phase 6

收口旧 Python 逻辑，保留薄适配层和验证工具。

对应文档：

- [phase6_thin_adapter.md](./phase6_thin_adapter.md)

状态：

- 已归档，最后记录日期为 2026-03-22
- Phase 5 中层路径继续扩张后，最新一轮更大切口仍未稳定越过主口径门槛，因此不再继续沿 `wrapper/info/command-chain` 的 Python 中层做局部优化
- 已新增统一 execution runtime adapter，在 [execution_runtime.py](/home/void0312/CMO/python/rl/execution_runtime.py) 收口 `reset_policy_state / prepare_action / finalize_step_result`
- `LeaderTrainingEnv` 现在不再直接依赖 `policy_env` 的 wrapper 细节；single-env runtime 和 shared runtime 也开始复用同一套 runtime hook 语义
- shared runtime 的 leader-specific `prepare/apply/reset/sync` 编排也已从 [leader_batched_vec_env.py](/home/void0312/CMO/python/rl/leader_batched_vec_env.py) 主循环搬到 [leader_world_batch_runtime.py](/home/void0312/CMO/python/rl/leader_world_batch_runtime.py)，vec-env 开始退回单纯调度层
- 这轮进一步把 shared leader step 生命周期的 `begin/live-collect/finish` 也搬进了 runtime group，`LeaderBatchedVecEnv.step_wait()` 不再直接知道 shared leader env 的 pending/live/finish 内部细节
- 这一步不宣称新增 wall-clock 收益；它当时的作用只是把继续削薄 Python ownership 所需的 runtime 边界先固定下来

## 5. 约束原则

### 5.1 不做“表面批处理”

如果只是把推理 batch 化，但 world stepping 仍逐 env 逐 Python 调度，不算完成重构目标。

### 5.2 不继续堆历史兼容层

短期可以保留过渡 API，但新 runtime 不能继续围绕旧 `ScenarioLoader` 设计。

### 5.3 先统一运行时，再讨论更大规模训练

在 world runtime 和命令链仍高度碎片化之前，单纯增加 `n_envs` 只会放大现有结构成本。

## 6. 评估方式

归档前，这轮重构要求每个阶段都同时给出：

- 结构变化
- 吞吐变化
- 行为一致性验证

最低验证口径：

- 合同测试不回退
- 关键 active 场景结果不回退
- 指定 probe 的 wall-clock 吞吐提升可量化

## 7. 当前结论

这轮重构的本质不是“继续优化训练参数”，而是：

- 把场景解释从运行时拆出去
- 把几何与任务热路径从 Python 拆出去
- 把 stepping 从单 world / 多进程模式改成 batch runtime
- 把 leader/execution 从 env 套 env 改成多速率控制 runtime

只有这样，速度提升才会从“百分之几”变成“架构量级”的变化。
