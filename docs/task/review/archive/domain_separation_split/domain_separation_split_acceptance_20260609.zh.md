# 域分离大拆分验收门槛

状态：`2026-06-10` accepted 证据台账；旧 domain-split 兼容入口已退役，宽 architecture guard 已验证。

父级：[域分离大拆分](README.zh.md)

## 验收决策

整体子项目状态：`accepted`。

原因：DS-M1-B 之前的命名实现簇已有聚焦 pass 证据，旧公开兼容路径也不再刻意保留。
无兼容入口 slice 已验证；此前 held 的宽 architecture residual 已通过更新 binding-surface
guard 收口，使其能解析当前多行 binding，并匹配当前显式 allowlist。

## 必需门槛

| Gate | Required evidence | Current status |
| --- | --- | --- |
| `G0 Subproject Surface` | README、task clusters、current status、dispatch queue、acceptance、archive 与 parent index links 存在。 | pass |
| `G1 Component Ownership` | `damage.h` 与 `weapon.h` 作为公开入口退役；consumer 直接 include common/domain-owned header。 | pass |
| `G2 System Ownership` | `damage_system.h`、air runtime system、naval logistics 与 propulsion readout 从误导性 generic owner 中拆出。 | pass |
| `G3 Model Ownership` | effects 与 sensor default model 通过 common/domain adapter 路由，而不是在 generic 文件中隐藏 Air/Naval-only 逻辑。 | pass |
| `G4 Compatibility` | 不刻意保留 domain-split 兼容 include path；退役路径有 guard 防止复活。 | pass |
| `G5 Focused Validation` | 聚焦 C++ build、runtime tests、退役 include search 与 architecture guards 通过。 | pass |
| `G6 Documentation` | `docs/task/review`、`docs/manual` 与受影响 source README 匹配已实现 ownership。 | pass |
| `G7 Claim Boundary` | Ground shell 与目录迁移不暗示完整域成熟度。 | pass |
| `G8 Broad Architecture Residual` | 无关 broad architecture baseline 已修复，或明确 hold 到本 domain split 之外。 | pass |

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
| `2026-06-09` | DS-C1-A | 新增 common/air/naval/ground damage owner headers。初始迁移使用过 public umbrella，已由 2026-06-10 清理退役。 | pass | consumer 必须直接 include owner header。 |
| `2026-06-09` | DS-C1-B | 新增 common/air/naval/ground weapon owner headers。初始迁移使用过 public umbrella，已由 2026-06-10 清理退役。 | pass | consumer 必须直接 include owner header。 |
| `2026-06-09` | DS-S1-A | 新增 common/air/naval/ground damage system headers。初始迁移使用过 registrar umbrella，已由 2026-06-10 清理退役。 | pass | kernel 直接调用 owner registrar。 |
| `2026-06-09` | DS-S1-B | Air systems 直接 include `damage_air.h`；旧 physics/tuning include path 现在删除，不再作为 wrapper 保留。 | pass | kernel 直接 include Air system owner。 |
| `2026-06-10` | DS-S1-C | `NavalUnderwayResupply` 已从 generic logistics 移到 `src/systems/domains/naval/naval_logistics_system.h`；kernel registration 在 common logistics 后注册；聚焦 naval underway tests 和 scoped diff check 通过。 | pass | generic logistics 通过 `components/physics/propulsion_readouts.h` 读取 propulsion readout。 |
| `2026-06-10` | DS-M1-A | `default_effects_model.cpp` 通过 `default_effects_domain_routing_detail.inc` 路由；Air consequence logic 位于 `src/models/domains/air/default_effects_air_domain.h`；Naval/Ground placeholder owner path 已存在；聚焦 structural/effects tests 通过。 | pass | Naval/Ground effects 路径仅为 placeholder。 |
| `2026-06-10` | DS-M1-B | `default_sensor_model.cpp` 不再直接 include 或读取 `ShipPlatform`；ship-specific maritime 读取位于 `src/models/domains/naval/naval_sensor_maritime_adapter.h`；聚焦 naval sensor tests 通过。 | pass | `default_acoustic_model.cpp` 的 ship 访问不属于本 sensor-routing packet。 |
| `2026-06-10` | DS-T1-A | 已新增 `test_domain_separation_split_generic_files_route_domain_owned_runtime`；selector `python -m pytest -q tests/architecture/structural_boundaries/test_structural_guardrails.py -k "domain_separation_split or structured_air_effects"` 通过。 | pass | 退役路径 guard 聚焦本拆分。 |
| `2026-06-10` | DS-T1-A | structural guard 已更新：退役 domain-split 公开路径若被重建、旧 include 若回流 maintained source，会直接失败；刷新后的聚焦 selector 通过。 | pass | 对 `src src/tests` 的退役 include search 无匹配。 |
| `2026-06-10` | DS-T1-B | `tests/architecture/structural_boundaries/test_structural_guardrails.py` 的 binding parser 现在支持多行 `.def(...)` binding、对重载名称去重，并显式 allowlist `debug_get_ground_contact_state`。 | pass | 完整 `tests/architecture/structural_boundaries` 通过。 |
| `2026-06-10` | DS-D1-A | source README index 与本 task surface 已同步到无兼容入口实现。 | pass | scoped `git diff --check` 通过。 |

## 实际验证命令

```bash
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/naval/test_naval_ship_database.py -k "underway_replenishment"
python -m pytest -q tests/runtime/naval/test_naval_sensor_realism_runtime.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k "dfm_p4 or component_damage"
python -m pytest -q tests/architecture/structural_boundaries/test_structural_guardrails.py -k "domain_separation_split or structured_air_effects"
python -m pytest -q tests/architecture/compatibility_quarantine/test_guard_enforcement.py
python -m pytest -q tests/architecture/structural_boundaries
git diff --check -- src tests docs/task/review/domain_separation_split docs/task/review/README.md docs/task/review/README.zh.md docs/manual
```

本 checkout 中的结果：

- `cmake --build build-workshop --target ef_py -j2`：pass。
- `test_naval_ship_database.py -k "underway_replenishment"`：2 passed, 20 deselected。
- `test_naval_sensor_realism_runtime.py`：5 passed。
- `test_weapon_guidance_realism_guards.py -k "dfm_p4 or component_damage"`：8 passed, 170 deselected。
- `test_structural_guardrails.py -k "domain_separation_split or structured_air_effects"`：2 passed, 16 deselected。
- `test_guard_enforcement.py`：15 passed。
- `tests/architecture/structural_boundaries`：18 passed。
- 对 `src src/tests` 的退役 include search：无匹配。
- 退役路径存在性检查：没有退役文件存在。
- scoped `git diff --check`：pass。

当前 checkout 以 `build-workshop` 作为验证 build tree。

此前的宽 architecture residual 已在本 slice 关闭：compatibility quarantine 与
structural-boundary guard 均通过，binding-surface guard 已刷新到当前
`bindings_core.cpp` 格式和显式 debug allowlist。

## 退役路径与 residual

已退役的 domain-split 公开路径：

- `src/components/combat/damage.h`
- `src/components/combat/weapon.h`
- `src/systems/combat/damage_system.h`
- `src/components/physics/flight_dynamics_tuning.h`
- `src/systems/physics/aero_state_system.h`
- `src/systems/physics/aerodynamics_system.h`
- `src/systems/physics/control_system.h`
- `src/systems/physics/propulsion_system.h`
- `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc`

非阻塞 follow-up 边界：

- Naval/Ground effects path 和 Ground damage/weapon shell 仍只是 ownership placeholder，不是完整 domain capability claim。

## 验收输出模板

```md
status: accepted | partial | held | rejected
accepted clusters:
held clusters:
commands/outcomes:
compatibility wrappers retained: none for this domain-split package
claim boundaries:
next package:
```
