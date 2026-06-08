# A7 验收门

状态：`2026-06-05` evaluated；`A7-EVC-C/D/E/F/G/H/I/J/K/L/M/N/O/P/Q/R/S/T/U/V/W/X`
implementation、validation、learned-evidence、index-sync、target-audit、
shadow-repair、projection-audit、projection-contract 与 projected legal-open
prototype/projection-eligibility/opportunity-contract/opportunity-prototype
slices、explicit state completion、value/policy breakpoint verification 与
online update-path isolation、online credit update repair、active update-window
diagnosis 已评估。V 后 A7 仍 held，
因为 protected credit-head update lane 是 live 的，并改善短训 credit advantage，
但 legal-open advantage 仍为负，deterministic probing 仍记录 `0` releases。W
将下一 blocker 定位为 PPO segment boundaries 上的 rollout-local first-event
label censoring，X 已在 focused tests 中修复该 label handoff，且 Y 已完成 post-X
learned-policy observation。A7 behavior 仍 held：deterministic probing 仍记录
`0` releases，stochastic releases 尽管 one-shot legality clean 但仍过早，长
stochastic probes 也没有 effects/damage chain。Z 已隔离 value-to-policy execution
breakpoint，AA 已实现 direct signed event-policy margin repair。AA 是 structural
pass，但 behavior 继续 held：短训 probes 显示 event fire probability 上升，但
deterministic probing 仍记录 `0` releases，stochastic releases 仍 early/prewindow。

父级：[README.zh.md](README.zh.md)。

## 可验收范围目标

A7 验收仅限于证明：在既有 A3/A5 legal event surface 下，event-value / advantage-credit
机制能够教会 first-event timing。

## Gate Matrix

| Gate | Required outcome | Current state |
| --- | --- | --- |
| Objective contract | A7 target 提供 counterfactual hold/fire credit，并命名 target source。 | pass：[objective contract](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md) |
| Policy head prototype | Head shape、zero init、optimizer lane、default-off behavior、serialization/load 与 A6 coexistence 有测试覆盖。 | pass：`tests/hmoe/test_hmoe_policy.py` |
| PPO auxiliary credit | Loss、masks、finite stats 与 event-logit coupling 有测试覆盖。 | pass：`tests/hmoe/test_a6_event_head_update_strength.py`、`tests/hmoe/test_hmoe_ppo_warmup.py` |
| Config/diagnostics | Active entries 与 callback/process-probe metrics 暴露 A7 credit behavior。 | pass：[config diagnostics evidence](a7_event_value_advantage_credit_head_config_diagnostics_20260604.md) |
| Legality boundary | A3/A5 masks 与 state machine 继续持有权威。 | required |
| HMoE risk handling | HMoE gap 在 head placement 与 diagnostics 中被考虑。 | partial：A7-C 将 credit 保持在 policy-head level，且不重设计 HMoE |
| Focused validation | training 前 compile、JSON、focused pytest 与 diff gates clean。 | pass：[focused validation sweep](a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md) |
| Learned evidence | Deterministic 在 quality window 内单发；stochastic early hazard 有界。 | held：[short learned evidence](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md) 与 [shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md) 记录 deterministic `0` releases、stochastic 过早 releases，以及 quality-window advantage 为负。 |
| Target construction audit | Early stochastic release 不删失 counterfactual quality-window evidence。 | repair 后 pass：[target construction and credit-sign audit](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.zh.md) 找到 zero-positive censoring fault；[shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md) 恢复 early accepted release 后的 `shadow_quality` positives。 |
| Post-repair coupling | Repaired shadow credit 改变 legal-open quality-state preference。 | held：32k repair probe 中 quality-window A7 advantage mean 仍为 `-0.902`，deterministic 仍为 `0` releases。 |
| Projection audit | Post-J blocker 与缺失 positives、HMoE redesign、coefficient-only tuning 区分开。 | pass：[legal-state projection and coupling audit](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md) 显示多数 repaired positives 是 closed-mask value-only shadow rows。 |
| Projection contract | Shadow evidence 可以在不做 closed-mask delta alignment 的前提下映射为 legal-open positive credit。 | pass；已由 M 实现：[legal-state projection contract](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md) 选择 projected legal-open positive value/delta alignment。 |
| Projection implementation | 下一轮 learned-policy wave 前实现并测试 projected legal-open credit。 | pass；N 后 held：[projected legal-open credit prototype](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md) 实现 `first_event_projection.py`、PPO projection loss、metrics、config knobs 与 focused tests。 |
| Projection learned evidence | Projected credit 改善 deterministic/stochastic first-shot timing，同时保持 one-shot legality。 | held：[short projection learned evidence](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.zh.md) 记录 projection 已启用且 one-shot legality 保持，但 deterministic 仍为 `0` releases，stochastic release steps 为 `2`、`47`、`5`，projection active rows 保持 `0.0`。 |
| Projection eligibility audit | 下一轮 training wave 前解释 projection active rows。 | pass：[projection eligibility root-cause audit](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.zh.md) 找到 candidate starvation：M projection 可在 `shadow_quality` rows 存在时 activate，但 N train diagnostics 没有 accepted releases，因此没有 projection candidates。 |
| Legal-open opportunity contract | 下一轮 implementation/training wave 前定义 non-starved legal-open opportunity credit。 | pass：[legal-open opportunity credit contract](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md) 选择 `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`。 |
| Legal-open opportunity implementation | P 合同被实现，且 focused tests 证明 non-starved legal-open positives。 | pass：[legal-open opportunity credit prototype](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.zh.md) 实现 source/loss/diagnostic path，并通过 focused gates。 |
| Opportunity learned evidence | Q 后 learned behavior 在 acceptance 前被测量。 | held：[short opportunity learned evidence](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.zh.md) 显示 legal-open source counts 是 live 的，但 deterministic 仍为 `0` releases，stochastic 仍过早 release，quality-window advantage 仍为负。 |
| Explicit state completion | M2 release 前测试缺失 window-age/readiness observability 是否为充分根因。 | pass；held：[explicit state completion probe](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.zh.md) 增加 `air_combat_c2_roe_v2`、focused tests 与 32k learned evidence；deterministic 仍为 `0` releases，quality-window advantage 仍为负。 |
| Value/policy coupling breakpoint | 将剩余 negative advantage 与 label starvation、显式状态、credit-head capacity 分离。 | pass；held：[value/policy coupling audit](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.zh.md) 显示固定 S batch 有 `1356` 个 legal-open positives，并可只用 credit head 拟合成正 advantage。 |
| Online update-path isolation | 将 online blocker 与 direct PPO credit-head overwrite、纯 label/state/capacity explanations 分离。 | pass；held：[online update-path isolation](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.zh.md) 显示 PPO-alone credit-head gradient 为 `0.0`，而 PPO+A7 global clipping 将 credit-head effective norm 从约 `0.4855` 压到 `0.00689`，且 A7 value/delta 在 shared actor/features 中冲突。 |
| Online credit update contract | 将 A7 value credit 从 shared PPO global clipping 与 shared actor/features representation drift 中解耦。 | pass；held：[online credit update contract](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.zh.md) 实现独立 detached-latent credit-head value updates、protected clipping、positive-only delta alignment、active config flags 与 nonfinite-probe parity；8k observation 后 behavior 仍 held。 |
| Active update-window diagnosis | 在更多 learned-policy waves 前解释 V 后 active-label disappearance。 | pass；held：[active update-window 诊断](a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.zh.md) 显示完整 episode 有 shadow-quality positives，但 `128` step rollout-local labels 会在 stochastic early release 后删失它们。 |
| Cross-rollout first-event state | Episode-level first-event credit 跨 PPO rollout boundaries 保留。 | pass；已由 Y 评估：[cross-rollout first-event credit state](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.zh.md) 证明 early-release/late-quality-window regression 下，`128` step chunked labels 能恢复完整 episode 的 `shadow_quality` positives。 |
| Post-X learned observation | 恢复后的 cross-rollout credit 改善 learned first-shot behavior，同时保持 one-shot legality。 | held：[post-X learned observation](a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.zh.md) 显示 restored credit 是 live 的，stochastic one-shot discipline clean，但 deterministic 仍为 `0` releases，stochastic release 过早，且没有 observed effects/damage events。 |
| Execution breakpoint analysis | 将 post-X 残余故障与缺失 labels、credit-head capacity、direct actor capacity 分离。 | pass；held：[execution breakpoint analysis](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.zh.md) 显示 direct signed event-logit supervision 能教 actor timing split，而旧 detached credit-advantage delta-align target 不能。 |
| Event-policy margin repair | 在 acceptance 前实现并测量 direct signed event-policy margin 与有边界 actor/event update lane。 | pass；held：[event-policy margin 修复](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.zh.md) 将 quality-window fire probability 从约 `0.0039` 提升到 `0.1126`，但 deterministic 仍为 `0` releases，stochastic timing 仍过早。 |
| Overclaim refusal | M2、HMoE redesign、missile authority、`2v2`、self-play 与 doctrine 继续 held。 | required |

## 失败条件

若出现以下情况，A7 继续 held 或必须 re-scope：

- implementation 只改变 L weights 或 generic reward magnitude；
- advantage head 只是 diagnostic-only，不能影响 event logits 或 policy updates；
- repaired shadow credit 仍未把 legal-open quality states 推成 positive `fire_once`
  advantage；
- projection 继续 candidate-starved，因为 active positive credit 依赖 early accepted
  release 采样；
- legal-open opportunity positives 出现在真实 legal-open quality-window rows 之外；
- non-starved legal-open opportunity positives 是 live 的，但 event-credit
  advantage 仍为负，deterministic event mode 仍停在 `hold`；
- explicit window-age/readiness state 已可见，但 event-credit advantage 仍为负，
  deterministic event mode 仍停在 `hold`；
- fixed-batch offline credit-head fitting 成功，但在线 learned checkpoint 仍让
  legal-open advantage 保持负值且 deterministic mode 为 `hold`；
- online update-path isolation 已定位 blocker，但 implementation 仍对 A7 credit
  使用单一 shared PPO backward/global clip/optimizer contract；
- cross-rollout first-event state 已在 focused tests 中携带，但 post-X
  learned-policy observation 仍让 legal-open advantage 为负、deterministic mode
  停在 `hold`；
- post-X observation 仍让 deterministic mode 停在 `hold`、stochastic
  near-immediate/prewindow release，或已发射导弹没有 observed effects/damage chain；
- event-policy margin repair 移动 event probability 后，deterministic argmax
  仍低于 fire threshold，或 stochastic releases 仍在 prewindow；
- implementation 把 raw closed-mask `shadow_quality` rows 直接对齐到 event logits，
  而不是先投影到 legal-open decision surface；
- deterministic 再次在 authorization/contact 后近立即发射；
- stochastic probing 破坏 one-shot release discipline；
- 在没有 A7 evidence 的情况下，用 HMoE gap 正当化 broad architecture rewrite。

## 验证命令

Initial docs gate：

```bash
git diff --check -- docs/task/air_combat docs/task/issues
```

`A7-EVC-B` 已选择 implementation gates：

- policy head shape、zero initialization 与 constructor serialization tests；
- pre-quality、quality、early accepted 与 shadow-quality cases 的 first-event credit
  label tests；
- PPO auxiliary-loss finite-value 与 mask-handling tests；
- event advantage signs 与 cumulative pre-window hazard 的 diagnostics tests；
- active config parsing 以及 focused compile/JSON gates。

`A7-EVC-C` focused gates：

```bash
python -m compileall -q python/rl/policy_algo/policies.py
pytest tests/hmoe/test_hmoe_policy.py -q
pytest tests/hmoe/test_a6_event_head_update_strength.py -q
git diff --check -- python/rl/policy_algo/policies.py tests/hmoe/test_hmoe_policy.py
```

观察结果：compileall 通过；HMoE policy tests 为 `31 passed`；A6 event-head
update-strength tests 为 `3 passed`；diff whitespace check 通过。

`A7-EVC-D` focused gates：

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
pytest tests/hmoe/test_a6_event_head_update_strength.py -q
pytest tests/hmoe/test_hmoe_ppo_warmup.py -q
pytest tests/hmoe/test_hmoe_policy.py -q
```

观察结果：compileall 通过；event-head/credit gradient tests 为 `5 passed`；
HMoE PPO warmup tests 为 `8 passed`；HMoE policy tests 为 `31 passed`。

`A7-EVC-E` focused gates：

```bash
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
python -m compileall -q python/training/diagnostics.py tools/diagnostics/air_combat_stage0_process_probe.py
pytest tests/training/test_a6_event_value_active_config.py -q
pytest tests/training/test_a6_event_value_diagnostics_callback.py -q
pytest tests/diagnostics/test_a6_event_value_process_probe.py -q
pytest tests/training/test_air_combat_active_training_entries.py -q
pytest tests/training/test_cooperative_diagnostics_callback.py -q
pytest tests/diagnostics/test_air_combat_process_probe.py -q
```

观察结果：JSON 与 compileall 通过；focused config/diagnostics/active tests
分别为 `6 passed`、`5 passed`、`3 passed`、`13 passed`、`13 passed` 与
`9 passed`。

`A7-EVC-F` focused validation sweep：

```bash
python -m json.tool <A7 active config>
python -m compileall -q python/rl/policy_algo/policies.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/training/diagnostics.py tools/diagnostics/air_combat_stage0_process_probe.py
pytest tests/hmoe/test_hmoe_policy.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py -q
pytest tests/training/test_a6_event_value_active_config.py tests/training/test_a6_event_value_diagnostics_callback.py tests/training/test_air_combat_active_training_entries.py -q
pytest tests/diagnostics/test_a6_event_value_process_probe.py tests/diagnostics/test_air_combat_process_probe.py tests/training/test_cooperative_diagnostics_callback.py -q
git diff --check -- <A7 write set>
```

观察结果：JSON 与 compileall 通过；pytest groups 分别为 `44 passed`、`24 passed`
与 `25 passed`；diff check 通过。

`A7-EVC-G` short learned evidence：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_event_credit_launch_window_32k_20260604_r3 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260671
```

观察结果：完成 `32768` steps；TensorBoard 在 step `32768` 记录
`a7/event_credit_loss`，证明 credit path 已激活。Deterministic probe 记录
`0` requests 与 `0` releases，且 prewindow/quality advantage 为负。Stochastic probe
记录 `3/3` authorized one-shot releases，steps 为 `14`、`47`、`2`，且无
unauthorized/violation/repeat/budget issues。这是有效证据，但不是验收。

`A7-EVC-H` closure/index sync outcome：A7 继续 held，下一有边界分发项为
`A7-EVC-I Target Construction And Credit Sign Audit`。

`A7-EVC-I` target-construction audit outcome：A7 继续 held。失败环节是 early
stochastic accepted release 后缺失 shadow-quality target repair。`A7-EVC-J` 已修复该
label-censoring 路径，并通过 focused tests。修复后的 32k learned-policy probe
仍 held：deterministic probing 记录 `0` releases，stochastic probing 在 steps
`4`、`43`、`2` 过早 release，quality-window A7 advantage mean 为 `-0.902`。

`A7-EVC-K` 随后已关闭 projection/coupling audit，`A7-EVC-L` 已选择 legal-state
projection contract，`A7-EVC-M` 已实现 projected legal-open prototype。M focused
validation 通过：

```bash
python -m compileall -q python/rl/policy_algo/first_event_projection.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
pytest tests/hmoe/test_a6_first_event_hazard.py -q
pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_shadow_quality_projection_aligns_projected_legal_open_event_logits -q
pytest tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py -q
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
pytest tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
```

观察结果：compileall 与 JSON 通过；focused test groups 分别为 `17 passed`、
`1 passed`、`15 passed` 与 `19 passed`；docs sync 后 combined focused rerun
通过，`51 passed`。`A7-EVC-N` 随后已完成为 held learned evidence。

`A7-EVC-N` short projection learned evidence：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_projection_credit_32k_20260604_r3 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260691
```

观察结果：完成 `32768` steps。TensorBoard 在 step `32768` 记录 ordinary
event-credit activity：`a7/event_credit_loss=0.322098`、
`a7/event_credit_active_count_mean=450.0` 与
`a7/event_credit_advantage_mean=-0.962887`；projection 已启用，
`a7/evc_proj_enabled=1.0`，但 `a7/evc_proj_active_count_mean=0.0`。
Deterministic probing 记录 `0` requests 与 `0` releases，quality-window
advantage 为 `-0.866`。Stochastic probing 记录 `3/3` authorized one-shot
releases，steps 为 `2`、`47`、`5`，且 zero unauthorized/repeat/budget violations。
这保持了 one-shot legality，但不满足 behavior acceptance。这触发了
`A7-EVC-O Projection Eligibility Root-Cause Audit`。

`A7-EVC-O` projection eligibility root-cause audit：

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py tests/hmoe/test_hmoe_ppo_warmup.py
pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_nonfinite_probe_records_a7_projection_credit_stats tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_shadow_quality_projection_aligns_projected_legal_open_event_logits -q
```

观察结果：compileall 通过；focused projection/nonfinite tests 通过，`2 passed`；
post-sync combined A6/A7/HMoE/active-config pytest 通过，`52 passed`，docs/code
diff check 通过。审计将 candidate starvation 与 unsupported projection rejection
区分开：N train diagnostics 没有 logged accepted releases；stochastic probe
reconstruction 只有在 early sampled release 后才产生 `3280` 个 `shadow_quality`
positives。接下来的有界分发项是
`A7-EVC-P Legal-Open Opportunity Credit Contract`。

`A7-EVC-P` legal-open opportunity credit contract：

```bash
git diff --check -- docs/task/air_combat
```

观察结果：contract 选择 `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` 作为 direct
legal-open quality positives，保留 `SHADOW_QUALITY` 作为 projection repair，并将
`DEADLINE` 保持为 fallback/diagnostic source。接下来的有界分发项是
`A7-EVC-Q Legal-Open Opportunity Credit Prototype`。

`A7-EVC-Q` legal-open opportunity credit prototype：

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py
pytest tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
```

观察结果：compileall 通过；combined A6/A7/HMoE/active-config pytest 通过，
`55 passed`。Q 只证明 implementation surface。接下来的有界分发项是
`A7-EVC-R Short Opportunity Learned Evidence`。

`A7-EVC-R` short opportunity learned evidence：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_legal_open_opportunity_32k_20260604_r1 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260701
```

观察结果：完成 `32768` steps。TensorBoard 在 step `32768` 记录 direct legal-open
source activity：`a7/event_credit_active_count_mean=512.0`、
`a7/event_credit_target_positive_frac=0.648438`、
`a7/event_credit_advantage_mean=-0.850262`、
`a7/evc_src_legal_open_quality_count_mean=332.0` 与
`a7/evc_src_legal_open_quality_positive_count_mean=332.0`。Deterministic probing
记录 `0` requests 与 `0` releases，open-window fire probability mean/max 为
`0.281221` / `0.293340`，quality-window advantage 为 `-0.792674`。Stochastic
probing 记录 `3/3` authorized one-shot releases，steps 为 `3`、`44`、`10`，且
zero unauthorized/repeat/budget violations。R 证明 source starvation 已修复，但
A7 继续 held，因为 timing 与 advantage sign acceptance 仍未满足。

`A7-EVC-S` explicit state completion probe：

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

观察结果：focused tests 通过，`105 passed`；`git diff --check` 通过。32k
state-completed train 在
`experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1` 下完成，最终记录
`a7/evc_src_legal_open_quality_count_mean=330`、
`a7/evc_src_legal_open_quality_positive_count_mean=330`、
`a7/event_credit_target_positive_frac=0.645` 与
`a7/event_credit_advantage_mean=-0.924`。Deterministic probing 在 `4` episodes
中记录 `0` requests 与 `0` releases，quality-window A7 advantage mean 为
`-0.8534`。Stochastic probing 记录 `8/8` authorized one-shot releases，steps 为
`[6, 42, 4, 2, 5, 46, 3, 46]`，且 zero unauthorized/repeat/budget violations。
S 改善 observability 并保持 one-shot legality，但不满足 behavior acceptance。

`A7-EVC-T` value/policy coupling audit：

```bash
python tools/diagnostics/a7_credit_head_offline_fit_probe.py \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 1200 \
  --fit_batch_size 512 \
  --eval_batch_size 512 \
  --scopes credit_head,credit_head_actor_mlp \
  --json_out experiments_tmp/a7_credit_head_offline_fit_probe_20260604.json
```

结果：固定 S batch 有 `2516` 个 active labels，其中 `1356` 个
`LEGAL_OPEN_QUALITY` positives；初始 legal-open advantage 为 `-0.8536`；
credit-head-only offline fitting 将 legal-open advantage 翻到 `+0.6417`，正号比例
`1.0`。保守的 value-coef-adjusted budget control 仍将 legal-open advantage 翻到
`+0.0083`，正号比例 `1.0`。这是 breakpoint evidence，不是 behavior acceptance。

`A7-EVC-U` online update-path isolation：

```bash
python -m compileall -q tools/diagnostics/a7_online_update_path_probe.py

python tools/diagnostics/a7_online_update_path_probe.py \
  --episodes 4 \
  --max_steps 640 \
  --online_episodes 4 \
  --online_max_steps 640 \
  --batch_size 512 \
  --eval_batch_size 512 \
  --update_steps 8 \
  --device auto \
  --json_out experiments_tmp/a7_online_update_path_probe_20260604.json
```

结果：compileall passed。Fixed-batch A7 value 与 delta-align gradients 在
actor/features 中冲突（actor MLP `cosine=-0.8954`，features `-0.9097`）。
Online PPO-alone credit-head gradient 为 `0.0`；PPO+A7 global clipping 将
credit-head effective norm 从约 `0.4855` 压到 `0.00689`。S TensorBoard review
显示 `train/value_loss` max `6526.7822`，而 `a7/event_credit_loss` max
`1.0749`。这是 blocker-localization evidence，不是 behavior acceptance。

`A7-EVC-V` online credit update contract：

```bash
python -m compileall -q python/rl/policy_algo/ppo_adaptive_kl.py python/rl/policy_algo/policies.py python/rl/support/nonfinite_probe.py tests/hmoe/test_hmoe_ppo_warmup.py
pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_nonfinite_probe_preserves_a7_event_credit_training_path tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_separate_credit_update_only_writes_credit_head -q
pytest tests/hmoe/test_hmoe_policy.py::HMoEPolicyTests::test_hybrid_event_credit_head_gets_dedicated_optimizer_lane_and_zero_outputs tests/hmoe/test_hmoe_policy.py::HMoEPolicyTests::test_hybrid_event_credit_head_exposes_hold_fire_values_without_changing_event_logits tests/hmoe/test_a6_event_head_update_strength.py -q
pytest tests/training/test_a6_event_value_active_config.py::A6EventValueActiveConfigTests::test_a7_event_credit_config_exposes_credit_head_without_reusing_a6_hazard_loss tests/training/test_air_combat_active_training_entries.py::AirCombatActiveTrainingEntryTests::test_stage1_c2_roe_a7_event_credit_probe_is_separate_from_a6_launch_window_baseline -q
```

结果：compileall 通过；focused separate-update 与 nonfinite-probe tests 为
`2 passed`；policy/update-strength tests 为 `7 passed`；active-config tests 为
`2 passed`；最终 combined focused rerun 为 `111 passed`；diff whitespace check
通过。

Protected-update 8k observation 完成 `8192` steps，并证明 separate lane 是 live
的（`a7/evc_separate_update_enabled=1.0`，早期 separate-update grad norm 非零）。
它将 A7 credit advantage 改善到约 `-0.0583`，但 final fixed-batch probing 仍为
`legal_open_quality_positive_advantage_mean=-0.05257667228579521`，positive sign
fraction 为 `0.0`；process probing 记录 `release_count=0` /
`fire_once_requested_count=0`。V 因此是 structural repair，不是 behavior
acceptance。
