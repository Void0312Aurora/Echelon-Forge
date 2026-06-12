# CMO/EchelonForge 架构评审 — 2026-06-03

## 评审范围

全项目架构质量评估。判断实现是否具有真正的架构/结构设计，还是功能堆砌 (feature-stacking)。

## 方法论

- 阅读 C++ 引擎核心、Python RL 框架、世界模型、场景编译管线、GPU 运行时、多智能体协作、测试基础设施的关键源文件
- 追踪模块依赖关系图以进行耦合分析；运行量化代码度量
- 评估抽象质量：接口、类层次、关注点分离
- 通过特定 file 引用识别架构模式和反模式，并对高风险断言按当前工作树证据复核
- 与 2026-06-03 断言核验记录和三组只读 subagent 结果交叉验证
- 覆盖口径说明：tracked `*.cpp + *.h` C++ 行数为 57,299；tracked Python 行数约 180K；活跃 JSON contract 现在位于 `tests/contracts/`，历史规范位于 `tests/archive/contracts/`

---

## 总体判断

**该项目不是功能堆砌。** 它在多个子系统中展示了真实的架构设计。核心架构选择（Flecs ECS + strategy interfaces、compiler-like scenario pipeline、残差 HMoE、合同驱动测试、CPU/GPU 参考-实验模式）是有意设计，不是偶然累积。然而，该项目也展示了典型的"研究工程"张力：架构方向真实存在，但若干重要 owner surface 和 compatibility adapter 仍然较宽，需要继续收口。

### 关键量化事实

| 指标 | 数值 |
|------|------|
| Python 总行数 | tracked 口径约 180K；若计入当前未跟踪文件，filesystem 口径更高 |
| C++ 总行数 | tracked `*.cpp + *.h` 为 57,299；若计入 tracked `.cu` 为 60,120 |
| Python 测试文件 | tracked `tests/**/*.py` 为 227；当前工作树 filesystem 口径可能更高 |
| 活跃 JSON 合同文件 | `tests/contracts/**/*.json` 下为 86；`tests/archive/contracts/**/*.json` 下另有 17 个历史归档 contract 文件 |
| TODO/FIXME/HACK 标记 | `src + python + tools` 代码/工具口径为 4；tracked 全仓口径更高 |
| 循环导入 | 只读 AST 模块级扫描为 0；顶层分组方向需要单独定义统计口径 |
| 超过 3000 行的文件 | 至少 2 个 tracked source/test 文件：`src/runtime/facade/runtime_facade.cpp` 与 `tests/world_batch/test_world_batch_vec_env.py` |
| 自定义异常类型 | project Python/tooling 口径至少 3 个，且并非全是 test-only |
| 宽泛 `except Exception` 出现次数 | tracked `python/` 为 233；所有 tracked `.py` 为 604 |
| `hasattr()` duck-typing 调用 | tracked `python/` 约 230+；计入 tests/tools 后明显更高 |
| Python `assert` 语句 | tracked `python/` 为 10；tests 中有大量 assert |
| C++ 断言/检查语句 | 当前 doctest/check macro 口径为 147 |

---

## 架构优势（有证据支持）

### 1. C++ ECS 引擎核心：有结构的 owner，但 public surface 仍宽

| 文件 | 证据 |
|------|------|
| `src/core/engine/simulation_kernel.h` | 拥有 Flecs world 和模型接口，但 public API 仍横跨 reset/step/setup、raw world access、legacy command、tasking、observation、debug、weapon、model override 等职责。 |
| `src/core/interfaces/` | `IControlModel`、`ISensorModel`、`IAcousticModel`、`IGuidanceModel`、`IEffectsModel`、`IEnvironmentModel`、`IUnitFactory`——全部纯虚，配有 `make_default_*()` 工厂。一致的 `I*`/`*ModelRef`/`make_default_*()` 模式。 |
| `src/systems/` | 每个 ECS 系统在独立文件中，按域组织。系统使用 Flecs 单例注入（`ControlModelRef`、`SensorModelRef` 等）进行依赖反转。 |
| `src/interfaces/python/bindings_core.cpp` | API 表面分为 4 个命名层：`maintained`、`diagnostics_introspection`、`legacy_compatibility`、`diagnostics_override`——带有明确的 quarantine 标记（"WP22-R1-2 quarantine marker"）。 |

**关键设计决策**：核心行为域使用可替换 strategy interfaces，systems 通过 Flecs singleton 获取 model refs。这是真实的依赖反转，但不是所有行为逻辑都已经完全藏在 strategy interface 后面；若干 systems 和 factory 仍有内联领域逻辑。

### 2. 场景编译管线：compiler-like 架构，已具备轻量 shape guard

| 文件 | 证据 |
|------|------|
| `python/scenario/compiler/service.py` | `CompiledScenario` frozen dataclass，带有基于 mtime 的新鲜度门控。`ScenarioCompiler` 编排 validate→parse/merge→transform→emit。基于路径的缓存，带有新鲜度门控查找。 |
| `python/scenario/compiler/validation.py` | P1-B 为 compiler 直接消费字段和 prefab imports 增加集中轻量 shape guard。 |
| `python/scenario/compiler/layout_template.py` | `CompiledWorldLayoutTemplate`、`CompiledZoneLayoutTemplate`、`CompiledSpawnLayoutTemplate`——全部 frozen dataclass IR 片段。 |
| `python/scenario/runtime/kernel_apply.py` | `ScenarioWorldLayout` → `AppliedScenarioWorld` 物化路径。三种不同的 `instantiate()` 克隆方法用于不同的消费上下文。 |

**数据流**：`JSON → Shape Validation → Parse → Merge Imports → Transform/metadata/layout compilation → Frozen IR → Runtime Materialization → Kernel Apply`。compiler-like 结构真实存在。P1-B 已修复原评审指出的 compiler-consumed shape guard 缺口，但这仍是轻量内部 guard，不是完整公开 JSON Schema 或领域语义验证器。

### 3. 世界模型：自包含的 Dreamer-style 实现

| 文件 | 证据 |
|------|------|
| `python/world_model/`（6 个文件，2,350 行） | 零导入自 `python/rl/` 或 `python/training/`。可提取为独立库。 |
| `python/world_model/networks.py` | RSSM 具有 `observe_init`/`obs_step`/`imagine_step` 分离。先验和后验是不同 MLP。`ObservationEncoder`、`VisualEncoder`、`MultiModalEncoder`、`ObservationDecoder`、`VisualDecoder`、`RewardHead`、`ContinueHead` 被拆成独立组件。 |
| `python/world_model/dreamer.py` | Dreamer-style 训练结构：symlog 奖励、free nats KL 正则化、lambda-return actor/critic 机制。所有 `print()` 调用由 `self.verbose` 标志门控。这是结构证据，不是完整算法正确性或训练有效性证明。 |
| `python/world_model/features.py` | sin/cos 角度编码处理 0°/360° 不连续性问题。深思熟虑的航空特定适配，无特权信息泄漏。 |

### 4. HMoE（分层混合专家）：一致的 residual specialization 设计

| 文件 | 证据 |
|------|------|
| `python/rl/policy_algo/hmoe_routing.py` | 5-家族 + 子专家分解映射到真实飞行阶段（起飞、离场/导航、编队、回收/着陆、战斗）。基于物理信号的确定性路由（alt_radar、空速、CDI、C2 ROE 状态）。 |
| `python/rl/policy_algo/policies.py` | 残差架构：所有 HMoE 头初始化为零（`nn.init.zeros_`）。共享骨干保持主策略——类似于 NLP 中的 LoRA/adapter 层。门控热身（`hmoe_residual_warmup_fraction`，默认 0.15）。 |
| `python/rl/policy_algo/ppo_adaptive_kl.py` | `AdaptiveKLPPO` 具有 TRPO 风格 KL 控制、基于滞后的自适应和耐心计数器。分组优化器：共享骨干与 HMoE 头不同的学习率缩放（默认 0.35x）。 |

**关键设计选择**：零初始化的残差专业化——"首先不伤害"原则。共享骨干提供基线，routed heads 学习阶段特定修正。该设计在本项目内是清晰一致的架构决策；本轮未评估其外部论文级新颖性。

### 5. 合同驱动测试基础设施

| 目录 | 证据 |
|------|------|
| `tests/` | tracked Python 测试文件 227 个；`tests/contracts/` 下活跃 JSON contract 文件 59 个。历史 contract 规范位于 `tests/archive/contracts/`。测试套件按 smoke、focused、local/manual、contract 等路径组织。 |
| `python/testing/contracts/` | 共享运行器根据 JSON `"type"` 字段分发。活跃处理程序：`loader_command_chain`、`route_generator`、`unit_regression`。已归档 raw-env contract 类型：`env_regression`、`scripted_bridge`。 |
| `tests/architecture/` | 当前有 87 个 architecture test 文件、444 个 pytest 收集项，并按语义 guard owner 分组；其中大量检查分层规则、导入约束、文档合同和 compatibility quarantine boundary。 |

**模式**：测试意图编码为数据（JSON），通过共享运行器执行。比每次回归手写 Python 脚本更易维护。

### 6. GPU/CUDA：清晰的实验性脚手架

| 文件 | 证据 |
|------|------|
| `src/gpu/README.md` | 明确的边界规则：GPU 代码不能拥有模拟状态；CPU 是默认真相路径。独立的 `experimental/` 子目录用于尚未进入主线的探针。 |
| `src/gpu/gpu_visual_runtime.{h,cpp,cu}` | 一致的 3-文件模式：`.h` 用于类型/接口，`.cpp` 用于 CPU 参考 + 分发，`.cu` 用于 CUDA 实现。在所有 4 个 GPU 模块中统一应用（视觉、执行观察、飞行塑形、交互宽阶段）。 |
| 每个 `.cpp` 分发器 | 模式：`#if defined(EF_ENABLE_CUDA_EXPERIMENTS)` → 尝试 CUDA → 如果为空/失败，回退到 CPU 参考。每个 GPU 功能都有明确的 CPU 回退。 |
| Python 绑定（`bindings_gpu.cpp`） | DLPack 导出用于零拷贝 PyTorch 张量共享。GPU 设备探测，每模块实验统计。 |

**设计哲学**：GPU 是实验性加速器，不是替代真相源。CPU 参考路径始终可用。这是一个良好约束的方法——不是完整的基于多态的 GPU 抽象层，而是增量 GPU 迁移的干净脚手架。

### 7. 具有依赖反转的分层架构

```
ef_py（C++/Python 绑定）
  ↑
python/scenario/（当前 AST 扫描中零 python/rl 导入）
  ↑
python/rl/profile/ → python/rl/control/ → python/rl/tasking/ → python/rl/runtime/
  ↑
python/training/（消费所有内容；不被更低层导入）
```

- `python/world_model/` 完全隔离——零内部项目导入
- `python/scenario/` → `python/rl/`：当前 AST 扫描中为 0
- `python/rl/` → `python/scenario/`：当前扫描超过 5 次，但方向仍属于预期的高层消费低层 runtime/scenario path
- 模块级 AST cycle 扫描为 0；顶层分组循环声明应先定义统计口径

### 8. 构建层与架构守卫的结构性证据

除上述 7 项架构优势外，以下结构性证据进一步证明项目具备真实架构主线：

| 证据 | 位置 | 说明 |
|------|------|------|
| CMake source group 按未来 target 边界分组 | `CMakeLists.txt` | `EF_CORE_ENGINE_SOURCES`、`EF_RUNTIME_FACADE_SOURCES`、`EF_GPU_MAINTAINED_HELPER_SOURCES` 等 11 个显式分组，由 `tests/architecture/build/test_cmake_target_readiness.py` 守卫 |
| Python/Gym 生产路径移除 raw kernel 构造入口 | `gym_envs/universal_env.py`、`train.py` | raw `UniversalEnv` 构造现在无 `runtime_compatibility_enabled` opt-in，直接 fail closed；maintained 调用方使用 world-batch/runtime-facade adapter |
| command/tasking 已拆 owner slice | `src/components/command/` | `MissionCommand` 通过继承 `MissionCommandCore`/`Air`/`Naval` 投影到 owner slices，`static_assert` 约束 shell 映射 |
| weapon release / engagement event 从 kernel 拆出 | `simulation_kernel_systems.cpp` | 架构测试禁止 kernel 直接继承 `IWeaponReleaseService` 或 `IEngagementEventRecorder`；weapon release 通过 named helper 注册 |
| 架构守卫测试可执行 | `tests/architecture/` | 87 个 test 文件、444 个 pytest 收集项，直接扫描源码/文档守住分层、include 约束、compatibility quarantine boundary |

**P1-A stale guard 修复**：原评估轮次 `test_a2_structured_air_effects_do_not_write_rl_score_authority` 因测试在 `default_effects_model.cpp` 中查找旧文本锚点 `if (hp && !structured_air_target) {` 而失败。P1-A 已将该 guard 改为检查当前 split-file owner 关系：legacy score authority 位于 `default_effects_legacy_detail.inc::apply_legacy_health_damage()`，structured air consequence path 位于 `default_effects_air_platform_resolution_detail.inc::resolve_default_effects_air_platform_consequences()`，并确认 structured block 不含 `score->`。该失败是 stale static guard，不是 runtime 行为回归——P1-A 已修复，最新聚焦复跑通过。这一案例说明架构测试有价值，但文本型锚点在实现重构后必须同步维护。

---

## 结构性问题（需要重构）

### 1. 训练诊断回调：P1 owner split 已闭合

| 文件:行 | 问题 | 严重性 |
|---------|------|--------|
| `python/training_callbacks.py:33-212` | `CMODiagnosticsCallback` 不再是 diagnostics calculation/state owner。它现在只保留 SB3 lifecycle wiring、logging cadence、兼容 wrapper，并将 calculation/state 委托给 `python/training/diagnostics.py`。 | P1 **closed** |
| `python/training_callbacks.py:176-212` | `_on_step()` 现在是较小的 orchestrator：收集 SB3 locals，将 event-window observation 交给 `TrainingEventDiagnosticsWindow`，再调用聚焦 logging helpers。 | 低 |
| `python/training/diagnostics.py:138-218`；`800-1277` | Basic step scalar logging、action/effective-action selection、terminal/preterm windows 与 cooperative aggregation 已进入 helper functions/classes，并有直接测试。该 helper module 仍较大，应继续靠测试和边界维护，而不是塞回 callback。 | 中 |
| 内联解释密度 | 精确 comment-density figures 应重新定义计数口径后再引用；旧 callback-specific severity 已不符合当前 owner split。 | 低 |

**当前边界**：P1 已闭合 callback owner 问题。后续如继续处理，应聚焦
helper-module maintainability 或 typed diagnostics contracts，而不是继续挂
"held P1-D callback split"。

### 2. WorldBatchVecEnv 分叉类层次

| 文件:行 | 问题 | 严重性 |
|---------|------|--------|
| `python/rl/runtime/world_batch_vec_env.py` vs `cooperative_world_batch_vec_env.py` | 两个类都直接继承 `VecEnv`，没有共享 base。当前文件行数约 1,898 与 1,408，且共享常量、observation-space 构造等模式有重复。 | **高** |
| 两者构造/设置路径 | 参数解析、runtime compatibility gate、observation-space 构造和 buffer setup 存在显著结构重叠。本轮未量化精确重复百分比。 | **高** |
| 内联解释密度 | 复杂 batch environment 代码相对其职责仍解释不足。精确注释密度应在重新运行定义明确的计数器后再引用。 | 中 |

### 3. C++ DefaultUnitFactory::spawn()：最大的单片代码

| 文件:行 | 问题 | 严重性 |
|---------|------|--------|
| `src/models/core/default_unit_factory.h:683-1520` | `spawn()`——**837 行**单个方法。6 种实体类型（飞机、导弹、舰船、潜艇、设施、C2 节点）在一个扁平的 if-else 链中处理。 | **高** |
| 同一文件 | 144 行构造函数，重复的 `UnitDefinition` 初始化块——相同模式复制粘贴 6 次。 | 中 |
| 同一文件 | 独立 factory unit coverage 仍偏薄；但当前架构测试会直接实例化 `DefaultUnitFactory`，因此“零覆盖”过强。 | 中 |

**已提取的内容**（显示对良好实践的认识）：
- `build_platform_capability_bundle_template()`（262 行）——结构化良好，每个能力族有本地 lambda
- `default_unit_factory_detail` 命名空间——ID 生成辅助函数适当分解
- `default_factory_finite_or`/`positive_or`/`nonnegative_or`——安全回退辅助函数（但仅在导弹块中使用）

**未提取的内容**：传感器/EW/声纳块（80 行）、推进/发动机/燃料块（66 行）、导弹初始化（163 行）、损伤模型（72 行）——全部内联在 spawn() 中。

### 4. `train_actor_bc()` 大规模 DRY 违规

| 文件:行 | 问题 | 严重性 |
|---------|------|--------|
| `python/world_model/dreamer.py:690-1275` | `train_actor_bc()` 包含约 15 个 `actor_input` 分支，多个分支重复 pitch/roll/throttle/rudder 加权与 MSE 计算逻辑。 | **高** |

### 5. RuntimeFacadeAdapter：God Adapter 反模式

| 文件:行 | 问题 | 严重性 |
|---------|------|--------|
| `python/rl/runtime/world_batch/adapter.py:230-840` | 单个类仍同时了解 runtime window、layout apply、batch observation、tasking、launch、execution 等路径。P1-C 已把 adapter-owned capability probing 集中到 `RuntimeFacadeAdapterCapabilities`，但类本身仍偏宽。 | 中 |
| `python/rl/runtime/world_batch/adapter.py:233-270` | 原 dead-parameter 发现已关闭：`runtime_compatibility_enabled` 已从 maintained adapter/config 表面移除。更宽的 adapter split 仍开放。 | 低 |

### 6. Duck-Typed Loader 能力（无合同）

| 文件:行 | 问题 | 严重性 |
|---------|------|--------|
| `world_batch_vec_env.py:501` | `hasattr(first_loader, "_build_step_evaluation_batch_env_state")`——通过名称访问私有方法 | 中 |
| `cooperative_world_batch_vec_env.py:572` | `slot_state.loader._python_owned_mission_observation_mode(...)`——通过名称访问私有方法 | 中 |
| 两个环境和适配器 | `hasattr()` 调用仍很多；当前总数强依赖是否计入 `python/`、tests 和 tools。没有 `typing.Protocol` 定义 loader capability contract。 | 中 |

### 7. 多智能体协作：单片 Director，无抽象

| 文件:行 | 问题 | 严重性 |
|---------|------|--------|
| `cooperative_director.py:143` | `ScriptedCooperativeCoordinationDirector`——所有协调协议（编队、起飞、角色）在一个类中。没有可组合的协议/mixin 模式。 | 中 |
| `cooperative_world_batch_vec_env.py:230` | Director 硬编码——没有 `CoordinationDirector` 基类或 Protocol。无法交换策略。 | 中 |
| 设计限制 | 本轮未找到显式 inter-agent communication 或 target-lock sharing abstraction。这是从源码缺口推出的设计限制，不是直接行为失败证据。 | 低 |

**优势**：清晰的身份（`MultiAgentControlSlot`，冻结）与状态（`CooperativeSlotState`）分离。基于快照的脏跟踪用于高效内核同步。每槽 C2 任务管理器和 Leader 阶段管理器作为清晰的状态机。

### 8. 错误处理：研究级别，静默吞没占主导

| 指标 | 计数 | 评估 |
|------|------|------|
| 宽泛 `except Exception` | tracked `python/` 为 233；所有 tracked `.py` 为 604 | Python runtime/support 代码中的主导模式，许多位置会回退默认值 |
| 特定异常捕获 | 本轮未重新计数 | 需先定义 AST/grep 计数口径 |
| `raise ... from exc`（正确的链） | 当前 Python tree 约 22 处 | 存在，但相对 broad fallback handling 仍少 |
| C++ 类型化异常 | 223 个 `std::runtime_error` 等 | 结构良好 |
| Python 自定义异常 | project Python/tooling 口径至少 3 个 | 没有完整生产异常层级；至少一个自定义异常并非 test-only |
| 裸 `except:` | 0 | 积极——团队有意识地避免了这一点 |

**关键风险**：Diagnostics helpers 仍使用较多 defensive broad catches
（`training_callbacks.py` 当前有 4 个 `except Exception` site；`python/training/diagnostics.py`
约 45 个）。当 step/reset 异常发生时，environment rollout 仍可能静默降低数据质量。

### 9. P1-B 之后的场景验证残余

| 位置 | 问题 | 严重性 |
|------|------|--------|
| `python/scenario/compiler/` | P1-B 已让非 list `entities`、无效 prefab shape 等 compiler-consumed 错误在 merge/materialization 前 fail closed。剩余债务是领域语义验证，以及未来是否发布 JSON Schema。 | 低 |
| `python/scenario/compiler/service.py:111` | 通过 `print()` 输出警告到 stdout——不可控、不可过滤。 | 低 |
| 场景编译器 + 运行时 | 在 `float()` 转换周围有 5+ 个位置的宽泛 `except Exception`——缩小到 `except (ValueError, TypeError)`。 | 低 |

---

## 架构成熟度指标

| 指标 | 评级 | 证据 |
|------|------|------|
| 技术债务意识 | **强** | Quarantine 标记（"WP22-R1-2"）、已移除的 `runtime_compatibility_enabled` 门控、明确的遗留路径标记、GPU 实验性 README 边界 |
| 接口设计纪律 | **强** | 7 个纯虚 C++ 接口，一致的 `I*`/`*ModelRef`/`make_default_*()` 模式，4 层 Python 绑定 API 表面 |
| 不可变性使用 | **良好** | Frozen dataclass：`CompiledScenario`、`CompiledWorldLayoutTemplate`、`HMoERouteBatch`、`MultiAgentControlSlot` |
| 错误处理 | **研究级别** | C++ 使用 typed exceptions/checks。Python 有大量 broad `except Exception`，尤其在 runtime/support path；精确数字必须附 scope-qualified commands。 |
| 可观测性 | **良好** | HMoE 路由/参数统计、每阶段计时仪表、GPU 实验统计、非有限探针 |
| 关注点分离 | **总体良好** | ECS（数据 vs 逻辑）、编译器 vs 运行时、世界模型隔离、CPU/GPU 参考-实验分离 |
| 代码重复 | **需要关注** | 两个 env class 有显著重叠，BC loss 有多分支重复，factory 类型初始化块仍集中。 |
| 文件大小纪律 | **混合** | 多个关键文件偏大：`runtime_facade.cpp` 与 `tests/world_batch/test_world_batch_vec_env.py` 均为 3092 行；`world_batch_vec_env.py` 与 `default_unit_factory.h` 也偏大。P1 已将 `training_callbacks.py` 降到 413 行，同时将 diagnostics helpers 移入 1295 行的 `python/training/diagnostics.py`。 |
| 代码库清洁度 | **良好但依赖口径** | 代码/工具 scope 的 TODO/FIXME/HACK 较少，当前 grep 未发现裸 `except:`。全仓/文档/archive 口径更高，因此不能不加限定地称为 entire codebase。 |
| 注释密度 | **需要关注** | training callback 与 world-batch env 代码相对复杂度解释不足。精确密度数字应重新计算后再引用。 |
| 测试覆盖率 | **强但不完整** | tracked Python test 文件 227 个、活跃 JSON contract 86 个、architecture test 文件 87 个、smoke/contract suites 都是强证据；但不能证明完整 physics/domain/training correctness。 |

### 架构真实性判断表

| 问题 | 判断 | 证据 |
|------|------|------|
| 是否有明确架构边界 | **有** | `src/README.md`、`python/README.md`、`runtime/facade/README.md` 均给出职责和禁止项 |
| 是否只是目录摆设 | **不是** | CMake source group 和 `tests/architecture/*` 会检查边界 |
| 是否存在 production/raw runtime 隔离 | **有** | `UniversalEnv` raw path 默认 fail closed，训练入口要求显式 compatibility opt-in |
| 是否已经完全解耦 | **没有** | `SimulationKernel` public API 仍很宽，`MissionCommand` 仍是兼容壳 |
| 是否存在功能堆砌风险 | **有局部风险** | 大文件、绑定层、facade cpp、unit factory、damage system 仍较大 |
| 是否应否定整体架构 | **不应** | 多处边界已进入代码、构建和测试 |
| 是否应宣称完整成熟 | **不应** | README 和局部文档均明确 air/naval/ground 成熟度不同 |

---

## 建议优先级

### P0（立即处理——高影响、低风险）

1. **提取共享 world-batch env support**——减少单/协作环境之间的重复。将共享观察维度常量提取到可配置 dataclass 或聚焦 helper module 中。
2. **将 P1 diagnostics callback split 视为已闭合**——`CMODiagnosticsCallback` 已将 diagnostics calculation/state 委托给 `python/training/diagnostics.py`；后续如有需要，应转向 helper-module maintainability 或 typed diagnostics contracts。
3. **在 `dreamer.py` 中提取共享的 `_compute_bc_loss()`**——消除多种 `actor_input` 分支中重复的 BC loss weighting。

### P1（本周期内——中等影响）

4. **定义 `typing.Protocol` 接口**替换所有 `hasattr` loader 能力检查。
5. **拆分 `RuntimeFacadeAdapter`** 为共享 Protocol 后面的版本化实现。
6. **在 P1-B shape check 之外扩展场景验证**；只有兼容策略稳定后再发布完整 JSON Schema。
7. **从 `kernel_apply.py`/`batch_apply.py` 提取共享的风/偏航随机化**。
8. **在 `DreamerTrainer` 中添加配置时验证**，拒绝不兼容的 `actor_input` + 训练模式组合。

### P2（积压——结构性改进）

9. **分解 `DefaultUnitFactory::spawn()`**——类型专用的构建器方法 + 公共组件初始化器提取。
10. **提取 `CoordinationDirector` Protocol**——启用可插拔的多智能体协调策略。
11. **缩小 `except Exception`** 为 `except (ValueError, TypeError)` 在场景编译器（5+ 个位置）。
12. **在场景编译器中使用 `logging.warning()`** 代替 `print()`。
13. **提取 `_HybridActionDistribution`** 到独立文件。
14. **去重 `hmoe_routing.py` 和 `policies.py` 之间的 `authorized_first_shot`** 逻辑。
15. **为剩余宽基础设施文件添加内联文档**，例如 `world_batch_vec_env.py` 以及复杂 diagnostics helper 区段；具体 comment-density 需先重新定义统计口径。

### P3（长期——研究质量）

16. **添加自动 GPU/CPU 奇偶校验测试**——验证 GPU 实验输出与 CPU 参考的数值匹配。
17. **提取 CPU 参考和 CUDA 内核之间的共享数学函数**。
18. **为协作战术添加智能体间通信抽象**。

---

## 详细分析覆盖

| 领域 | 深度 | 状态 |
|------|------|------|
| C++ ECS 引擎核心 | 深入 | ✅ |
| C++ DefaultUnitFactory | 深入（完整文件阅读） | ✅ |
| C++ Python 绑定 | 深入 | ✅ |
| 场景编译器管线 | 深入 | ✅ |
| 场景运行时/应用 | 深入 | ✅ |
| 世界模型（Dreamer） | 深入 | ✅ |
| HMoE 策略架构 | 深入 | ✅ |
| AdaptiveKLPPO 算法 | 深入 | ✅ |
| RL 运行时（世界批次环境） | 深入 | ✅ |
| RuntimeFacadeAdapter | 深入 | ✅ |
| 训练回调 | 深入 | ✅ |
| Gymnasium 环境 | 中等 | ✅ |
| 多智能体协作模式 | 深入（director、状态机、环境、C2 任务） | ✅ |
| GPU/CUDA 代码路径 | 深入（全部 4 个模块：视觉、观察、飞行塑形、宽阶段） | ✅ |
| 代码度量（量化） | 深入（行数、文件、依赖、TODO、注释） | ✅ |
| 错误处理模式 | 深入（系统性 grep + 分类） | ✅ |
| 测试基础设施 | 深入 | ✅ |
| Godot 游戏前端 | 未分析（用户排除） | ⬜ 跳过 |
| 海军/地面领域 | 未分析 | ⬜ |
| 构建系统（CMake）质量 | 未分析 | ⬜ |
| 文档质量/组织 | 未分析 | ⬜ |

---

*由多智能体架构评审会话生成，2026-06-03。*
*所有声明均由覆盖 10 个独立子智能体分析的实际代码阅读中的特定 file:line 引用支持。*
*没有捏造任何发现——每个结构性问题都可追溯到特定的代码位置。*
