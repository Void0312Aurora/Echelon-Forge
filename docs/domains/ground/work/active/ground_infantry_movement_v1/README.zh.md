# Ground 单兵移动 v1

语言：[英文规范页](README.md)；本页为中文配套。

Document kind: `work-package`
Lifecycle: `active`
Canonical: `docs/domains/ground/work/active/ground_infantry_movement_v1/README.md`
Owner: `domains/ground`
Accepted: `2026-09-24`

## 目的

在不假装陆上域已经具备路线规划、队形或完整物理的前提下，为单个徒步
Ground fixture 准入第一条维护中的原生移动切片。

## 合同

- `Ground_Infantry_Soldier_MVP` 以原生 `UnitType::Ground` 身份加载。
- active 的 `MissionCommand` 且 `ground_task_mode = MoveStatic` 提供 NAV 航向和请求速度。
- `GroundInfantryMovement` 以 `builtin.system.ground_infantry_movement` 注册到默认组合
  stage 34。
- 系统在当前位置读取共享 `IEnvironmentModel`，应用地表代价（铺装 1.0、硬压实土
  0.90、软土 0.75、水/障碍 0.0）和有界坡度代价，然后推进水平运动学步。无效或
  inactive 命令会让单元停下。
- 命令传输仍使用维护中的 command path；聚焦测试把 link latency 设为零，只为隔离
  movement stage。

## 明确的非目标

本包不准入 route following、waypoint 规划、队形、加速度、疲劳、掩体/隐蔽、视线、
河流或桥梁通行性、武器、火力、压制、后勤或 RL policy training。Arnis 东部平原包
仍是测试地图资产；把该包接入原生 environment provider 属于后续工作包。

## 证据

- `tests/runtime/ground/test_ground_infantry_native_unit.py`
- `tests/architecture/composition/test_simulation_composition_contract.py`
- `tests/architecture/composition/test_runtime_composition_evidence_contract.py`
- `tests/architecture/composition/test_runtime_profile_projection_contract.py`
- `src/runtime/contracts/composition/default_compatibility_manifest.v1.generated.h`
- `src/runtime/contracts/composition/runtime_composition_evidence.v1.generated.h`

2026-09-24 批次使用仓库固定的 Windows 依赖完成构建。聚焦 Python 套件为 `36 passed,
1 skipped`；composition lifecycle、composition evidence 和 backend-provider migration
doctest 可执行文件通过。Cordis conformance 可执行文件需要其文档规定的
request/lock/manifest 参数，因此没有把无参数调用当作 smoke test。
