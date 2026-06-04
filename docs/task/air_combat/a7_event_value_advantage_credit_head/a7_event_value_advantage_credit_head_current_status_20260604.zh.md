# A7 当前状态

状态：`2026-06-04` active implementation。A7 已选定 objective contract，并完成
`A7-EVC-C Policy Head Prototype`、`A7-EVC-D PPO Auxiliary Credit` 与
`A7-EVC-E Config And Diagnostics`；`A7-EVC-F Focused Validation Sweep` 也已通过。
`A7-EVC-G Short Learned Evidence` 已完成为有效证据，但 learned-policy outcome
继续 held。`A7-EVC-I Target Construction And Credit Sign Audit` 已将主要结构性故障定位为
缺失 shadow-quality target repair。`A7-EVC-J Shadow Quality Target Repair` 已修复
确认过的 label-censoring bug，并通过 focused tests 与 32k repair probe；但 learned
first-shot timing 仍 held。`A7-EVC-K Legal-State Projection And Coupling Audit`
已关闭 post-repair 诊断，`A7-EVC-L Legal-State Projection Contract` 已选择下一机制；
`A7-EVC-M Projected Legal-Open Credit Prototype` 已完成该机制的 focused
implementation 与验证。Projection 后 learned-policy behavior 尚未评估。

父级：[README.zh.md](README.zh.md)。

## 本检查点

- A3 已作为 accepted C2/ROE evidence packet 归档，并通过 pointer README 保持可达。
- A6 在 root-cause analysis 后继续 held；L tuning 暂停。
- A7 开启，用于实现 counterfactual event-value / advantage credit。
- Objective contract 已选定：
  [a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md)。
- `A7-EVC-C Policy Head Prototype` 已完成：zero-safe `hybrid_event_credit_head`
  API 已暴露，并由 focused HMoE policy tests 覆盖。
- `A7-EVC-D PPO Auxiliary Credit` 已完成：A7-only coeffs 可采集 first-event
  labels，credit head 接收 value loss，delta alignment 可更新 event logits，且不改变
  runtime masks。
- `A7-EVC-E Config And Diagnostics` 已完成：A7 active config 打开 credit
  head/loss 路径，callback/process-probe diagnostics 暴露 credit values、
  advantage signs 与 cumulative early-fire hazard。
- `A7-EVC-F Focused Validation Sweep` 已完成：JSON、compileall、focused
  HMoE/A7、active-entry、diagnostics、process-probe 与 diff gates 通过。
- `A7-EVC-G Short Learned Evidence` 已完成为 held evidence：有效 r3 training run
  记录到 live `a7/event_credit_loss`，但 deterministic probing 仍为 `0` releases，
  stochastic probing 仍在 steps `14`、`47`、`2` 过早发射。
- `A7-EVC-I Target Construction And Credit Sign Audit` 已完成：stochastic r3
  label reconstruction 只有 `19` 个 active labels 与 `0` 个 positives，而每个
  early-release episode 随后都有超过 `1000` 个 shadow quality states。
- `A7-EVC-J Shadow Quality Target Repair` 已作为 implementation repair 完成：
  stochastic early accepted episodes 不再塌缩成 zero-positive A7 target samples；
  但修复后的 short learned evidence 仍未达到 timing acceptance。
- `A7-EVC-K Legal-State Projection And Coupling Audit` 已完成：repaired positives
  存在，但大多位于 closed-mask `FiredAssess` observations，并且被有意排除出
  delta alignment。
- `A7-EVC-L Legal-State Projection Contract` 已作为 design contract 完成：raw
  shadow rows 变成 projection/opportunity evidence，positive value/delta alignment
  只允许在 projected legal-open observations 上发生。
- `A7-EVC-M Projected Legal-Open Credit Prototype` 已作为 implementation slice
  完成：projected legal-open observations 现在可为 shadow-quality evidence 训练
  positive value/delta alignment，raw closed-mask rows 继续排除出 ordinary
  delta alignment。
- HMoE hierarchical computation gap 被记录为 architecture risk：A7 不应只依赖 hard-routed
  subexpert behavior；但当前 A7 failure 已经在被删失的 target construction 与 event-credit
  advantage sign 上可见。

## 成熟度矩阵

| Surface | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| A7 docs | active | README/task clusters/current status/dispatch/acceptance/objective contract 已存在。 | 仅 documentation 与 dispatch surface。 |
| Objective contract | pass | 已选合同定义 counterfactual target semantics、window balancing、head placement、loss coupling、diagnostics 与 rollback gates。 | 只授权 focused implementation，不释放 broad architecture。 |
| Policy head prototype | pass | `python/rl/policy_algo/policies.py` 暴露 `hybrid_event_credit_head_lr_scale`、`get_hybrid_event_credit()` 与 distribution-side credit values；`tests/hmoe/test_hmoe_policy.py` 覆盖 default-off、zero init、optimizer lane、A6 coexistence、load smoke 与 bootstrap zeroing。 | 不声明 PPO auxiliary loss 或 training 已完成。 |
| PPO auxiliary credit | pass | `first_event_hazard.py` 增加带 finite masking 与 window mass caps 的 `compute_first_event_credit_loss()`；`ppo_adaptive_kl.py` 增加 A7 coeffs、A7-only label collection、credit loss coupling、delta alignment 与 finite logs；focused HMoE tests 已通过。 | 不声明 learned-policy。 |
| Config and diagnostics | pass | [config diagnostics evidence](a7_event_value_advantage_credit_head_config_diagnostics_20260604.md) 增加 A7 active entry、callback A7 credit/hazard metrics 与 process-probe A7 summaries。 | 不声明 learned-policy。 |
| Focused validation | pass | [focused validation sweep](a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md) 记录 JSON、compileall、focused pytest 与 diff checks。 | 不声明 learned-policy。 |
| Short learned evidence | pass；held outcome | [short learned evidence](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md) 记录 nonfinite-probe 修复后的有效 r3 training/probe evidence。 | A7 不能 accepted：deterministic 仍为 `0` releases，stochastic 过早发射，quality-window advantage 仍为负。 |
| Target construction audit | pass；已由 J 修复 | [target construction and credit-sign audit](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.zh.md) 证明 early stochastic accepted release 会从 A7 labels 中删失后续 quality-window positives。 | J 已修复该 target-construction bug；剩余 blocker 是修复后的 projection/coupling，不是再调 coefficient。 |
| Shadow-quality target repair | pass；held outcome | [shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md) 增加 `A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY`、early accepted release 后的 positive shadow labels、A7 config knob、diagnostics 覆盖，并让 shadow rows 跳过 delta alignment。 | Label censoring 已修复，但 behavior 仍 held：deterministic `0` releases、stochastic 过早 release、quality-window advantage 为负。 |
| Legal-state projection audit | pass；held outcome | [legal-state projection and coupling audit](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md) 显示 shadow positives 已恢复，但仍是 closed-mask rows 上的 value-only 信号，legal-open quality states 继续为负。 | 这是结构性诊断，不是验收。 |
| Legal-state projection contract | pass；已由 M 实现 | [legal-state projection contract](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md) 选择 projected legal-open positive credit，并禁止 raw closed-mask delta alignment。 | 合同已作为 focused prototype 实现；仍不证明 learned-policy behavior。 |
| Projected legal-open credit prototype | pass；learned behavior not evaluated | [projected legal-open credit prototype](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md) 增加 `first_event_projection.py`、projection coeffs、PPO projected-distribution loss、projection metrics、active config knobs 与 focused tests。 | M 只证明机制和 gradient path；A7 behavior acceptance 仍需要 short projection learned-policy probe。 |
| HMoE relation | watch item | issue board 记录 flat subexpert input 与 combat-family collapse。 | 除非正确 credit signs 已学到但 policy coupling 仍以可归因于 hierarchy gap 的方式失败，否则 A7 不修 HMoE。 |

## 立即下一步

运行 `A7-EVC-N Short Projection Learned Evidence`：M 已提供 projected legal-open
training path，focused tests 也证明 projected positive event-logit pressure 存在。
下一有界问题是它能否在不削弱 A3/A5 masks 的前提下改变 deterministic release timing
与 stochastic early-fire behavior。

## 验证快照

- `python -m compileall -q python/rl/policy_algo/policies.py`：pass。
- `pytest tests/hmoe/test_hmoe_policy.py -q`：pass，`31 passed`。
- `pytest tests/hmoe/test_a6_event_head_update_strength.py -q`：pass，`5 passed`。
- `pytest tests/hmoe/test_hmoe_ppo_warmup.py -q`：pass，`8 passed`。
- `git diff --check -- python/rl/policy_algo/policies.py tests/hmoe/test_hmoe_policy.py`：pass。
- `python -m json.tool <A7 active config>`：pass。
- `python -m compileall -q python/training/diagnostics.py tools/diagnostics/air_combat_stage0_process_probe.py`：pass。
- `pytest tests/training/test_a6_event_value_active_config.py -q`：pass，`6 passed`。
- `pytest tests/training/test_a6_event_value_diagnostics_callback.py -q`：pass，`5 passed`。
- `pytest tests/diagnostics/test_a6_event_value_process_probe.py -q`：pass，`3 passed`。
- `pytest tests/training/test_air_combat_active_training_entries.py -q`：pass，`13 passed`。
- `pytest tests/training/test_cooperative_diagnostics_callback.py -q`：pass，`13 passed`。
- `pytest tests/diagnostics/test_air_combat_process_probe.py -q`：pass，`9 passed`。
- `pytest tests/hmoe/test_hmoe_policy.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py -q`：pass，`44 passed`。
- `pytest tests/training/test_a6_event_value_active_config.py tests/training/test_a6_event_value_diagnostics_callback.py tests/training/test_air_combat_active_training_entries.py -q`：pass，`24 passed`。
- `pytest tests/diagnostics/test_a6_event_value_process_probe.py tests/diagnostics/test_air_combat_process_probe.py tests/training/test_cooperative_diagnostics_callback.py -q`：pass，`25 passed`。
- `git diff --check -- <A7 write set>`：pass。
- `python -m compileall -q python/rl/support/nonfinite_probe.py python/training/diagnostics.py tests/hmoe/test_hmoe_ppo_warmup.py`：pass。
- `pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_nonfinite_probe_preserves_a7_event_credit_training_path tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_event_credit_only_collects_labels_and_updates_credit_head tests/training/test_a6_event_value_diagnostics_callback.py -q`：pass，`7 passed`。
- A7 r3 TensorBoard scalar check：`a7/event_credit_loss` 在 step `32768` 存在；
  active count `450.0`；advantage mean `-0.978105`。
- A7 r3 deterministic probe：`0` requests、`0` releases、`1880` open-window steps，
  open-window fire probability mean/max 为 `23.1%` / `23.3%`，且 prewindow/quality
  advantage 均为负。
- A7 r3 stochastic probe：`3/3` authorized one-shot releases，steps 为 `14`、
  `47`、`2`，且 `0` unauthorized/violation/repeat/budget issues。
- A7-EVC-I label reconstruction：
  - deterministic r3：`1880` 个 active labels、`1076` 个 positives、`804` 个
    negatives；
  - stochastic r3：`19` 个 active labels、`0` 个 positives、`19` 个 negatives；
  - stochastic early-release episodes 随后仍暴露 `1080`、`1061`、`1081` 个
    post-accepted shadow quality states。
- A7-EVC-J focused repair gates：touched policy/diagnostic files 的 compileall
  通过；`pytest tests/hmoe/test_a6_first_event_hazard.py -q` 通过，`15 passed`；
  focused HMoE/PPO tests 通过，`14 passed`；focused config/diagnostics/active-entry
  tests 通过，`27 passed`。
- A7-EVC-J 修复后的 label reconstruction：
  - old r3 deterministic：`1880` 个 active labels、`1076` 个 positives、`804`
    个 negatives；
  - old r3 stochastic：`3241` 个 active labels、`3222` 个 positives、`19` 个
    negatives，且 `shadow_quality=3222`；
  - repaired r1 stochastic probe：`3215` 个 active labels、`3209` 个 positives、
    `6` 个 negatives，且 `shadow_quality=3209`。
- A7-EVC-J 32k repair run 在
  `experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1` 下完成 `32768`
  steps；deterministic probe 仍为 `0` releases，open-window fire probability
  mean/max 为 `25.5%` / `27.2%`，quality-window A7 advantage mean 为 `-0.902`；
  stochastic probe 记录 `3/3` authorized one-shot releases，steps 为 `4`、`43`、
  `2`，且 `0` unauthorized/repeat/budget violations。
- A7-EVC-M focused repair gates：`first_event_projection.py`、
  `first_event_hazard.py` 与 `ppo_adaptive_kl.py` 的 compileall 通过；
  `pytest tests/hmoe/test_a6_first_event_hazard.py -q` 通过，`17 passed`；
  focused projected-loss PPO test 通过，`1 passed`；focused HMoE/PPO group
  通过，`15 passed`；JSON parsing 与 active config/entry tests 通过，
  `19 passed`；docs sync 后 combined focused rerun 通过，`51 passed`。

## Held Items

- M2 release。
- HMoE redesign 或 soft routing。
- Missile/Pk/fuze/damage authority。
- `2v2`、self-play 与 real doctrine。
