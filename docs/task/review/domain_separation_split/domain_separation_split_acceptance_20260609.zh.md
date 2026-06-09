# 域分离大拆分验收门槛

状态：`2026-06-10` 集成证据台账；实现簇已落地，但子项目尚未 accepted。

父级：[域分离大拆分](README.zh.md)

## 验收决策

整体子项目状态：`partial / not accepted`。

原因：DS-M1-B 之前的命名实现簇已有聚焦 pass 证据，但最终 acceptance 仍被 Air
propulsion helper dependency policy 和更宽 architecture gate 卡住；这些 gate 当前在既有/无关表面失败。

## 必需门槛

| Gate | Required evidence | Current status |
| --- | --- | --- |
| `G0 Subproject Surface` | README、task clusters、current status、dispatch queue、acceptance、archive 与 parent index links 存在。 | pass |
| `G1 Component Ownership` | `damage.h` 与 `weapon.h` 拆为 common/domain-owned header，或仅保留有明确理由的 compatibility wrapper。 | pass |
| `G2 System Ownership` | `damage_system.h`、air runtime system 与 naval logistics 从误导性 generic owner 中拆出。 | partial |
| `G3 Model Ownership` | effects 与 sensor default model 通过 common/domain adapter 路由，而不是在 generic 文件中隐藏 Air/Naval-only 逻辑。 | pass |
| `G4 Compatibility` | 仍保留的公开 include path 只是 wrapper，并记录保留/弃用理由。 | partial |
| `G5 Validation` | 聚焦 C++ build、runtime tests 与 architecture guards 通过。 | partial |
| `G6 Documentation` | `docs/task/review`、`docs/manual` 与受影响 source README 匹配已实现 ownership。 | partial |
| `G7 Claim Boundary` | Ground shell 与目录迁移不暗示完整域成熟度。 | pass |

## 最小验证命令

```bash
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/architecture/compatibility_quarantine/test_guard_enforcement.py
python -m pytest -q tests/architecture/structural_boundaries
python -m pytest -q tests/runtime/naval
python -m pytest -q tests/runtime/air_combat
git diff --check -- src tests docs/task/review/domain_separation_split docs/task/review/README.md docs/task/review/README.zh.md docs/manual
```

每个实现簇可以缩小 runtime selector，但最终验收必须记录实际 selector，以及为何 hold 更宽范围 selector。

## 禁止的验收捷径

- 不得因为目录存在就验收子项目。
- 如果 generic 文件仍拥有 domain-only 行为，只是 include 了改名 header，则不得验收实现簇。
- 不得把 Ground placeholder 转成完整 Ground capability claim。
- 不得用 architecture cleanup 掩盖行为漂移；必须记录 first failing stage，并修复或 hold。
- 不得把无关 dirty worktree 变更计为本子项目证据。

## 证据台账

| Date | Cluster | Evidence | Result | Notes |
| --- | --- | --- | --- | --- |
| `2026-06-09` | DS-P0-A | 子项目文件集和父级 review index link 已创建；docs 范围 `git diff --check` 通过。 | pass | 实现门槛 pending。 |
| `2026-06-09` | DS-P0-B | 通过只读 `rg` / 文件检查向 current status 增加 inventory；current-status 文件 `git diff --check` 通过。 | pass | 仅诊断；无实现验收。 |
| `2026-06-09` | DS-C1-A | `damage.h` 已降为 compatibility umbrella；新增 common/air/naval/ground damage owner headers；combined `ef_py` build 与 component diff checks 通过。 | pass | System split 仍 pending。 |
| `2026-06-09` | DS-C1-B | `weapon.h` 已降为 compatibility umbrella；新增 common/air/naval/ground weapon owner headers；combined `ef_py` build 与 component diff checks 通过。 | pass | direct include migration 后续处理。 |
| `2026-06-09` | DS-S1-A | `damage_system.h` 已降为 compatibility umbrella；新增 common/air/naval/ground damage system headers；combined `ef_py`、include search 与 diff checks 通过。 | pass | G2 到 naval logistics 拆分前保持 partial。 |
| `2026-06-09` | DS-S1-B | Air systems 直接 include `damage_air.h`；旧 physics/tuning 路径保持 include-only wrapper；combined `ef_py`、include search 与 diff checks 通过。 | pass | logistics Air fuel-flow helper dependency remain。 |
| `2026-06-10` | DS-S1-C | `NavalUnderwayResupply` 已从 generic logistics 移到 `src/systems/naval/naval_logistics_system.h`；kernel registration 在 common logistics 后注册；`cmake --build build-local-win --target ef_py -j2`、聚焦 naval underway tests 和 scoped diff check 通过。 | pass | Air propulsion helper dependency 不属于 naval extraction，仍保留为 residual。 |
| `2026-06-10` | DS-M1-A | `default_effects_model.cpp` 通过 `default_effects_domain_routing_detail.inc` 路由；Air consequence logic 位于 `src/models/air/default_effects_air_domain.h`；Naval/Ground placeholder owner path 已存在；聚焦 structural/effects tests 通过。 | pass | Naval/Ground effects 路径仅为 placeholder。 |
| `2026-06-10` | DS-M1-B | `default_sensor_model.cpp` 不再直接 include 或读取 `ShipPlatform`；ship-specific maritime 读取位于 `src/models/naval/naval_sensor_maritime_adapter.h`；聚焦 naval sensor tests 通过。 | pass | `default_acoustic_model.cpp` 的 ship 访问不属于本 sensor-routing packet。 |
| `2026-06-10` | DS-T1-A | 已新增 `test_domain_separation_split_generic_files_route_domain_owned_runtime`；selector `python -m pytest -q tests/architecture/structural_boundaries/test_structural_guardrails.py -k "domain_separation_split or structured_air_effects"` 通过。 | partial | 完整 architecture 文件仍在无关 direct-sim allowlist、binding-count assertion 与 Windows snippet linking 上失败。 |
| `2026-06-10` | DS-D1-A | source model/naval README index 和本 task surface 已同步已实现 ownership 与 residual。 | partial | final accepted 状态需等 G2/G4/G5 residual 关闭或被显式保留。 |

## 实际验证命令

```bash
cmake --build build-local-win --target ef_py -j2
python -m pytest -q tests/runtime/naval/test_naval_ship_database.py -k "underway_replenishment"
python -m pytest -q tests/runtime/naval/test_naval_sensor_realism_runtime.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k "dfm_p4 or component_damage"
python -m pytest -q tests/architecture/structural_boundaries/test_structural_guardrails.py -k "domain_separation_split or structured_air_effects"
git diff --check -- src tests docs/task/review/domain_separation_split docs/task/review/README.md docs/task/review/README.zh.md docs/manual
```

文档中原列出的 `build-workshop` 目录在当前 checkout 不存在；本地可用 build tree 是
`build-local-win`。

更宽 architecture 尝试被记录为 residual evidence，而不是本 slice 的 acceptance 通过证据：

- `python -m pytest -q tests/architecture/compatibility_quarantine/test_guard_enforcement.py`
  在既有 direct-sim allowlist hits，以及 Windows snippet 链接 flecs socket symbols 时失败。
- `python -m pytest -q tests/architecture/structural_boundaries` 在既有 `bindings_core`
  allowlist/count assertion 上失败，与本域拆分无关。

## 保留兼容与 residual

- `src/components/combat/damage.h`、`src/components/combat/weapon.h` 和
  `src/systems/combat/damage_system.h` 仍作为 compatibility umbrella 保留。
- 旧 `systems/physics/*` air-system headers 与
  `components/physics/flight_dynamics_tuning.h` 仍作为 include-only wrapper 保留。
- `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc`
  作为指向 Air-owned effects helper 的 compatibility bridge 保留。
- generic physics/logistics 文件仍消费 Air propulsion helper state；子项目 accepted 前需要命名 adapter 或显式 retained-dependency 决定。

## 验收输出模板

```md
status: accepted | partial | held | rejected
accepted clusters:
held clusters:
commands/outcomes:
compatibility wrappers retained:
claim boundaries:
next package:
```
