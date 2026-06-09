# A2 Damage Consequence Reward Surface Dispatch Queue

Status: `2026-06-09` current-session dispatch for DCR-D and DCR-E. DCR-D-W1,
DCR-E-X1, and DCR-E-P1 returned.

Chinese companion:
[damage_consequence_reward_surface_dispatch_queue_20260609.zh.md](damage_consequence_reward_surface_dispatch_queue_20260609.zh.md)

Parent task cluster:
[damage_consequence_reward_surface_task_clusters_20260609.md](damage_consequence_reward_surface_task_clusters_20260609.md)

## Boundary

This queue only dispatches the reward-extension follow-on after DCR-A-C. It does
not create a new conversation thread, does not reopen sealed A2, and does not
claim real Pk, deterministic fuze, stock AIM-120C / MQ-9 lethality, or Stage-2
acceptance.

## Active Packets

| Packet | Cluster | Assignee | Write set | Required output | Status |
| --- | --- | --- | --- | --- | --- |
| `DCR-D-W1` | `DCR-D Scenario Opt-In` | current-session worker `019eaa3f-40b8-7f72-b078-717e91722ad2` / Schrodinger | `scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json`; `examples/config/training/active/air_combat/README.md`; `examples/config/training/active/air_combat/README.zh.md` | Decide and, if justified, implement explicit low-weight Stage-2 consequence reward opt-in plus active-entry docs. | integrated pass |
| `DCR-E-X1` | `DCR-E Probe Evidence` | read-only explorer `019eaa3f-41c0-7083-a7a7-ef40c0286981` / Hegel | none | Map the shortest probe/replay path for separate release/effects/damage/consequence reward evidence. | returned pass |
| `DCR-E-P1` | `DCR-E Probe Evidence` | current-session diagnostics worker `019eaa45-751b-7d43-a18e-4042b9c92686` / Aquinas | `tools/diagnostics/air_combat_stage0_process_probe.py`; `tests/diagnostics/test_air_combat_process_probe.py` or a narrow diagnostics test | Add DCR reward-prefix aggregation to process-probe rows/summaries without changing release/effects/damage semantics. | integrated pass |

## Returned Packet Notes

### DCR-D-W1

Worker returned `pass`.

- Stage-2 training-shaped scenario opt-in uses low weights:
  `air_combat_damage_consequence_shaping_enabled=true`,
  `air_combat_target_damage_consequence_scale=0.05`,
  `air_combat_self_damage_consequence_scale=0.02`, and
  `air_combat_damage_consequence_delta_clip=0.5`.
- Existing release/C2/ROE rewards were left unchanged.
- `train.py --test_only` reached runtime preflight; a later candidate Stage-2
  model probe produced no release. This is a deferred learned-policy evidence
  path, not a kill-chain blocker.

### DCR-E-X1

Explorer returned `pass`.

- Best future learned-policy probe entry:
  `tools/diagnostics/air_combat_stage0_process_probe.py --mode model`.
- `train.py --test_only` is not enough for DCR-E because it does not expose
  per-step reward terms or engagement events.
- Proof condition: the first nonzero DCR reward-term step must occur after the
  first effects/damage step and after release; release rewards alone do not
  count as consequence evidence.
- For the current kill-chain work, do not wait on a learned Stage-2 model; use a
  controlled hit/fixed-release/replay probe. If a later Stage-2 rerun still has
  release but no effects/damage, record that training-consumer evidence as
  `partial/held`, not accepted.

### DCR-E-P1

Worker returned `pass`.

- Process-probe rows now export `damage_consequence_reward_total`,
  `target_damage_consequence_reward_total`, and
  `self_damage_consequence_reward_total`.
- Episode summaries now include the same totals plus first nonzero DCR
  target/self/combined steps.
- Focused diagnostics tests passed.
- The main thread later ran a 2 episode x 512 step model-mode probe with a
  candidate Stage-2 model. That model did not fire; release/effects/damage/DCR
  reward stayed at 0, so it is not live consequence evidence.

## Worker Packet Contract

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Integration Notes

- Main thread owns final status edits and DCR-F closure/index sync.
- DCR-D and DCR-E must not change reward runtime or focused reward tests.
- No active current-session workers remain for this queue.
- Any probe evidence document should be created from a controlled kill-chain
  probe or replay artifact first; learned Stage-2 evidence can be added later.
