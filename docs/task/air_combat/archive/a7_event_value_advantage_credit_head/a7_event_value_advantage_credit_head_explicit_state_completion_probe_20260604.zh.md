# A7 显式状态补全探针

状态：`2026-06-04` 通过；学习行为仍 held。

父项目：[README.zh.md](README.zh.md)。

## 目的

本切片验证一个 pre-M2 假设：A7/R 停滞，可能是因为 policy 无法从
`temporal_history_len=16` 推断 `min_window_age_steps=32` 所需的合法窗口年龄，
且 `air_combat_c2_roe_v1` 没有显式暴露 legal-open age、launch-window readiness
或 quality-window readiness。

实验新增兼容的 `air_combat_c2_roe_v2`，保留 v1 与 A3/A5 mask，并新增：

- `fire_mask_open`
- `launch_window_open`
- `quality_window_ready`
- `legal_open_age_steps` / `legal_open_age_norm`
- `launch_window_age_steps` / `launch_window_age_norm`
- `target_range_m`
- `target_track_age_s`

## 实现面

- `python/mission_obs_taxonomy.py`：新增 29D 的 `air_combat_c2_roe_v2`。
- `gym_envs/scenario_loader/mission_observation.py`：生成显式合法窗口、发射窗口、年龄、目标距离和 track age；年龄计数以 loader step 为 key，避免同一步多次读取导致虚增。
- `gym_envs/universal_env_parts/air_combat_event_action.py` 与
  `gym_envs/scenario_loader/loading.py`：在 episode/scenario 边界重置补全状态。
- `python/rl/policy_algo/policies.py`、`hmoe_routing.py`、
  `ppo_adaptive_kl.py`、`first_event_projection.py`：按 taxonomy 字段名兼容
  v1/v2，不再依赖 20D 硬编码。
- `python/models/transformer.py`：为空战 C2/ROE mission token 增加尺度预处理。
- 新 active config 只把 A7/R 的 `mission_obs_mode` 从
  `air_combat_c2_roe_v1` 改为 `air_combat_c2_roe_v2`，其他 A7 超参保持不变。

## 验证

聚焦测试：

```bash
pytest tests/runtime/mission/test_mission_obs_taxonomy.py \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/hmoe/test_hmoe_routing.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_air_combat_active_training_entries.py -q
```

结果：`105 passed in 27.58s`。

`git diff --check`：通过。

## 学习探针

32k 短训完成并保存：

```text
experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1/final_model.zip
```

关键训练观察：

- 早期 `LEGAL_OPEN_QUALITY` 正样本很快进入训练路径：`3072` 步时
  `count_mean=225`，advantage 约 `-0.153`。
- 中段 legal-open quality 正样本经常达到 `410` 到 `450` 条/rollout，但
  event-credit advantage 仍保持负值。
- 最终 rollout 仍有 `count_mean=330`、`positive_count_mean=330`，
  `target_positive_frac=0.645`，但 advantage 约 `-0.924`。
- open-window event-fire probability 约升至 `0.305`，但 deterministic event
  mode 仍是 `hold`。

deterministic probe：

- 4 episodes 中 `0` fire requests、`0` accepted releases、`0` violations、
  `0` repeats。
- fire mask open steps 为 `[599, 559, 599, 599]`。
- authorized-window event-fire probability mean 为 `0.2634`。
- quality-window A7 advantage mean 为 `-0.8534`。

stochastic probe：

- 8 episodes 中 `8` fire requests、`8` accepted releases、`8` release executions。
- `0` unauthorized/violation releases、`0` repeat releases、`0` shot-budget violations。
- release steps 为 `[6, 42, 4, 2, 5, 46, 3, 46]`。
- 仍是早发，基本没有等到 quality window 成熟。

## 结论

显式状态补全改善了 observation contract，并让窗口年龄/质量窗口状态对 policy
可见；它也提升了 open-window fire probability。

但它不是根治。模型仍在 pre-window 与 quality-window 上学出负的
`Q_fire_once - Q_hold`，deterministic mode 仍保持 `hold`。因此下一步不应是
继续调系数，而应定位正标签/value credit 为什么被转换成负 advantage，以及
event-logit coupling 为什么跟随这个负 advantage。

## 下一步

进入结构性的 value/policy coupling audit。M2 仍可能是长期方向，但本探针说明
眼前问题并不只是“policy 看不见 window age”；当前学习到的 value/advantage
对象本身仍然错误，或其和 event policy 的耦合方向有问题。
