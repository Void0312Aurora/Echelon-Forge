# T11 内容 escape-hatch schema 勘查（2026-07-21）

语言：
- 英文规范版：[t11_content_schema_survey_20260721.md](t11_content_schema_survey_20260721.md)
- 中文伴随版：`t11_content_schema_survey_20260721.zh.md`

文档类型：`reference`
生命周期：`maintained`
规范路径：`docs/plan/unified_architecture_program/t11_content_schema_survey_20260721.md`
负责人：`unified architecture program workline`
最后核实：`2026-07-21`
基线提交：`1d25c4d1`

状态：面向[统一架构计划](README.zh.md)的 T11 第二切片内容 escape-hatch schema 勘查，
执行普查第 3 节切片顺序的第 2 步（"内容 escape-hatch schema 勘查（文档 + schema 草案；
不改 parse）"）。它将面 (i) 识别的 **106** 个内容顶层键 —— 在 `parse_unit_json` 中
**直接**读取的 **54** 个，加上 `parse_missile_tuning_json_fields` 在整个顶层 entry 上读取的
**52** 个 —— 覆盖全部 **27** 个定义文件形式化，复用 T1 `dto_schema` codec escape-hatch
先例。本文是描述性普查登记（`reference`），非独立评审：它记录经核实的基线，不携带评审结论。
它不改变任何行为，也不改动 `src/**` / `python/**` / `examples/config/**` 代码；它伴随一份
机器可读的 schema **草案**（`tools/maintenance/dto_schema/drafts/content_unit_schema_draft.json`），
该草案刻意**未接入**生成器（第 4 节）。它建立在
[T11 内容编译流水线普查（2026-07-21）](t11_content_pipeline_census_20260721.zh.md)之上，
并遵守该普查第 3 节红线（在第 6 节复现）。

## 0. 方法与范围

- **键提取。** `src/content/unit_definition_loader.cpp` 中每一处
  `entry.value(...)`、`entry.contains(...)` 与 `entry[...]` 访问点均先经正则枚举，再在基线
  `1d25c4d1` 上逐行对照源码复核。`parse_unit_json`（`:804-1585`）在其 `entry` 参数上访问
  **54** 个不同顶层键。对 `Missile` 类型单位，它还把*整个* `entry` 交给
  `parse_missile_tuning_json_fields`（`:350-427`，在 `:1450` 调用），后者读取**另外 52** 个与前
  54 个不相交的顶层键，语义上共 **106** 个键。54/52 的分界与 106 总数与普查第 1(i) 节完全一致
  （此处独立重新推导；不相交性经程序化检查 —— 两个键集无共同成员）。引用的读取行遵循
  **调用行约定**：多行语句取实际 `.value(...)` / `parse_vector(...)` 调用（含带引号的
  键字面量）所在行，而非赋值起始行。
- **分布。** `examples/config/database` 下每个 **27** 定义文件（排除 2 个
  `damage/vulnerability_evidence` 描述符，它们经独立描述符路径加载）都被解析，记录其顶层键与
  JSON 值类型。计数：**11** 单位平台、**12** 模块、**3** 武器、**1** 设施。每张表的
  "Files [U/M/W/F]" 列报告在顶层携带该键的文件总数，并按类别拆分（U = 单位平台，M = 模块，
  W = 武器，F = 设施）。
- **目标结构体。** `UnitDefinition` 有 **58** 个直接成员（`unit_definition.h:177-265`）；
  `MissileTuningDefinition` 有 **56** 个字段（`unit_definition.h:63-122`）。每个键行都映射到其
  成员并带 `file:line` 声明引用。
- **识别 vs 使用。** `Files` 值为 `0` 表示解析器识别该键但当前没有定义文件在顶层携带它
  （一个识别但未使用的兼容面 —— 对扁平 escape-hatch 形态与多数导弹调参标量而言属预期）。这是
  数据覆盖事实，而非 parse 缺口。
- **可审计性。** 逐键与未读键表体（第 1、3 节）在本文件与其英文规范版之间逐字节一致；仅表头行
  与第 5 节裁定语句经翻译。零行为变更；不改 `src/**`；不改测试。

## 1. 逐键规格表

族与哨兵代码从简；其完整定义位于 schema 草案的 `escape_hatch_families` 与 `sentinel_legend`
对象。简短图例：

- **族（Family）** —— `REQ` 必填判别键 · `ID` 身份 · `MASS` 标量质量 · `REF` 组件引用字符串
  · `ENG` 引擎扁平或嵌套双路径 · `LOAD` 挂点/挂载 · `HP` 生命值 · `SEN` 传感器：
  `sensor_ref` 独立 if + refs/内联/旗标 三路互斥链 · `SON` 声呐 · `FLT` 飞行模型 ·
  `LG` 起落架 · `SCORE` 计分 ·
  `AERO` 机体/aero_tuning 双路径 · `NAV` 海军平台块 · `DMG` 伤害模型（多态
  `dependencies[]`、双形态 `failure_modes`、嵌套/扁平几何）· `AMMO` 弹药 · `MSL` 导弹调参
  三源合并 · `WAR` 战斗部 · `FUZ` fuze/fuse 双拼 + 嵌套半径/逻辑别名 · `EW` 电子战块 ·
  `CMD` 指挥链路 · `DL` 数据链标量。
- **默认 / 哨兵** —— `REQ` 必填 · `type_str` 可选，缺省回退 `type` 字符串 · `0` 数值零 ·
  `16`/`1`/`-1` 整型默认/哨兵 · `true`/`false` 布尔默认 · `NaN` `quiet_NaN` 未设标记 ·
  `FLAG` `has_*` 存在旗标 · `{}` 结构体值初始化/零字面量（无命名预设）· `PRESET` 在命名
  codec 预设之上合并（见第 2 节）· `{100}` loader 字面量生命值 `{100,100}`（`:875`）·
  `[]` 空容器/无操作 · `unset` 空字符串/沿用旧值。

### 1.1 直接顶层键（54）—— `parse_unit_json`

| # | 键 | JSON 类型 | 目标成员 (`unit_definition.h`) | 读取点 (`unit_definition_loader.cpp`) | 默认 / 哨兵 | 族 | 形态 / 别名 | 文件 [U/M/W/F] |
|---:|-----|-----------|-------------------------------|---------------------------------------|-------------|-----|-------------|----------------|
| 1 | `type` | string | `UnitDefinition::type` (unit_definition.h:178) | `807,812` | `REQ` | REQ | discriminant | 27 [U11 M12 W3 F1] |
| 2 | `name` | string | `UnitDefinition::name` (unit_definition.h:179) | `818` | `type_str` | ID | optional: falls back to the type string (:818); single-object load_file path gates on presence (:1617) but the units[] path does not | 27 [U11 M12 W3 F1] |
| 3 | `mass_kg` | number | `UnitDefinition::mass_kg` (unit_definition.h:250) | `819` | `0` | MASS | - | 4 [U1 W3] |
| 4 | `engine_ref` | string | `UnitDefinition::engine_ref` (unit_definition.h:184) | `825,826` | `unset` | REF | unchecked get<string> | 2 [U2] |
| 5 | `engine` | object | `UnitDefinition::engine_data` (unit_definition.h:193) | `829,830` | `{}` | ENG | nested form; nested tuning -> default_engine_tuning() preset (:836-839) | 2 [M2] |
| 6 | `mil_thrust_n` | number | `UnitDefinition::engine_data.mil_thrust_n` (unit_definition.h:193) | `842` | `0` | ENG | flat form | 0 |
| 7 | `ab_thrust_n` | number | `UnitDefinition::engine_data.ab_thrust_n` (unit_definition.h:193) | `843` | `0` | ENG | flat form | 0 |
| 8 | `sfc_mil` | number | `UnitDefinition::engine_data.sfc_mil` (unit_definition.h:193) | `844` | `0` | ENG | flat form | 0 |
| 9 | `sfc_ab` | number | `UnitDefinition::engine_data.sfc_ab` (unit_definition.h:193) | `845` | `0` | ENG | flat form | 0 |
| 10 | `bypass_ratio` | number | `UnitDefinition::engine_data.bypass_ratio` (unit_definition.h:193) | `846` | `0` | ENG | flat form | 0 |
| 11 | `engine_tuning` | object | `UnitDefinition::engine_data.tuning` (unit_definition.h:193) | `847,852` | `PRESET` | ENG | alias of engine.tuning; default_engine_tuning() preset-then-merge (:848-852) | 0 |
| 12 | `hardpoints` | array | `UnitDefinition::hardpoints` (unit_definition.h:189) | `855,856` | `[]` | LOAD | - | 2 [U2] |
| 13 | `default_loadout` | object | `UnitDefinition::default_loadout` (unit_definition.h:190) | `869,870` | `[]` | LOAD | int-key map; std::stoi(key); COMMA-BLOCKER | 2 [U2] |
| 14 | `health` | object | `UnitDefinition::health` (unit_definition.h:230) | `876,877` | `{100}` | HP | - | 11 [U10 F1] |
| 15 | `sensor_ref` | string | `UnitDefinition::sensor_ref` (unit_definition.h:182) | `889,890` | `unset` | SEN | independent if (:889-893), can coexist with the chain; unchecked get<string> | 5 [U5] |
| 16 | `sensor_refs` | array | `UnitDefinition::sensor_refs` (unit_definition.h:183) | `894,895` | `[]` | SEN | three-way chain head (if, :894) | 2 [U2] |
| 17 | `sensor` | object | `UnitDefinition::sensor` (unit_definition.h:232) | `899,901;1490` | `PRESET+FLAG` | SEN | three-way chain else-if (:899); object form only; merges over make_unit_definition_default_sensor() 30 km preset (:883, missile re-preset :1491) | 8 [U1 M6 F1] |
| 18 | `has_sensor` | bool | `UnitDefinition::has_sensor` (unit_definition.h:231) | `905,906` | `FLAG` | SEN | three-way chain tail (else-if, :905) | 0 |
| 19 | `mounted_sensors` | array | `UnitDefinition::mounted_sensors` (unit_definition.h:233) | `909,910` | `[]` | SEN | per-mount make_unit_definition_default_sensor() preset (:914) | 1 [U1] |
| 20 | `sonar` | object | `UnitDefinition::sonar` (unit_definition.h:235) | `922,924` | `PRESET+FLAG` | SON | inline; merges over make_default_sonar_definition() 25 km preset (:886) | 1 [M1] |
| 21 | `mounted_sonars` | array | `UnitDefinition::mounted_sonars` (unit_definition.h:236) | `926,927` | `[]` | SON | per-mount make_default_sonar_definition() preset (:931) | 2 [U2] |
| 22 | `has_flight_model` | bool | `UnitDefinition::has_flight_model` (unit_definition.h:238) | `939` | `FLAG` | FLT | - | 0 |
| 23 | `flight_model` | object | `UnitDefinition::flight_model` (unit_definition.h:239) | `941,943` | `{}+FLAG` | FLT | in-block literals when key present: min_g -3.0 (:951), takeoff 80 / landing 70 / taxi 15 (:953-955) | 8 [U5 W3] |
| 24 | `has_landing_gear` | bool | `UnitDefinition::has_landing_gear` (unit_definition.h:243) | `958` | `FLAG` | LG | - | 0 |
| 25 | `landing_gear` | object | `UnitDefinition::landing_gear` (unit_definition.h:244) | `960,962` | `PRESET+FLAG` | LG | loader-literal paved-only preset {false,0.02,3.0,2.0,1.0,false,5.0} (:959) | 1 [U1] |
| 26 | `has_score` | bool | `UnitDefinition::has_score` (unit_definition.h:246) | `973` | `true` | SCORE | default true | 1 [U1] |
| 27 | `score` | object | `UnitDefinition::score` (unit_definition.h:247) | `975,976` | `{}` | SCORE | - | 0 |
| 28 | `airframe` | object | `UnitDefinition::airframe` (unit_definition.h:212) | `983,984` | `{}` | AERO | nested tuning -> default_aero_tuning() preset (:994-997) | 5 [U5] |
| 29 | `aero_tuning` | object | `UnitDefinition::airframe.tuning` (unit_definition.h:212) | `1000,1005` | `PRESET` | AERO | alias of airframe.tuning; default_aero_tuning() preset-then-merge (:1001-1005) | 0 |
| 30 | `stall_state` | object | `UnitDefinition::stall_state` (unit_definition.h:241) | `1007,1009` | `{}+FLAG` | AERO | - | 0 |
| 31 | `ship_platform` | object | `UnitDefinition::ship_platform` (unit_definition.h:214) | `1014,1016` | `{}+FLAG` | NAV | - | 4 [U4] |
| 32 | `submarine_platform` | object | `UnitDefinition::submarine_platform` (unit_definition.h:216) | `1060,1062` | `{}+FLAG` | NAV | - | 1 [U1] |
| 33 | `naval_stores` | object | `UnitDefinition::naval_stores` (unit_definition.h:218) | `1093,1095` | `{}+FLAG` | NAV | - | 2 [U2] |
| 34 | `naval_logistics` | object | `UnitDefinition::naval_logistics` (unit_definition.h:220) | `1116,1118` | `{}+FLAG` | NAV | - | 1 [U1] |
| 35 | `naval_weapon_system` | object | `UnitDefinition::naval_weapon_system` (unit_definition.h:222) | `1139,1140` | `{}+FLAG` | NAV | mounts[] required | 1 [U1] |
| 36 | `embarked_air_ops` | object | `UnitDefinition::embarked_air_ops` (unit_definition.h:224) | `1169,1171` | `{}+FLAG` | NAV | in-block enabled defaults true (:1184) | 1 [U1] |
| 37 | `damage_model` | object | `UnitDefinition::damage_model` (unit_definition.h:225) | `1189,1190` | `{}` | DMG | poly dependencies[]: string\|object (:1232-1254); failure_modes array\|object (:1305-1331) + failure_mode_weights overlay (:1332-1345); geometry nested-object\|flat-key dual path (:84-154, call :1351) with size/offset box fallback (:1352-1360) | 9 [U8 F1] |
| 38 | `has_ammo` | bool | `UnitDefinition::has_ammo` (unit_definition.h:252) | `1435` | `FLAG` | AMMO | - | 2 [U2] |
| 39 | `ammo` | object | `UnitDefinition::ammo` (unit_definition.h:253) | `1437,1439` | `{}+FLAG` | AMMO | - | 1 [U1] |
| 40 | `missile_tuning` | object | `UnitDefinition::missile_tuning` (unit_definition.h:264) | `1452,1453` | `{}` | MSL | merge source 2 (nested) | 0 |
| 41 | `guidance` | object | `UnitDefinition::missile_tuning` (unit_definition.h:264) | `1455,1456` | `{}` | MSL | merge source 3; alias active_seek_range,off_boresight_cap; type->seeker_type | 3 [W3] |
| 42 | `warhead` | object | `MissileTuningDefinition::warhead_profile` (unit_definition.h:118) | `1481,1482` | `{}+FLAG` | WAR | - | 3 [W3] |
| 43 | `fuze` | object | `MissileTuningDefinition::fuze_profile` (unit_definition.h:120) | `1484,1485` | `{}+FLAG` | FUZ | spelling A; radius alias trigger_radius_m\|trigger_radius\|radius_m (:476-482); trigger_logic\|trigger_mode fallback (:485-486) | 3 [W3] |
| 44 | `fuse` | object | `MissileTuningDefinition::fuze_profile` (unit_definition.h:120) | `1487,1488` | `{}+FLAG` | FUZ | spelling B (alias of fuze); same nested radius/logic aliases (:476-482, :485-486) | 0 |
| 45 | `has_command_link` | bool | `UnitDefinition::has_command_link` (unit_definition.h:255) | `1521` | `FLAG` | CMD | - | 9 [U9] |
| 46 | `command_link` | object | `UnitDefinition::command_link` (unit_definition.h:256) | `1523,1525` | `{}+FLAG` | CMD | - | 8 [U8] |
| 47 | `has_data_link` | bool | `UnitDefinition::has_data_link` (unit_definition.h:258) | `1530` | `FLAG` | DL | - | 11 [U10 F1] |
| 48 | `data_link_network_id` | int | `UnitDefinition::data_link_network_id` (unit_definition.h:259) | `1531` | `0` | DL | - | 8 [U8] |
| 49 | `data_link_max_reports_per_update` | int | `UnitDefinition::data_link_max_reports_per_update` (unit_definition.h:260) | `1533` | `16` | DL | max(0,x) | 0 |
| 50 | `data_link_max_messages_per_update` | int | `UnitDefinition::data_link_max_messages_per_update` (unit_definition.h:261) | `1535,1536` | `-1` | DL | falls back to reports value | 0 |
| 51 | `rwr` | object | `UnitDefinition::rwr_data` (unit_definition.h:203) | `1540,1541` | `{}` | EW | - | 1 [M1] |
| 52 | `jammer` | object | `UnitDefinition::jammer_data` (unit_definition.h:202) | `1545,1546` | `{}` | EW | - | 1 [M1] |
| 53 | `countermeasures` | object | `UnitDefinition::cms_data` (unit_definition.h:206) | `1563,1564` | `{}` | EW | member is cms_data | 1 [M1] |
| 54 | `esm` | object | `UnitDefinition::esm_data` (unit_definition.h:205) | `1574,1575` | `{}+FLAG` | EW | - | 1 [U1] |

### 1.2 导弹调参 helper 键（52）—— `parse_missile_tuning_json_fields` 作用于顶层 entry

读取点为 helper 行；`(@1450)` 标记传入整个顶层 `entry` 的调用。同一 helper 还被作用于嵌套的
`missile_tuning`（`:1453`）与 `guidance`（`:1457`）；那些是相同键名的嵌套读取，而非额外的顶层键。

| # | 键 | JSON 类型 | 目标成员 (`unit_definition.h`) | 读取点 (`unit_definition_loader.cpp`) | 默认 / 哨兵 | 族 | 形态 / 别名 | 文件 [U/M/W/F] |
|---:|-----|-----------|-------------------------------|---------------------------------------|-------------|-----|-------------|----------------|
| 1 | `max_speed` | number | `MissileTuningDefinition::max_speed` (unit_definition.h:64) | `365 (@1450)` | `NaN` | MSL | seed=flight_model.max_speed | 0 |
| 2 | `turn_rate` | number | `MissileTuningDefinition::turn_rate` (unit_definition.h:65) | `366 (@1450)` | `NaN` | MSL | seed=flight_model.max_turn_rate | 0 |
| 3 | `fuse_distance` | number | `MissileTuningDefinition::fuse_distance` (unit_definition.h:66) | `367 (@1450)` | `NaN` | MSL | also set by warhead/fuze radius | 0 |
| 4 | `damage` | number | `MissileTuningDefinition::damage` (unit_definition.h:67) | `368 (@1450)` | `NaN` | MSL | also set by warhead | 0 |
| 5 | `seeker_fov_deg` | number | `MissileTuningDefinition::seeker_fov_deg` (unit_definition.h:68) | `369 (@1450)` | `NaN` | MSL | - | 0 |
| 6 | `seeker_lock_range` | number | `MissileTuningDefinition::seeker_lock_range` (unit_definition.h:69) | `370 (@1450)` | `NaN` | MSL | alias active_seek_range@guidance:1469 | 0 |
| 7 | `guidance_delay_s` | number | `MissileTuningDefinition::guidance_delay_s` (unit_definition.h:70) | `371 (@1450)` | `NaN` | MSL | - | 0 |
| 8 | `guidance_update_period_s` | number | `MissileTuningDefinition::guidance_update_period_s` (unit_definition.h:71) | `373 (@1450)` | `NaN` | MSL | - | 0 |
| 9 | `max_flight_time_s` | number | `MissileTuningDefinition::max_flight_time_s` (unit_definition.h:72) | `374 (@1450)` | `NaN` | MSL | - | 2 [W2] |
| 10 | `nav_gain` | number | `MissileTuningDefinition::nav_gain` (unit_definition.h:73) | `375 (@1450)` | `NaN` | MSL | used nested@guidance | 0 |
| 11 | `apn_target_accel_gain` | number | `MissileTuningDefinition::apn_target_accel_gain` (unit_definition.h:74) | `376 (@1450)` | `NaN` | MSL | used nested@guidance | 0 |
| 12 | `sensor_max_range` | number | `MissileTuningDefinition::sensor_max_range` (unit_definition.h:75) | `377 (@1450)` | `NaN` | MSL | alias@guidance:1471; entry.sensor.max_range | 0 |
| 13 | `sensor_fov_deg` | number | `MissileTuningDefinition::sensor_fov_deg` (unit_definition.h:76) | `378 (@1450)` | `NaN` | MSL | entry.sensor.fov_deg | 0 |
| 14 | `sensor_scan_period` | number | `MissileTuningDefinition::sensor_scan_period` (unit_definition.h:77) | `379 (@1450)` | `NaN` | MSL | - | 0 |
| 15 | `sensor_detection_prob` | number | `MissileTuningDefinition::sensor_detection_prob` (unit_definition.h:78) | `380 (@1450)` | `NaN` | MSL | - | 0 |
| 16 | `sensor_bearing_noise_std` | number | `MissileTuningDefinition::sensor_bearing_noise_std` (unit_definition.h:79) | `382 (@1450)` | `NaN` | MSL | - | 0 |
| 17 | `sensor_range_noise_std` | number | `MissileTuningDefinition::sensor_range_noise_std` (unit_definition.h:80) | `384 (@1450)` | `NaN` | MSL | - | 0 |
| 18 | `sensor_track_memory_s` | number | `MissileTuningDefinition::sensor_track_memory_s` (unit_definition.h:81) | `385 (@1450)` | `NaN` | MSL | - | 0 |
| 19 | `seeker_type` | int | `MissileTuningDefinition::seeker_type` (unit_definition.h:82) | `386 (@1450)` | `-1` | MSL | inferred from guidance.type | 0 |
| 20 | `seeker_activation_range_m` | number | `MissileTuningDefinition::seeker_activation_range_m` (unit_definition.h:83) | `388 (@1450)` | `NaN` | MSL | - | 0 |
| 21 | `seeker_gimbal_limit_deg` | number | `MissileTuningDefinition::seeker_gimbal_limit_deg` (unit_definition.h:84) | `390 (@1450)` | `NaN` | MSL | - | 0 |
| 22 | `seeker_ifov_deg` | number | `MissileTuningDefinition::seeker_ifov_deg` (unit_definition.h:85) | `391 (@1450)` | `NaN` | MSL | - | 0 |
| 23 | `bearing_filter_tau_s` | number | `MissileTuningDefinition::bearing_filter_tau_s` (unit_definition.h:86) | `392 (@1450)` | `NaN` | MSL | - | 0 |
| 24 | `elevation_filter_tau_s` | number | `MissileTuningDefinition::elevation_filter_tau_s` (unit_definition.h:87) | `394 (@1450)` | `NaN` | MSL | - | 0 |
| 25 | `range_filter_tau_s` | number | `MissileTuningDefinition::range_filter_tau_s` (unit_definition.h:88) | `395 (@1450)` | `NaN` | MSL | - | 0 |
| 26 | `track_break_time_s` | number | `MissileTuningDefinition::track_break_time_s` (unit_definition.h:89) | `396 (@1450)` | `NaN` | MSL | - | 0 |
| 27 | `boost_time_s` | number | `MissileTuningDefinition::boost_time_s` (unit_definition.h:90) | `397 (@1450)` | `NaN` | MSL | - | 0 |
| 28 | `sustain_time_s` | number | `MissileTuningDefinition::sustain_time_s` (unit_definition.h:91) | `398 (@1450)` | `NaN` | MSL | - | 0 |
| 29 | `boost_thrust_n` | number | `MissileTuningDefinition::boost_thrust_n` (unit_definition.h:92) | `399 (@1450)` | `NaN` | MSL | - | 0 |
| 30 | `sustain_thrust_n` | number | `MissileTuningDefinition::sustain_thrust_n` (unit_definition.h:93) | `400 (@1450)` | `NaN` | MSL | - | 0 |
| 31 | `reference_area_m2` | number | `MissileTuningDefinition::reference_area_m2` (unit_definition.h:94) | `401 (@1450)` | `NaN` | MSL | - | 0 |
| 32 | `cd0_subsonic` | number | `MissileTuningDefinition::cd0_subsonic` (unit_definition.h:95) | `402 (@1450)` | `NaN` | MSL | - | 0 |
| 33 | `cd0_supersonic` | number | `MissileTuningDefinition::cd0_supersonic` (unit_definition.h:96) | `403 (@1450)` | `NaN` | MSL | - | 0 |
| 34 | `induced_drag_k` | number | `MissileTuningDefinition::induced_drag_k` (unit_definition.h:97) | `404 (@1450)` | `NaN` | MSL | - | 0 |
| 35 | `cd0_mach_breakpoints` | array | `MissileTuningDefinition::cd0_mach_breakpoints` (unit_definition.h:98) | `405 (@1450)` | `[]` | MSL | parse_vector | 0 |
| 36 | `cd0_mach_values` | array | `MissileTuningDefinition::cd0_mach_values` (unit_definition.h:99) | `406 (@1450)` | `[]` | MSL | parse_vector | 0 |
| 37 | `induced_drag_k_mach_breakpoints` | array | `MissileTuningDefinition::induced_drag_k_mach_breakpoints` (unit_definition.h:100) | `407 (@1450)` | `[]` | MSL | parse_vector | 0 |
| 38 | `induced_drag_k_mach_values` | array | `MissileTuningDefinition::induced_drag_k_mach_values` (unit_definition.h:101) | `408 (@1450)` | `[]` | MSL | parse_vector | 0 |
| 39 | `propellant_mass_kg` | number | `MissileTuningDefinition::propellant_mass_kg` (unit_definition.h:102) | `409 (@1450)` | `NaN` | MSL | - | 0 |
| 40 | `max_lateral_g` | number | `MissileTuningDefinition::max_lateral_g` (unit_definition.h:103) | `410 (@1450)` | `NaN` | MSL | seed=flight_model.max_g | 0 |
| 41 | `autopilot_tau_s` | number | `MissileTuningDefinition::autopilot_tau_s` (unit_definition.h:104) | `411 (@1450)` | `NaN` | MSL | used nested@guidance | 0 |
| 42 | `autopilot_damping` | number | `MissileTuningDefinition::autopilot_damping` (unit_definition.h:105) | `412 (@1450)` | `NaN` | MSL | - | 0 |
| 43 | `autopilot_order` | int | `MissileTuningDefinition::autopilot_order` (unit_definition.h:108) | `413 (@1450)` | `1` | MSL | nonzero default sentinel | 0 |
| 44 | `max_accel_response_g_per_s` | number | `MissileTuningDefinition::max_accel_response_g_per_s` (unit_definition.h:109) | `415 (@1450)` | `NaN` | MSL | used nested@guidance | 0 |
| 45 | `mach_transonic_start` | number | `MissileTuningDefinition::mach_transonic_start` (unit_definition.h:110) | `416 (@1450)` | `NaN` | MSL | - | 0 |
| 46 | `mach_transonic_end` | number | `MissileTuningDefinition::mach_transonic_end` (unit_definition.h:111) | `417 (@1450)` | `NaN` | MSL | - | 0 |
| 47 | `cd0_power_on_ratio` | number | `MissileTuningDefinition::cd0_power_on_ratio` (unit_definition.h:112) | `418 (@1450)` | `NaN` | MSL | - | 0 |
| 48 | `min_launch_range_m` | number | `MissileTuningDefinition::min_launch_range_m` (unit_definition.h:113) | `419 (@1450)` | `NaN` | MSL | alias@guidance:1475 | 0 |
| 49 | `max_launch_off_boresight_deg` | number | `MissileTuningDefinition::max_launch_off_boresight_deg` (unit_definition.h:114) | `421 (@1450)` | `NaN` | MSL | alias off_boresight_cap@guidance:1473 | 0 |
| 50 | `lobl_required` | bool | `MissileTuningDefinition::lobl_required` (unit_definition.h:115) | `422 (@1450)` | `false` | MSL | also@guidance:1479 | 0 |
| 51 | `midcourse_datalink_supported` | bool | `MissileTuningDefinition::midcourse_datalink_supported` (unit_definition.h:116) | `424 (@1450)` | `false` | MSL | also@guidance:1477 | 0 |
| 52 | `use_kalman_seeker` | bool | `MissileTuningDefinition::use_kalman_seeker` (unit_definition.h:117) | `425 (@1450)` | `false` | MSL | - | 0 |

## 2. escape-hatch 族（经核实源码行）

- **字段别名 / 双表示。** `fuze` **与** `fuse` 都路由到 `parse_fuze_json_fields`
  （`:1484-1489`）。引擎为嵌套 `engine` 对象**或**扁平顶层
  `mil_thrust_n`/`ab_thrust_n`/`sfc_mil`/`sfc_ab`/`bypass_ratio`（`:829-846`）；扁平形态存在时
  覆盖嵌套形态。`engine_tuning`（顶层）别名 `engine.tuning`（`:847-853`）；`aero_tuning`
  （顶层）别名 `airframe.tuning`（`:1000-1006`）。在 `fuze`/`fuse` 内部，触发半径接受
  `trigger_radius_m` / `trigger_radius` / `radius_m`（首个匹配生效的 `if/else-if`，
  `:476-482`），`trigger_logic` 回退到 `trigger_mode`（`:485-486`）。
- **四种 sensor 变体（独立 `if` + 三路互斥链）。** `sensor_ref`（字符串）是**独立**的 `if`
  （`:889-893`）；`sensor_refs`（数组）/ 内联 `sensor`（对象）/ `has_sensor`（布尔）构成
  互斥的 `if / else-if` 链（`:894-907`），链内仅第一个匹配的形态生效。因此 `sensor_ref`
  可与链中任一形态同时生效 —— 维护中的 `ddg51_flight_i_uss_arleigh_burke.json` 同时携带
  `sensor_ref` 与 `sensor_refs`。
- **三源导弹调参合并。** `parse_missile_tuning_json_fields` 作用于扁平顶层 `entry`（`:1450`），
  再作用于嵌套 `missile_tuning`（`:1453`）与嵌套 `guidance`（`:1457`）。`guidance` 块新增按键
  别名：`active_seek_range` → `seeker_lock_range`（`:1469`）、`off_boresight_cap` →
  `max_launch_off_boresight_deg`（`:1473`）、以及 `guidance.type` → `seeker_type` 推断
  （`:1459-1466`）。`warhead`（`:1481-1483`）与 `fuze`/`fuse`（`:1484-1489`）贡献进一步的嵌套
  合并，也可设置 `fuse_distance`/`damage`。
- **多态 / 双形态嵌套节点。** 伤害组件 `dependencies[]` 条目可为裸字符串**或**对象
  （`:1232-1254`）—— 面 (i) 中唯一的字符串或对象多态。组件 `failure_modes` 块本身是双形态：
  模式名数组**或**模式到权重的对象（`:1305-1331`），另有独立的 `failure_mode_weights` 对象
  覆盖层（`:1332-1345`）。组件几何是嵌套-vs-扁平双路径：类型化键由
  `parse_damage_component_geometry_json_fields`（`:84-154`，调用点 `:1351`）读取，既接受
  嵌套 `geometry` 对象（`primitive`、`source`、`vertices_m`、`thin_prism`、
  `obb.axes`/`half_extents_m`，`:107-145`），也接受扁平 `geometry_*` 键（`:90-105`、
  `:146-153`）；当无正半长时回退到旧式 `size`/`offset` 盒半长（`:1352-1360`）。
- **回退链。** 组件 `offset`/`size` 回退到父 hitbox（`:1277-1291`）；`component.system` 回退到
  `component.name`（`:1225`）。
- **哨兵与 codec 预设。** `std::numeric_limits<double>::quiet_NaN()` "未设"标记（在
  `MissileTuningDefinition` 中普遍存在）、`has_*` 存在旗标、以及负整型哨兵（`seeker_type = -1`、
  `data_link_max_messages_per_update = -1`）门控工厂默认；`autopilot_order = 1` 是刻意的非零内容
  默认（`unit_definition.h:106-108`）。五个面在命名 codec **预设**之上合并，而非值初始化的零：
  `sensor` / 每挂载 / 导弹导引头 sensor（`make_unit_definition_default_sensor()`，30 km ——
  `:883`、`:914`、`:1491`）、`sonar` / 每挂载 sonar（`make_default_sonar_definition()`，25 km
  —— `:886`、`:931`）、`engine.tuning`/`engine_tuning`（`flight_dynamics::default_engine_tuning()`
  —— `:838`、`:850`）、`airframe.tuning`/`aero_tuning`（`flight_dynamics::default_aero_tuning()`
  —— `:996`、`:1003`）、以及 `landing_gear`（loader 字面量 paved-only 预设 —— `:959`）；`health`
  落在 loader 字面量 `{100,100}` 上（`:875`），`flight_model` 携带块内回退字面量（`min_g` -3.0、
  takeoff 80 / landing 70 / taxi 15，`:951-955`）。

## 3. 存在但未读取的顶层键与普查交叉核对

有七个顶层键出现在 27 个定义文件中，但**不**在解析器读取的 106 个键之内：

| 键 | 文件 [U/M/W/F] | 类别 |
|-----|-----------------|------|
| `_deferred_runtime_claims` | 1 [U1] | annotation (underscore-prefixed) |
| `_ground_schema` | 1 [U1] | annotation (underscore-prefixed) |
| `_provenance` | 12 [U7 M5] | annotation (underscore-prefixed) |
| `_real_world` | 3 [U3] | annotation (underscore-prefixed) |
| `ew_suite_ref` | 1 [U1] | SEMANTIC (unread by parser) |
| `rcs` | 2 [M2] | SEMANTIC (unread by parser) |
| `rcs_profile_ref` | 1 [U1] | SEMANTIC (unread by parser) |

- **四个下划线注释**（`_provenance` ×12、`_real_world` ×3、`_ground_schema`、
  `_deferred_runtime_claims`）是溯源/schema 注释，按约定被解析器忽略。
- **三个语义未读键** —— `ew_suite_ref`、`rcs_profile_ref`、`rcs` —— 携带被解析器静默丢弃的真实
  内容。与普查交叉核对：普查第 1(i) 节将 `ew_suite_ref`/`rcs_profile_ref` 列为 `UnitDefinition`
  成员（它们确实存在：`unit_definition.h:185-186`），并称 `spawn`"按名解析
  `sensor_ref`/`engine_ref`/`ew_suite_ref`/`rcs_profile_ref` …"。本勘查加以精化：`parse_unit_json`
  **从不赋值** `def.ew_suite_ref` 或 `def.rcs_profile_ref`（在 `unit_definition_loader.cpp` 上
  grep 返回零匹配；这两个符号仅出现于 `unit_definition.h` 与
  `src/models/core/default_unit_factory.h`），故 spawn 时的解析作用在空字符串上 —— 这两个键是
  死内容边。同理 `rcs`（`RCSProfile` 模块载荷）从不被读取，故 2 个 `RCSProfile` 模块文件仅以
  `name`+`type` 加载，`UnitDefinition::rcs_data` 保持默认初始化。这**不**改变 **106** 总数：这些
  键存在于数据但未被读取，且 **54**/**52** 分界与 **106** 总数与普查完全一致。无需修正普查数字；
  这是关于存在但未读取内容键的补充精度，转交协调者裁定。

## 4. 机器可读 schema 草案（格式与"未接线"证据）

草案是 `tools/maintenance/dto_schema/drafts/content_unit_schema_draft.json` —— 一份静态 JSON
勘查产物，编码每个键的静态规格：`key`、`json_type`、`polymorphic`（仅指顶层值形态可变性；
嵌套多态记录于 `forms_aliases` 与族描述）、`target`（结构体 / 成员 / 声明 `file:line`）、
`read_site`、`default_or_sentinel`、`escape_hatch_family`、`forms_aliases`
与 `distribution`。它镜像 T1 `dto_schema` `Field` 模型概念（`name`、`cpp_type`、`default`，以及
`tools/maintenance/dto_schema/model.py` 中的 `json_key`/`hidden`/`readonly` 保留绑定元数据），
并为内容关切扩展（别名、多态形态）。它还携带 `escape_hatch_families`、`sentinel_legend`、
`present_but_unread_top_level_keys` 与 `xmacro_comma_blockers`。

"未接线"是结构性保证，而非约定：

- 草案是 **JSON**，非 Python 模块：`generate.py` 仅导入
  `tools/maintenance/dto_schema/schemas/__init__.py`（`SCHEMA_MODULES`）中列出的模块；它不做目录
  扫描，故未被导入的文件无法进入生成集。
- 它位于新的 `drafts/` 子目录，**不**在 `schemas/` 下。新鲜度门
  `tests/architecture/governance/test_dto_schema_freshness.py` 对 `schemas/*.py` 做 glob 并断言该
  集合等于已注册清单；`drafts/` 下的 JSON 文件既不被该 glob 匹配也不在 `SCHEMA_MODULES` 中。
- 因非 `.py`，它在 `ruff` 的 Python 面与 DTO builder 之外。
- 文件的 `_draft` 对象声明 `status: "draft, not wired"` 并注明来源普查。第 7 节的验证显示
  `generate.py --check` 输出与每个生成产物逐字节不变。

## 5. X-macro 逗号阻塞清单

对全部 **58** 个 `UnitDefinition` 成员与全部 **56** 个 `MissileTuningDefinition` 字段扫描了类型
声明含尖括号内逗号的情形（T1 X-macro 机制会误拆的 token，因为 C 预处理器只配对圆括号）。恰有
**一个**成员符合：

| 结构体 | 成员 | 类型 | 声明 | 裁定建议 |
|--------|------|------|------|----------|
| `UnitDefinition` | `default_loadout` | `std::unordered_map<int, std::string>` | `unit_definition.h:190` | **HELD**（保留手写），依据 I31 `ExecutionBatchStepResult`（`std::vector<std::array<double, 4>>`）先例；在进入任何 X-macro 列表前须裁定；显式排除别名/`typedef` 豁免（它会破坏迁移所需的类型 token 逐字节等价）。 |

`MissileTuningDefinition` **无**：其唯一的模板成员是 `std::vector<double>`
（`cd0_mach_breakpoints`、`cd0_mach_values`、`induced_drag_k_mach_breakpoints`、
`induced_drag_k_mach_values`），均无尖括号内逗号。这确认并补全了普查红线关于 `default_loadout`
"已知在列"的说明，且它是两个目标结构体中唯一的阻塞项 —— 切片 4（表驱动化
`unit_definition_loader`）的前置裁定。

## 6. 红线（复现自普查第 3 节）

- **内容 JSON 兼容性冻结。** `examples/config/**`（单位数据库与 24 文件实验矩阵）不得改动；迁移
  逐束并带 fixture 对拍。`dto_schema` 生成器不得加入常规 CMake 构建（计划非目标）。
- **ABI。** `UnitDefinition` 成员顺序（被 `DefaultUnitFactory::spawn` 逐字段消费）与能力/spawn 的
  `detail/*.inc` 字段顺序均为 ABI；未经兼容外壳不得重排/改类型/删除。
- **X-macro 逗号阻塞。** 每个尖括号内逗号字段（此处：`default_loadout`）在进入 X-macro 列表前须
  依 I31 先例显式裁定（held，或显式裁定别名豁免）。
- **codec escape hatch 必须保留。** `fuze`/`fuse` 别名、引擎扁平-vs-嵌套、
  `engine_tuning`/`aero_tuning` 双路径、`sensor_ref`/`sensor_refs`/内联/`has_sensor` 变体、
  entry+`missile_tuning`+`guidance` 三源合并、以及字符串或对象的 `dependencies[]` 多态是外部
  JSON 契约，而非偶然。
- **哨兵语义。** NaN "未设"标记与 `has_*` 存在旗标门控工厂默认；其含义须在任何 codec 迁移中
  存续。
- **物化行为。** `spawn()` 实体输出须保持字节/行为一致（由 `test_naval_ship_database.py`、
  `platform_spawn` 套件与武器制导真实性套件钉扎）。
- **增量式扩展。** 新校验 / 阶段经版本化或 opt-in 路径引入并带再生成新鲜度门；兼容外壳仅在 T7
  最终残留审计时退役。

## 7. 验证

- `python tools/maintenance/dto_schema/generate.py --check` —— 所有产物为最新；对生成树
  （`gym_envs/scenario_loader/_generated/` 与 `src/**/detail/*.inc`）的 `git diff` 为空，证明草案
  未接线。
- `python tools/maintenance/document_link_audit.py` —— 0 issues。
- `python tools/maintenance/translate_docs_batch.py audit` —— 新配对
  `plan/unified_architecture_program/t11_content_schema_survey_20260721` 报告为 `unregistered`
  （其 `pair_id` 尚未进入 `docs/standards/bilingual_document_clusters.json`）；`pair_count` 从
  84 升到 85，而 `synced` 保持 84，`diverged`/`missing` 保持 0。注册表刷新（`clusters --write`）
  与迭代台账登记是落地方的步骤，遵循普查第 5 节的范围裁定先例。
- `git diff --check` —— 干净（仅新增未跟踪文件；无跟踪文件空白改动）。`ruff` 不适用于草案
  （它是 JSON）。
- 双语自查 —— 中英文携带相同标题数、相同表格行数（54 / 52 / 7 表体行），以及关键数字
  （106、54、52、58、56、27）相等的出现次数。

## 相关权威

- [T11 内容编译流水线普查（2026-07-21）](t11_content_pipeline_census_20260721.zh.md)（本切片扩展的普查；第 3 节切片顺序与红线）
- [统一架构计划](README.zh.md)（T11 track 定义与风险；T3 loader 条目）
- [仿真系统架构设计](../architecture/simulation_system_architecture_design.zh.md)（SCAL 语义图面；`P0 ContentCompile`）
- [仓库整合计划](../repository_consolidation/README.zh.md)（迭代台账与协议）
