# 域分离大拆分验收门槛

状态：`2026-06-09` 初始 gate 定义；尚无实现簇 accepted。

父级：[域分离大拆分](README.zh.md)

## 验收决策

整体子项目状态：`not accepted`。

原因：当前只创建了持久执行表面。审计指出的主要 ownership hotspot 仍需要实现簇和验证证据。

## 必需门槛

| Gate | Required evidence | Current status |
| --- | --- | --- |
| `G0 Subproject Surface` | README、task clusters、current status、dispatch queue、acceptance、archive 与 parent index links 存在。 | pass |
| `G1 Component Ownership` | `damage.h` 与 `weapon.h` 拆为 common/domain-owned header，或仅保留有明确理由的 compatibility wrapper。 | pass |
| `G2 System Ownership` | `damage_system.h`、air runtime system 与 naval logistics 从误导性 generic owner 中拆出。 | partial |
| `G3 Model Ownership` | effects 与 sensor default model 通过 common/domain adapter 路由，而不是在 generic 文件中隐藏 Air/Naval-only 逻辑。 | pending |
| `G4 Compatibility` | 仍保留的公开 include path 只是 wrapper，并记录保留/弃用理由。 | pending |
| `G5 Validation` | 聚焦 C++ build、runtime tests 与 architecture guards 通过。 | pending |
| `G6 Documentation` | `docs/task/review`、`docs/manual` 与受影响 source README 匹配已实现 ownership。 | pending |
| `G7 Claim Boundary` | Ground shell 与目录迁移不暗示完整域成熟度。 | pending |

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
