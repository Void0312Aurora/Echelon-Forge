# Echelon Forge 架构结构性实现评估记录

**评估日期：** 2026-06-03
**仓库：** `/home/void0312/Workshop/CMO`
**评估主题：** 判断当前实现是否具备架构/结构性实现，而不是随机功能堆砌。
**工作树说明：** 本记录基于当前工作区只读分析与一次聚焦架构测试执行。工作树同时存在其它 Agent 或人工改动；本记录不接管、不归档、不修改那些变更。

---

## 1. 结论

当前实现不是单纯乱堆功能。更准确的判断是：

> 项目已有明确的分层架构、领域成熟度边界、runtime/facade 收口方向、兼容路径隔离机制，以及一批直接扫描源码/文档的架构守卫测试；但它仍处于持续迁移阶段，`SimulationKernel` 宽公共接口、大文件、大兼容壳等结构债仍然真实存在。

因此不能把它描述为“已经完全优雅拆分完成”，也不应把它描述为“没有架构、只是功能堆叠”。当前状态属于“架构主线成立，但历史宽接口和兼容层还在被逐步收窄”。

---

## 2. 结构性实现证据

### 2.1 仓库层入口已经明确项目边界

`README.zh.md` 明确将项目定义为多域仿真与强化学习工作台，包含 C++ ECS 内核、Python 绑定、场景编译/运行时、Gymnasium 环境、批量 rollout、协作训练、评估诊断与契约回归工具。该描述与目录结构一致，至少说明项目不是单一实验脚本集合。

同一入口还明确声明：

- 本仓库是活跃研究/工程代码库，不是完整产品发布。
- CPU runtime 是规范 world-step 真值。
- GPU 路径存在，但应谨慎对待。
- Air/execution、Cooperative、Naval、Ground、Air combat、Visualization/game、Model/world-model 的成熟度不同。

这类成熟度边界是结构性工程的正面证据：项目没有把所有存在的目录都宣传成已完成能力。

### 2.2 `src/` 具备明确依赖方向与目录职责

`src/README.md` 给出了维护中的依赖方向：

```text
interfaces/python
  -> runtime/facade
    -> core/engine and core/mission
      -> systems
        -> models / components / content

gpu
  -> core/runtime data packets or systems-visible packets
  -> no ownership of canonical world-step truth
```

同一文档把 `components/`、`systems/`、`models/`、`content/`、`core/`、`runtime/`、`interfaces/`、`gpu/` 的职责分别列出，并禁止为了 include 路径方便而把 command/tasking/mission/runtime/binding 逻辑塞进宽目录。

这不是单纯“看起来有目录”。这些规则已经被测试和 CMake 结构部分执行。

### 2.3 CMake 已按未来 target 边界分组

`CMakeLists.txt` 中存在如下显式 source group：

- `EF_CORE_ENGINE_SOURCES`
- `EF_CORE_GEOMETRY_SOURCES`
- `EF_CORE_MISSION_RUNTIME_SOURCES`
- `EF_CORE_MISSION_EPISODE_SOURCES`
- `EF_CORE_MISSION_EPISODE_DETAIL_SOURCES`
- `EF_RUNTIME_FACADE_SOURCES`
- `EF_MODEL_DEFAULT_SOURCES`
- `EF_CONTENT_SOURCES`
- `EF_PYTHON_BINDING_SOURCES`
- `EF_GPU_MAINTAINED_HELPER_SOURCES`
- `EF_GPU_EXPERIMENT_SOURCES`

`tests/architecture/test_cmake_target_readiness.py` 会检查这些 source group 存在，并要求 `add_library(ef_core STATIC)` 与 `nanobind_add_module(ef_py)` 消费分组变量，而不是重新退化成扁平文件列表。

这说明构建层也在为结构边界服务。

### 2.4 `RuntimeFacade` 是真实收口点

`src/runtime/facade/runtime_facade.h` 只 include `runtime/facade/runtime_facade_types.h`，对 `WorldBatchRuntime` 使用前向声明，并在 private 区域持有 `std::unique_ptr<WorldBatchRuntime>`。

对应 README 明确说明：

- facade 是维护中的 C++ 应用层 API。
- facade 使用 typed request/result，避免暴露底层 world owner 细节。
- 不应盲目复制 `WorldBatchRuntime` 低层 API。
- 不得重新引入 `RuntimeFacade.runtime_compatibility_quarantine()`。
- 不应缓存 raw `WorldBatchRuntime`。

`tests/architecture/test_runtime_facade_layering.py` 直接测试这些边界，包括：

- `RuntimeFacade` header 不应暴露 `runtime_compatibility_quarantine`。
- runtime contract/facade type headers 不应 include `core/engine/*`。
- facade public header 不应 include `core/engine/world_batch_runtime.h`。
- world-batch adapter 不应构造 raw `ef_py.WorldBatchRuntime`。
- scenario runtime 生产路径不应构造 raw `ef_py.SimulationKernel` 或 `ef_py.WorldBatchRuntime`。

这是“架构边界进入自动化守卫”的强证据。

### 2.5 Python/Gym 生产路径隔离 raw kernel

`gym_envs/universal_env.py` 中 raw `ef_py.SimulationKernel` 路径默认关闭；未显式传入 `runtime_compatibility_enabled=True` 会抛出错误，提示使用 `WorldBatchVecEnv/RuntimeFacadeAdapter`。

`train.py` 也在非 world-batch 路径中检查 `env.runtime_compatibility_enabled`，未显式启用时拒绝进入 raw `UniversalEnv` 路径。

这说明 Python 训练主线不再默认绕开 facade/adapter 直接抓 kernel，属于真实的结构性收口。

### 2.6 command/tasking 已开始拆 owner slice

`src/components/command/README.md` 明确说明 command 侧已从 `air + ship` 粗糙分法转为 `common + air + naval`：

- `common` 承载跨域 command transport 和 shared execution intent。
- `air` 承载成熟 aviation execution surface。
- `naval` 承载 ship/maritime command slice。
- `ground command` 尚未成为维护中的 C++ command slice。

`src/components/command/mission_command.h` 中的 `MissionCommand` 仍是 flat compatibility shell，但它通过继承 `MissionCommandCore`、`MissionCommandAir`、`MissionCommandNaval` 投影到 owner slices，并用 `static_assert` 约束 shell 必须映射到显式 owner slices。

这是一种兼容期设计，而不是把所有域字段无说明地堆到一个结构里。

### 2.7 weapon release / engagement event 已有从 kernel 拆出的结构

`tests/architecture/test_wp22_structural_guardrails.py` 对 weapon release 和 engagement event 的拆分做了大量源码级断言，例如：

- `simulation_kernel_systems.cpp` 不应继续堆 inline OnUpdate weapon release 系统。
- `PilotWeaponRelease` 和 `NavalMissionWeaponRelease` 应通过 named helper 注册。
- `SimulationKernel` 不应继承 `IWeaponReleaseService` 或 `IEngagementEventRecorder`。
- engagement event state 应进入 `SimulationKernelEngagementEventStore`。
- weapon release service 不应持有 `SimulationKernel&`。

这些守卫说明，项目已经在主动拆除“kernel 直接包办所有事”的旧结构。

---

## 3. 结构债与不应过度美化的部分

### 3.1 `SimulationKernel` public surface 仍然很宽

`src/core/engine/simulation_kernel.h` 的 public 区域仍同时包含：

- reset / step / exact stage trace
- spawn / raw `get_world()`
- database / terrain / wind / maritime setup
- legacy command API
- pilot action / mission command / task order / leader intent / pilot report
- observation / sensor / instrument / debug view
- weapon fire / debug damage
- model override / unit definition loading

虽然已有 `SimulationKernelCommandSurface` 和若干 service/store 拆分，但 kernel 仍是重要的结构债中心。后续不能仅靠“已有 facade”就宣布 kernel 公共面问题完全解决。

### 3.2 大文件仍然存在

本轮用 `wc -l` 抽查，仍有多个大文件：

| 文件 | 行数 |
| --- | ---: |
| `src/runtime/facade/runtime_facade.cpp` | 3092 |
| `src/interfaces/python/bindings_runtime.cpp` | 2487 |
| `python/rl/runtime/world_batch_vec_env.py` | 1898 |
| `src/content/unit_definition_loader.cpp` | 1686 |
| `src/models/core/default_unit_factory.h` | 1580 |
| `src/systems/combat/damage_system.h` | 1525 |
| `python/training_callbacks.py` | 1346 |
| `src/runtime/contracts/world_batch_contracts.h` | 1316 |
| `src/core/engine/world_batch_runtime.cpp` | 1285 |

这不等于“乱实现”，但说明架构收口尚未完成，仍需继续拆职责、拆 facade 方法组、拆绑定和 loader。

### 3.3 `MissionCommand` 是兼容壳，不是完全域解耦

`src/components/command/README.md` 自身承认 `MissionCommand` 仍是高风险 consumer convergence point，并且“shared shell + a lot of air payload”的特征仍在。

因此 naval/ground 相关评估必须区分：

- 能运行/能过测试
- 是否已拥有独立 domain owner surface
- 是否还借用了 air-shaped compatibility shell

### 3.4 `default_effects_model` 已模块化，但仍是大翻译单元

当前 `src/models/weapons/default_effects_model.cpp` 已经把大量逻辑放入 `models/weapons/detail/default_effects_*.inc` 私有片段。`.cpp` 本身可读性明显改善，并且注释说明这些 fragment 是匿名 namespace 内部实现片段。

但 `.cpp + detail/*.inc` 合计仍然是一个很大的 default effects 翻译单元。它是“已经被模块化的复杂实现”，不是“完全拆分完成的小模型”。

### 3.5 架构测试曾存在 stale guard，P1-A 已修复

原评估轮次执行聚焦架构测试：

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q \
  tests/architecture/test_cmake_target_readiness.py \
  tests/architecture/test_runtime_facade_layering.py \
  tests/architecture/test_wp22_tasking_bridge_retirement.py \
  tests/architecture/test_wp22_structural_guardrails.py
```

结果：

```text
75 passed, 1 failed
```

失败项：

```text
tests/architecture/test_wp22_structural_guardrails.py::test_a2_structured_air_effects_do_not_write_rl_score_authority

后续 `engineering_governance_p1` 已将该 guard 改为检查当前 split-file
ownership：legacy score authority 位于
`default_effects_legacy_detail.inc::apply_legacy_health_damage()`，structured
air consequence path 位于
`default_effects_air_platform_resolution_detail.inc::resolve_default_effects_air_platform_consequences()`，
并确认 structured block 不含 `score->`。该项现在是已修复历史发现，而不是当前
architecture test blocker。
```

失败原因不是运行时行为直接失败，而是测试仍在 `default_effects_model.cpp` 中寻找旧文本锚点：

```python
text.index("if (hp && !structured_air_target) {")
```

当前实现已经变为：

```cpp
if (hp && !structured_air_target &&
    apply_legacy_health_damage(target_entity, missile, score, *hp)) {
    return result;
}
```

legacy score 写入迁移到了 `src/models/weapons/detail/default_effects_legacy_detail.inc` 的 `apply_legacy_health_damage()`；structured air platform consequence 路径在 `default_effects_air_platform_resolution_detail.inc` 中处理。也就是说，测试的静态锚点需要同步到新结构。

这条失败反而说明：架构测试很有价值，但如果依赖文本切片，也必须随着结构重构维护，否则会把“实现已重构”误报成“结构回归”。

---

## 4. 真实判断表

| 问题 | 判断 | 证据 |
| --- | --- | --- |
| 是否有明确架构边界 | 有 | `src/README.md`、`python/README.md`、`gym_envs/README.md`、`runtime/facade/README.md` 均给出职责和禁止项 |
| 是否只是目录摆设 | 不是 | CMake source group 和 `tests/architecture/*` 会检查边界 |
| 是否存在 production/raw runtime 隔离 | 有 | `UniversalEnv` raw path 默认 fail closed，训练入口要求显式 compatibility opt-in |
| 是否已经完全解耦 | 没有 | `SimulationKernel` public API 仍很宽，`MissionCommand` 仍是兼容壳 |
| 是否存在功能堆砌风险 | 有局部风险 | 大文件、绑定层、facade cpp、unit factory、damage system 仍较大 |
| 是否应否定整体架构 | 不应 | 多处边界已进入代码、构建和测试 |
| 是否应宣称完整成熟 | 不应 | README 和局部文档均明确 air/naval/ground 成熟度不同 |

---

## 5. 后续建议

1. **持续减少脆弱文本锚点。**
   P1-A 已修复 `test_a2_structured_air_effects_do_not_write_rl_score_authority`。后续新增或维护 architecture tests 时，应优先检查符号、include、函数签名、禁止调用和 owner 文件位置，而不是依赖整段旧代码形状。

2. **继续缩窄 `SimulationKernel` public surface。**
   已有 command/read surface 是正确方向。下一步可以按 Observation、Weapon、Debug/Diagnostics、Setup 分组继续做非破坏性 surface。

3. **为 `RuntimeFacade` 准备方法组拆分。**
   当前 facade header 仍承载 setup、execution、observation、tasking、engagement、diagnostics、counterfactual 等多组能力。可按 README 中 Session/Setup/Execution/Observation/Diagnostics/Engagement/Capability 分组规划下一轮拆分。

4. **把“能运行”和“领域 owner 完成”分开评估。**
   Naval/Ground 尤其需要保持这个口径：测试通过只能证明某个 slice 可用，不等于完整 naval/ground domain runtime 成熟。

5. **保留架构测试，但持续校准锚点。**
   对必须用文本扫描的守卫，应优先检查符号、include、函数签名、禁止调用和 owner 文件位置，并在代码拆分后及时更新 guard 证据。

---

## 6. 本轮未做事项

- 未修改 `docs/evaluation/archive/` 下已有归档材料。
- 未处理当前工作树中 air combat、policy、training callback 等其它改动。
- 未修复 failing 架构测试；这里只记录发现与判断。
- 未运行完整 smoke/contract suite；仅运行了与本评估主题直接相关的架构测试子集。
