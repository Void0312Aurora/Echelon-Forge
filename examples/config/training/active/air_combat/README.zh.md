# 空战 1v1 训练条目

此目录存放正在维护的 `1v1` 空战执行配置。

## 范围

- 该路线的场景配对为：
  - [air_combat_1v1_headon_sensor_smoke_v1.json](../../../../../scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)
    - 由 scripted-red `F-16C` smoke 和 8k probe 条目使用。
  - [air_combat_1v1_stage0_drone_weapon_employment_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json)
    - 由 Stage-0 drone weapon-employment reactive 和 temporal world-batch probe 条目使用。
  - [air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json)
    - 由 Stage-1 BVR non-maneuvering target world-batch probe 条目使用。
  - [air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json)
    - 在杀伤链和 hybrid 动作接口都可用后，由 Stage-1 M1 hybrid shaped 训练探针使用。
  - [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json)
    - 由 additive Stage-1 A3 C2/ROE hybrid shaped 与 temporal shaped 探针使用；既有 M1 baseline 条目仍保持 `mission_obs_mode=basic`。
  - [air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json)
    - 由 A1 Stage-2 C2/ROE M3-S2 续训入口使用；目标是把已验收的 Stage-1 发射纪律迁移到机动红方、红方无武器场景。
    - 从 DCR-D 起，它显式 opt-in 低权重 damage consequence reward terms；这些项只作为 synthetic training shaping。
- 当前基线为：
  - 蓝方学习者：`F-16C_Block50`
  - 早期课程目标：Stage 0 和 Stage 1 使用无武器 `MQ-9_Reaper` 替身
  - scripted-red smoke 对手：场景声明的 `F-16C_Block50`
  - 策略架构：`HierarchicalMoEExecutionPolicy`
- canonical Stage-2 和 Stage-3 的 `scenarios/air_combat/1v1` 文件仍是受维护的课程场景；本目录目前只为 Stage-2 C2/ROE training-shaped 入口提供 active config，Stage-3 仍未配对 active training config。

## 条目

- [air_combat_1v1_f16c_scripted_red_smoke_v1.json](air_combat_1v1_f16c_scripted_red_smoke_v1.json)
  - 在标准 `execution` vec-env 路径上的最小引导烟雾测试。
  - 直接使用维护中的 HMoE 策略表面，而非共享策略回退。

- [air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json](air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json)
  - 在维护中的默认 `WorldBatchVecEnv` 路径上的对应烟雾测试条目。
  - 当你希望验证脚本化红方对手和 HMoE 策略也能在批处理运行时路径上正确推进时，请使用此项。

- [air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1.json](air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1.json)
  - 维护中的 `WorldBatchVecEnv` 路径上的短程 HMoE 训练探针。
  - 它超过 smoke 长度，但仍足够小，适合高频诊断。
  - 在进入 32k/64k resume ramp 前，先用它确认早期终止是否仍被飞行稳定性伪影主导。

- [air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json](air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json)
  - 维护中的 `WorldBatchVecEnv` 路径上的 TG-P7 目标几何代理 opt-in 探针。
  - 通过 `runtime.database_path` 加载 R3 代理数据库，同时保持默认 `examples/config/database` 的 F-16 毁伤模型不变。
  - 携带 `A2_TARGET_GEOMETRY_PROXY_F16C_R22` 元数据，使几何代理训练证据与默认毁伤模型 authority 分离。

- [air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1.json](air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1.json)
  - 阶段零无人机武器使用探针，保留单帧 `TransformerExtractor` 作为 reactive 对照。
  - 用于观察基础开火流程、重复发射和奖励/终止链路。

- [air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1.json](air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1.json)
  - 阶段零的 M1 temporal HMoE 探针。
  - 它启用 `temporal_history_len=16` 与 `TemporalTransformerExtractor`，其余主要超参贴近 reactive 对照。
  - 这是路径 C 前的验证入口，不代表正式 sequence-native 因果策略。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json)
  - Stage-1 类 BVR 距离扩展探针，对手仍是无武器、非机动目标。
  - 保持与 Stage 0 相同的 HMoE execution surface，同时用更长接触保持和导弹飞行时间增加 rollout horizon 压力。
  - 这是杀伤模型完成后的第一个继续推进入口；仍是 active probe，不是 fixed-fire win gate 或 frozen baseline。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1.json)
  - Stage-1 的 M1 temporal HMoE 探针。
  - 它启用 `temporal_history_len=16` 与 `TemporalTransformerExtractor`，其余主要超参贴近 Stage-1 reactive 对照。
  - 用于在杀伤链路恢复后比较 temporal window 是否改善重复发射、发射间隔和固定诊断指标。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json)
  - Stage-1 的 M1 action-interface probe，使用 `action_mode=air_combat_hybrid_v1`。
  - 飞行控制仍是连续轴，雷达 / TMS / master-arm / fire / weapon-select 在 policy 侧使用 hybrid action 语义。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_world_batch_probe_v1.json)
  - Stage-1 的 M1 action-interface + temporal probe。
  - 用于把动作可达性修复和 observation-window temporal 证据分开比较。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json)
  - Stage-1 的 M1 hybrid shaped 训练探针。
  - 使用 training-shaped Stage-1 场景，加入稳定飞行塑形和首枚有效发射奖励，同时保留 canonical Stage-1 的几何、武器和毁伤 runtime。
  - 启用一个很窄的稳定飞行残差 wrapper，只 blend 飞控轴 `[0, 1, 2, 3]`；hybrid 作战命令不锁定、不 snap。
  - 这是检查修复后的动作接口能否恢复 release exploration 的维护入口，再往后才进入更长 M1 evidence run。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json)
  - Stage-1 A3 C2/ROE hybrid shaped 探针，使用 `mission_obs_mode=air_combat_c2_roe_v1`。
  - 使用 C2/ROE training-shaped Stage-1 场景，并显式给出 single-shot-then-assess command state。
  - 这是 reward/process metrics 仍由 A3 reward/diagnostics stream 处理期间的 additive partial probe 入口。
  - 从 A4 起，此条目使用五族 HMoE route surface `[3, 2, 3, 1, 3]`，第五族为 `combat_weapons`。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json)
  - Stage-1 A3 C2/ROE hybrid temporal shaped 对照探针，使用 `mission_obs_mode=air_combat_c2_roe_v1`。
  - 与 A3 C2/ROE reactive shaped 条目配对，只额外启用 `temporal_history_len=16` 和 `TemporalTransformerExtractor`。
  - 这是 post-launch mission observation 动态化后，重跑 reactive/temporal learned-policy 对照的维护入口。
  - 从 A4 起，它与 reactive C2/ROE shaped probe 共享 `combat_weapons` family；已拒绝的 pulse-prior 试验不保留。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json)
  - Stage-1 A6 deadline-bootstrap 探针，使用相同的 C2/ROE temporal shaped surface。
  - 合法性继续由 A3/A5 event mask 与状态转移持有。
  - 将短暂衰减 curriculum 替换成 open-window 年龄阈值之后的持续 deadline target；它是 A6 re-scope 证据，不释放 M2。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json)
  - Stage-1 A6-EVT-K event-head optimization 探针，使用相同的 deadline-bootstrap C2/ROE temporal shaped surface。
  - 增加 `hybrid_event_head_lr_scale=10.0`，作为零初始化的 `hold/fire_once` event-logit 专用更新通道。
  - 它用于在 event-head update-strength audit 后测试 optimizer ownership；不削弱 A3/A5 masks，也不释放 M2。
  - 32k A6-EVT-K probe 已跨过 deterministic argmax 并保留 one-shot discipline，但 A6 因 launch-window timing quality 继续 held。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json)
  - Stage-1 A6-EVT-L launch-window timing-contract 探针，使用相同的 event-head C2/ROE temporal shaped surface。
  - 通过 policy-observed contact range / track age 与 legal-window age，将 legal authorization 与 quality-window launch labels 分开。
  - early accepted releases 会变成 negative labels；deadline/curriculum positives 由 launch window gate 约束。
  - 这是下一轮短探针的 implementation/evidence entry，不是 M2 release、doctrine、missile-authority 或 Pk evidence。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json)
  - Stage-1 A7 event-credit 探针，使用相同的 C2/ROE temporal shaped surface 与 launch-window gate。
  - 关闭 A6 hazard loss，用 value credit 与 event-logit delta alignment 训练 zero-initialized `hybrid_event_credit_head`。
  - 包含 `a7_event_credit_shadow_quality_weight=1.0`，用于 A7-EVC-J shadow-quality target repair 路径。
  - 从 A7-EVC-M 起，启用 projected legal-open credit：
    `a7_event_credit_legal_projection_enabled=true`、
    `a7_event_credit_projection_value_coef>0` 与
    `a7_event_credit_projection_delta_align_coef>0`。
  - 从 A7-EVC-V 起，启用 protected online credit update contract：
    `a7_event_credit_separate_update_enabled=true`、
    `a7_event_credit_separate_update_max_grad_norm=0.5` 与
    `a7_event_credit_delta_align_positive_only=true`。
  - A3/A5 legality masks 与 one-shot state-machine authority 保持不变。
  - 它已用于 A7-G r3 与 A7-EVC-J repair evidence；两者均有效但 held，因为 deterministic releases 仍为 `0`，quality-window advantage 仍为负。
  - 它现在是 A7-EVC-N short projection learned evidence 的维护入口。
  - 它不是 M2 release、doctrine、missile-authority 或 Pk evidence；focused projection tests 仍不等于 behavior acceptance。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json)
  - Stage-1 A7 显式状态补全探针，使用 `mission_obs_mode=air_combat_c2_roe_v2`。
  - 保持 A7/R event-credit 超参数不变，但在 mission observation 中显式暴露当前 legal-open age、launch-window readiness、quality-window readiness、目标距离和目标 track age。
  - 包含 A7-EVC-V protected credit update contract：独立 credit-head value
    updates、positive-only delta alignment 与独立 clip budget。
  - 32k S probe 已完成为 held evidence：focused tests 通过，open-window fire probability 上升，但 deterministic probing 仍记录 `0` releases，quality-window advantage 仍为负。
  - 它是 pre-M2 结构可观测性实验；不释放 sequence-native M2、doctrine、missile-authority 或 Pk evidence。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json)
  - Stage-1 M3-S1 grouped stopping 短探针，复用 A7 显式状态补全 observation surface。
  - 打开 independent `m3_stopping_head` 与 `m3s1_grouped_stopping_*` auxiliary objective，同时保持 A7 系数和 A3/A5 legality masks 不变。
  - 使用 8k budget 形成 validation evidence，不是 promoted formal training run。
  - 该条目只能证明 M3 stop-boundary movement；在 stopping head 与 hybrid event action path 连接或对照前，executable fire timing 仍 held。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json)
  - Stage-1 M3-S2 direct fire-boundary 短探针，复用 A7 显式状态补全 observation surface。
  - 保留 HMoE 与 `air_combat_hybrid_v1`，但在该配置中让 `hybrid_event_head` 成为唯一 executable hold/fire owner；M3 stopping 与 window-classifier event adapter 均显式关闭。
  - 复用 grouped sidecar 的 legal/quality rows 作为 boundary labels，在最终 executable fire-minus-hold logit 上计算 loss，并将 dedicated auxiliary update 限定为只写 `hybrid_event_head` 参数。
  - 使用显式 logit calibration：非质量 legal rows 被压到负 ceiling 以下，quality-window rows 被推向正 floor。
  - 使用 support-preserving collection，并保留 quality-window hold，使 sidecar 可以看到完整 legal-to-quality transition 后再谈行为验收。
  - 使用 8k budget 形成 validation evidence；行为验收仍需要 learned-policy release probes。

- [air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json](air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json)
  - A1 Stage-2 C2/ROE M3-S2 续训入口，使用机动红方、红方无武器的 training-shaped Stage-2 场景。
  - 复用 Stage-1 M3-S2 direct fire-boundary owner 与 `air_combat_c2_roe_v2` observation surface，
    不削弱 A3/A5 发射合法性和 one-shot 状态机。
  - `2026-06-08` 8k init-from-Stage-1 短训后的 deterministic/stochastic 单集 probe 都保住一次授权发射，
    但没有 effects/damage/kill；因此它是 Stage-2 训练入口，不是阶段验收。
  - 配对的 Stage-2 training-shaped 场景现在显式启用低权重 damage consequence shaping：
    `air_combat_damage_consequence_shaping_enabled=true`、
    `air_combat_target_damage_consequence_scale=0.05`、
    `air_combat_self_damage_consequence_scale=0.02`，以及
    `air_combat_damage_consequence_delta_clip=0.5`。
  - 这些项只从已经观测到的 consequence state 提供 synthetic 训练反馈；它们不闭合发射行为，不声明真实 Pk/击杀权威，不改变 weapon 或 damage runtime，也不构成 Stage-2 验收证据。

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1.json)
  - Stage-1 的 M1 hybrid temporal shaped 对照探针。
  - 与 hybrid shaped 条目使用同一 training-shaped 场景、同一稳定飞行残差 wrapper 和同一低初始探索噪声。
  - 只额外启用 `temporal_history_len=16` 与 `TemporalTransformerExtractor`，用于重新比较时间窗口是否改善早发、多发和发射间隔。

## 设计说明

- 这些烟雾测试条目有意设为非可视化。
  - 目标是首先验证作战任务契约和运行时链路，而非可视吞吐量。
- 这些烟雾测试条目直接使用当前 HMoE 主线架构。
  - `1v1` 并不将独立的共享策略活动条目作为其主要维护路径。
- 当前 legacy `1v1` smoke 和 M1 baseline 条目仍使用 `mission_obs_mode=basic`。
  - 因此 HMoE 策略处于活跃状态，但暴露给策略的维护路线语义仍然最小化。
  - 在当前烟雾日志中，这意味着路由停留在导航族/子专家上，这对于链路验证是可接受的，但尚未形成完全差异化的作战路由配置。
  - A3/A4 C2/ROE 探针是单独的 additive entries；不能据此推断既有 M1 baseline 已改变 observation mode。
  - 专用 `combat_weapons` HMoE family 只在策略看到 `mission_obs_mode=air_combat_c2_roe_v1` 时可达。
- raw `full`、hybrid 和 temporal 烟雾测试条目有意不启用维护中的脚本化残差动作封装。
  - shaped hybrid 与 hybrid temporal shaped 训练探针是例外：它们只把前四个飞控轴和 stable-flight baseline 做残差混合，雷达 / master-arm / fire / weapon-select 仍保持策略直接控制。
  - 在首次 `1v1` 烟雾测试中，我们仍希望学习者保留原始动作表面。
- 这些条目尚未成为验收/冻结基线。
  - 仅在 `1v1` 奖励/终止/评估行为足够稳定（可跨运行比较）之后才进行提升。
- temporal 条目只增加策略可见的短历史。
  - 它不改变导弹物理、弹药、冷却或环境侧战术记忆。
- hybrid 条目只改变训练侧动作接口。
  - 它把 `fire_weapon` 暴露为 policy-facing pulse/effective transport 语义；不改变武器释放内核、发射包线或杀伤模型。
