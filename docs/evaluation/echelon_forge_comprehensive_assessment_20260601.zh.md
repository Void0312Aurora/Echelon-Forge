# Echelon Forge 综合评估报告

**评估日期：** 2026-06-01
**仓库：** `/home/void0312/Workshop/CMO`
**分支：** `main` (HEAD: `8609078`)
**评估方法：** 同时分析文档声明与代码实现的一致性，覆盖 C++ 引擎、Python RL 框架、测试基础设施、文档体系四个维度。

**二次核验：** 2026-06-01 由 C++、Python/RL、测试/文档三组 subagent 只读复核，并在本轮修复后更新明显失准的数字和状态。

---

## 1. 项目全景

### 1.1 规模数据

| 维度 | 数据 |
|------|------|
| C++ 源码 | ~63,000 行 (`.cpp`/`.h`/`.cu`) |
| Python RL 框架 | ~33,800 行 (`python/` 目录) |
| Python 测试 | ~72,800 行 (218 个 `.py` 文件) |
| Python 总量 (含 gym_envs/tools) | ~174,700 行 |
| JSON 契约文件 | ~103 个 |
| 文档 (Markdown) | 250+ 个文件 |
| 场景 | 47 个 JSON 场景文件 (takeoff/cruise/landing/naval/ground/air_combat/combined) |
| 实验记录 | 29+ 个目录 (checkpoints/logs) |

### 1.2 项目身份

Echelon Forge 是一个**研究/工程层面的多域军事仿真与强化学习工作台**，而非商业化产品。其 README 直言不讳："本仓库是一个活跃的研究/工程代码库，并非完善的产物发布。" 这一自我认知贯穿于文档和实现的各个层面。

**命名层次：**
- 人向标识：Echelon Forge
- CMake 标识：`EchelonForge`
- Python 包标识：`cmo`（遗留，保持兼容性）
- C++ 绑定模块：`ef_py`

---

## 2. C++ 引擎层评估

### 2.1 架构设计

**ECS 架构 (flecs v4.0.0)：** 选用工业级 ECS 框架是合理决策。组件类型丰富（53个头文件，涵盖 basic/combat/command/physics/systems/tasking/naval/visual），系统管线清晰（physics → combat → systems → visual 的分层执行）。

**核心类 `SimulationKernel`（[src/core/engine/simulation_kernel.h](src/core/engine/simulation_kernel.h)）：**
- 478 行头文件，229 行实现——职责集中但不算过度膨胀
- 采用策略模式注入模型：`IEffectsModel`、`ISensorModel`、`IAcousticModel`、`IControlModel`、`IGuidanceModel`、`IEnvironmentModel`
- `MissileTuning` 结构体（约 45 个成员字段）属于数据导向设计，但字段较多且多用 `NaN` 做默认值，存在可维护性隐患
- `exact_stage_inventory.cpp` 暗示存在精确的阶段追踪机制——这是正确性保障的关键基础设施

**子系统管线：**
- `simulation_kernel_systems.cpp` 注册所有 ECS 系统
- 已识别的系统：燃油消耗、空气动力学、力清除、力聚合、控制、仪表、蛙跳积分、地面接触、运动、旋转、传感器、数据链、电子战、声纳、导航、指挥链、损伤、制导、武器释放、后勤、舰船运动、潜艇运动、舰载机作业、视觉

**GPU 路径（[src/gpu/](src/gpu/)）：**
- 4 个 `.cpp` 实现 + 4 个 `.cu` CUDA 文件
- 5 个 `phase0_probe` 可执行文件——明确标记为实验性
- `EF_ENABLE_CUDA_EXPERIMENTS` 编译选项默认为 `OFF`
- 设计合理：CPU 路径始终作为规范真值保留，GPU 为可选加速路径

### 2.2 C++ 层健康评分：5/10

C++ 引擎层在架构概念上设计良好（清晰的 ECS 分层、依赖反转、GPU 侧车模式），但在实现纪律方面存在明显短板：

| 问题 | 严重度 | 说明 |
|------|--------|------|
| **缺少 C++ 单元测试框架/CTest** | **严重** | 未发现 Google Test/Catch2/doctest/CTest 注册；存在 `ef_app`、GPU probe 和 Python 测试中的临时 C++ 编译片段，但没有项目级 C++ 单元测试网 |
| **`default_unit_factory.h` 1,580 行** | **中** | 仍是较大的 header，内含默认单位工厂实现和定义表；此前“71,908 行”断言不属实 |
| **`SimulationKernel` God-class** | **高** | 478 行头文件，公共 API 粗略超过 90 项，横跨多个 API 表面 |
| **`default_effects_model.cpp` 4,805 行** | **高** | 单一文件包含所有弹头类型、爆轰/破片/聚能/侵彻计算、组件级失效概率 |
| **README 文件清单口径不一致** | **中** | `src/` 多个子目录 README 与同目录源文件不完全对应；“12 个文件”不可复现且偏低 |
| **系统实现主要 header-only** | **中** | `src/systems/combat/damage_system.h` 1,487 行全部内联——任何修改触发较大范围重编译 |
| **组件头文件含算法逻辑** | **低** | `damage.h` 中有 `derive_aircraft_damage_from_component_state` 等内联函数 |
| **魔法数字** | **低** | 气动/损伤系统中硬编码阈值（如 `0.06, 0.12, 0.03`） |

### 2.3 Python 绑定 (nanobind)

**绑定模块（[src/interfaces/python/](src/interfaces/python/)）：**
- `python_module.cpp`：顶层 `NB_MODULE(ef_py, m)` ，分发到 5 个子模块
- `bindings_command.cpp`、`bindings_core.cpp`、`bindings_episode.cpp`、`bindings_runtime.cpp`、`bindings_gpu.cpp`
- `binding_utils.h` 提供共享工具
- `dlpack_minimal.h` 支持与 PyTorch 的零拷贝张量互操作——这是高级 RL 集成能力

### 2.4 模型层

**默认模型实现（[src/models/](src/models/)）：**
- `default_effects_model.cpp`：武器效果
- `default_sensor_model.cpp`：传感器
- `default_acoustic_model.cpp`：声学
- `default_environment_model.cpp`：环境
- `default_control_model.cpp`：控制
- `default_guidance_model.cpp`：制导
- `missile_guidance_math.h` + `missile_guidance_types.h`：导弹制导数学库
- `naval_weapon_mounts.h`：海军武器挂载点

所有模型都通过接口抽象注入到 `SimulationKernel` 中，符合依赖反转原则。

### 2.5 组件设计 ([src/components/](src/components/))

**领域覆盖广度：**
- `combat/damage.h`：结构化损伤模型，包含 `DamageComponent`、`DamageComponentDependency`、`Hitbox`——支持组件级损伤与依赖级联
- `combat/health.h`：生命值
- `combat/weapon.h`：武器
- `naval/`：舰船平台、潜艇平台、舰载机作业
- `tasking/`：空中/海军/通用任务分配与报告

损伤组件设计值得特别指出：支持 `redundancy_group`、`armor_mm`、`threshold_scale`、`mechanism_threshold_scales`——这是一个较为精细的损伤建模基础设施。

### 2.6 C++ 层存在的问题

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **严重** | **缺少 C++ 单元测试框架/CTest** | 无项目级 C++ 单元测试框架；验证主要通过 Python 集成测试、Python 中临编 C++ snippet、demo/probe 间接完成——物理/损伤重构的回归风险仍高 |
| **高** | **`SimulationKernel` God-class** | 公共 API 粗略超过 90 项，涵盖命令/观察/武器/视觉/损伤调试/交战事件——任何重构都有级联中断风险 |
| **高** | **`default_effects_model.cpp` 4,805 行** | 单一文件：爆轰/破片/聚能/侵彻+组件失效概率+脆弱性剖面+证据溯源——不可分解 |
| **中** | `MissileTuning` 结构体约 45 个字段，多用 NaN 默认 | 难以区分"未设置"与"有意设为零" |
| **中** | 系统文件刻意放在 `src/systems/systems/` | 目录名与父目录重复，README 已承认此问题 |
| **中** | `default_unit_factory.h` 1,580 行 | 较大的 header 内含工厂实现与默认单位定义；不是 71,908 行巨型数据库，但仍可考虑后续分离 |
| **中** | README 文件清单口径不一致 | `src/` 多个子目录 README 不保证列全同目录源文件；需先明确 README 是否承担完整清单职责 |
| **中** | 系统实现主要 header-only | `src/systems/combat/damage_system.h`（1,487 行）全内联——任何修改触发较大范围重编译 |
| **低** | `main.cpp` 仅含 24 行 demo 代码 | 有 `ef_app` 和 GPU probe，但没有独立 C++ 单元测试入口 |
| **低** | CUDA 文件缺少 C++/CTest 级测试覆盖 | Python 绑定层已有 `tests/test_gpu_runtime_bindings.py` 部分覆盖；CUDA kernel/probe 缺少原生测试网 |
| **低** | 组件头文件包含算法逻辑 | `damage.h` 中有内联函数（可接受但偏离纯数据原则） |
| **低** | 字符串匹配的组件分派 | `damage_dependency_system_name_matches()` 用 `std::string::find()` 做子串匹配——脆弱 |
| **低** | 魔法数字 | 气动/损伤系统中硬编码阈值（如 `0.06, 0.12, 0.03`） |
| **信息** | `src` 下 3 个 TODO，均在 `logistics_system.h` | Python/gym 路径未命中 TODO/FIXME；C++ TODO 并非只有 1 个 |

---

## 3. Python RL 框架层评估

### 3.1 架构分层

Python 框架遵循清晰的关注点分离：

```
env_config → taxonomy → profile → tasking → bridge → runtime → vec_env → policy
```

**关键模块一览：**

| 模块 | 职责 | 质量评级 |
|------|------|----------|
| `env_config.py` | CLI args + train_config → 扁平 env settings | ★★★★★ |
| `mission_obs_taxonomy.py` | 所有观察模式的定义、维度、索引 | ★★★★★ |
| `rl/profile/{air,naval,ground}_profile.py` | 领域特定的任务命令构建 | ★★★★☆ |
| `rl/tasking/bridge.py` | 运行时配置文件调度 | ★★★★★ |
| `rl/tasking/leader_tasking.py` | 基于规则的 C2 任务管理器 | ★★★★☆ |
| `rl/runtime/world_batch_vec_env.py` | 单进程批量执行环境 | ★★★★★ |
| `rl/runtime/cooperative_world_batch_vec_env.py` | 多智能体协同批量执行 | ★★★★★ |
| `rl/policy_algo/policies.py` | HMoE + SquashedMultiInputPolicy | ★★★★★ |
| `rl/policy_algo/ppo_adaptive_kl.py` | TRPO风格自适应KL PPO | ★★★★★ |
| `rl/support/nonfinite_probe.py` | NaN/Inf 检测与诊断 | ★★★★★ |

### 3.2 关键设计亮点

1. **Law 14 合规（agent_shim.py）：** 生产/maintained 消费者只能读取 `facade_observation_packet` 和 `decision_belief_packet`；raw/privileged 信息保留为 `diagnostics_only`，不得冒充 maintained 面。这是一个经过深思熟虑的安全边界。

2. **legacy 隔离：** 需要显式传入 `runtime_compatibility_enabled=True` 才能使用旧的 `SimulationKernel` 直接路径。编译路径是新代码的默认路径。

3. **编译观察批处理：** `ef_py.compute_execution_observation_batch_numpy` 将观察构建从 Python 移到 C++，避免逐样本的 Python 开销。

4. **SharedMemorySubprocVecEnv：** 通过 `multiprocessing.shared_memory` 在父子进程间传递 Dict 观察，绕过了 pickle 瓶颈。这是对 SB3 默认实现的真实性能改进。

5. **HMoE 路由：** 确定性的任务观察 → 专家家族映射，残差公式（共享主干 + 每专家的差异头）。设计优雅。

6. **NonFiniteProbe：** 一个完整的 NaN/Inf 调试工具，遍历策略/价值/特征网络参数、激活和梯度。在生产 RL 系统中极其宝贵。

### 3.3 Python 层存在的问题

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **中** | `wrappers.py` (~50KB) 和 `leader_tasking.py` (~53KB) 过大 | 单体文件难以维护 |
| **低** | `world_model/` 生产集成程度需核验 | 子包并非骨架，已有 Dreamer/RSSM/replay 等实质实现；仍需确认它在当前训练主线中的权威程度 |
| **低** | `Any` 类型在 C++ 边界大量使用 | 不可避免但削弱类型安全 |
| **低** | 地面配置文件标记为 "兼容性外壳" | G1 阶段尚未定义地面指挥语义 |
| **信息** | Python/gym 路径零 TODO/FIXME | 或反映预提交清理纪律；C++ 层另有 `logistics_system.h` 的 TODO |

---

## 4. 测试基础设施评估

### 4.1 测试规模与结构

| 指标 | 值 |
|------|-----|
| 测试文件总数 | 218 |
| 测试函数 | ~1,372 |
| `unittest.TestCase` 子类 | 95 |
| JSON 契约文件 | ~103 |
| 总测试代码行数 | ~72,800 |
| CI smoke 覆盖 | 仅 9 个路径 |

### 4.2 测试分层

```
tests/architecture/   (441 函数 — 元测试/架构守卫)
tests/runtime/        (核心运行时集成测试，按域组织)
tests/world_batch/    (批量执行系统测试 — 最高质量的一批)
tests/scenario/       (场景编译/加载测试)
tests/leader/         (领导者/分层RL测试)
tests/training/       (训练基础设施测试)
tests/hmoe/           (HMoE 路由测试)
tests/eval/           (评估测试)
tests/contracts/      (JSON契约 — 声明式、数据驱动)
```

### 4.3 测试质量亮点

1. **确定性：** 固定种子（`seed=20260526`、`seed=41`）普遍使用，无随机性
2. **精确断言：** 广泛使用 `assertAlmostEqual(..., places=6)`
3. **架构守卫：** `tests/architecture/` 扫描源文件以强制执行分层约束——在重构后防止回归
4. **契约测试：** 103 个 JSON 文件构成声明式测试层——测试不写代码即可添加
5. **极佳的可追溯性：** 测试名称包含工作包标识符（`test_wp5_`、`test_wp9_`）
6. **WorldBatch 系统测试：** ~3,000 行，覆盖视觉确定性、命令链导出、影子比较、错误处理

### 4.4 测试质量问题

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **高** | CI smoke 仅覆盖 9 个路径 | 相对于 218+103 个测试资产的极薄烟雾层 |
| **中** | 无项目级 `conftest.py` | 无共享 fixture/参数化——夹具通过导入共享 |
| **中** | 架构测试大量使用"源码扫描器" | `tests/architecture/` 共有 441 个测试函数，其中大量/多数为源码或文档扫描式守卫——有价值但脆弱 |
| **中** | 风格不一致 | `unittest.TestCase` 与纯 `def test_*` 混用 |
| **低** | 无覆盖率配置 | 无 `.coveragerc`/`pyproject.toml` 覆盖率节 |
| **低** | 文档测试脆弱 | 检查 Markdown 文件中的确切措辞 |
| **低** | eval 覆盖不足 | 整个评估子系统仅有 11 个测试函数 |
| **低** | GPU 原生测试不足 | Python 绑定层有部分覆盖；缺少 C++/CTest 级 CUDA/probe 验证 |

---

## 5. 文档体系评估

### 5.1 总体评级：优秀

文档系统的**权限框架**是见过的最佳实践。每个文档类别（plan/task/standards/agent/manual/forward/Archive）都有明确定义的权威边界和过期规则。

### 5.2 结构

```
docs/
├── standards/      (联合/服务/域标准 — 最成熟的文档层)
├── task/           (16 条工作线，按域和生命周期组织)
├── plan/           (架构/运行时外观/协同计划)
├── agent/          (AI agent 面向的表面)
├── manual/         (维护者/操作员手册)
├── forward/        (未排期的积压)
├── book/           (外部参考 PDF)
├── log/            (日志摘要保留说明)
├── Archive/        (历史文档)
└── evaluation/     (本次评估)
```

### 5.3 关键优势

1. **权限层级：** foundation → joint → services → domain 的四层所有权金字塔
2. **成熟度标签：** G0-G7 现实梯度防止能力超卖
3. **双语策略：** A/B/C 层级模型，务实且定义明确
4. **agent 表面：** 为 AI agent 提供专用文档（提示模板、权限映射）
5. **高引用完整性：** 测试的 30+ 个引用全部有效

### 5.4 已知问题复核 (来自 2026-05-18 审计)

**P1 复核状态：**
1. `c2_communication.md` — 本轮已修复错误文件路径，并将不存在的 `PendingCommand` 改为实际的 `PendingMovementCommand` / `PendingActionCommand` / `PendingMissionCommand` 表述。
2. `rl_selfplay.md` — 本轮已移除对不存在的 `examples/training/train_self_play.py` 与 `examples/training/selfplay_config.json` 的已实现声明。
3. `landing_task_notes.md` / `takeoff_to_cruise_mixedmode_notes.md` — 当前维护文档未再复现 `/home/void0312/CMO/` 根路径错误。

**P2（~33 项）：** 各类疏漏、过期标签、编辑问题

### 5.5 新发现的问题

| 严重度 | 问题 | 说明 |
|--------|------|------|
| **已修复** | `docs/book/` 缺 README | 本轮新增中英文 README，说明第三方 PDF 的权威边界和权利核验要求 |
| **已修复** | `docs/log/` 为空 | 本轮新增中英文 README，说明日志摘要保留规则 |
| **已修复** | `docs/forward/temp/` 未记录 | 本轮新增中英文 README，说明 7 组 temp 笔记配对的草稿属性与权威边界 |
| **低** | `simulation_architecture/README.md` 1,152 行 | 过于冗长 |

---

## 6. 关键跨领域发现

### 6.1 实现与文档一致性

**总体：良好。** 代码和文档之间的对应关系维持在较高质量。但有重要例外：

| 方向 | 状态 |
|------|------|
| C++ 源文件在 README 中的映射 | **部分** — 多个 README 与同目录源文件不完全对应；需先明确 README 是否应承担完整清单职责 |
| Python README 列出的模块 | **部分** — 7 个模块未列入 |
| 标准声明 ↔ 代码实现 | **大部分一致** — `air/obs.md` 描述的是理想而非实际暴露的内容 |
| 前向文档声称的实现 | **已修复主要 P1** — `rl_selfplay.md` 与 `c2_communication.md` 的错误实现声明已在本轮收回/改准 |
| 测试 README 描述的目录结构 | **过时** — `tests/diagnostics/` 声称有脚本但只有 README |

### 6.2 代码质量一致性

**C++ ↔ Python 质量差异：**
- C++ 层：良好的 ECS 架构、策略模式、接口抽象。但 `MissileTuning` 的 NaN 默认值、`src/systems/systems/` 目录名重复等细节问题偏多。
- Python 层：极高的代码纪律——Python/gym 路径零 TODO/FIXME、一致的错误消息格式、深思熟虑的隔离机制。质量略高于 C++ 层。

### 6.3 领域成熟度演进

与 [README.zh.md](README.zh.md) 中声明的成熟度快照对比：

| 领域 | 文档声明 | 代码证据 | 评估 |
|------|----------|----------|------|
| Air/execution | "最成熟的运行时" | 场景数量多、训练线路完备、测试丰富 | **一致** |
| Cooperative | "活跃集成主线" | WorldBatch/Cooperative 环境实现完整 | **一致** |
| Naval | "活跃领域...武器/毁伤结果仍是后续工作" | 场景+测试存在，武器释放路径有限 | **一致** |
| Ground | "早期 tasking/runtime bootstrap" | 地面配置文件明确标记为引导程序 | **一致** |
| Air combat/A2 | "聚焦的战斗与高保真毁伤模型工作线" | 深度嵌套的校准文档+对应测试 | **一致** |
| Visualization/game | "探索性" | Godot 已归档，Arma 桥接存在但极小 | **一致** |
| Model/world model | "策略/模型侧规划" | HMoE 已实现，`python/world_model/` 已有 Dreamer/RSSM/replay 实现，但主线集成权威仍需核验 | **部分一致** |

### 6.4 开发模式分析 (基于 git 历史)

最近 30 个提交显示：
- **高强度迭代：** 平均每天多次提交
- **领域拆分：** "Split naval domain surface adapters" — 有意识的多域重构
- **文档纪律：** `docs:` 前缀的提交占 ~20%
- **特性模式：** `feat:` → `chore:` → `docs:` 的三段式推进
- **无 `fix:` 提交：** 可能意味着修复被合并到 `chore:` 或 `feat:` 中

---

## 7. 优先级分级改进建议

### P0 — 应立即处理

1. **添加 C++ 测试框架：** 缺少 C++ 单元测试框架/CTest 是最大系统性风险——至少需要 `SimulationKernel` 的 reset/step/spawn 烟雾测试
2. **把本轮 P1 文档修复纳入审计收口记录：** `c2_communication.md`、`rl_selfplay.md` 与 manual 路径复核结果需要在后续审计状态页中关闭或重新定级

### P1 — 高优先级

1. **拆分 `SimulationKernel` 公共接口：** 按关注点分离（CommandAPI、ObservationAPI、WeaponAPI 等）为聚焦的 API 对象
2. **分解 `default_effects_model.cpp`：** 4,805 行单体文件拆分为 warhead/fuze/vulnerability/component 子模块
3. **扩展 CI smoke 套件：** 当前仅 9 个路径——应覆盖至少 50 个关键测试 + 10 个 JSON 契约
4. **添加项目级测试配置：** 创建 `conftest.py`、pytest 参数化、覆盖率配置
5. **将架构测试与行为测试分离：** `tests/architecture/` 中大量源码/文档扫描式守卫应独立运行

### P2 — 中优先级

1. **拆分大型 Python 文件：** `wrappers.py`（50KB）、`leader_tasking.py`（53KB）
2. **明确 src/ README 文件清单策略：** 若 README 承担文件清单职责，应批量补齐；否则应改成边界说明，避免被误读为完整清单
3. **将 header-only 系统移到 `.cpp`：** `damage_system.h`（1,487 行）和 `aerodynamics_system.h` 的内联逻辑移到实现文件
4. **提取魔法数字：** 气动/损伤系统中的硬编码值改为命名常量或可调配置
5. **核验 `world_model/` 的主线集成状态：** 该子包已有实质实现，后续问题是权威入口、测试覆盖和训练线路是否清晰
6. **统一测试风格：** 选择 `unittest.TestCase` 或纯 pytest 函数风格
7. **维护 `docs/log/` 和 `docs/forward/temp/` 说明：** 本轮已补 README，后续需保持临时材料不被误读为实现权威

### P3 — 低优先级

1. **添加 GPU 路径的 smoke 测试**
2. **为 C++ `MissileTuning` 添加字段验证/文档**
3. **考虑重命名 `src/systems/systems/`**
4. **为 `realism_authority_boundary.zh.md` 生成英文版本**
5. **拆分 `simulation_architecture/README.md` 的 1,152 行为活跃+归档两部分**

---

## 8. 总体结论

**Echelon Forge 是一个在研究/工程质量方面超乎寻常的项目。** 它在多个维度上展示了值得称赞的工程实践：

| 维度 | 评级 | 说明 |
|------|------|------|
| C++ 引擎 | ★★★☆☆ | ECS 分层架构优秀，但缺少 C++ 单元测试框架/CTest、4.8k 行单体损伤模型、header-only 系统和 God-class 内核——实现纪律逊于设计概念 |
| Python RL 框架 | ★★★★★ | 生产级质量——Law 14 安全边界、编译批处理路径、完善的 KL 自适应 |
| 测试基础设施 | ★★★★☆ | 覆盖全面、确定性、架构守卫——但 CI 烟雾层过薄、风格不一致 |
| 文档体系 | ★★★★★ | 权限框架是实践中的最佳水平——清晰、务实、引用完整 |
| 构建系统 | ★★★★☆ | CMake + FetchContent 配置干净，CUDA 可选；`default_unit_factory.h` 是 1,580 行较大 header，但不是 71k 行巨型文件 |
| 跨领域一致性 | ★★★☆☆ | 文档与代码大体一致——但 C++ 与 Python 的质量不对称明显，README 文件清单口径需统一，本轮已修复主要 P1 前向文档错误 |

**核心优势：**
- 文档权限框架防止了夸大声明——每个文档都知道自己的权威边界
- 现实梯度标签（G0-G7）使成熟度透明化
- "路径A"渐进式现代化模式（legacy → compiled → GPU）是务实的架构演进策略
- Law 14 生产安全边界是深思熟虑的 RL 工程
- 测试可追溯性（工作包标识符）提供了与需求的直接映射
- Python 层代码纪律极高——Python/gym 路径零 TODO/FIXME、一致的错误消息、完善的隔离机制

**核心改进空间：**
- **缺少 C++ 单元测试框架/CTest**——这是最大系统性风险，物理/损伤重构缺少 C++ 级单元测试安全网
- **`SimulationKernel` God-class**（公共 API 粗略超过 90 项）和 **`default_effects_model.cpp`**（4,805 行单体）需要分解
- CI 烟雾层覆盖过窄（9/321+ 个测试资产）
- 2026-05-18 审计中的主要 P1 前向文档不一致已在本轮修复，后续需要同步审计状态
- C++/Python 质量不对称——Python 层代码纪律优于 C++ 层
- 部分大型 Python 文件需要拆分
- GPU 路径缺少 C++/CTest 级测试覆盖，Python 绑定层已有部分测试
- 架构元测试（441 个测试函数，其中大量为源码/文档扫描式守卫）与行为测试混在一起

**最终评估：该项目处于活跃的健康演进状态——但 C++ 引擎层存在不容忽视的技术债务。** 已知文档问题有追踪（2026-05-18 审计），近期提交显示有意识的多域重构和文档维护。

**最大系统性风险（按严重度排序）：**
1. **缺少 C++ 单元测试框架/CTest**——63,000 行 C++ 代码缺少项目级 C++ 单元测试安全网，许多验证通过 Python 间接进行
2. **`default_effects_model.cpp` 4,805 行 + `damage_system.h` 1,487 行**——损伤管线单体化、全内联，校准变更极易出错
3. **CI 烟雾层过窄（9/321+ 资产）**——大多数测试从未在 CI 中运行
4. **`SimulationKernel` God-class**——公共 API 粗略超过 90 项，耦合多个 API 表面
5. **README 文件清单口径不一致**——多处文档无法明确区分边界说明与完整源文件索引

Python RL 框架是该项目最成熟的资产（5/5），文档体系是实践中的最佳水平（5/5），但 C++ 引擎层（3/5）需要系统性的测试引入和模块分解投入才能维持长期可维护性。
