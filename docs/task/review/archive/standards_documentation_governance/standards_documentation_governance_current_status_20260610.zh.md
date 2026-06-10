# 标准化文档治理当前状态

状态：`2026-06-10`，standards drift governance 的已归档 accepted 状态。

父子项目：[标准化文档治理](README.zh.md)

语言：

- 英文主文：[standards_documentation_governance_current_status_20260610.md](standards_documentation_governance_current_status_20260610.md)
- 中文辅文：`standards_documentation_governance_current_status_20260610.zh.md`

## 状态摘要

P0 已完成：治理通道、标准维护政策、review 索引、双语 registry 记录和 guard 测试均已存在。

本归档状态记录已接受的 closure surface。
[标准化-实现对齐审查 2026-06-10](../standards_implementation_alignment_review_20260610.zh.md)
中的六个 gap 仍按 drift 类型、owner、写集、依赖、验证和收口门槛受控。
GAP-001 到 GAP-005 已关闭。GAP-006 因等待 MLF-3 acceptance 仍显式 held。
本状态页用于让已接受切片和 held 残余保持有界，而不是演变成开放式 standards rewrite。

## Gap 控制账本

| Gap | Drift 类型 | 标准 owner | 实现 owner | 治理决策 | 必需写集 | 验证门槛 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GAP-001 | 语义错配 | `docs/standards/ground/minimal_task_structure*` | `src/components/domains/ground/tasking/**` | 已通过将静态 move task mode 正名为 `MoveStatic` 关闭，同时保留数值 `1`；G0/G1 静态限制仍明确。 | Ground tasking enum、受影响文档、受影响测试 | Ground architecture tests；若 header 改动则运行聚焦 C++ build/test；双语 audit | closed |
| GAP-002 | 实现超前标准 | `docs/standards/air/obs*`；`docs/standards/naval/obs*` | `python/mission_obs_taxonomy.py`；mission observation runtime/tests | 已通过将 `air_combat_c2_roe_v1/v2` 注册到 air specialization、将 `naval_screen_station_v1` 注册到 naval specialization 关闭；无需重设计 observation taxonomy。 | Air obs 标准、naval obs 标准、naval standards README、受影响索引 | 聚焦 mission observation import/test、standards link check、双语 audit | closed |
| GAP-003 | 实现超前标准 | `docs/standards/joint/command_link_and_reporting_baseline*` | `src/components/command/common/mission_command_core.h`；codec/tests | 已通过将四个字段归类为 command-context target provenance metadata 关闭；这些字段支撑 ROE/assignment，但不让 common core 拥有 track fusion。 | Joint command-link baseline 双语对、必要时受影响 command docs/tests | Mission command roundtrip tests、Markdown inspection、双语 audit | closed |
| GAP-004 | 状态/日期陈旧 | air、bridge、joint、naval 标准 header | 无直接 runtime owner | 已通过刷新 air action、air observation、bridge runtime workflow、joint command/modeling、joint command-link、naval minimal tasking 与 naval observation 入口的陈旧或缺失状态行关闭。 | 陈旧 standards header 和最近索引 | Markdown inspection、双语 audit | closed |
| GAP-005 | Planning supplement drift | `docs/standards/planning/modularization_plan*`；standards overview/alignment map | `src/components/domains/**`、`src/systems/domains/**`、`src/models/domains/**` | 已通过保留 active planning supplement、并补充已实现 `domains/` roots 的 current-layout 说明关闭；其中明确 ground runtime held 边界和 no-empty-owner 规则。 | Modularization plan 双语对、standards overview、document alignment map、governance guard test | Structural boundary tests、Markdown inspection、双语 audit | closed |
| GAP-006 | Held standards admission | 未来 air weapon-effects 或 weapons standards owner | MLF-3 任务文档与测试 | 在 MLF-3 warhead-effects 任务验收前保持 held；不得仅凭 untracked 或未接受测试创建生产 standards owner。 | 接受触发前无写集；接受后再建 standards entry | MLF-3 acceptance evidence、source admission gates、standards link check | held |

归档位置：`docs/task/review/archive/standards_documentation_governance/`。

## 批次顺序

推荐 remediation 批次：

1. `Batch A`：GAP-001 与 GAP-003。
   - 状态：closed。
   - GAP-001 将活跃 task mode 正名为 `MoveStatic`，没有改变其数值 wire value。
   - GAP-003 已在 joint command-link 标准中登记活跃的 `MissionCommandCore`
     threat/target provenance 字段。
2. `Batch B`：GAP-002，然后 GAP-004。
   - 状态：closed。
   - 已将 air-combat C2/ROE 与 naval screen/station observation mode 登记到
     domain specialization owner，然后刷新触及同文件的状态行。
   - 已完成 air action、bridge runtime workflow、joint command/modeling 与
     naval minimal tasking 的剩余 status/header 刷新。
3. `Batch C`：GAP-005。
   - 状态：closed。
   - 保留 modularization plan 作为 active planning，但补充当前 `src/*/domains`
     布局说明，使其不再像一张纯未来 target map。
4. `Batch D`：GAP-006。
   - 在 MLF-3 acceptance evidence 出现前保持 held。

## 当前生效的治理规则

- 不得为了教学目的添加生产路径的 `demo` domain 或空 owner shell。
- standards 页面不得在未命名 code、test、scenario 或 accepted task evidence 的情况下声明实现成熟。
- Planning supplement 必须说明它何时不是 current runtime contract。
- Tier-A standards governance 文件必须双语成对更新。
- Gap 收口需要验证证据，不只是 prose edits。

## 当前残余

- 默认双语审计仍报告既有问题：`docs/standards/foundation/realism_authority_boundary.zh.md` 缺英文 peer。
- 更宽的 `tests/architecture/governance` suite 因当前树缺少 simulation-architecture WP 历史路径而存在既有失败。
- GAP-005 已关闭；modularization plan 现在区分已实现的 domain owner root 与仍处于规划中的接口。
- GAP-006 因等待 MLF-3 acceptance，仍有意保持 held。

## 验证证据

Batch A：

```text
cmake --build build-workshop --target ef_py -j2: pass
python -m pytest -q tests/architecture/ground/test_tasking_component_boundary.py tests/runtime/mission/test_mission_command_ground_fields_roundtrip.py tests/leader/test_tasking_profile_contracts.py tests/runtime/mission/test_mission_command_roe_fields.py: pass, 24 passed
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py: pass, 5 passed
python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json: pass, 66 registry pairs synced, no registry drift；既有英文 peer 缺口仍为 docs/standards/foundation/realism_authority_boundary.zh.md
```

Batch B：

```text
python -m pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py tests/runtime/naval/test_naval_n4_reward_surface.py: pass, 31 passed
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py: pass, 7 passed
python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write: pass, registry pair_count 67
python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json: pass, 67 registry pairs synced, no registry drift；既有英文 peer 缺口仍为 docs/standards/foundation/realism_authority_boundary.zh.md
git diff --check for touched Batch B standards/governance paths: pass
```

Batch C 与最终 status/header closure：

```text
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py: pass, 9 passed
python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write: pass, registry pair_count 67
python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json: pass, 67 registry pairs synced, no registry drift；既有英文 peer 缺口仍为 docs/standards/foundation/realism_authority_boundary.zh.md
git diff --check -- docs/standards docs/task/review/standards_documentation_governance tests/architecture/governance/test_standards_documentation_governance.py: pass
```
