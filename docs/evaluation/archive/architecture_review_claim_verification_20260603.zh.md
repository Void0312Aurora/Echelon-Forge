# Echelon Forge 架构审阅文档断言核验记录

**核验日期：** 2026-06-03
**仓库：** `/home/void0312/Workshop/CMO`
**核验对象：** `docs/evaluation/` 下 2026-06-03 架构审阅文档，以及归档的 2026-06-01 综合评估。
**核验目标：** 确认这些文档中关于架构、子架构、结构性问题、行业规范符合度与实现正确性的论述是否有当前代码证据支持。

## 0. 工作树与核验方式

当前工作树有并行 Agent 或人工改动，尤其 `python/rl/policy_algo/`、`python/training_callbacks.py`、`python/rl/runtime/world_batch_vec_env.py`、`docs/evaluation/` 等文件存在未提交变化。本记录不回滚、不覆盖这些变更，只记录本轮可复现证据。

本轮使用了三组只读 subagent 核对：

- **Socrates**：复算 `architecture_review_20260603.*` 的量化指标。
- **Kepler**：逐项核对 `Structural Problems` 是否属实。
- **Erdos**：核对架构优势、行业规范与正确性表述是否过满。

同时本地复跑了聚焦测试与 C++ smoke：

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q \
  tests/architecture/build/test_cmake_target_readiness.py \
  tests/architecture/runtime_facade \
  tests/architecture/command_tasking/test_tasking_bridge_guardrails.py \
  tests/architecture/structural_boundaries \
  tests/runtime/facade/test_runtime_facade.py \
  tests/runtime/core/test_world_setup_compat.py \
  tests/runtime/mission/test_mission_command_split_semantics.py \
  tests/runtime/mission/test_mission_command_naval_fields_roundtrip.py \
  tests/runtime/ground/test_ground_native_platform_schema.py \
  tests/runtime/naval/test_ship_naval_station_command.py
```

结果：

```text
129 passed, 1 failed
```

唯一失败仍为：

```text
tests/architecture/structural_boundaries/test_domain_separation_boundaries.py::test_a2_structured_air_effects_do_not_write_rl_score_authority
ValueError: substring not found
```

失败原因是测试仍在 `src/models/weapons/default_effects_model.cpp` 查找旧文本锚点 `if (hp && !structured_air_target) {`。当前实现已把 legacy health damage 写入迁移到 `src/models/weapons/detail/default_effects_legacy_detail.inc`，因此这是 stale static guard，而不是本轮样本中的 runtime 行为失败。

**P1 更新（2026-06-04 追踪）：** `engineering_governance_p1` 已修复该 guard，使其检查当前 split-file owner 关系；最新聚焦复跑 `tests/architecture/structural_boundaries` 通过。P1-D 也已将 `CMODiagnosticsCallback` 的 diagnostics calculation/state owner 拆出：basic step scalars、policy-distribution、HMoE、action、leader、step reward、A6 event-window info、A5 event info、runway/gear、terminal/preterm windows 与 cooperative aggregation 均进入 `python/training/diagnostics.py` helper，callback 现在保留 SB3 lifecycle 适配与 wrapper。

C++ smoke：

```bash
cmake --build build-workshop --target ef_test -j2
ctest --test-dir build-workshop -R ef_test_all --output-on-failure
```

结果：

```text
100% tests passed, 0 tests failed out of 1
```

## 1. 总体核验结论

`architecture_structure_assessment_20260603.zh.md` 与 `architecture_norms_correctness_review_20260603.zh.md` 的主判断整体可信：项目不是功能堆砌，已有明确分层、facade 收口、兼容隔离、架构守卫测试、C++ model interface、scenario compiler、GPU truth boundary 与 domain ownership 文档；但 `SimulationKernel`、facade、bindings、world-batch adapter、unit factory、training callback 等结构债仍真实存在。

`architecture_review_20260603.md` 与 `architecture_review_20260603.zh.md` 的方向多数成立，但有两类问题：

1. **量化表中多项没有写明口径，部分当前不可复现。**
2. **部分优势措辞过满。** 例如 `Clean Orchestrator`、`Correct Dreamer Implementation`、`all behavioral logic behind strategy interfaces` 应改成更克制的表述。

归档的 `archive/echelon_forge_comprehensive_assessment_20260601.zh.md` 作为背景材料基本与当前审阅方向一致，尤其已经承认 `SimulationKernel` 公共面仍宽、C++ test coverage 仍薄、`default_effects_model` 已模块化但仍是大翻译单元。它不应被当作当前唯一数字来源。

## 2. 量化断言核验

以下表格主要核对 `architecture_review_20260603.*` 的 `Key Quantitative Facts`。这些数字在当前工作树会随并行改动轻微漂移，因此本表重点记录口径。

| 指标 | 文档值 | 当前核验结果 | 判断 |
| --- | ---: | --- | --- |
| Python 总行数 | 180,166 | `git ls-files -z '*.py'` 口径约 180k；filesystem 口径约 181k，且工作树有未跟踪 `.py` | **口径缺失/轻微不一致** |
| C++ 总行数 | 57,299 | `git ls-files -z '*.cpp' '*.h'` 可复现 57,299；若计入 `.cu` 为 60,120 | **成立，但需注明排除 CUDA / `.inc`** |
| Python test files | 227 | tracked `tests/**/*.py` 为 227；filesystem 为 231 | **tracked 口径成立** |
| JSON contract files | 86 | `tests/contracts/**/*.json` 排除 `Archive/` 为 86；`tests/contracts` 全部为 103 | **成立，但需注明排除 Archive** |
| TODO/FIXME/HACK | 4 | `src + python + tools` 为 4；tracked 全仓为 15 | **数字可复现，但“entire codebase”措辞不成立** |
| Circular imports | 0 | subagent AST 模块级 SCC 扫描为 0；但顶层分组存在 `scenario` 与 `scenario_compiler` 双向关系 | **模块级成立，顶层口径需限定** |
| Files exceeding 3000 lines | 0 | 当前 tracked source/json 口径至少 2 个：`src/runtime/facade/runtime_facade.cpp` 与 `tests/world_batch/test_world_batch_vec_env.py` 均为 3092 行 | **不成立** |
| Custom exception types | 2 test-only | 当前可见至少 `NonFiniteProbeError`、`ContractSkipped`、`NonFiniteTraceError` 三个；且 `NonFiniteProbeError` 不是 test-only | **不成立** |
| Broad `except Exception` | 221 | `python/` tracked 当前为 233；all tracked `.py` 当前为 604 | **不成立/口径缺失** |
| `hasattr()` | 231 | `python/` tracked 当前约 233；all tracked `.py` 接近 490+ | **接近但口径缺失** |
| Python `assert` | 14 | `python/` tracked 当前为 10；all tracked `.py` 为 5492 量级 | **不成立/口径缺失** |
| C++ assertion/check | 126 | doctest/check macro 口径当前为 147 | **不成立/口径缺失** |

可复现命令示例：

```bash
git ls-files -z '*.cpp' '*.h' | wc -l --files0-from=- | awk '/ total$/ {print $1}'
git ls-files -z '*.cpp' '*.h' '*.cu' | wc -l --files0-from=- | awk '/ total$/ {print $1}'
git ls-files 'tests/contracts/**/*.json' 'tests/contracts/*.json' | rg -v '/Archive/' | wc -l
git grep -n -E 'TODO|FIXME|HACK' -- src python tools | wc -l
git grep -n -E 'TODO|FIXME|HACK' -- . ':!docs/evaluation/architecture_review_20260603.md' | wc -l
git grep -n -E '\bexcept[[:space:]]+Exception\b' -- 'python/**/*.py' 'python/*.py' | wc -l
git grep -n -E '\bhasattr[[:space:]]*\(' -- 'python/**/*.py' 'python/*.py' | wc -l
git grep -n -E '^[[:space:]]*assert\b' -- 'python/**/*.py' 'python/*.py' | wc -l
git grep -n -E '\b(CHECK|CHECK_FALSE|REQUIRE|REQUIRE_FALSE|ASSERT|EXPECT)[A-Za-z_]*[[:space:]]*\(' -- '*.cpp' '*.h' | wc -l
git ls-files -z '*.py' '*.cpp' '*.h' '*.json' | xargs -0 wc -l | awk '$1 > 3000 {print}'
```

## 3. 架构优势断言核验

| 文档断言 | 当前判断 | 核验证据 |
| --- | --- | --- |
| C++ ECS core 是 clean orchestrator，不是 God Object | **需降级** | `src/core/engine/simulation_kernel.h` 确实持有 strategy models 并注册 ECS systems，但 public API 同时覆盖 reset/step/setup、raw `get_world()`、legacy command、tasking、observation、debug、weapon、model override 等。它是有架构收口方向的 broad owner，不是已经干净的小 orchestrator。 |
| C++ strategy interfaces 与 Flecs singleton injection | **大体成立** | `src/core/interfaces/` 中存在 `IControlModel`、`ISensorModel`、`IAcousticModel`、`IGuidanceModel`、`IEffectsModel`、`IEnvironmentModel`、`IUnitFactory` 等接口；`simulation_kernel_systems.cpp` 注册并 `ecs.set<*ModelRef>`，systems 用 `it.world().get<*ModelRef>()` 读取。但“所有行为逻辑都在 strategy interface 后面”过满，系统与 factory 仍有大量内联领域逻辑。 |
| Scenario compiler 是 compiler-like pipeline | **成立但有缺口** | `python/scenario/compiler/service.py` 有 frozen `CompiledScenario`、mtime freshness cache、merge/metadata/layout template 编译；`layout_template.py` 有 frozen layout IR；runtime materialization 存在。缺口是主 `compile_*` 路径没有统一 schema validation stage，仍有默认值吞吐、`print()` warnings 与 broad `except Exception`。 |
| `python/world_model/` isolation | **成立** | `python/world_model/` 当前 6 个 `.py` 文件约 2351 行，只导入自身包与 torch/numpy/dataclass 等，不依赖 `python/rl` 或 `python/training`。 |
| Dreamer implementation 是 correct | **需降级** | RSSM prior/posterior、`observe_init` / `obs_step` / `imagine_step`、symlog reward、free nats、lambda-return 都存在；但本轮没有证明数学等价、训练有效性或所有 actor/BC 分支正确。应称为 Dreamer-style implementation with structural evidence。 |
| HMoE residual zero-init / adaptive KL | **成立** | `hmoe_routing.py` 有 5-family + subexpert routing；`policies.py` 中 residual heads `nn.init.zeros_`，有 warmup gate 和 HMoE head LR scale；`ppo_adaptive_kl.py` 有 target KL、自适应倍率与 patience。 |
| Contract-driven tests | **成立但数字需限定** | `python/testing/contracts/__init__.py` 根据 JSON `type` 分发到 `loader_command_chain`、`route_generator`、`env_regression`、`unit_regression`、`scripted_bridge`；`tests/architecture` 当前有 86 个 `test_*.py` 文件、442 个 test 函数。contract JSON 数字应说明是否排除 `Archive/`。 |
| GPU/CUDA scaffold | **成立但不能外推正确性** | `src/gpu/README.md` 明确 CPU `SimulationKernel::step()` 是 default truth path；`EF_ENABLE_CUDA_EXPERIMENTS` 默认 OFF；4 个 GPU 模块均有 `.h/.cpp/.cu`，`.cpp` 有 CPU reference/fallback；bindings 有 DLPack/device/stats。不能据此宣称 GPU/CPU 完整语义等价。 |
| Python layered dependency direction | **大体成立但计数错误** | AST 抽查显示 `python/scenario -> python/rl` 为 0，`world_model` 不依赖 `rl/training`，lower layers 不导入 `python.training`。但 `python/rl -> python/scenario` 不是文档写的 5 次，本轮扫描超过 5 次。 |
| RuntimeFacade / quarantine / fail-closed | **成立但 facade/adapter 已变宽** | `runtime_facade/README.md` 禁止 raw escape hatch；`world_setup.py` maintained setup 拒绝 raw runtime-shaped target；`gym_envs/universal_env.py` raw `SimulationKernel` 默认 fail closed；`train.py` 非 world-batch 路径要求显式 opt-in。保留问题是 `runtime_facade.cpp` 3092 行、`RuntimeFacadeAdapter` 813 行，仍接近继续拆分阈值。 |

## 4. 结构性问题断言核验

`architecture_review_20260603.*` 的 `Structural Problems` 大方向多数成立，但多处精确数字和绝对化描述需要修正。

| 结构问题 | 当前判断 | 修正口径 |
| --- | --- | --- |
| `CMODiagnosticsCallback` 是 god class | **原问题已由 P1-D 闭合** | `python/training_callbacks.py` 中该类当前为第 33-212 行，`_on_step()` 为第 176-212 行，主要负责 SB3 lifecycle、log cadence 和 wrapper 调度。`python/training/diagnostics.py:138-218` 负责 basic step/action array helper，`TrainingEventDiagnosticsWindow` 位于 `python/training/diagnostics.py:800-1277`，负责 terminal/preterm 与 cooperative/stateful event-window state。聚焦训练诊断测试当前 17 passed。后续可继续关注 helper module maintainability，但不应再把 callback split 作为 held P1。 |
| `WorldBatchVecEnv` 与 cooperative env 分叉 | **基本成立** | 两者均直接继承 `VecEnv`，没有共享 base，常量与 observation space 构建有重复。但当前 `cooperative_world_batch_vec_env.py` 为 1408 行，不是约 2000 行；70-80% 结构同一性没有被本轮量化证明。 |
| `DefaultUnitFactory::spawn()` 单片实现 | **成立** | `src/models/core/default_unit_factory.h:683` 开始的 `spawn()` 仍跨传感器、声纳、mass/propulsion、missile runtime、damage、datalink、logistics 等职责。文档中“zero unit test coverage”应降级，因为架构测试会直接实例化 `DefaultUnitFactory`，但缺少独立工厂单元测试网的判断仍合理。 |
| `train_actor_bc()` DRY 问题 | **成立** | `python/world_model/dreamer.py:690` 开始的 `train_actor_bc()` 确实按多种 `actor_input` 重复 pitch/roll/throttle/rudder 加权与 MSE 计算。当前分支数约 15，不是 13。 |
| `RuntimeFacadeAdapter` god adapter + dead parameter | **已部分收敛** | P1-C 让 `runtime_compatibility_enabled` 成为 adapter capability snapshot 的显式字段，并把多处 facade/binding probing 收敛到 `RuntimeFacadeAdapterCapabilities`。类仍同时处理 runtime window、layout apply、observation/tasking/execution 等，因此更宽的 adapter split 仍未完成。 |
| loader duck typing / private method | **成立** | `world_batch_vec_env.py` 与 `cooperative_world_batch_vec_env.py` 仍通过 `hasattr` 和 `_build_step_evaluation_batch_env_state`、`_prepare_step_evaluation`、`_python_owned_mission_observation_mode` 等私有能力探测/调用。`hasattr` 总数需重新按口径计。 |
| cooperative director 单片 / 无 Protocol | **基本成立** | `ScriptedCooperativeCoordinationDirector` 单类处理 formation、role metadata、takeoff、slot apply 等；`cooperative_world_batch_vec_env.py` 硬编码创建该 director。无 `Protocol` 基类属实。无 target-lock / communication abstraction 属于从源码缺口推出的设计限制，应标为推断。 |
| Python broad exception / silent fallback | **问题成立，数字不成立** | `except Exception` 确实广泛存在；P1 后 `training_callbacks.py` 只剩少量 callback/curriculum/early-stop defensive catches，诊断侧主要集中到 `python/training/diagnostics.py`。world-batch env、scenario compiler/runtime 仍有 silent fallback。`bare except:` 为 0 是积极事实。但 `raise ... from exc` 不是 2，本轮核对为 22 量级。 |
| 缺少 centralized scenario validation | **已由 P1-B 部分修复** | 主 `ScenarioCompiler.compile_*` 路径现在有轻量 shape guard，非 list `entities` 和无效 prefab shape 会 fail closed。剩余问题是领域语义验证、公开 JSON Schema 与 warning 输出策略，而不是原来的“缺少 compiler-consumed shape validation”。 |

## 5. 对其它评估文档的可信度判断

### 5.1 `architecture_structure_assessment_20260603.zh.md`

总体可信。它的核心判断是“不是功能堆砌，但也不能宣称完全优雅拆分完成”，这与本轮源码、架构测试和 subagent 核对一致。

该文已经正确记录了：

- `SimulationKernel` public surface 仍宽。
- 大文件仍存在，且 `runtime_facade.cpp` 与 `test_world_batch_vec_env.py` 超过 3000 行。
- `MissionCommand` 仍是兼容壳。
- `default_effects_model` 已模块化但仍是大翻译单元。
- 聚焦架构测试曾存在 stale guard；P1-A 已修复，后续应继续减少脆弱文本锚点。

建议保留该文基调，只需后续随工作树漂移更新具体行数。

### 5.2 `architecture_norms_correctness_review_20260603.zh.md`

总体可信，且比英文/中文 `architecture_review_20260603.*` 更克制。它明确把“架构边界正确性、构建 smoke、facade 合同、domain slice、复杂物理/传感器/武器正确性、RL 训练有效性、发布级可复现”分层，这符合本轮核验结果。

该文的一个关键优点是没有把已通过的 slice 测试外推为整体仿真正确性。建议保留其“分级确认”的主线。

### 5.3 `architecture_review_20260603.md` / `.zh.md`

方向多数可信，但需要修订。建议优先改以下几类表述：

- 把 `C++ ECS Engine Core: Clean Orchestrator, Not God Object` 改为“ECS + strategy-interface owner with broad public surface under active narrowing”。
- 把 `World Model: Self-Contained, Correct Dreamer Implementation` 改为“Self-contained Dreamer-style implementation; training correctness not fully verified here”。
- 把 `Evidence-Backed` 与 `Key Quantitative Facts` 中的数字改成带命令口径的表格。
- 删除或限定 `Files exceeding 3000 lines: 0`。
- 删除或限定 `Only 4 TODO/FIXME/HACK markers across entire codebase`。
- 把 `Custom exception types: 2 (test-only)` 改为当前可复现口径。
- 把 `231 hasattr`、`221 broad except`、`14 assert`、`126 C++ checks` 改为可复现命令输出，或从“关键事实”降级为“样本统计”。
- 把 `70-80% structural identity`、`zero unit test coverage`、`each method guards on hasattr` 等绝对表述改为“存在显著重复/独立覆盖不足/能力探测较多”。

### 5.4 `archive/echelon_forge_comprehensive_assessment_20260601.zh.md`

作为归档背景材料仍有价值。它已经承认多个旧断言被修复或需要改口径，例如 C++ doctest/CTest 已建立、`default_effects_model.cpp` 不再是单一 4805 行 `.cpp`、`SimulationKernel` 公共面仍宽。

使用该文时应注意：

- 它是 2026-06-01 报告、2026-06-02 复核更新，不是 2026-06-03 当前工作树快照。
- 它的规模数字和 HEAD 信息不能直接继承到当前审阅。
- 它适合作为“架构演进历史”，不适合作为当前所有计数的权威来源。

## 6. 结论

本轮可以确认：

> `docs/evaluation` 下关于“项目不是功能堆砌，而是有真实架构主线”的论述整体属实；关于“仍存在结构债、实现正确性只能按子架构和 slice 分级确认”的论述也属实。

但也必须修正：

> `architecture_review_20260603.*` 中若干精确指标、行数、coverage/duplication 估计和满格优势措辞没有当前口径支撑，不能作为不加限定的事实引用。

后续最合理的处理不是否定这些评审，而是把它们整理成分层证据：

1. **结构性事实**：目录、接口、source group、facade/quarantine、tests/architecture、contract runner。
2. **可复现计数**：必须附命令和范围。
3. **架构评价**：允许保留，但要标注为工程判断。
4. **正确性结论**：只按测试/contract/smoke 覆盖到的 slice 声明。

这一路径比简单说“架构很好”或“文档夸大”都更真实，也更适合后续继续研究子架构设计是否符合一般行业规范。
