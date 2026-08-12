# Default Effects Modularization

状态：`2026-06-02 closed / archived / DFM-P3F structure-spatial helper pass`。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

Inputs:

- 父任务入口：[A2 高保真空战毁伤模型](../README.zh.md)
- Agent 子项目创建标准：[subproject_creation_standard.zh.md](../../../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- Subagent 使用规范：[subagent_usage_policy.zh.md](../../../../../engineering/automation/standards/subagent_usage_policy.zh.md)
- 触发评估：[Echelon Forge 综合评估](../../../../../evaluation/archive/echelon_forge_comprehensive_assessment_20260601.zh.md)
- 代码面：[default_effects_model.cpp](../../../../../../src/models/weapons/default_effects_model.cpp)

## Purpose

本子项目用于固化 `src/models/weapons/default_effects_model.cpp` 的结构化拆分与稳定化任务清单。
目标是可维护性：让默认 effects model 可导航、helper 链接保持本地、运行时行为不漂移，
并为后续编辑保留明确的验证门。

本子项目不提升 A2 fidelity authority、Pk authority、deterministic fuze authority 或工业级准入。
它只治理 default effects model 的代码结构与回归任务面。

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| 主翻译单元拆分 | closed-pass | `default_effects_model.cpp` 已转为 orchestration 并 include 私有 detail 片段。 | 不证明物理或 vulnerability calibration 权威。 |
| Direct hit helper | pass | `detail/default_effects_direct_hit_detail.inc`；`DFM-P4` runtime fixtures | fixed-RNG direct component 与 protected-system fallback 路径已有 runtime fixture 覆盖，尚非 C++ golden harness。 |
| Spatial projection helper | pass | `detail/default_effects_spatial_projection_detail.inc` 和共享 candidate helpers；`DFM-P4` runtime fixtures | broad / non-broad near-miss 路径已有 runtime fixture 覆盖。 |
| System effect helper | pass | `detail/default_effects_system_effect_detail.inc` | 已有 build/runtime guard 覆盖，尚非逐字段 golden 对比。 |
| Air platform resolution helper | pass-for-structure | `detail/default_effects_air_platform_resolution_detail.inc` | platform-only、aircraft sensor/avionics、aircraft propulsion/fuel、aircraft control/hydraulic、aircraft crew-role、aircraft mission/combat、aircraft structure-spatial 与 aircraft fire-zone consequence blocks 已有命名 helper。 |
| Verification | pass-for-current-slice | `cmake --build build --target ef_core -j2`；`cmake --build build --target ef_py -j2`；runtime guard `155 passed` | 本模型还没有专用 C++ 单元测试网。 |

## Scope

In scope:

- 保持 `default_effects_model.cpp` 作为 `make_default_effects_model` 的本地入口。
- 在 `src/models/weapons/detail/` 下拆分私有实现 helper。
- 保留行为、公式、RNG、result 字段和指针生命周期。
- 固化有限任务簇、验证命令、关闭门和 residual。
- 为 direct hit、protected-system fallback、broad spatial projection、
  non-broad component projection、structured air-platform early return 补窄回归。

Out of scope:

- 替换 effects model 架构或公开 `IEffectsModel` contract。
- 将任何 evidence row、candidate package 或 source scan 提升为权威 stock runtime capability。
- 在结构性清理中更改 warhead physics 公式、fragility curves 或 vulnerability source authority。
- 解决项目级 C++ 单元测试框架缺口。

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 固定范围、authority 和任务清单。 | A2 评估指出 `default_effects_model.cpp` 过大。 | README 和任务簇存在，并由父入口链接。 | pass |
| `P1 Extraction` | 将单体 helper 逻辑移入本地 detail 片段。 | baseline 可构建。 | direct、spatial、system-effect、result、state、warhead、geometry、component、legacy helpers 编译通过。 | pass |
| `P2 Internal Cleanup` | 降低重复公式和 scratch 更新。 | P1 helper 边界编译通过。 | 统一 component-scale 和 warhead-sample helpers。 | pass |
| `P3 Air Resolution Split` | 在不改公式的前提下压薄 air-platform consequence 内部。 | P2 pass。 | 机制载荷、scale 聚合、platform-only、sensor/avionics、propulsion/fuel、control/hydraulic、crew-role、mission/combat、structure-spatial、fire-zone、finalize 与后续 consequence blocks 有命名 helper。 | pass / DFM-P3F structure-spatial helper pass |
| `P4 Regression Fixtures` | 为高风险路径补窄行为 fixture。 | P1-P3 构建通过。 | 专用 fixture 或 runtime snapshot 覆盖命名路径。 | direct/spatial/early-return pass |
| `P5 Closure` | 同步 docs、status、archive 和 residual。 | P4 pass 或明确 held residual。 | acceptance gate、current status 和 archive record 更新。 | closed / archived |

## Task Clusters

- 任务簇计划：[default_effects_modularization_task_clusters_20260601.md](default_effects_modularization_task_clusters_20260601.md)
- 当前状态：[default_effects_modularization_current_status_20260601.md](default_effects_modularization_current_status_20260601.md)
- 第一轮验收：[default_effects_modularization_acceptance_20260601.md](default_effects_modularization_acceptance_20260601.md)
- 收口同步：[default_effects_modularization_closure_sync_20260602.md](default_effects_modularization_closure_sync_20260602.md)
- 归档收口：[archive/default_effects_modularization_closeout_20260602.md](archive/default_effects_modularization_closeout_20260602.md)

## Outputs And Evidence

- [default_effects_model.cpp](../../../../../../src/models/weapons/default_effects_model.cpp)
- `src/models/weapons/detail/default_effects_*_detail.inc`
- [weapons README](../../../../../../src/models/weapons/README.md)
- [weapons README.zh.md](../../../../../../src/models/weapons/README.zh.md)
- Build gate: `cmake --build build --target ef_core -j2`
- Runtime guard: `CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest tests/runtime/air_combat/test_weapon_guidance_realism_guards.py --tb=short -ra`

## Acceptance Gate

本子项目只有在以下条件满足后才能标为 accepted：

- `ef_core` 在 include-order 检查后构建通过。
- 现有 runtime guard tests 通过。
- direct、spatial 和 air platform early-return 命名路径有专用 golden / fixture 覆盖，
  或这些缺口被明确标记为 held。
- `src/models/weapons/detail/` 与修改后的入口文件一起纳入跟踪。
- README/status/task-cluster 表面继续拒绝更宽泛的 realism 或 authority 声明。

## Residuals And Next Steps

- 后续任务若触碰该表面，必须保持已接受的 direct、spatial 与 structured
  air-platform early-return runtime fixtures 为绿。
- C++ 单元测试框架只作为后续项目级测试倡议处理。
- 先前 held 的 aircraft structure-spatial helper extraction 已完成；任何进一步
  air-platform 重构都必须重新建立有限任务簇，并继续保持公式、authority strings
  与 public contracts 不变。

## Archive

- Archive index：[archive/README.md](archive/README.md)
- 最终收口：[archive/default_effects_modularization_closeout_20260602.md](archive/default_effects_modularization_closeout_20260602.md)
