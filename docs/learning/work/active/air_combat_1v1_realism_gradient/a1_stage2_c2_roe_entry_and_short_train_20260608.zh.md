# A1 Stage-2 C2/ROE 入口与短训 2026-06-08

状态：`stage-2 entry prepared / short train behavior preserved / not accepted`。

## 问题

发射问题已经由 M3-S2 在 active Stage-1 C2/ROE 场景与配置上做了有边界验收。A1
下一步是否可以进入更高真实度的 Stage-2：机动红方战斗机、红方无武器、仍保持蓝方单发
授权发射纪律？

本记录只回答训练入口和短训行为，不验收命中、毁伤、击杀或完整 `combat_win`。

## 新增入口

新增 Stage-2 C2/ROE training-shaped 场景：

`scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json`

新增 active training config：

`examples/config/training/active/air_combat/air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`

设计边界：

- 几何、平台、弹药和脚本红方行为继承 canonical Stage-2 evasive fighter 场景。
- 红方仍无可用导弹。
- mission command 补齐 Stage-1 M3-S2 使用的 C2/ROE single-shot-then-assess 字段。
- 训练配置继承 M3-S2 direct fire-boundary owner；不削弱 A3/A5 合法性和 one-shot 状态机。

## 入口探针

Stage-1 完整后果窗口 baseline：

- artifact：
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/baseline_deterministic_seed20260608_ep1_2400.json`
- 模型：
  `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip`
- 结果：deterministic 在 step `423` 发射一次，step `938` 有 effects/damage report，
  但 target health 仍为 `40.0`，最终 `combat_timeout`。

旧 Stage-2 场景直接套 Stage-1 config 的短 smoke：

- artifact：
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/stage2_smoke_model_seed20260608_ep1_64.json`
- 结果：能运行，但没有 active Stage-2 C2/ROE training entry；`policy_event_mask_fire_once_open_count = 0`，
  `authorized_window_step_count = 0`。

新 Stage-2 C2/ROE oracle smoke：

- artifact：
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/stage2_c2_roe_legal_mask_fire_range30k_seed20260608_ep1_3200.json`
- 结果：30 km range-gated `legal_mask_fire` 在 step `1071` 发射一次；
  requested / accepted / rejected 为 `1 / 1 / 0`；
  release / authorized / violation / repeat-before-assessment 为 `1 / 1 / 0 / 0`；
  effects/damage 为 `0 / 0`，最终 `combat_timeout`。

M3-S2 Stage-1 final model 迁移 smoke：

- artifact：
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/stage2_c2_roe_model_seed20260608_ep1_3200.json`
- 结果：deterministic 在 step `1311` 发射一次；
  requested / accepted / rejected 为 `1 / 1 / 0`；
  release / authorized / violation / repeat-before-assessment 为 `1 / 1 / 0 / 0`；
  effects/damage 为 `0 / 0`，最终 `combat_timeout`。

## Stage-2 8k 短训

命令：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1 \
  --init_from experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip \
  --n_envs 1 \
  --torch_threads 1 \
  --seed 20260608 \
  --diagnostics \
  --diagnostics_every 2048
```

Artifacts：

- `experiments_tmp/a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1/final_model.zip`
- `experiments_tmp/a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1/checkpoints/`
- `experiments_tmp/a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1/logs/`

训练观察：

- 训练完成 `8192` steps。
- 中段能看到有效 fire-boundary rows，例如 step `1536` 附近
  `m3s2/fb_active_count = 179`、`fb_cross_in_window_ratio = 1`。
- 后续 rows 覆盖不稳定，多段 rollout 记录 `fb_active_count = 0`。
- final diagnostics 看到 open mask 与 event mode 跨阈值：
  `diag/pi_event_fire_mask_frac = 1`、`diag/pi_event_fire_p_mean = 0.568`、
  `diag/pi_event_mode_fire_frac = 1`。
- 训练期间仍没有产生 accepted release；behavior 必须以保存模型 probe 为准。

## Final Model Probes

Deterministic：

- artifact：
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/stage2_c2_roe_after_8k_deterministic_seed20260608_ep1_3200.json`
- first release：step `1126`
- requested / accepted / rejected：`1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment：`1 / 1 / 0 / 0`
- effects / damage：`0 / 0`
- final target health：`100.0`
- termination：`combat_timeout`

Stochastic：

- artifact：
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/stage2_c2_roe_after_8k_stochastic_seed20260608_ep1_3200.json`
- first release：step `1082`
- requested / accepted / rejected：`1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment：`1 / 1 / 0 / 0`
- effects / damage：`0 / 0`
- final target health：`100.0`
- termination：`combat_timeout`

## 判定

Stage-2 C2/ROE 入口可以进入下一轮训练：运行时能接住 single-shot release discipline，
M3-S2 Stage-1 final model 可以迁移出一次授权发射，8k Stage-2 续训后的 deterministic 与
stochastic 单集 probe 也都保住一次授权发射。

但 Stage-2 不接受：

- 当前只验证了单 seed deterministic/stochastic behavior，没有 batch seed 验收。
- fire-boundary rows 在 Stage-2 8k 训练中覆盖不稳定。
- final probes 没有 effects、damage、health drop、kill 或 `combat_win`。
- stochastic probe 的 quality-window rows 为 `0`，说明随机单集虽然发射干净，但不能作为时机质量证据。

下一步应做小批量 Stage-2 firing-retention validation，然后再决定是否扩大训练或调整
Stage-2 window/support collection。不要把本记录解释成 Stage-2 战果闭合。
