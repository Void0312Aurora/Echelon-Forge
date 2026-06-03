# A4 授权首发 Post-Routing Probe - 2026-06-03

状态：`2026-06-03`，保留 `combat_weapons` HMoE route 后的 learned-policy
证据。A4 继续 held；M2 继续 held。

语言：

- 英文规范页：
  [a4_authorized_first_shot_post_routing_probe_20260603.md](a4_authorized_first_shot_post_routing_probe_20260603.md)
- 中文辅文：`a4_authorized_first_shot_post_routing_probe_20260603.zh.md`

## Scope

本 probe 检查保留的 `combat_weapons` HMoE family 是否能让维护中的 S1 C2/ROE
temporal probe 学到 deterministic 授权首发。它也记录一次被拒绝的 A4-only
pulse-prior 放松试验，避免把两个结果混淆。

当前保留实现是 `combat_weapons` routing surface 以及 C2 config 的 family-count 更新。
代码中不保留 pulse-prior 放松。

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a4_authorized_first_shot_routed_retained_temporal_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260624
```

Result：

- 完成 `32768` timesteps。
- final model 保存到
  `experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/final_model.zip`。
- final rollout reward 约 `-2.77e3`。
- HMoE diagnostics 证明 route 修复生效：
  - `hmoe/fam/combat = 1`；
  - 早期 diagnostics 中 `sub/combat/first_shot = 1`；
  - 后期 diagnostics 中 `sub/combat/first_shot = 0.5`、
    `sub/combat/assess = 0.5`。
- 与被拒绝的 pulse-prior trial 相比，runtime no missiles remaining warning 明显稀疏。

## Probe Commands

deterministic：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260625 \
  --max_steps 2400
```

stochastic：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/final_model.zip \
  --episodes 3 \
  --seed 20260625 \
  --max_steps 2400 \
  --stochastic
```

## Results

| Probe | Episodes | Termination | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts | Damage reports |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 15 | 9 | 3 | 6 | 6 | 2 |

逐 episode stochastic summary：

| Episode | Attempts | Releases | Authorized | Violations | Invalid attempts | Final missiles | Damage reports |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 5 | 4 | 1 | 3 | 1 | 0 | 1 |
| 1 | 7 | 4 | 1 | 3 | 3 | 0 | 1 |
| 2 | 3 | 1 | 1 | 0 | 2 | 3 | 0 |

## Interpretation

保留的 route change 是有价值且已验证的：C2/ROE mission semantics 现在进入
`combat_weapons`，不再进入通用 `nav/vector`。相比 reward-only probe，stochastic
行为有小幅改善：attempts 从 `20` 降到 `15`，releases 从 `11` 降到 `9`，
violation releases 从 `8` 降到 `6`，invalid attempts 从 `9` 降到 `6`，
damage reports 从 `1` 增加到 `2`。

这仍不是 A4 验收：

- deterministic policy 仍不 fire；
- stochastic policy 能发现授权首发，但 3 个 episode 中有 2 个仍会在发射后重复发射；
- 剩余问题比此前更窄：deterministic `fire_weapon` binary logit 仍不过阈值；
  stochastic pulse sampling 能发现 release，但学不到发射后抑制。

## Rejected Pulse-Prior Relaxation

另一次 A4-only safe-action bias relaxation 在
`experiments_tmp/a4_authorized_first_shot_routed_temporal_32k_20260603` 中被测试。
它让 `tms_up` / `fire_weapon` 探索不那么稀疏，但已被拒绝并从保留代码中移除。

| Probe | Episodes | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts | Damage reports |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | 125 | 12 | 3 | 9 | 113 | 0 |

被拒绝 trial 的 final rollout reward 约 `-2.28e4`，且 stochastic 每个 episode 都打空
4 枚导弹。它证明单纯增加 pulse exploration 不是正确修复。

## Next Work

- binary logits/probabilities 已在
  [a4_authorized_first_shot_binary_diagnostics_20260603.zh.md](a4_authorized_first_shot_binary_diagnostics_20260603.zh.md)
  中记录。
- 下一步在 PPO 前考虑 supervised 或 curriculum-style pulse-action target，或采用
  route-specific initialization：只抬高 `authorized_first_shot` subexpert，并抑制
  `post_launch_assess`。
- 在保留 route 和 reward surface 下证明 deterministic 授权首发前，M2 继续 held。
