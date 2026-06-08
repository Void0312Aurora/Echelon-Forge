# M3-S2 开火时机可学习性审计任务簇

状态：`历史任务簇计划已归档；dispatch 已于 2026-06-08 关闭`。

保留的写入范围是归档证据包。原
`docs/task/model/m3_s2_fire_timing_learnability_audit/` 路径现在只保留
pointer README。

## 边界决定

M3-S2 是审计和诊断切片。它可以增加 diagnostics、tests 与 evidence docs；不得打开新的
training tune，不得削弱 C2/ROE，也不得宣称 learned-policy success。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M3S2-P0 Boundary` | main thread | n/a | 定义 masked edge-triggered stopping 对象与断点。 | `docs/task/model/archive/m3_s2_fire_timing_learnability_audit/**` | 新算法声明；训练修改。 | Markdown inspection。 | README 命名形式对象、范围与验收门。 | First；serial。 | 1 | pass |
| `M3S2-P1 Diagnostic Tooling` | main thread | n/a | 增加 hold、legal-mask oracle pulse modes 与 aggregate verdict runner。 | `tools/diagnostics/air_combat_stage0_process_probe.py`；`tools/diagnostics/air_combat_fire_timing_learnability_audit.py`；focused tests | reward tuning；policy changes；C2/ROE weakening。 | `py_compile`；focused pytest。 | tooling 可区分 hold、early high、legal pulse、delayed legal pulse。 | After P0；serial。 | 2 | pass |
| `M3S2-P2 Oracle Evidence` | read-only diagnostics worker | n/a | 运行有边界 Stage-1 oracle audit 并保留 artifact。 | `experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json`；evidence note | long training；model acceptance。 | Audit command exits 0；JSON verdict present。 | Verdict 命名 release reachability、reward delta、timing spread、effects visibility 与 edge hazard。 | After P1；serial。 | 1 | pass |
| `M3S2-P3 Root-Cause Synthesis` | main thread | n/a | 判定当前 blocker 是 action adapter、reward/effects observability 还是 optimizer。 | current status 与 oracle evidence docs | 在同一 packet 打开 P4 remediation。 | Markdown inspection；evidence links。 | status 命名 primary 与 secondary breakpoint，不 overclaim。 | After P2；serial。 | 1 | accepted |
| `M3S2-P4 Remediation Selection` | future worker | n/a | 从已接受诊断中起草下一实现切片。 | new task 或 follow-up plan only | 未选择就实现；默认释放 M2。 | Review against P3 evidence。 | 选定一个有边界下一切片，或明确 held。 | After P3；serial。 | 1 | held / follow-on only |

## 历史分发规则

本归档不再保留 active worker dispatch；以下规则仅作为 sealed packet 的历史约束保留。

- 每个 worker packet 必须映射到上表一个 cluster。
- Diagnostics worker 只能把实验 artifact 写入 `experiments_tmp/`，除非显式分配 docs。
- 在本审计确认断点前，不得修改 reward、C2/ROE legality、missile effects 或 model losses。

## Worker Packet 要求

- 写清 scenario、train config、command、seed、episode count 与 max steps。
- 报告 release count、accepted/rejected fire count、effects event count、damage report count、
  target health drop、total reward 与 release steps。
- 分离 release-vs-hold reward 与 legal timing reward spread。
- 标注任何 claim 是否仅为 diagnostic。

## 验证计划

```bash
python -m py_compile \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  tools/diagnostics/air_combat_fire_timing_learnability_audit.py \
  tests/diagnostics/test_air_combat_process_probe.py \
  tests/diagnostics/test_air_combat_fire_timing_learnability_audit.py

python -m pytest \
  tests/diagnostics/test_air_combat_process_probe.py \
  tests/diagnostics/test_air_combat_fire_timing_learnability_audit.py -q

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_fire_timing_learnability_audit.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json \
  --episodes 2 \
  --seed 31 \
  --max_steps 2000 \
  --delays 0,31,63 \
  --json_out experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json
```

## 验收标准

- Focused diagnostics tests pass。
- Audit verdict 可从 retained artifact 复现。
- Root-cause status 区分 release reachability 与 legal timing identifiability。
- 后续工作被表述为 model/environment contract decision，而不是 coefficient tuning。

## 残余图

- `legal_timing_unidentifiable_from_current_return`：primary breakpoint。
- `cumulative_prewindow_hazard_support_collapse`：primary learned-policy
  support-collapse breakpoint。
- `edge_trigger_adapter_credit_hazard`：secondary transport breakpoint。
- `post_release_effect_observable=false`：在声明 timing-quality acceptance 前，需要继续调查
  environment/effects/reward。
