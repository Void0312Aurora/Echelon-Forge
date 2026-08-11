# A3 C2/ROE P4 探针证据 - 2026-06-03

状态：`2026-06-03`，用于 M1 复盘的 A3-aware process-probe 证据。

语言：

- 英文规范页：[a3_c2_roe_p4_probe_evidence_20260603.md](a3_c2_roe_p4_probe_evidence_20260603.md)
- 中文辅文：`a3_c2_roe_p4_probe_evidence_20260603.zh.md`

## 范围

本记录检查新的 S1 C2/ROE probe 是否能把导弹发射行为拆成授权类别和违规类别。
它不是 learned-policy 验收，也不释放 M2。

场景/config：

- `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json`

## 命令

```powershell
.\tools\maintenance\cmo_env.ps1 python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json --mode forced_fire --episodes 1 --seed 20260603 --max_steps 240 --json_out "$env:TEMP\cmo_a3_p4_forced_fire.json" --csv_out "$env:TEMP\cmo_a3_p4_forced_fire.csv"
```

```powershell
.\tools\maintenance\cmo_env.ps1 python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json --mode switch_explore --episodes 1 --seed 20260603 --max_steps 360 --json_out "$env:TEMP\cmo_a3_p4_switch_explore.json" --csv_out "$env:TEMP\cmo_a3_p4_switch_explore.csv"
```

## 结果

| Probe | Steps | Fire attempts | Releases | Authorized releases | Violation releases | Invalid fire attempts | Release steps | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `forced_fire` | 240 | 1 | 1 | 1 | 0 | 0 | `[1]` | 首次有效发射发生在 `roe_state=2` 且 `authorization_to_fire=1` 的状态下。 |
| `switch_explore` | 360 | 90 | 4 | 1 | 3 | 86 | `[13, 52, 81, 99]` | 同一 C2/ROE 合同能把首发和后续违规发射拆开。 |

`switch_explore` 额外摘要：

- `release_count_by_authorization_state={"authorized":1,"unauthorized":0,"violation":3,"legacy_or_unknown":0}`
- `min_release_interval_steps=18`
- `fire_under_hold_count=0`
- `legacy_roe_fallback_release_count=0`

## 对 M1 的解释

A3 改变了重复发射证据的解释方式。原始 `release_count > 1` 不再足以直接说明这是
temporal memory 失败。当前 probe 表面已经能拆分：

- 授权首发；
- single-shot 合同下的后续违规发射；
- 没有实际发射的无效 fire attempt；
- 如果显式使用 legacy 场景，也可记录 legacy fallback。

当前证据继续保持 M2 held。它证明 A3 已能分类重复发射行为，但还没有证明 learned
temporal policy 已经在 C2/ROE 合同下解决武器使用。
