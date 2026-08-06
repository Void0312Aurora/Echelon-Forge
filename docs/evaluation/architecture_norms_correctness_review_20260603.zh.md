# Echelon Forge 架构规范性与实现正确性进一步评估

**评估日期：** 2026-06-03
**仓库：** `/home/void0312/Workshop/CMO`
**评估对象：** 总体架构与主要子架构，包括 C++ kernel/ECS、runtime facade/contracts、mission/episode runtime、Python scenario/runtime adapter、command/tasking/domain standards、GPU helper、测试治理与发布治理。
**评估目标：** 对照一般工程行业实践，判断当前设计是否合理，并确认已有实现证据能支持到什么程度。
**范围说明：** 本文不是正式安全认证、军事模型鉴定、DO-178/ISO/IEC 质量体系认证或全量代码审计。本文只基于当前仓库文档、代码、架构守卫、聚焦测试和 smoke 证据给出工程判断。

---

## 1. 本轮使用的“行业规范”对照维度

这里的“行业规范”按通用软件工程与仿真/RL 工程实践理解，落成以下可检查维度：

| 维度 | 一般行业期望 | 本仓库对照口径 |
| --- | --- | --- |
| 分层与依赖方向 | 高层通过稳定 API 依赖低层能力，低层不反向依赖 UI/绑定/训练脚本 | `src/README.md`、`runtime/facade`、architecture tests |
| 接口封装 | 外部调用方不直接依赖底层 owner、world/entity、内部调度顺序 | `RuntimeFacade`、`RuntimeFacadeAdapter`、raw runtime quarantine |
| 领域边界 | common/core 与 air/naval/ground specialization 分离，避免成熟领域反向污染 common | `docs/standards/*`、command/tasking owner slices |
| 单一职责与模块化 | 大 owner 拆成明确服务、模型、系统、DTO、adapter；构建层也能反映边界 | CMake source groups、`SimulationKernel*Service/Surface`、README rules |
| 可替换模型 | 控制、传感器、制导、效果、环境等模型可替换，不把所有逻辑硬编码在 kernel | `IControlModel`、`ISensorModel`、`IEffectsModel` 等接口 |
| 可测试性 | 功能测试、契约测试、架构守卫、smoke suite 分层存在，并能 fail closed | `tests/architecture`、`tests/runtime`、contract runner、CTest |
| 兼容治理 | legacy/diagnostics 路径显式隔离，不默默成为主线 | compatibility/quarantine 命名和测试 |
| 可观测性与证据 | 运行结果能导出 trace、packet、event、diagnostics，支持回放/定位 | engagement/diagnostics DTO、runtime window evidence |
| 可复现与发布治理 | 依赖、版本、release checklist、许可证/provenance 有基本治理 | `release_and_dependency_policy`，但 lockfile/release checklist 仍缺 |
| 正确性边界 | 区分结构正确、接口正确、运行时正确、领域真实性正确、训练有效性正确 | gradient realism、accepted/held docs、聚焦测试结果 |

结论先行：本仓库在“架构边界意识、接口收口、兼容治理、契约测试、领域所有权文档”方面明显高于临时研究脚本水平；在“单体文件收敛、C++ target 物理拆分、完整 correctness proof、领域真实性校准、发布级可复现”方面仍未达到成熟产品或严格安全关键软件标准。

---

## 2. 总体设计是否符合一般工程规范

### 2.1 分层架构：基本符合，且有自动化守卫

`src/README.md` 给出维护中的依赖方向：

```text
interfaces/python
  -> runtime/facade
    -> core/engine and core/mission
      -> systems
        -> models / components / content
```

这符合行业中常见的 layered architecture / ports-and-adapters / facade 方向：绑定层和前端不应直接拥有领域真值，低层也不应知道 Python/Gym/UI 细节。

实现侧存在对应证据：

- `RuntimeFacade` 对 `WorldBatchRuntime` 使用前向声明和 private `unique_ptr`，public header 不 include engine owner header。
- `python/scenario/runtime/world_setup.py` 的 maintained setup target 会拒绝 raw runtime shaped target。
- `gym_envs/universal_env.py` raw `UniversalEnv` 构造入口已移除并 fail closed。
- `train.py` 不再提供非 world-batch raw `UniversalEnv` opt-in 路径。
- `tests/architecture/runtime_facade` 用 AST/文本扫描守住这些边界。

评价：符合一般行业方向，而且不是只靠文档，已有守卫测试。弱点是底层仍存在很宽的 `SimulationKernel` public API，高层收口并不等于底层已经完全拆干净。

### 2.2 Facade/API 设计：方向正确，但 facade 自身接近继续拆分阈值

`src/runtime/facade/README.md` 明确规定 facade 应暴露 typed request/result，而不是把 `WorldBatchRuntime` 底层方法逐个复制出去。这符合稳定 API 与信息隐藏原则。

当前 `runtime_facade.h` 暴露的能力已经覆盖：

- batch/session setup
- world setup/layout
- candidate query
- pilot action / launch request
- maintained mission/tasking batch
- execution episode batch
- observation/tasking/engagement/diagnostics export
- counterfactual snapshot/branch/experiment
- runtime window

这说明 facade 是真实应用层契约，但也说明它已经开始变宽。README 中提到当 maintained public request/result 方法接近约 40 个时，应规划 Session、Setup、Execution、Observation、Diagnostics、Engagement、Capability 分组拆分。这个判断合理，应作为后续架构收口方向。

评价：API 治理符合行业规范；当前实现达到“可用 facade”阶段，但还没达到“精细稳定 API family”阶段。

### 2.3 ECS 与 systems/models/components 分离：选择合理，但 header-only 系统有维护成本

仿真系统使用 ECS 是合理选择。项目把：

- `components/` 作为 ECS component / DTO-like 数据
- `systems/` 作为每 tick mutation logic
- `models/` 作为可替换领域模型
- `content/` 作为静态 schema / unit definition / loader

这符合 ECS 的一般实践：数据、系统、模型、内容不应混写。

实现证据：

- `simulation_kernel_systems.cpp` 负责注册组件与系统。
- control/sensor/acoustic/guidance/effects/environment 通过接口注入。
- weapon release 与 engagement event store 已从 kernel inheritance/inline system 中拆出一部分。

保留问题：

- `src/systems/combat/damage_system.h` 仍约 1525 行，属于大 header-only system。
- `src/models/core/default_unit_factory.h` 约 1580 行，仍是大 header。
- `simulation_kernel_systems.cpp` 仍承担大量系统装配，虽然注册 helper 已经改善局部。

评价：ECS 总方向符合行业实践；实现仍需要继续降低 header-only 大系统与中心装配文件的维护成本。

### 2.4 领域建模与 DDD-like 边界：文档设计强，代码处于兼容迁移期

`docs/standards/README.zh.md` 明确区分：

- `foundation/` 与 `bridge/`：跨域规则、runtime workflow、DTO/contract 约束
- `joint/`：跨军种共享语义、authority、command relationship
- `services/`：军种画像
- `air/naval/ground`：领域特化

这非常接近行业中 bounded context / domain ownership 的做法，尤其是它避免了“空战先成熟，所以 air 概念自动提升为 common core”的常见错误。

实现侧已有部分对应：

- `MissionCommand` 被拆成 `MissionCommandCore`、`MissionCommandAir`、`MissionCommandNaval` owner slice，但外部仍保留 flat compatibility shell。
- tasking 侧有 common/air/naval 目录。
- Naval/Ground 文档反复区分 accepted slice 与 held capability。

保留问题：

- `MissionCommand` 仍是重要 convergence point，README 自身承认它是 high-risk consumer convergence point。
- Ground command/runtime 仍是 bootstrap/evidence-only，不应过度解释为完整地面域 runtime。
- Naval 仍存在 air-shaped compatibility residual，例如历史上被关注的 `PilotAction`、flat `MissionCommand`、部分 Python fallback/config 名称。

评价：领域建模理念符合一般规范，甚至比很多研究仓库更清晰；代码实现仍在从 air-first 历史路径迁移到 common/service/domain 分层。

### 2.5 测试治理：强于普通项目，但有一个现实缺陷

本仓库测试体系包含：

- `tests/architecture/`：源码/文档/边界守卫
- `tests/runtime/`：按 capability/domain 分组的 runtime tests
- `tests/contracts/`：JSON contract specs
- `tests/runners/`：contract batch runner
- `tests/smoke/ci_smoke_suite.json` 与 `ci_contract_suite.json`
- C++ doctest/CTest `ef_test_all`

这符合行业里“单元/集成/契约/架构守卫/CI smoke”分层测试的方向。

本轮验证：

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q \
  tests/architecture/build/test_cmake_target_readiness.py \
  tests/architecture/runtime_facade \
  tests/architecture/command_tasking/test_tasking_bridge_guardrails.py \
  tests/architecture/structural_boundaries \
  tests/runtime/facade/test_runtime_facade.py \
  tests/runtime/core/test_world_setup_facade_contracts.py \
  tests/runtime/mission/test_mission_command_split_semantics.py \
  tests/runtime/mission/test_mission_command_naval_fields_roundtrip.py \
  tests/runtime/ground/test_ground_native_platform_schema.py \
  tests/runtime/naval/test_ship_naval_station_command.py
```

结果：

```text
129 passed, 1 failed
```

唯一失败：

```text
tests/architecture/structural_boundaries/test_domain_separation_boundaries.py::test_a2_structured_air_effects_do_not_write_rl_score_authority
```

失败原因是测试仍使用旧文本锚点查找：

```python
text.index("if (hp && !structured_air_target) {")
```

当前实现已经把 legacy score 写入移到 `default_effects_legacy_detail.inc::apply_legacy_health_damage()`，主 `.cpp` 改为调用 helper。因此这是 stale static guard，而不是本轮样本中的 runtime 行为失败。P1-A 后续已把该 guard 改为检查当前 split-file owner 关系，最新聚焦复跑通过。

C++ 原生验证：

```bash
cmake --build build-workshop --target ef_test -j2
ctest --test-dir build-workshop -R ef_test_all --output-on-failure
```

结果：

```text
100% tests passed, 0 tests failed out of 1
```

评价：测试治理明显存在，而且能捕捉架构漂移；当前短板是部分架构测试依赖脆弱文本锚点，需维护为更稳定的符号/文件/禁止调用检查。

---

## 3. 子架构评价

### 3.1 C++ Kernel / ECS 子架构

**规范符合度：中高。**

优点：

- ECS 分层适合多实体、多系统仿真。
- 模型接口注入符合依赖倒置。
- CPU truth path 与 GPU helper 分离，符合仿真正确性保守原则。
- `SimulationKernel` 不再直接继承 weapon release/event recorder 接口，说明 God object 拆分已经推进。

问题：

- `SimulationKernel` public surface 仍覆盖 setup、legacy command、tasking、observation、debug、weapon、model override 等大量职责。
- 原生 C++ 测试已有但覆盖仍薄，主要证明 smoke/lifecycle/component sanity，不证明复杂域正确性。
- 物理引擎与仿真引擎目标层还没有形成独立 target/API。

正确性判断：

- 可以说：kernel 基础 smoke、spawn/step/observation/reset 等维护路径有测试支撑。
- 不能说：整个仿真物理或所有领域行为已经被严格验证。

### 3.2 Runtime Facade / Contracts 子架构

**规范符合度：高。**

优点：

- facade 使用 request/result，隐藏 raw runtime owner。
- contracts 目录定位为 DTO，不拥有 world state、ECS registry 或 scheduling。
- facade header 与 runtime contract headers 被架构测试禁止 include `core/engine/*`。
- Python maintained path 通过 `RuntimeFacadeAdapter`，不再默认缓存 raw `WorldBatchRuntime`。

问题：

- facade cpp 仍约 3092 行，已经成为新的大汇聚点。
- facade method family 需要按 Setup/Execution/Observation/Engagement/Diagnostics 等继续拆分治理。

正确性判断：

- 本轮 `tests/runtime/facade/test_runtime_facade.py` 在聚焦测试中通过。
- 可以确认 facade 主路径在样本范围内可用；不能把它解释成所有 facade DTO 和 runtime window 组合已完全验证。

### 3.3 Mission / Episode Runtime 子架构

**规范符合度：中高。**

优点：

- `src/core/mission/README.md` 明确分为 `runtime/`、`episode/`、`episode/detail/`。
- `runtime/` 负责纯 mission/runtime products。
- `episode/` 负责 episode state、batch prepare、controller。
- `episode/detail/` 被限定为 controller 内部 helper。
- 架构测试禁止 `core/mission/episode/detail/` 泄露到非 controller 域。

问题：

- Mission layer 仍最成熟于 air execution；naval command 字段多为 bounded codec/state seam；full naval mission orchestration 和 full ground runtime 仍不在维护范围。
- Python scenario loader 与 C++ mission runtime 之间仍有较多桥接层，虽然已有分层文档，但部分 ownership 仍处在迁移中。

正确性判断：

- 本轮 mission command split/naval roundtrip 测试通过，说明 command shell/slice roundtrip 样本正确。
- 不能证明所有 reward/termination/objective 计算的领域正确性。

### 3.4 Python Scenario / Runtime Adapter 子架构

**规范符合度：中高。**

优点：

- `python/README.md` 明确 Python 不是杂脚本目录，而是 C++ runtime 之上的 support layer。
- `python/scenario/runtime/world_setup.py` 对 maintained setup target fail closed。
- `gym_envs/README.md` 明确 `UniversalEnv` 是 compatibility/eval/diagnostics 稳定入口，生产训练应走 world-batch runtime adapter。

问题：

- `world_batch_vec_env.py` 仍约 1898 行。
- `gym_envs/scenario_loader/core.py` 仍是大 orchestration surface。
- Adapter 层为了兼容历史 Python 运行时仍大量使用 `Any`，类型边界弱于 C++ DTO。

正确性判断：

- 本轮 `test_world_setup_facade_contracts.py` 通过，支持 maintained setup 和 raw setup 拒绝边界判断。
- 不能证明训练闭环、policy 收敛或所有 scenario loader 分支正确。

### 3.5 Command / Tasking / Domain Standards 子架构

**规范符合度：设计高，实现中等偏高。**

优点：

- `joint/common core -> service profile -> domain specialization` 是合理的领域建模方向。
- authority、ROE、Intent/Order/Execution Command/Report 被作为显式合同，而不是藏入运动参数。
- `MissionCommand` flat shell 有 owner slice 投影和 static_assert。
- tasking bridge tests 禁止 production path 直接 `loader.sim.set_task_order` / `set_leader_intent` / `set_pilot_report`。

问题：

- flat `MissionCommand` 仍是兼容汇聚点。
- Naval/Ground 仍需要继续从 air-shaped 历史路径中剥离。
- Domain standards 与 runtime 实现成熟度不同步时，需要持续防止过度声明。

正确性判断：

- 本轮 naval station command、ground native platform schema、mission command split 测试样本通过。
- 可以确认这些 slice 的合同/桥接实现有可执行证据。
- 不能确认 naval/ground 完整 domain runtime 正确，因为当前文档也没有这样声明。

### 3.6 GPU / Accelerator 子架构

**规范符合度：中高，但实现成熟度有限。**

优点：

- `src/gpu/README.md` 明确 GPU helper 不拥有 canonical world-step truth。
- `EF_ENABLE_CUDA_EXPERIMENTS` 默认 OFF。
- GPU 被定位为 helper/probe，而不是未冻结的 alternative truth path。
- 架构测试检查 facade capability projection 不应由 CUDA helper 信号悄悄提升。

问题：

- 还不是 exact backend。
- CUDA/probe 侧原生测试和 parity evidence 仍有限。
- 若未来做 resident-state，需要更强 state shard/version/parity budget 证据。

正确性判断：

- 可以说当前 GPU 路径在架构上被安全隔离。
- 不能说 GPU path 与 CPU truth 已达到完整语义等价。

### 3.7 测试、文档、发布治理子架构

**规范符合度：中高。**

优点：

- 文档权威层级清楚：`docs/plan`、`docs/standards`、`docs/task`、`docs/operations` 责任不同。
- `tests/README.md` 明确 architecture/runtime/contracts/suites 的职责。
- release/dependency policy 区分 optional dependency groups 与 smoke constraints。
- 文档多处主动声明 accepted/held/deferred，避免把进展夸大为完成。

问题：

- 当前没有完整 lockfile。
- release policy 明确记录 CMake `0.1.0` 与 Python distribution `0.2.0` 的版本同步缺口。
- 缺 canonical CHANGELOG 与专用 release checklist。
- 文档量大，存在历史/归档/活跃材料混淆风险，需要持续入口治理。

正确性判断：

- 治理结构存在且可追踪。
- 尚不能满足成熟发布产品的可复现/版本/发布门禁标准。

---

## 4. 实现正确性分层结论

必须把“正确”拆成不同层级：

| 正确性层级 | 当前判断 | 依据 |
| --- | --- | --- |
| 架构边界正确性 | 较强；P1-A 已修复原 stale guard | 原样本为 `129 passed, 1 failed`；后续 P1-A 聚焦复跑通过 |
| 构建/原生 smoke 正确性 | 当前样本通过 | `ef_test_all` 通过 |
| Facade/adapter 合同正确性 | 样本范围内通过 | facade、world setup、tasking bridge 测试通过 |
| Mission command/domain slice 正确性 | 样本范围内通过 | split、naval fields roundtrip、naval station、ground schema 测试通过 |
| 复杂物理/传感器/武器/毁伤正确性 | 不能整体确认 | 需要更广 runtime + calibration + scenario evidence |
| RL 训练有效性 | 本轮未确认 | 未运行训练、评估或统计收敛验证 |
| 发布级可复现正确性 | 不满足成熟发布标准 | 无完整 lockfile，版本同步缺口，release checklist 缺 |
| 领域真实性正确性 | 必须按 gradient realism 分级确认 | 文档已建立 G0-G7 门槛，但每个场景需单独证据 |

因此，本轮可以确认：

> 关键架构路径和若干核心 runtime slice 当前有可执行证据支撑；但不能据此宣称整个仿真、所有领域模型、训练结果或发布包已经“完全正确”。

---

## 5. 与一般行业规范的总体差距

### 已经接近或符合的方面

1. **分层依赖和 facade 隔离。**
   高层通过 facade/adapter 使用 runtime，raw kernel path 被 quarantine。

2. **DTO/contracts 与 owner classes 分离。**
   `runtime/contracts` 不拥有 world state 或 ECS registry。

3. **模型可替换与依赖倒置。**
   control/sensor/guidance/effects/environment 等模型通过接口注入。

4. **架构守卫测试。**
   使用 pytest/AST/text checks 守住 include、raw runtime、compatibility escape hatch、source group 等。

5. **领域所有权文档。**
   standards 明确 common/service/domain 层级，能防止 air-first 概念无意污染 common core。

6. **兼容路径显式化。**
   compatibility/quarantine 命名广泛存在，并由测试约束。

### 仍明显低于成熟行业产品的方面

1. **构建 target 还没有真正按 architecture 拆分。**
   `ef_core` 仍包含 engine、mission、facade、models、content 等，source group 只是过渡。

2. **大文件/大 header 仍多。**
   facade、bindings、world-batch adapter、unit factory、damage system 都仍较大。

3. **C++ 测试覆盖深度不足。**
   CTest smoke 有效，但不能覆盖复杂仿真行为。

4. **静态架构测试有脆弱锚点。**
   P1-A 已修复原 stale guard，但文本型守卫仍应继续升级为更稳定的符号/禁止调用/文件归属检查。

5. **发布治理不完整。**
   lockfile、版本同步、CHANGELOG、release checklist 仍有明确缺口。

6. **领域正确性需要证据链。**
   对传感器、ROE、武器、毁伤、地面/海军真实性，不能只靠结构图判断正确。

---

## 6. 建议的后续研究任务

### R1. 建立架构规范矩阵

在 `docs/evaluation/` 或 `docs/task/simulation_architecture/` 下建立矩阵：

| Norm | Repo Rule | Code Evidence | Test Evidence | Gap | Owner |
| --- | --- | --- | --- | --- | --- |

先覆盖分层、facade、contracts、compatibility、domain ownership、GPU truth boundary、release governance。

### R2. 继续减少脆弱 architecture guard 锚点

P1-A 已把 `test_a2_structured_air_effects_do_not_write_rl_score_authority` 改为：

- legacy score authority 检查 `default_effects_legacy_detail.inc::apply_legacy_health_damage()`。
- structured air consequence 检查 `default_effects_air_platform_resolution_detail.inc::resolve_default_effects_air_platform_consequences()` 不含 `score->`。
- 主 `.cpp` 只检查 structured/legacy 路由关系，而不依赖旧 block 形状。

后续工作应把这套做法推广到其它文本型 architecture guard。

### R3. 为 `SimulationKernel` 制定 public surface 缩窄路线

按以下 surface 切分并逐步迁移调用方：

- SetupSurface
- CommandSurface / CommandReadSurface
- ObservationReadSurface
- WeaponReleaseSurface
- DiagnosticsDebugSurface
- EngagementEventExportSurface

保留 Python 兼容绑定，但让 C++ mainline 尽量依赖 narrow surface。

### R4. RuntimeFacade 方法组拆分预研

先不急着改类名，先按 README 中的 group 分类 public 方法：

- Session
- Setup
- Execution
- Observation
- Tasking/Command
- Engagement
- Diagnostics
- Capability/Counterfactual

然后确认哪些 group 应成为 helper、子对象、free function，或只是文档分组。

### R5. 正确性证据分级

把正确性证据分成：

- architecture guard
- C++ unit/smoke
- Python runtime test
- JSON contract
- scenario rollout/scripted diagnostic
- calibration/provenance gate
- training/eval statistical evidence

每个场景或领域 slice 只声明其已有证据支持的最高等级。

### R6. 发布工程缺口收口

在进入任何对外 release 前，至少关闭：

- CMake/Python version mismatch。
- canonical CHANGELOG。
- release checklist packet。
- artifact/provenance review。
- 对 smoke constraints 与 optional dependency groups 的边界说明。

---

## 7. 最终评价

从一般行业实践角度看，Echelon Forge 当前架构设计是合理且有工程自觉的。它具备：

- 分层架构目标
- facade/API 收口
- contracts/DTO 层
- ECS 数据/系统分离
- 可替换模型接口
- domain standards 与 ownership map
- compatibility quarantine
- architecture tests 与 runtime/contract tests

这些都说明它不是“功能堆砌式研究代码”。

但从成熟工程产品角度看，它仍有明显迁移债：

- `SimulationKernel` 仍宽。
- facade/bindings/world-batch adapter 仍大。
- C++ target 仍未物理拆分。
- C++ 测试覆盖仍薄。
- 领域真实性不能整体确认。
- 发布治理尚未成熟。

因此建议采用下面的工作判断：

> 设计原则总体符合一般行业工程规范；实现已有多处正确性证据，但正确性只能按子架构和 slice 分级确认。当前最有价值的工作不是重写，而是继续把已有架构规则转换成更稳定的 narrow API、source/target 边界、非脆弱架构测试和领域真实性证据。
