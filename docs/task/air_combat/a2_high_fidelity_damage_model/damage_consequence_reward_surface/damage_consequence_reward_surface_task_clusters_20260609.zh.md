# A2 损伤后果奖励面任务簇

状态：`2026-06-11`，用于
[README.zh.md](README.zh.md) 的有限任务簇计划。DCR-A-D 已验证；DCR-E probe 导出、
diagnostics-only bridge 和只读 re-scope 已验证，但 fixed-fire DCR totals 仍为 0。受控非零
consequence-chain 证据仍是下一道非训练门槛；DCR-F 仍为 planned。

英文规范页：
[damage_consequence_reward_surface_task_clusters_20260609.md](damage_consequence_reward_surface_task_clusters_20260609.md)

## 边界决定

本 follow-on 可以增加训练奖励：读取已经可观察的损伤后果，包括 damage report、飞机损伤
debug state 和触地生命周期 state。它不能修改武器效果权威，不能发明真实 Pk，不能声明
stock AIM-120C / MQ-9 杀伤，也不能用“直接坠毁规则”替代损伤链。

第一刀实现应奖励变化量和状态转移，而不是反复奖励“目标已经受损”这个静态事实。这样火灾、
燃油泄漏、操纵下降和严重触地这类延迟后果可以给训练反馈，但策略不会因为停在旁边等待而
持续拿同一份奖励。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DCR-A Boundary And Observable Map` | main thread | n/a | 把 held idea 升级为 active A2 follow-on，并列出可读的后果来源。 | `docs/task/air_combat/a2_high_fidelity_damage_model/damage_consequence_reward_surface/**`，必要时 A2 指针 README | 改标准文档、创建 A9、重开 sealed A2 archive | `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/damage_consequence_reward_surface` | README 和任务簇存在，且禁止声明清楚。 | first, serial | 1 | pass |
| `DCR-B Runtime Reward Surface` | main thread | n/a | 为飞机损伤变化量和严重触地转移增加可选奖励项。 | `gym_envs/scenario_loader/reward_runtime/air_combat.py` | 武器物理修改、直接坠毁替代规则、无配置的默认训练行为大改 | 聚焦 reward 单测 | runtime 每步读取后果 state，并只在配置/启用时输出命名项。 | after A | 2 | pass |
| `DCR-C Focused Tests` | main thread | n/a | 覆盖目标奖励、自身受损惩罚、变化量语义和安全触地边界。 | `tests/runtime/air_combat/test_air_combat_reward_surface.py`，可选 1v1 fixture 聚焦测试 | 慢训练、大范围场景重写 | `python -m pytest -q tests/runtime/air_combat/test_air_combat_reward_surface.py` | 测试证明奖励层只消费事实，不改变物理权威。 | after or with B | 2 | pass |
| `DCR-D Scenario Opt-In` | current-session worker | n/a | 让 Stage-2 后续能够消费低权重后果项。 | `scenarios/air_combat/1v1/**`、`examples/config/training/active/air_combat/**`、active-entry README | 把 Stage-2 训练当作杀伤链前置、改发射闭合、提速优化、Stage-3/self-play | 场景/config smoke 或 JSON 检查 | opt-in 是显式的，且权重写明只是训练 synthetic。 | after B/C | 1 | pass |
| `DCR-E Probe Evidence` | read-only diagnostics explorer，然后 diagnostics worker | n/a | 做受控命中/固定发射/replay probe，把发射项和后果项分开报告。 | `tools/diagnostics/air_combat_stage0_process_probe.py`、聚焦 diagnostics tests、后续本子项目 diagnostics output 文档 | 单 seed 幸运验收、用 release reward 掩盖无效果射击、把 learned Stage-2 model 当作前置 | 受控 probe 或 replay summary | 证据显示后果奖励发生在 effects/damage 之后，而不是只发生在 release 之后。 | after D | 1 | partial：export/bridge/re-scope ready；下一步为 `DCR-E-P3` fixture evidence |
| `DCR-F Closure And Index Sync` | main thread | n/a | 按证据标记 accepted slice 或 residual，并同步父级指针。 | 本 README/task cluster、`docs/task/air_combat/README*`、A2 pointer README | 过度声明真实杀伤或 Stage-2 最终验收 | docs diff check 和聚焦测试 | status line 与 residual map 和证据一致。 | last, serial | 1 | planned |

## 派发规则

- 每个 worker packet 必须只对应上表一个 cluster。
- reward runtime、场景 reward 权重、status line 不允许并行写。
- A/B/C 可以由 main thread 在同一刀完成，因为 B 的写入范围很窄。
- D/E/F 必须和后续多 world 提速工作分开。
- 严禁创建新的 Codex 会话线程；如使用 subagent，也必须留在当前会话和 cluster 写入范围内。
- 当前派发队列：
  [damage_consequence_reward_surface_dispatch_queue_20260609.zh.md](damage_consequence_reward_surface_dispatch_queue_20260609.zh.md)

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 验证计划

第一刀聚焦验证：

```bash
git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model/damage_consequence_reward_surface \
  gym_envs/scenario_loader/reward_runtime/air_combat.py \
  tests/runtime/air_combat/test_air_combat_reward_surface.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_reward_surface.py
```

最新本地验证：

```bash
python -m py_compile gym_envs/scenario_loader/reward_runtime/air_combat.py tests/runtime/air_combat/test_air_combat_reward_surface.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_reward_surface.py
python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py::AirCombat1v1FixtureTests::test_loader_damage_report_shaping_consumes_nonterminal_structured_damage_once \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py::AirCombat1v1FixtureTests::test_loader_compute_full_step_consumes_structured_damage_report_for_combat_win
python -m py_compile tools/diagnostics/air_combat_stage0_process_probe.py tests/runtime/air_combat/test_diagnostics_probe_contracts.py
python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
python -m json.tool scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json >/dev/null
git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model \
  gym_envs/scenario_loader/reward_runtime/air_combat.py \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py \
  scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json \
  examples/config/training/active/air_combat/README.md \
  examples/config/training/active/air_combat/README.zh.md
```

`train.py --test_only` 已能进入 Stage-2 runtime preflight。随后用
`experiments_tmp/a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1/final_model.zip`
做了 2 episode x 512 step model-mode probe；模型没有发射，没有 effects/damage，DCR reward 为
0。它只能证明 probe/export 可运行，不能证明后果奖励发生在损伤之后。DCR-E 下一步应使用受控命中、
固定发射或 replay artifact。

受控杀伤链证据存在后，后续 learned-policy probe 验证：

```bash
python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --test_only
```

## 验收标准

- 奖励项按后果类型命名，并且能和 release reward 分开看。
- 目标损伤后果可以给正奖励；自身损伤后果可以给负奖励。
- 默认不反复奖励静态损伤存在。
- 普通安全触地不能作为战斗后果奖励；只有配置启用时，严重撞击、起落架折断或坠毁残骸转移才可奖励。
- 子项目继续拒绝 Pk、确定性引信、stock weapon-outcome 和特定目标击杀权威声明。

## 残余图

| Residual | Owner | Exit condition |
| --- | --- | --- |
| Stage-2 后果信号可能仍然稀疏 | Future training consumer | 受控杀伤链证据已存在；后续 learned-policy probe 在实际 release 后报告 effects/damage/consequence terms。当前候选模型未发射，不能验收。 |
| 受控杀伤链后果证据缺失 | DCR-E | fixed-hit、fixed-release 或 replay probe 在同一记录中给出 effects/damage 与非零 DCR term timing。 |
| fixed-fire bridge 的 DCR totals 为 0 | DCR-E follow-up | `DCR-E-P3` controlled fixture 产生 DCR-readable consequence fields，或另行定界 damage-report projections 到 DCR terms 的 reward mapping。 |
| reward 权重只是 synthetic 训练旋钮 | DCR-D/F | 文档和 config 明确它不是武器真值。 |
| 延迟火灾/燃油动力可能太弱 | Future A2 calibration | 单独 fidelity/calibration 任务改变物理后果强度。 |
| 吞吐量可能限制证据收集 | Future performance task | 多 world 或等价提速放到奖励子项目之外。 |
