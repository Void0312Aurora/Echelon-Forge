# A2 损伤后果奖励面派发队列

状态：`2026-06-11`，当前会话内 DCR-D 与 DCR-E 派发记录。DCR-D-W1、DCR-E-X1、
DCR-E-P1、DCR-E-X2、DCR-E-P2 和 DCR-E-R1 均已返回。DCR-E 仍为 partial，因为
fixed-fire bridge 的 DCR totals 为 0。`DCR-E-P3` 是下一步推荐实现包。

英文规范页：
[damage_consequence_reward_surface_dispatch_queue_20260609.md](damage_consequence_reward_surface_dispatch_queue_20260609.md)

父任务簇：
[damage_consequence_reward_surface_task_clusters_20260609.zh.md](damage_consequence_reward_surface_task_clusters_20260609.zh.md)

## 边界

本队列只派发 DCR-A-C 之后的奖励扩展 follow-on。它不创建新的会话线程，不重开 sealed A2，
不声明真实 Pk、确定性引信、stock AIM-120C / MQ-9 杀伤，也不声明 Stage-2 验收。

## 当前派发包

| Packet | Cluster | Assignee | Write set | Required output | Status |
| --- | --- | --- | --- | --- | --- |
| `DCR-D-W1` | `DCR-D Scenario Opt-In` | current-session worker `019eaa3f-40b8-7f72-b078-717e91722ad2` / Schrodinger | `scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json`；`examples/config/training/active/air_combat/README.md`；`examples/config/training/active/air_combat/README.zh.md` | 判断并在合理时实现 Stage-2 显式低权重后果 reward opt-in，同时更新 active-entry 文档。 | integrated pass |
| `DCR-E-X1` | `DCR-E Probe Evidence` | read-only explorer `019eaa3f-41c0-7083-a7a7-ef40c0286981` / Hegel | none | 找出最短 probe/replay 路径，用来分开报告 release、effects、damage 和 consequence reward evidence。 | returned pass |
| `DCR-E-P1` | `DCR-E Probe Evidence` | current-session diagnostics worker `019eaa45-751b-7d43-a18e-4042b9c92686` / Aquinas | `tools/diagnostics/air_combat_stage0_process_probe.py`；`tests/runtime/air_combat/test_diagnostics_probe_contracts.py` 或窄 diagnostics 测试 | 给 process-probe row/summary 增加 DCR reward 前缀聚合，不改变 release/effects/damage 语义。 | integrated pass |
| `DCR-E-X2` | `DCR-E Probe Evidence` | read-only explorer `019eb24e-8a69-7a50-a4eb-1ecbc8294693` / Mill | none | 找出最短受控命中、固定发射或 replay 路径，证明 effects/damage 早于非零 DCR reward terms。 | returned partial |
| `DCR-E-P2` | `DCR-E Probe Evidence` | current-session diagnostics worker `019eb268-fafc-7950-9058-901e318b659c` / Ohm | diagnostics/probe surface only | 复用 Stage-0 fixed-fire 证据路径，在 diagnostics-only 桥接中启用 DCR terms 并捕获 timing fields。 | returned partial |
| `DCR-E-R1` | `DCR-E Probe Evidence` re-scope | read-only explorer `019eb24e-8a69-7a50-a4eb-1ecbc8294693` / Mill | none | 选择下一条可验收 DCR-E 路径：带 DCR-readable consequence fields 的受控 replay/fixture，或另行定界的 damage-report projections 到 DCR terms 的 reward mapping。 | returned pass |
| `DCR-E-P3` | `DCR-E Probe Evidence` | future diagnostics worker | `tools/diagnostics/air_combat_stage0_process_probe.py`；`tests/runtime/air_combat/test_diagnostics_probe_contracts.py` | 增加 controlled fixture/probe 路径，产生 DCR-readable consequence fields，并证明首个非零 DCR 晚于 effects/damage。 | ready |

## 已返回派发包记录

### DCR-D-W1

Worker 返回 `pass`。

- Stage-2 training-shaped 场景 opt-in 低权重：
  `air_combat_damage_consequence_shaping_enabled=true`、
  `air_combat_target_damage_consequence_scale=0.05`、
  `air_combat_self_damage_consequence_scale=0.02`，以及
  `air_combat_damage_consequence_delta_clip=0.5`。
- 既有 release/C2/ROE rewards 未改动。
- `train.py --test_only` 到达 runtime preflight；后续候选 Stage-2 模型 probe 未触发发射，
  这只是延后的 learned-policy 证据路径，不是杀伤链 blocker。

### DCR-E-X1

Explorer 返回 `pass`。

- 最佳后续 learned-policy probe 入口：
  `tools/diagnostics/air_combat_stage0_process_probe.py --mode model`。
- `train.py --test_only` 不足以作为 DCR-E，因为它不暴露逐步 reward terms 或 engagement events。
- 证明条件：首个非零 DCR reward-term step 必须晚于首个 effects/damage step，也晚于 release；
  只看到 release reward 不能算后果证据。
- 当前杀伤链工作不要等待 learned Stage-2 model；应使用受控命中/固定发射/replay probe。
  如果后续 Stage-2 重跑仍然只有 release、没有 effects/damage，则把训练消费者证据记录为
  `partial/held`，不能 accepted。

### DCR-E-P1

Worker 返回 `pass`。

- Process-probe row 现在导出 `damage_consequence_reward_total`、
  `target_damage_consequence_reward_total` 和 `self_damage_consequence_reward_total`。
- Episode summary 现在包含同样的 totals，以及 target/self/combined DCR 首个非零 step。
- 聚焦 diagnostics tests 通过。
- 主线程随后用候选 Stage-2 模型跑了 2 episode x 512 step model-mode probe；该模型未发射，
  release/effects/damage/DCR reward 均为 0，不能作为 live consequence evidence。

### DCR-E-X2

Explorer 返回 `partial`。

- 最短现有 live 路径是 Stage-0 `forced_fire` process probe：它显示 release 在 step `1`，
  effects/damage report 在 step `137`，并有 7 条 lethality-chain rows。
- 它不能证明非零 DCR reward，因为 Stage-0 没有 opt into damage-consequence shaping；
  DCR totals 保持 `0.0`。
- 本地没有可用 replay artifact；learned Stage-2 候选模型仍然不是 consequence evidence，
  因为它没有发射。
- 最小下一步是 `DCR-E-P2`：做一个 diagnostics-only bridge，把受控 fixed-fire effects/damage
  与启用的 DCR reward terms 放到同一条记录中，并报告 timing fields。

### DCR-E-P2

Worker 返回 `partial`；主线程复验匹配该 blocker。

- 新增 probe-only `--diagnostic_dcr_bridge` reward overrides 和简洁的
  `controlled_consequence_bridge_records`。
- 聚焦 diagnostics tests 通过：`25 passed`。
- demonstrator 显示 `first_release_step=1`、
  `first_effects_event_step=137`、`first_damage_report_step=137`，
  且有 7 条 lethality-chain rows。
- 同一记录仍为 `first_damage_consequence_reward_step=null` 和
  `damage_consequence_reward_total=0.0`，因此不是 accepted DCR-E consequence evidence。
- blocker：受控 fixed-fire damage report 仍是 `combat_capable`，
  `system_health_delta=0.0`，且没有 mission/mobility/sensor kill，所以 reward 层没有
  DCR-readable consequence。

### DCR-E-R1

只读重定界包返回 `pass`。

- 推荐下一包：`DCR-E-P3 Controlled Consequence Fixture Probe`。
- 首选路径：通过 diagnostics probe surface 做 controlled fixture/debug-hit 证据。
- 验收条件：compact bridge record 有 release/effects/damage，`first_damage_consequence_reward_step`
  非 null 且晚于 effects/damage，并且 target/combined DCR totals 非零。
- 保留路径：damage-report projections 到 DCR terms 的 reward mapping 应作为单独 semantic packet，
  只触及 reward runtime/tests，且默认关闭。

## Worker Packet 合同

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 集成说明

- 主线程负责最终 status 修改和 DCR-F closure/index sync。
- DCR-D 和 DCR-E 不能修改 reward runtime 或聚焦 reward tests。
- DCR-E 需要 `DCR-E-P3` controlled fixture evidence 后才能 accepted；不得用 fixed-fire
  zero totals 将 DCR-E 标为 accepted。
- damage-report projections 到 DCR terms 的 reward mapping 仍保留为单独 semantic follow-up，
  如果 fixture 路线不能收口再启用。
- probe evidence 文档应先来自受控杀伤链 probe 或 replay artifact；learned Stage-2 证据以后再追加。
