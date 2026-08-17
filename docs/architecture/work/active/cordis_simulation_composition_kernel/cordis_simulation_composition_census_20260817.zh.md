# Cordis 仿真组合普查 — 2026-08-17

状态：`2026-08-17` P1-A composition census 已通过；本文是基于源码的基线，
不是 runtime 实现，也不是已冻结的 P1-B schema。

语言：

- 英文规范页：[cordis_simulation_composition_census_20260817.md](cordis_simulation_composition_census_20260817.md)
- 中文配套页：`cordis_simulation_composition_census_20260817.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_census_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

父项目：[Cordis 仿真组合内核](README.zh.md)

## 决策摘要

当前 runtime 已有若干有价值的接缝，但不存在单一 composition authority。
`SimulationKernel` 持有具体默认 provider/service，
`register_components_and_systems()` 持有固定的跨 domain Flecs 图，
`RuntimeFacade` 选择具体 CPU backend，而 host binding 暴露三个不同 runtime 层级。
Stage 语义还由另外两个不生成 Flecs registration graph 的 registry 描述。

因此即使引入 Cordis，也必须建立原生组合内核。Cordis 可以解析和描述已准入组合，
但原生代码必须重新验证、持有资源、编译 executable graph、冻结影响真值的选择，
并执行确定性 rollback/disposal。用 JavaScript 或 Cordis callback 直接替换当前
constructor，只会转移 ownership 问题，不会解决它。

P1-B contract 必须定义唯一 canonical resolved manifest 与唯一 native realization
路径。既有 constructor、setter、registration list、backend selection 和 raw binding
tier 只能成为 compatibility input 或 migration target，不能继续作为第二条维护中的
composition truth。

## 核验边界与方法

已检查：

- 原生 kernel construction、shutdown、reset、step 和 model setter；
- model/factory/service interface、default maker、Flecs singleton ref、raw capture
  及其 consumer；
- component/system registration、exact-stage inventory 与维护中的 stage-node manifest；
- world-batch construction 与 world-layout/reset 行为；
- backend SPI、facade construction、backend admission 与 CUDA-resident candidate；
- Python module、`SimulationKernel`、`WorldBatchRuntime`、`RuntimeFacade` binding；
- CMake ownership 与聚焦 architecture/runtime test。

从仓库根目录执行的代表性可复现命令：

```powershell
rg -n "make_default_|DefaultUnitFactory|WeaponReleaseService|set_.*_model|set_unit_factory" src/core src/models
rg -n "Ref>|\.get\(\)|\[env\]|IEnvironmentModel \*|IWeaponReleaseService" src/core src/systems src/models
rg -n "register_.*system|ecs\.component<|ecs\.set<.*Ref>" src/core/engine/simulation_kernel_systems.cpp
rg -n "ExactStepStageDescriptor|stage_node_manifest_registry_seed|\.node_id =" src/core/engine src/runtime/contracts
rg -n "make_unique<FlecsCpuBackend>|IWorldBatchBackend|CudaResidentBackend|admit_backend_request" src/runtime
rg -n "class_<SimulationKernel|class_<WorldBatchRuntime|class_<runtime::RuntimeFacade" src/interfaces/python
rg -n "SimulationKernel|WorldBatchRuntime|RuntimeFacade|stage_node_manifest|cuda_resident" tests
```

本 inventory 使用文本检索并直接检查控制流和 ownership。它不声明已完成 whole-program
alias proof、动态 trace coverage 或 AST 生成的 dependency graph。production composition
type 存在后，P2/P3 guard 应补充这些更强检查。

## 定量基线

| 表面 | 已观察基线 | 含义 |
| --- | ---: | --- |
| kernel-owned 可替换 model/factory provider | 7 | environment、unit factory、effects、sensor、acoustic、control、guidance |
| kernel-owned service/event object | 3 | engagement event store、weapon-release damage bridge、weapon-release service |
| 发布到 Flecs 的 singleton service/model ref | 7 | 六个 model ref 加 engagement recorder；unit factory 通过 release service 使用 |
| 中央函数内 component registration call | 82 | component availability 固定在一条 constructor-time 路径 |
| 中央函数内 active system registration call | 34 | common、air、naval、ground、combat、EW、logistics 一并安装 |
| exact-step stage descriptor | 30 | 有序 trace/step inventory；只有子集存在详细 contract descriptor |
| 维护中的 stage-node manifest seed entry | 5 | 语义 lifecycle slice，不是完整 executable system graph |
| Python 可见 runtime ownership tier | 3 | `SimulationKernel`、`WorldBatchRuntime`、`RuntimeFacade` |

这些计数是导航基线，不是能力声明。在生成式 composition evidence 替代手工基线前，
计数变化必须触发 census review。

## 构造与 Ownership Inventory

| Edge | 当前 owner 与 construction | Publication / consumer rule | Scope 与 replacement rule | Migration disposition |
| --- | --- | --- | --- | --- |
| environment model | `SimulationKernel` 在 `simulation_kernel.cpp:42-53` 调用 `make_default_environment_model()` | 发布 `EnvironmentModelRef`；多个 physics/model/sensor/guidance/world-layout consumer 读取它，但 ground contact 还捕获 raw pointer | world lifetime；`set_environment_model()` 可在 active kernel 内替换 owner 与 singleton ref | world-scope provider key；禁止 episode-time replacement；兼容 setter 退出前移除 raw capture |
| unit factory | `SimulationKernel` 构造 `DefaultUnitFactory` | 不发布 Flecs ref；`SimulationKernelWeaponReleaseService` 持有 owning `unique_ptr` 的引用 | world lifetime；service 引用的是 `unique_ptr` 槽而不是当前 pointee，因此可看到 setter 替换 | typed provider/handle；release service 通过显式 dependency 构造，不再依赖 owner member alias |
| effects model | default maker，由 `SimulationKernel` 持有 | `EffectsModelRef`；common damage 和 debug effects API 解析当前 ref | world lifetime；setter 更新 singleton ref | frozen graph 中的 immutable world provider；仅允许执行前受控 barrier compatibility replacement |
| sensor model | default maker，由 `SimulationKernel` 持有 | `SensorModelRef`；sensor system 解析当前 ref | world lifetime；setter 更新 singleton ref | 绑定 sensor capability/stage contract 的 model provider contribution |
| acoustic model | default maker，由 `SimulationKernel` 持有 | `AcousticModelRef`；sonar system 解析当前 ref | world lifetime；setter 更新 singleton ref | 绑定 acoustic/naval capability contract 的 model provider contribution |
| control model | default maker，由 `SimulationKernel` 持有 | `ControlModelRef`；air-control system 解析当前 ref | world lifetime；setter 更新 singleton ref | 绑定 control/exact-stage contract 的 model provider contribution |
| guidance model | default maker，由 `SimulationKernel` 持有 | `GuidanceModelRef`；guidance system 解析当前 ref | world lifetime；setter 更新 singleton ref | 绑定 guidance/combat contract 的 model provider contribution |
| engagement event store | `SimulationKernel` 持有具体对象 | 发布 recorder ref；guidance、damage、structural、ground-contact 路径写入 | store 随 world 持续存在；`reset()` 清空 episode event | 拆分 world-scoped recorder service 与 episode-scoped event state/generation |
| weapon-release damage bridge | `SimulationKernel` 持有具体对象 | 以引用传给 weapon-release service | world lifetime；手工在 model 之前销毁 | 声明完整 effects/damage dependency 的显式 service provider |
| weapon-release service | `SimulationKernel` 持有具体 `SimulationKernelWeaponReleaseService` | pilot/naval release system 捕获或使用 `IWeaponReleaseService&` | world lifetime；无公开 replacement API；依赖 factory owner alias、tuning、RNG、recorder、bridge | 具有完整 dependency declaration 与原生 lifetime ordering 的 scoped service provider |

默认 model maker 位于既有 model-owner 目录，而 ownership decision 集中在
[`simulation_kernel.cpp`](../../../../../src/core/engine/simulation_kernel.cpp)。
目标 provider catalog 必须保留 model owner 与 capability admission，不得让 composition
package 成为新的 model semantic owner。

## Lifecycle 与 Reset 边界

| 边界 | 当前行为 | Composition 含义 |
| --- | --- | --- |
| kernel construction | 创建全部默认 provider/service，注册全部 component/system，禁用 `ResupplyLogic`，然后调用 `reset(42)` | construction、graph compilation 与首个 episode initialization 被融合 |
| normal step | 调用 `ecs.progress(time_step)`；exact-stage tracing 使用独立 guarded path | 维护中的 hot path 必须保持 native，不得出现 Cordis/Node callback |
| episode reset | 清 engagement event，删除 `SimObject` entity，重置 ECS clock，并 reseed RNG | provider、system、environment config、backend 属于 world scope；entity/time/RNG/event generation 属于 episode scope |
| batch resize | 每个新增 world 分配完整 `SimulationKernel` | resolved application/profile 数据应可共享，可变 world resource 必须隔离 |
| batch setup | 应用 layout/configuration，然后按确定 seed mapping reset 每个 world | setup 是受控 pre-episode transition，不是 plugin hot reload |
| shutdown | 结束 trace，删除 entity，reset ECS，再按固定顺序手工 reset service/model | 原生 composition transaction 必须推导 reverse dependency disposal，并证明 failure rollback |

当前 reset 行为可以映射到 application catalog、backend/batch、world、episode 四层目标，
但不能把每个 Cordis scope 都实现成独立 runtime callback。Scope mapping 必须在 manifest
中显式声明，并由 native realization 执行。

## Raw Capture 与 Replacement 风险

置信度最高的 correctness defect 是 environment edge：

1. `SimulationKernel::register_components_and_systems()` 将
   `environment_model_.get()` 传给 `register_ground_contact_system()`；
2. `GroundContactSystem` 在 Flecs run lambda 中捕获该 `IEnvironmentModel*`；
3. `SimulationKernel::set_environment_model()` 可以销毁旧 owner，并发布新的
   `EnvironmentModelRef`；
4. 其他 consumer 读取当前 singleton ref，而 ground contact 保留旧地址。

结果是 replacement semantic 不一致，并可能出现 dangling pointer。P2/P3 可以在完整
provider migration 之前先修复直接缺陷，但最终规则更强：影响真值的 service 在 graph
realization 时解析为带 generation/scope identity 的 native handle，episode graph active
期间不可变。

Weapon-release service 不存在同样的即时 stale-pointee 缺陷，因为它引用
`unit_factory_` owner 槽；但它仍编码隐藏 lifetime coupling，所以仍是 migration target。

## System Registration Inventory

中央 registration 路径按以下顺序安装 active call：

| Family | Registration calls |
| --- | --- |
| command/control | `register_command_link_system`、`register_action_mapping_system`、`register_command_lag_system`、`register_control_system` |
| air/physics | `register_force_clear_system`、`register_aero_state_system`、`flight_dynamics::register_propulsion_system`、`register_force_system`、`flight_dynamics::register_actuator_system`、`register_aerodynamics_system`、`register_ground_contact_system`、`register_rotational_integration_system`、`register_leapfrog_integration_system` |
| motion/navigation | `register_ship_motion_system`、`register_submarine_motion_system`、`register_navigation_system` |
| sensing/C2 | `register_sensor_system`、`register_sonar_system`、`register_track_manager_system`、`register_data_link_system`、`register_embarked_air_ops_system` |
| combat/effects | `register_guidance_system`、`register_pilot_weapon_release_system`、`register_naval_mission_weapon_release_system`、`register_damage_system_common`、`register_aircraft_damage_system`、`register_structural_failure_system`、`register_structural_consequence_system`、`register_naval_damage_system`、`register_ground_damage_system` |
| observation/EW/logistics | `register_instrument_system`、`register_ew_system`、`register_logistics_system`、`register_naval_logistics_system` |

只有 ground-contact registration 接收可替换 model 的 raw pointer。Pilot 与 naval
weapon-release registration 接收 service reference。多数其他调用只接收 Flecs world，
在执行期查找 singleton service。

该清单是 implementation order，不是 admitted dependency graph。每个 world 都得到 combined
family set，即使其 content/profile 不使用所有 domain。P3 必须以 native contribution
替代这份清单，并在 Flecs registration 前验证 component、service、stage、capability、
read/write、conflict 与 ordering requirement。Cordis package order 绝不能成为 system
execution order。

## 三个调度真值表面

| 表面 | 当前用途 | 覆盖 | 目标处置 |
| --- | --- | --- | --- |
| `simulation_kernel_systems.cpp` | 构造 executable Flecs component/system graph | 82 个 component call 与 34 个 active registration call | 从已准入 native contribution 生成/realize |
| `exact_stage_inventory.cpp` | exact-step trace inventory 与选定 stage 详细 contract | 30 个 descriptor；详细 contract 覆盖选定 exact 子集 | 使用相同 canonical node identity，并拒绝未解释 parity gap |
| `stage_node_manifest_registry.h` | 维护中的 causal/runtime semantic manifest | 维护中 selected slice 的 5 个 node | 保持 semantic authority，并成为 admission input，而非平行 executable graph |

本文不会把三者声明为当前等价。P1-B schema 必须区分 semantic stage identity、executable
system contribution 与 trace/evidence projection，同时提供 stable join key。P3 acceptance
必须证明一个 resolved composition 同时产出 Flecs graph 与 evidence view，而不是只同步
三份手工清单。

## Backend Composition Inventory

| Edge | 当前状态 | Migration disposition |
| --- | --- | --- |
| semantic backend SPI | `IWorldBatchBackend` 定义 configuration、content、reset、setup、injection、evaluation、advance、export、diagnostics 表面 | 保留为 facade semantic seam；provider factory 返回此接口 |
| CPU realization | 两个 `RuntimeFacade` constructor 都直接创建 `FlecsCpuBackend` | 移到由 resolved native manifest 选择的 admitted backend provider |
| CUDA-resident candidate | `CudaResidentBackend` 实现 SPI，但保持 candidate/experimental，并通过有界 probe/test 使用 | catalog visibility 不等于 admission；保留 fail-closed profile contract |
| request admission | backend profile contract 与 `admit_backend_request()` 验证请求，但 admission 不构造或替换 backend | 在一个 transaction 中统一 request validation/materialization，同时分别记录 requested/realized evidence |
| capabilities | facade capability report 对未维护 GPU operation 有意 fail-closed | composition 不得提升 capability，只能 realize 已准入 profile |

核心缺口不是没有 interface，而是 static admission contract 与 constructor-time
materialization 分离。P4 必须闭合这条裂缝，且不允许 Cordis discovery 提升 experimental
backend。

## Binding 与 Host Inventory

[`python_module.cpp`](../../../../../src/interfaces/python/python_module.cpp)
组装 command、core、episode、runtime、GPU binding group。维护中的 Python module 暴露：

| Tier | 当前 exposure | Composition risk 与目标 policy |
| --- | --- | --- |
| `SimulationKernel` | 直接 construction、reset、step、shutdown、setup/configuration 与 diagnostics | raw kernel construction 可绕过未来 facade composition policy；只保留为显式 native compatibility profile 或窄 test surface |
| `WorldBatchRuntime` | 直接 batch construction、setup、reset、step 与相关 batch operation | 第二条 host-visible construction path 必须消费相同 resolved profile，不得持有独立 default |
| `RuntimeFacade` | 主要 semantic API、configuration、admission、setup、step、export、replay、evidence | 目标 host boundary 与 composition request/result DTO owner；realization 仍在 native composition code |

当前不存在维护中的 Node package 或 Node-API target。未来 Node host 应绑定 coarse
facade/composition construction boundary，不得暴露 Flecs 或引入 stage callback。Python
与 standalone C++ 必须在没有安装 Node/Cordis 时完整可用。

## Build 与 Test Ownership

当前 CMake 将 content、core、facade、Python module 分为不同 target。`ef_py` 链接 facade
和 core，所以未来 native composition library 应能被 core/facade 独立链接，不得依赖
binding 或 Node package。

现有 migration 相关证据：

| Evidence surface | 当前证明 | Composition 缺口 |
| --- | --- | --- |
| kernel lifecycle guard 与 teardown stability test | active/shutdown guard 及重复 create/reset/step/destroy 行为 | 无 provider dependency rollback、generation handle 或 failed-construction matrix |
| stage-node manifest architecture test | manifest validation、maintained visibility、barrier、selected-slice rule | 不生成完整 executable graph |
| facade contract-boundary test | fail-closed facade/GPU separation | 无 provider materialization parity |
| CUDA-resident profile/admission test | unsupported candidate 保持受限并被拒绝 | 无 admitted runtime provider selection |
| binding surface test | 维护中的 Python DTO/method shape | 无 cross-host composition parity 或 raw-tier retirement policy |
| world-batch test | 确定 world 使用与 facade adapter 行为 | 无 shared resolved-profile memory/startup evidence |

P2 及以后必须增加 deterministic permutation resolution、duplicate/conflict rejection、
dependency-cycle diagnostics、failed-provider rollback、reverse-order disposal、scope
isolation、generation mismatch rejection、default profile replay parity 与 composition
identity round trip。

## 风险登记

| ID | 风险 | 严重度 | 证据 | 必需控制 |
| --- | --- | --- | --- | --- |
| `CEN-01` | model replacement 后 environment pointer stale/dangling | high correctness | setter 更新 singleton ref，而 ground contact 捕获 raw pointer | 移除 raw capture；freeze 或 generation-check handle |
| `CEN-02` | constructor monolith 保持第二条 composition truth | high architecture | `SimulationKernel` 内具体 model/service construction | 仅从 validated manifest realize builder |
| `CEN-03` | 三种 scheduling description 漂移 | high determinism/evidence | central registration、exact inventory、semantic manifest seed | canonical node identity 与 generated/validated join |
| `CEN-04` | admitted backend request 与实际 constructor backend 不一致 | high capability integrity | facade 固定创建 CPU backend | 单一 admission/materialization transaction，并记录 requested/resolved evidence |
| `CEN-05` | direct binding tier 绕过 composition policy | medium-high governance | 三个 Python 可见 runtime tier | 一个 native resolver；显式 compatibility profile 与 retirement gate |
| `CEN-06` | 手工 teardown 顺序或部分构造泄漏资源 | medium-high lifetime | 固定 owner reset order | transactional construction 与 dependency-derived reverse disposal |
| `CEN-07` | 每个 world 承担 combined graph/provider 成本 | medium scale | batch 每个 world 分配完整 kernel | shared immutable resolution + scoped per-world realization + benchmark |
| `CEN-08` | plugin discovery 被误认为 semantic admission | high authority | backend candidate/stage contract 已采用 fail-closed policy | native revalidation；Cordis 不得提升 capability/stage |

## 从普查推导的 P1-B Contract 要求

P2 实现前，P1-B 必须确定：

1. 具有 canonical encoding、stable requested/resolved identity 的 versioned、host-neutral
   `SimulationCompositionManifest`；
2. 稳定的 provider、service、system-contribution、backend-profile、capability、
   semantic-stage、executable-node、evidence-projection identifier；
3. 显式 application、backend/batch、world、episode scope mapping；scope-capture violation
   必须构成 invalid manifest；
4. 与 discovery order 无关的确定性 provider selection、dependency ordering、
   duplicate/conflict handling、optional contribution rule 与 cycle diagnostics；
5. 带 generation/scope identity 的 typed native handle；manifest 不得要求 raw owning
   pointer 跨 provider replacement 存活；
6. 声明 component、service、stage join key、read/write state、barrier、conflict、
   domain/capability requirement、registration factory 的 system contribution schema；
7. 将既有 request admission 与 realization 连接起来、且不提升 candidate capability 的
   backend provider contract；
8. 精确命名当前 7 个 provider、3 个 service、82 个 component registration 与 34 个
   system call 的 default compatibility profile；任何 accepted deviation 必须显式记录；
9. manifest hash、resolver version、provider version、executable graph hash、backend
   profile、host mode、scope generation 等 composition evidence field；
10. 将 `RuntimeFacade` 定为维护中的 coarse host seam，并定义 direct kernel/batch
    constructor 的有界去向。

在 P1-B test 证明 contract 前，production C++ type name 与目录布局仍保持开放。以上
semantic requirement 作为 census output 冻结；后续变更必须有显式 architecture decision
与更新后的 evidence。

## 验证结果

`2026-08-17` 验证结果：

- 本子项目与 architecture owner 定向 audit：18 个 document、110 个 repository-local
  link、0 issue；
- maintained-surface audit：150 个 document、1,433 个 link、0 issue；
- strict maintained bilingual audit：74/74 pair 同步，无 missing/diverged peer；
- documentation governance：使用主工作区 repository-local `ef_py` artifact 后，23 个 test
  通过；pytest 成功退出后仍输出已知 Windows 临时目录 cleanup warning；
- 聚焦 stage/backend architecture test：13 个通过，7 个因 test helper 强制调用 `g++`
  而无法启动；当前 Windows PATH 未安装或不可见 `g++`。这 7 项都是环境 launch failure，
  不是 assertion failure；
- `git diff --check`：干净；
- 计数复核：82 个 component registration、34 个 active system registration、30 个
  exact-stage descriptor、5 个 stage-node manifest seed entry。

Full-tree link audit 仍报告 effects review archive 下一个既有 missing target；full-tree
bilingual scan 仍报告 strict maintained surface 外的历史单语文档。两类问题都不由本子项目
产生，也不指向本子项目；本回合没有修改它们，也不声明关闭它们。

## P1-A Closure Assessment

P1-A 通过，因为所有要求的 composition 类别都已有 owner、scope、replacement rule、
hazard classification 与 migration disposition：constructor、setter、raw capture、service
ref、registration entry、backend selection、reset boundary、stage registry、binding、build
ownership 和 relevant test。

本回合未修改 runtime 文件。该 pass 只证明 P1-B 可以在不隐藏已知 ownership edge 的
情况下开始；它不证明 manifest correctness、lifecycle safety、Cordis runtime feasibility、
behavioral parity 或 performance benefit。

P1-A 收口时，下一 eligible cluster 是 `P1-B Manifest And Resolution Contract`；P2 与
全部 constructor migration 受其 schema、canonical fixture、invalid-manifest matrix 与
deterministic-resolution gate 约束。上述 gate 随后已在
[P1-B contract baseline](cordis_simulation_composition_contract_20260817.zh.md)中通过；
P2-A 随后作为隔离的原生 lifecycle baseline 通过。当前下一步是 P2-B constructor
migration，且继续受本 census 约束。
