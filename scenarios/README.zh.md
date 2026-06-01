# 场景 README

`scenarios/` 存储规范的使命/场景 JSON 文件，按任务领域分组，而不是将所有变体混合在顶层。

维护中的配置文件、工具和测试应继续使用相对于仓库的 `scenarios/...` 路径引用规范场景。`examples/scenarios/` 保留给轻量级示例夹具，除非未来的迁移添加了对两个位置的兼容性并有意更新所有引用。

`scenarios/` 是受维护的仓库输入表面的一部分，预计会保留在 git 版本控制中。这与 `experiments/`、`datasets/` 和 `output/` 不同，后者是运行时/工件工作空间，默认被忽略。

## 布局

- `scenarios/takeoff/`
  - 跑道起飞、离场和地面滑行相关的任务。
- `scenarios/stable_flight/`
  - 针对航向、高度和速度稳定的空中保持和命令跟踪任务。
- `scenarios/cruise/`
  - 航点导航和巡航路线任务，包括 OOD 评估变体。
- `scenarios/air_combat/`
  - 早期的 `1v1` 空战引导夹具和受维护的作战任务冒烟场景。
- `scenarios/naval/`
  - 受维护的 naval bootstrap 与 `N4` pre-fire fixtures，覆盖 ship spawning、escort/screen geometry、tasking、contact/report evidence 与 threat/ROE visibility，但不把 weapon release、damage 或 kill rewards 声明为 `N4` lane 的能力。
- `scenarios/ground/`
  - 受维护的 G0/G1 ground tasking compatibility fixtures。native ground platform-schema 证据在这些场景之外单独维护；movement、terrain、sensing、fires、damage 与完整 ground runtime 行为仍保持 held。
- `scenarios/landing/`
  - 着陆特定任务，如 ILS 进近和滑跑评估。
- `scenarios/combined/`
  - 多阶段任务，在一个场景中涵盖起飞、巡航和着陆。
- `scenarios/templates/`
  - 用于编写新任务的通用场景模板。
- `scenarios/test/`
  - 轻量级内核或物理验证场景，非训练任务。

## 命名指导

- 在将场景文件移动到不同类别文件夹时，保留现有的场景文件名。
- 新场景优先放在其主要评估的任务领域下。
- 当任务有意跨越多个操作阶段时，使用 `combined/`。
- 将 `test/` 保留给最小验证场景，而不是训练/评估内容。

## 维护说明

- 移动场景时，更新所有脚本、合约和工件引用。
- 优先使用完整的仓库相对路径引用场景，例如 `scenarios/combined/takeoff_to_landing_continuous_eval_v1.json`。
- 当工件本地的 OOD 场景是生成的实验输入而非规范共享场景时，将其保留在 `artifacts/.../ood_scenarios/` 下。

## 保留策略

- `scenarios/` 应仅保留规范的维护任务、活跃的回归夹具以及仍然被维护文档或冻结工件清单引用的历史场景。
- 对于一次性调优变体，一旦它们不再是受维护的训练/评估入口、不受合约覆盖且不需要用于工件溯源，则不要保留。
- 当一个场景被更新的规范变体取代时，先更新引用，然后移除过时文件，而不是让多个近乎重复的入口点堆积。
- 如果某个场景仅需要一个实验目录或生成的 OOD 批次，则将其保留在该工件谱系附近，并在文档中记录保留路径，而不是提升到 `scenarios/` 中。

## 受维护的规范集合

- `takeoff/`
  - `takeoff.json`
  - `takeoff_stage1.json`
  - `takeoff_stage1_runway45.json`
  - `takeoff_stage1_runway45_stresswind.json`
  - `cooperative_interval_takeoff_departure_navv2_train_v1.json`
- `stable_flight/`
  - `stable_flight.json`
  - `stable_flight_stresswind.json`
  - `stable_flight_stresswind_rewardbalance_v3.json`
- `cruise/`
  - `cruise_waypoints_paramroute_navv2_train_v1.json`
  - `cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json`
  - `cruise_waypoints_stresswind_rewardbalance_v1.json`
  - `cruise_waypoints_ood_geometry_v1.json`
  - `cruise_waypoints_ood_profile_v1.json`
  - `cruise_waypoints_ood_wind_v1.json`
- `air_combat/`
  - `air_combat_1v1_headon_sensor_smoke_v1.json`
    - 规范对称 `F-16C_Block50 vs F-16C_Block50` `1v1` 引导夹具，具有场景级弹药覆盖和最小击杀目标终止条件。
  - `1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json`
    - 阶段零 drone weapon-employment 夹具，用于 fixed-fire/runtime fire-chain 验证和当前 active Stage-0 probe configs。
  - `1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json`
    - 更远距离的非机动无武装目标夹具，用于 contact persistence 与 missile time-of-flight 检查。
  - `1v1/air_combat_1v1_stage2_evasive_fighter_no_weapons_v1.json`
    - 没有 reciprocal weapon pressure 的 scripted evasive fighter 夹具。
  - `1v1/air_combat_1v1_stage3_limited_weapons_fighter_v1.json`
    - 在任何完整 peer `1v1` 提升前使用的 bounded reciprocal-threat 夹具。
- `naval/`
  - `ddg51_take1_screen_closing_contact_v1.json`
    - contact-geometry 变体，保留 DDG/T-AKE screen tasking，并验证移动 surface contact 与 closest-approach evidence，不涉及 weapons employment。
  - `ddg51_take1_screen_contact_report_v1.json`
    - DDG/T-AKE screen baseline fixture，用于验证 ship spawning、naval task semantics、surface-contact geometry 与 report sharing，仍处于 weapons employment 之前。
  - `ddg51_take1_screen_threat_roe_v1.json`
    - 已接受的 `N4` pre-fire threat/ROE fixture，仅为 contract visibility 携带 engagement-authority 与 assigned-target command state。
  - `ddg51_take1_screen_threat_roe_offstation_recovery_v1.json`
    - 已接受的 `N4` off-station recovery 变体，用于验证 scripted station recovery 与固定 original-task reward reference，同时保持 weapons、interception、damage 与 kill out of scope。
- `ground/`
  - `ground_platoon_tasking_smoke_v1.json`
    - 最小 Army/ground tasking smoke fixture。它仍是 G0 compatibility-shell 场景，只验证共享 loader 与 `TaskOrder -> LeaderIntent -> PilotReport` status chain；native ground schema 证据另行维护。
  - `ground_platoon_static_occupy_v1.json`
    - G1 realism-gradient static occupy fixture。它验证 Army/ground `TASK_OCCUPY` status 语义，并明确延后 movement、terrain、sensing、fires 与 damage。
  - `ground_platoon_support_relationship_v1.json`
    - G1 realism-gradient support relationship fixture。它验证 `TASK_SUPPORT` support IDs 与 common-core status propagation，并明确延后 fire support、sustainment、movement、sensing 与 damage。
- `landing/`
  - `landing_ils_final_train_v1.json`
  - `landing_ils_final_eval_v1.json`
- `combined/`
  - `cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json`
  - `cooperative_takeoff_to_cruise_landing_continuous_train_v1.json`
  - `cooperative_takeoff_to_cruise_landing_continuous_eval_v1.json`
  - `cruise_to_landing_continuous_train_v1.json`
  - `takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json`
  - `takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json`
  - `takeoff_to_cruise_paramroute_navv2_multileg_eval_v1.json`
  - `takeoff_to_cruise_paramroute_navv2_train_v1.json`
  - `takeoff_to_landing_c2_task_demo_fasttrain_v1.json`
  - `takeoff_to_landing_c2_task_demo_v1.json`
  - `takeoff_to_landing_c2_task_only_demo_v1.json`
  - `takeoff_to_landing_c2_task_only_train_v1.json`
  - `takeoff_to_landing_continuous_train_v1.json`
  - `takeoff_to_landing_continuous_eval_v1.json`
- `test/`
  - `test_aero.json`
    - 最小空中空气动力学夹具，明确设定零风速，使内核真实性检查与场景默认风行为隔离。
  - `test_free_fall.json`
    - 最小零速度空中夹具，明确设定零风速，用于重力主导的合理性检查。
- `templates/`
  - `template.json`
