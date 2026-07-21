# T11 内容编译流水线普查（2026-07-21）

语言：
- 英文规范版：[t11_content_pipeline_census_20260721.md](t11_content_pipeline_census_20260721.md)
- 中文伴随版：`t11_content_pipeline_census_20260721.zh.md`

文档类型：`reference`
生命周期：`maintained`
规范路径：`docs/plan/unified_architecture_program/t11_content_pipeline_census_20260721.md`
负责人：`unified architecture program workline`
最后核实：`2026-07-21`
基线提交：`9a054c0a`

状态：面向[统一架构计划](README.zh.md)的 T11 第一切片内容面普查。T11 的职责是"将场景/单位内容加载演进为分阶段的 `P0 ContentCompile` 模型：类型化 setup 包、在 `spawn_unit` 兼容性之后的能力束展开、把内容 schema 校验作为一个编译阶段；吸收并取代 T3 的 loader 条目"，目标是"新内容与新域通过编译过的、校验过的能力组合进入"，关键风险是"内容 JSON 兼容性是硬性外部面；迁移必须逐束进行并带 fixture 对拍"。本文是描述性普查登记（`reference`），非独立评审：它记录经核实的基线现状，不携带评审结论。它不改变任何行为，也不改动 `src/**` / `python/**` 代码；它清点现存物，以便后续 T11 切片在第 3 节红线约束下扩展。术语遵循
[仿真系统架构设计](../architecture/simulation_system_architecture_design.zh.md)
中的 SCAL 语义图（Semantic Graph）面与 `P0 ContentCompile` 阶段（第 6 节生命周期表 `P0 ContentCompile` 行；第 6.1 节阶段契约修正案）。

## 0. 方法与范围

- 在基线 `9a054c0a` 普查了受维护的内容面：`src/content/**` 与
  `src/models/core/default_unit_factory.h`（只读）、
  `src/runtime/contracts/platform_capability_contracts.h`、`python/scenario/**`、
  `python/experiment/**`、`gym_envs/scenario_loader/**`、
  `tools/maintenance/dto_schema/schemas/**`、`tools/maintenance/experiment_matrix/**`、
  `examples/config/**`（只读），以及 `tests/**` 与 `src/tests/**` 下的钉扎测试。
- 全文使用的 `P0 ContentCompile` 参考定义是第 6 节生命周期行：负责人为
  `content/` + 适配器 + facade setup；输入"scenario files, unit data, backend
  capability requests"；输出"typed setup packets, content ids"；不得拥有"per-tick
  behavior"。第 2 节差距矩阵所用的分析性分解 **parse -> validate -> resolve ->
  materialize** 是本普查的透镜，而非文档原文：架构以输入/输出/不得拥有及第 6.1 节
  阶段契约字段（`semantic_stage`、`sub_graph`、`read_set`/`write_set`、
  `clock_domain`、`information_layer_*`、`extension_points`）定义 P0，并未命名这四个
  子阶段。文档未表态处标记 **（待裁定）**。
- loader 的量化数据直接在 `9a054c0a` 的 `src/content/unit_definition_loader.cpp`
  上统计（正则匹配计数；在第 1(i) 节复现）。
- 零行为变更。未新增可选只读架构测试；决定与理由记于第 4 节。

## 1. 内容面普查

### (i) 单位定义加载器（JSON -> `UnitDefinition`）

| 方面 | 结论 |
|------|------|
| 入口 | `load_unit_definitions_json(path, out_definitions, error)`（声明于 `src/content/unit_definition_loader.h:37`；实现于 `unit_definition_loader.cpp:1836-1881`）。目录路径先加载脆弱性证据描述符（经 `load_vulnerability_evidence_descriptors`，`:1634`），再用 `fs::recursive_directory_iterator` 遍历每个**直接**父目录不是 `damage/vulnerability_evidence/` 的 `.json`：跳过判据 `entry.path().parent_path() == vulnerability_evidence_dir`（`:1855`）只比较直接父目录，故它排除的是那两个描述符文件本身，但**不会**排除该目录下假想的嵌套子树（当前无此嵌套，故行为暂等价于整子树跳过）。文件路径直接进入 `load_file`（`:1587-1632`），后者接受 `{"units": [...]}` 数组或带 `name`+`type` 的单个对象，否则报错 `"expected 'units' array or a single unit object"`。C++ 钉扎经 `SimulationKernel::load_database`/`load_definitions`（`src/core/engine/simulation_kernel.cpp:173,213`）加载整个 `examples/config/database` 树，故递归遍历把**全部 27 个定义文件**送入 `load_file` -> `parse_unit_json`（不止单位）：**11 个单位平台文件**（`aircraft/units/*.json` x5、`ships/units/*.json` x5、`ground/units/*.json` x1）；**12 个模块文件**（`aircraft/modules/{engines x2, ew_suites x1, rcs_profiles x2, sensors x2}` + `ships/modules/sensors x5`，解析为 `Engine`/`EWSuite`/`RCSProfile`/`Sensor` 定义）；**3 个武器文件**（`weapons/air_to_air/*.json`，`type: Missile`）；**1 个设施文件**（`facilities/generic_airbase.json`，`type: Facility`）。每个都带顶层 `name`+`type` 并落入同一 `name -> UnitDefinition` 映射，故单位按名解析 `engine_ref`/`sensor_ref`/`ew_suite_ref`/`rcs_profile_ref`/`default_loadout`（如 `f16c_block50.json` -> `"F110-GE-129"`、`"AN/APG-68(V)9"`、`"AIM-120C-7"`）。那 2 个 `damage/vulnerability_evidence/*.json` 描述符经独立描述符路径加载，数据库根下共 29 个 JSON 文件。 |
| 中间表示 | 唯一的手写映射器 `parse_unit_json`（`:804-1585`，约 782 行）填充一个扁平的 `UnitDefinition` 结构体（`src/content/unit_definition.h:177-265`），58 个直接成员（逐字段清点）：type/name、组件**引用**（`sensor_ref`、`sensor_refs`、`engine_ref`、`ew_suite_ref`、`rcs_profile_ref`）、`hardpoints`、`default_loadout`（`unordered_map<int,string>`）、内联组件块（`engine_data`、`jammer/rwr/esm/cms`、`rcs_data`、`airframe`、舰船/潜艇平台、naval stores/logistics/weapon system、embarked air ops、`damage_model` `HitboxConfig`、`aircraft_vulnerability`、`health`、`sensor`+`mounted_sensors`、`sonar`+`mounted_sonars`、`flight_model`、`stall_state`、`landing_gear`、`score`、`ammo`、`command_link`、data-link 标量），以及 56 字段的 `MissileTuningDefinition`（`unit_definition.h:63-122`）。 |
| escape hatch / 手写映射量化（`9a054c0a` 核实） | `unit_definition_loader.cpp` = **1,881 行**（100 空行；`Measure-Object -Line` 读到的 1,781 是因为排除了空行）——与 README T3 "1,881-line hand mapping" 一致。调用点计数：`.value(key, default)` **x430**；`.contains(key)` **x79**；类型守卫 `.is_object()` **x50**、`.is_array()` **x23**、`.is_number()` **x12**、`.is_string()` **x7**、`.is_boolean()` **x0**；显式 `.get<...>()` **x25**。`parse_unit_json` **直接访问 54 个不同的顶层 JSON key**，且对导弹类单位还会把*整个* `entry` 交给 `parse_missile_tuning_json_fields`（`:1450`），后者读取**另外 52 个与前 54 个不相交的顶层 key**（维护中的 `aim_120c.json` 确实带顶层 `max_flight_time_s`），语义上**共识别 106 个顶层 key**。十六个手写 `parse_*` 辅助函数（如 `parse_vec3_array`、`parse_sensor_json_fields`、`parse_missile_tuning_json_fields`、`parse_unit_type`、`parse_sensor_type_code`）。escape hatch 模式：**字段别名 / 双表示** —— `fuze`+`fuse` 都解析（`:1484-1489`）；引擎为嵌套 `engine` 对象**或**扁平 `mil_thrust_n`/`ab_thrust_n`/`sfc_mil`/`sfc_ab`/`bypass_ratio`（`:830-846`）；`engine_tuning` 顶层 vs `engine.tuning`；`aero_tuning` vs `airframe.tuning`；传感器经 `sensor_ref` / `sensor_refs` / 内联 `sensor` / `has_sensor`（`:889-906`）；导弹调参从扁平 `entry`**与** `missile_tuning`**与** `guidance` 合并，并带按键别名（`active_seek_range`、`off_boresight_cap`）（`:1450-1480`）。**多态节点** —— 伤害组件 `dependencies[]` 条目可为裸字符串**或**对象（`:1232-1254`）。**回退链** —— 组件 `offset`/`size` 回退到父 hitbox（`:1277-1291`）；`component.system` 回退到 `component.name`（`:1225`）。**哨兵** —— `std::numeric_limits<double>::quiet_NaN()` "未设"标记加 `has_*` 存在标志加 `-1` 整型哨兵。**非 schema 溯源**：`tools/maintenance/dto_schema/schemas/` 下没有 `unit_definition_*`/`content_*` 文件（对比：`capability_bundle_fields.py`、`platform_capability_fields.py`、`typed_platform_spawn_*_fields.py`、`world_spawn_request_fields.py` 均为 schema 溯源）。 |
| 消费者（resolve + materialize） | `DefaultUnitFactory`（`src/models/core/default_unit_factory.h`）持有 `name -> UnitDefinition` 映射。`spawn(ecs, unit_name, params)`（`:619-1439`，含闭合括号共 821 物理行）**先门禁后物化**：调用 `resolve_platform_spawn_plan_for_type_name` -> `build_platform_capability_bundle_template`（`:321-531`，从结构体的 `has_*` 标志派生一个 `CapabilityBundle`，分到 sensing/mobility/communication/command/launching/survivability/doctrine 能力并合成 `evidence_refs`）-> `validate_resolved_platform_spawn_plan`，失败则拒绝返回 `flecs::entity::null()`；随后手工物化 flecs 实体，在 spawn 时通过 `definitions_.find(...)` 解析 `sensor_ref`/`engine_ref`/`ew_suite_ref`/`rcs_profile_ref`/`default_loadout`/`embarked_air_ops.helo_unit_name`。类型化契约层是 `runtime::platform_capabilities`（`src/runtime/contracts/platform_capability_contracts.h`）：schema 溯源的 `Capability`/`CapabilityBundle`/`ResolvedPlatformSpawnPlan` 结构体（`detail/*.inc`）带 fail-closed 校验器；请求种类 `type_name_projection` / `typed_platform_request`；物化策略 `factory_projection_materialization` / `resolved_spawn_plan_bridge`。目前仅 `type_name_projection` + `factory_projection_materialization` 路径有生产者。 |
| 测试钉扎 | C++ `src/tests/test_components_basic.cpp`；Python `tests/architecture/platform_spawn/`（6 个：`test_platform_capability_contracts.py`、`test_typed_platform_spawn_contracts.py`、`test_default_factory_spawn_plan_resolution.py`、`test_default_factory_spawn_command_projection.py`、`test_boundary_guards.py`、`test_runtime_setup_consume_bridge.py` —— **均非 smoke**）；`tests/runtime/naval/test_naval_ship_database.py`（**smoke**）；`tests/runtime/air_combat/weapon_guidance_realism/` 下的武器制导真实性套件消费单位定义。 |
| 与 `P0 ContentCompile` 的差距 | **parse** 是 1,881 行手写映射，非 schema 溯源（即 T3/T11 目标）。parse 处的 **validate** 仅结构性（type 存在且已知、units/单对象）加 I47 脆弱性权威降级（`:1397-1409`）与描述符 `dataset_id`+`target_type` 要求（`:1810`）；唯一的 fail-closed 结构化校验（`validate_capability_bundle`）在 **spawn**（物化）时运行，而非作为编译阶段。**resolve**（交叉引用）与 **materialize** 在 `spawn()` 内交织。`CapabilityBundle` 是**从**单体结构体**派生的投影**，非真值源；且 `typed_platform_request` 路径（真正的 `spawn_platform({capabilities...})`）没有由内容驱动的生产者。输出是 flecs 实体，而非文档的"typed setup packets + content ids"。 |

### (ii) 场景 JSON 加载与编译链

| 方面 | 结论 |
|------|------|
| 入口 | `ScenarioCompiler.compile_path(source_path)` / `compile_data(scenario_data)`（`python/scenario/compiler/service.py:82-99`），带类级 `_path_cache` 与新鲜度门（`CompiledScenario.is_fresh` 基于 `dependency_mtimes_ns`，`:63-71`；缓存命中在 `:84-90` 重新校验）。规范负责人边界由一个 smoke 测试强制（见钉扎）。 |
| 中间表示 / 阶段 | `_compile_from_data`（`:110-185`）运行有序流水线：(1) **parse** `_compile_from_path` `json.load`，须为 dict（`:102-107`）；(2) **validate（形状）** `validate_scenario_compiler_shape`（`compiler/validation.py:74-149`）—— 可选 dict/list 形状、`_require_object_entries`、`_require_unique_entity_names`；文档串声明它只校验"编译器直接消费的形状"；(3) **resolve/merge** `_compile_merged_scenario_data`（prefab 合并 + `imports` 解析 -> `merged, imported_files, warnings`）；(4) **ingest** `ingest_projection_setup_payloads_into_scenario`（环境基底；fail-closed 带 `rejection_reason`，`:119-126`）；(5) **重新校验** 合并后文档（`:128-132`）；(6) **materialize** 类型化 IR `CompiledScenarioRuntimeMetadata`（任务指令模板、奖励、航路点缓存、布局模板、条件目标、ILS 信标）到冻结的 `CompiledScenario` dataclass（`:43-71`、`:175-185`）。 |
| 消费者（物化到 kernel） | `gym_envs/scenario_loader/core.py::ScenarioLoader` 持有 `_compiled_scenario`/`_compiled_runtime_metadata`，暴露 `load_scenario`/`load_compiled_scenario`/`load_scenario_data`（`:355-361`）；经 `__getattr__`/`__setattr__`（`:180-216`）委派到负责人模块。运行时物化是 `python/scenario/runtime/kernel_apply.py::apply_world_layout_to_kernel`（`:339`），它对每个 spawn 调用 `sim.spawn_unit(side, type_name, x, y, z, heading, pitch, roll, vx, vy, vz)`（`:389`）—— 即经由 `type_name` 字符串重新进入面 (i)。 |
| 测试钉扎 | `tests/scenario/test_scenario_compiler.py`（**smoke**）；`tests/scenario/test_scenario_generation_contracts.py`（**smoke**）；`tests/architecture/runtime_facade/test_scenario_setup_facade_boundary.py::test_maintained_python_paths_use_the_canonical_scenario_compiler_owner`（**smoke**）；`tests/scenario/test_environment_projection_contracts.py`；`tests/world_batch/test_batch_scenario_runtime.py`。 |
| 与 `P0 ContentCompile` 的差距 | 这是现存对 P0 最贴近的类比：它已分阶段 parse -> validate -> merge/resolve -> ingest -> materialize，带新鲜度缓存与类型化 IR。差距：(a) 它位于 Python Experiment World（`python/scenario/compiler`），而文档将 P0 负责人命名为 `content/` + 适配器 + facade setup；(b) 校验仅形状、无 schema、**无跨内容检查** —— 例如实体 `type_name` 在编译期从不对照单位数据库校验，只在 spawn 时（警告/拒绝）；(c) 它与单位编译（面 i）**未链接** —— 两条流水线只在 `spawn_unit(type_name)` 字符串处相遇；(d) IR 是 dict 形态的 `merged_scenario_data` + 临时 dataclass，而非文档的"typed setup packets" DTO。 |

### (iii) 实验矩阵 -> 运行配置展开（I30）

| 方面 | 结论 |
|------|------|
| 入口 / 负责人 | `python/experiment/` 是 T5 Experiment 面负责人。`definition.py` 将 `Experiment = ScenarioRef x ConfigComposition x SeedSpec x EvaluationProtocol` 冻结为经校验的冻结 dataclass，并有 `ExperimentRegistry` 注册插座（对重复/悬挂引用快速失败，`:153-225`）。`composition.py` 拥有确定性 `compose_config(base, delta)`（base 键序保留，delta 键追加）、`freeze_json_mapping`、`ensure_json_value`。`air_combat_matrix.py`（868 行）是已注册的空战矩阵（I30）。`report_envelope.py` 是 I44 的可选报告信封。 |
| 中间表示 / 输出 | 运行配置是已注册定义的**投影**；渲染到文件由生成器 `tools/maintenance/experiment_matrix/generate.py`（受新鲜度门）拥有。磁盘输出是 **24 文件**空战矩阵 `examples/config/training/active/air_combat/*.json`（计数已核实 = 24）。该包仅标准库（按设计不导入 runtime/gym/training 依赖）。 |
| 消费者 | 训练/评估入口加载渲染出的运行配置 JSON，后者提供进入场景编译器（面 ii）的场景引用。 |
| 测试钉扎 | `tests/experiment/test_experiment_definition.py`；`tests/experiment/test_report_envelope.py`；`tests/architecture/governance/test_experiment_matrix_freshness.py`（**smoke** —— 对矩阵的再生成新鲜度门）。 |
| 与 `P0 ContentCompile` 的差距 | 此面是 **Experiment 面**（T5 / 基线修正案 (a)），位于 P0 的**上游**：它选择*编译哪个*场景/配置；它本身不是内容编译。它已是四个面中最成熟的分阶段/声明式/注册式系统（类型化定义 + 确定性组合 + 生成器 + 新鲜度门）。其与 P0 相关的差距是**边界性**的：它应保持归 T5 所有，**不应**并入 T11；T11 消费它产出的场景引用。已注册但暂缓：§1.5 的课程阶段 / 可比性约束已命名但按规矩尚未成为字段（`definition.py` 文档串）。此处纳入为普查语境，非 T11 工作项。 |

### (iv) 内容校验、默认值与版本化

| 方面 | 结论 |
|------|------|
| 校验面 | **单位**：parse 处仅结构性；脆弱性证据描述符要求 `dataset_id`+`target_type`（`unit_definition_loader.cpp:1810`）；除非有标定证据匹配否则降级权威标志（I47，`:1397-1409`）；无 JSON schema。**场景**：`validate_scenario_compiler_shape`（仅形状，运行两次）+ fail-closed 环境 ingestion。**实验**：强构造期校验（标识符正则、种子归一化、JSON 安全深冻结、注册表悬挂引用检查）。**能力/spawn**：fail-closed 的 `validate_capability`/`validate_capability_bundle`/`validate_resolved_platform_spawn_plan` 带拒绝原因词汇 —— 但在 spawn 时调用，而非内容编译时。 |
| 默认值 | **单位**：普遍的内联 `.value(key, default)`、NaN 哨兵、`make_unit_definition_default_sensor()` / `default_aero_tuning` / `default_engine_tuning`、六个内建 `DefaultUnitFactory` 定义（Aircraft/Missile/Ship/Submarine/Facility/AWACS）与程序化 `generate_default_hitboxes`；缺失键静默取默认。**场景**：`.get(key, default)` 加奖励元数据构建器。**实验**：显式类型化 dataclass 默认。 |
| 版本化 | **单位 JSON 无顶层版本字段**（已核实：`examples/config/database/aircraft/units/f16c_block50.json` 无）。版本化仅存在于嵌套证据块 —— `kVulnerabilityEvidenceSchemaVersion = "a2.vulnerability_evidence.v1"`、`kVulnerabilitySurrogateValidationManifestSchemaVersion = "a2.vulnerability_surrogate_validation.v1"`（`:17-19`）—— 以及 Python 侧的 `SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION`（场景生成）、`ENVELOPE_SCHEMA_VERSION`（报告信封，I44）、以及 "WP14-A vocabulary" 常量（能力/spawn）。因此内容版本化是碎片化的：无统一内容 schema 版本。 |
| 错误报告形态 | **单位**：`std::string* error` 出参 + `bool` 返回，首次失败即返回（不累积），加物化时对未知引用的 `spdlog::warn/error`。但并非所有失败都走出参：若干单位映射路径调用未检查的转换器会**抛异常** —— `default_loadout` 条目上的 `std::stoi(key)` 与 `val.get<std::string>()`（`:871`），以及未检查的 `entry["engine_ref"].get<std::string>()`（`:826`）/ `entry["sensor_ref"].get<std::string>()`（`:890`）/ hardpoint `type` 元素的 `t.get<std::string>()`（`:862`）。`load_unit_definitions_json` 的 `try` 只捕获 `fs::filesystem_error`（`:1871`），故非整数的 `default_loadout` key（`std::invalid_argument`）或非字符串引用（`nlohmann::json::type_error`）会**未被捕获**地逃出 loader，而非变成 `bool`/`error` 失败。**场景**：`_compile_from_path` 对非 dict 文件内容抛带源路径上下文的 `ValueError`（`service.py:105`），但 `compile_data` 入口对非 dict 参数抛 `TypeError`（`:94`），`_compile_from_data` 在环境 ingestion 失败时抛 `ValueError`（`:122`）—— 故场景面同时暴露 `TypeError` 与 `ValueError`，非仅 `ValueError`。**实验**：构造/注册时抛 `ValueError`/`TypeError`/`KeyError`。**能力**：结构化 `PlatformCapabilityValidationResult{valid, fail_closed, rejection_reason, errors[]}`。 |
| 与 `P0 ContentCompile` 的差距 | 无统一内容校验编译阶段、无内容 schema 版本；单位 parse 校验最小、场景 parse 校验仅形状；四个面用四种不同错误报告形态；唯一结构化 fail-closed 校验在 spawn 而非编译时运行。 |

## 2. 对分阶段 P0 模型的差距矩阵

行是分析性子阶段（第 0 节透镜）；单元格陈述各面今日所处。"SoT" = 真值源。

| 子阶段 | (i) 单位 | (ii) 场景 | (iii) 实验 |
|--------|----------|-----------|-----------|
| parse | 1,881 行手写映射，非 schema 溯源 | `json.load` + 形状守卫 | 声明式 dataclass 构造 |
| validate | parse 处仅结构性；能力校验推迟到 spawn | 仅形状，x2，无 schema，无跨内容引用检查 | 构造期强校验（正则/归一/冻结/注册表） |
| resolve | 引用在 `spawn()` 内惰性解析（与物化交织） | 编译期 prefab 合并 + imports；`type_name` 在 spawn 解析 | base+delta `compose_config` |
| materialize | 821 行手写 `spawn()` -> flecs 实体（无类型化 setup 包） | 类型化 IR `CompiledScenario` -> `apply_world_layout_to_kernel` -> `spawn_unit` | 生成器渲染运行配置 JSON（受新鲜度门） |
| 阶段契约（§6.1）字段声明 | 无 | 无（仅隐式阶段顺序） | 不适用（上游 Experiment 面） |

横切差距：

- **G-A 两条未链接的内容流水线。** 单位编译（C++，面 i）与场景编译（Python，
  面 ii）不共享任何类型化契约；只在无类型的 `spawn_unit(type_name)` 字符串处相遇。
  P0 要一条统一的分阶段编译，产出类型化 setup 包 + content ids。
- **G-B parse 手写，输出契约却已生成。** *输入* parse（`UnitDefinition` +
  1,881 行映射器）为手工维护，而 *输出* 契约（`CapabilityBundle`、typed platform
  spawn）已在 `dto_schema` 下 schema 溯源。T11/T3 正是要闭合这一不对称。
- **G-C 能力束是投影而非 SoT。** `spawn_unit -> CapabilityBundle` 展开已存在
  （架构的便捷快捷方式目标），但束由单体结构体派生；"新域贡献能力实现"的
  `typed_platform_request` / `spawn_platform({capabilities...})` 方向没有由内容
  驱动的生产者。
- **G-D 无内容编译校验阶段 / 无内容 schema 版本。** 校验在单位 parse 处仅结构性、
  在场景 parse 处仅形状；无内容 schema 版本，且有四种分歧的错误报告形态。
- **G-E 负责人错配。** 最像 P0 的分阶段位于 Python Experiment World
  （`python/scenario/compiler`），而非文档的 P0 负责人（`content/` + 适配器 +
  facade）。**（待裁定）** P0 所有权应将场景编译迁向 `content/`/facade，还是以一个
  声明式 facade-setup 边界满足 —— 转交架构工作线裁定。

## 3. 后续切片建议顺序与红线

本次普查之后建议的 T11 切片顺序。按计划排序，T11"跟随 T1 的 escape-hatch 校验并取代
T3 的 loader 条目"；每切片逐束进行并带 fixture 对拍。

1. **冻结普查 + 差距 + 红线（本切片）。**
2. **内容 escape-hatch schema 勘查（文档 + schema 草案；不改 parse）。** 将面 (i) 的
   106 个语义顶层 key（54 个直接访问 + 52 个经导弹调参 helper）与别名 / 多态 / 哨兵
   模式 —— 覆盖全部 27 个定义文件（单位平台、模块、武器、设施），而非仅 11 个单位平台
   文件 —— 形式化为内容 schema 规范，复用 T1 `dto_schema` codec escape-hatch 先例
   （继承注册、JSON 别名、隐藏切片）。交付物是 schema 草案 + 勘查，而非代码替换。
3. **在现有 API 之后把单位编译分阶段。** 在 `load_unit_definitions_json`/`spawn`
   之后把 parse -> validate -> resolve -> materialize 拆为*声明式*通道，引入真正的
   validate 通道（schema）与 resolve 通道（引用解析），同时保持 `spawn()` 物化字节/
   行为一致。
4. **表驱动化 `unit_definition_loader`（T3 的 loader 条目）。** 把 1,881 行手写映射
   迁到 T1 机制上，逐束进行并带嵌入式参考 fixture 对拍 —— 但已知的尖括号内逗号成员类型
   （如 `default_loadout` 的 `std::unordered_map<int, std::string>`）是已知障碍，须按
   I31 先例先行裁定，X-macro 列表方可纳入它们（见红线）。
5. **能力束作为真值源。** 让内容直接定义能力束（`typed_platform_request` 路径），
   使 `spawn_platform({capabilities...})` 无需从单体结构体派生即可工作；新域通过能力
   注册（G5）接入。
6. **统一内容校验 + 错误报告 + 内容 schema 版本**（跨单位与场景面）。
7. **（边界）** 保持 T5 Experiment 面与场景编译器负责人各自独立；通过类型化 setup 包
   链接单位+场景编译，而非合并流水线。将 P0 所有权问题（G-E）转交架构工作线。

**红线**（T11 关键风险：内容 JSON 是硬性外部面）：

- **内容 JSON 兼容性冻结。** `examples/config/**`（单位数据库与 24 文件实验矩阵）
  不得改动；迁移逐束并带 fixture 对拍。`dto_schema` 生成器不得加入常规 CMake 构建
  （计划非目标）。
- **ABI。** `UnitDefinition` 成员顺序（被 `DefaultUnitFactory::spawn` 逐字段消费）与
  能力/spawn 的 `detail/*.inc` 字段顺序均为 ABI；未经兼容外壳不得重排/改类型/删除。
- **X-macro 逗号阻塞（表驱动化，第 4 步）。** T1 的 X-macro 机制会误拆任何类型声明含
  尖括号内逗号的成员，因为 C 预处理器只配对圆括号；类型别名规避又会破坏迁移所需的类型
  token 逐字节等价。迭代台账的 I31 条目已因同一形状把 `ExecutionBatchStepResult`（其
  `std::vector<std::array<double, 4>>` 字段）整类保留手写。`UnitDefinition::default_loadout`
  （`std::unordered_map<int, std::string>`，`unit_definition.h:190`）已知在列；每个此类
  尖括号内逗号字段须显式裁定（held，或显式裁定别名豁免）方可进入 X-macro 列表。
- **codec escape hatch 必须保留。** `fuze`/`fuse` 别名、引擎扁平-vs-嵌套、
  `engine_tuning`/`aero_tuning` 双路径、`sensor_ref`/`sensor_refs`/内联/`has_sensor`
  变体、entry+`missile_tuning`+`guidance` 三源合并、以及字符串或对象的
  `dependencies[]` 多态是外部 JSON 契约，而非偶然。
- **哨兵语义。** NaN "未设"标记与 `has_*` 存在标志门控工厂默认；其含义须在任何 codec
  迁移中存续。
- **物化行为。** `spawn()` 实体输出须保持字节/行为一致（由
  `test_naval_ship_database.py`、`platform_spawn` 套件与武器制导真实性套件钉扎）。
- **增量式扩展。** 新校验 / 阶段经版本化或 opt-in 路径引入并带再生成新鲜度门；
  兼容外壳仅在 T7 最终残留审计时退役。

## 4. 只读架构测试决定

切片预算允许至多一个可选只读架构测试来钉扎一个原本无守卫的内容面。未新增，原因有二：

1. **已被钉扎。** 每个面均有现存钉扎（第 1 节），多个受 smoke 门：
   `test_naval_ship_database.py`（单位数据库）、`test_scenario_compiler.py` /
   `test_scenario_generation_contracts.py` / `test_scenario_setup_facade_boundary.py`
   （场景编译）、`test_experiment_matrix_freshness.py`（实验矩阵），加上非 smoke 的
   `platform_spawn` 套件（能力/spawn 契约）。
2. **避免固化 T11 必须替换的现状。** 最"无守卫"的事实恰是 T11 受命转换的手写映射
   escape hatch 与仅投影的能力束；此刻钉扎它们只会阻碍迁移而非保护它。

这使本切片保持纯普查 + 文档，符合零行为变更纪律与 T10 / SCAL 普查先例。

## 5. 验证

- 基线（本文之前）在 `9a054c0a` 的受维护 smoke：**459 passed, 45 subtests passed**，
  148.84s（`tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json`，
  `CMO_BUILD_DIR=build-local-win`）。`ef_core`/`ef_py` 构建为 I46 `ef_content` 拆分
  干净地重新 configure（"ninja: no work to do"）。
- 在不做 `clusters --write` 注册表刷新（按切片纪律刻意推迟）的情况下加入这对双语文档，
  会使受 smoke 门的
  `tests/architecture/governance/test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface`
  标记这对未注册的新文档。注册表刷新与迭代台账登记是落地方的步骤（T10 与 SCAL 普查先例
  作了相同的范围裁定）。确切的前后 smoke 数字记于迭代台账条目。

## 相关权威

- [统一架构计划](README.zh.md)（T11 track 定义与风险；T3 loader 条目）
- [仿真系统架构设计](../architecture/simulation_system_architecture_design.zh.md)（SCAL 语义图面；`P0 ContentCompile`；第 6.1 节阶段契约）
- [SCAL 一致性普查（2026-07-20）](scal_conformance_census_20260720.zh.md)（T0 普查先例与格式）
- [T10 证据脊柱普查（2026-07-21）](t10_evidence_spine_census_20260721.zh.md)（相邻普查先例）
- [T6 残留台账（2026-07-20）](t6_residual_ledger.zh.md)
- [仓库整合计划](../repository_consolidation/README.zh.md)（迭代台账与协议）
