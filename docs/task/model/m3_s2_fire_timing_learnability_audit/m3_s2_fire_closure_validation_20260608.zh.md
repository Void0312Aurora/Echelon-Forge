# M3-S2 发射闭合验证 2026-06-08

状态：`fire behavior reproduced / focused stochastic gate cleaned after A5
weapon-arm action-frame fix; batch closure pending`。

## 问题

如果把 gate 限定为 executable legal `fire_once` release behavior，并把
damage/effects 与 kill-chain 结果排除在外，当前 active M3-S2 模型能否证明发射闭合？
如果不能，阻塞 gate 的具体原因是什么？

当前模型：

- `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip`

本次检查使用的 gate：

- `fire_once_requested_count >= 1`
- `fire_once_accepted_count >= 1`
- `release_count >= 1`
- `authorized_release_count >= 1`
- `violation_release_count = 0`
- `repeat_release_before_assessment_count = 0`
- clean closure 还要求 stochastic probes 中 `fire_once_rejected_count = 0`，
  或对任何 rejection 给出有界且成文的例外理由。

## 证据

已有 2400-step deterministic probe：

- artifact：
  `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/m3s2_deterministic_probe.json`
- seed：`20260525`
- first release：step `423`
- requested / accepted / rejected：`1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment：`1 / 1 / 0 / 0`
- 判定：clean firing gate passes。

新增 2400-step deterministic 复现：

- artifact：
  `experiments_tmp/m3s2_fire_closure_validation_20260608_r1/deterministic_seed20260608_ep1.json`
- seed：`20260608`
- first release：step `423`
- requested / accepted / rejected：`1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment：`1 / 1 / 0 / 0`
- 判定：clean firing gate passes。

新增 800-step deterministic 短窗复现：

- artifact：
  `experiments_tmp/m3s2_fire_closure_validation_20260608_r1/deterministic_seed20260609_ep1_800.json`
- seed：`20260609`
- first release：step `423`
- requested / accepted / rejected：`1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment：`1 / 1 / 0 / 0`
- 判定：在已知 release window 内 clean firing gate passes。

已有 2400-step stochastic probe，A5 master-arm alignment fix 之前：

- artifact：
  `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/m3s2_stochastic_probe.json`
- seed：`20260525`
- first release：step `290`
- requested / accepted / rejected：`2 / 1 / 1`
- rejection reason：`{"weapon_not_ready": 1}`
- release / authorized / violation / repeat-before-assessment：`1 / 1 / 0 / 0`
- fix 前判定：progress gate passes，但 clean firing closure fails。

新增 800-step stochastic 复现，A5 master-arm alignment fix 之前：

- artifact：
  `experiments_tmp/m3s2_fire_closure_validation_20260608_r1/stochastic_seed20260608_ep1_800.json`
- seed：`20260608`
- first release：step `290`
- requested / accepted / rejected：`2 / 1 / 1`
- rejection reason：`{"weapon_not_ready": 1}`
- release / authorized / violation / repeat-before-assessment：`1 / 1 / 0 / 0`
- fix 前判定：progress gate passes，但 clean firing closure fails。

Root cause：

- 被拒绝的 stochastic step 中，policy sampling 产生了 `fire_once` pulse，但同一个
  12 维动作帧里武器保险开关（代码字段 `master_arm`）是关的，即 `master_arm = 0`。
- A5 正确地把这一组合解释为 `weapon_not_ready`。
- 这是动作转换层的不一致：对模型来说 `fire_once` 已经是“发射一次”的事件，
  但旧的武器保险开关仍能在同一帧把这次发射关掉。

Patch：

- `gym_envs/universal_env_parts/air_combat_event_action.py` 现在在 A5/C2-ROE
  有效动作帧中，只要出现 `fire_once` pulse，就先派生武器保险开关打开
  （`master_arm = 1`），再评估 support。
- `tests/runtime/air_combat/test_air_combat_a5_event_action_runtime.py` 增加回归：
  在 authorized support 下，`fire=True, master_arm=False` 会作为复合
  `fire_once` event 被接受。

After-fix stochastic checks：

- artifact：
  `experiments_tmp/m3s2_fire_closure_validation_20260608_r1/stochastic_seed20260608_ep1_800_after_master_arm_fix.json`
- seed：`20260608`
- first release：step `283`
- requested / accepted / rejected：`1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment：`1 / 1 / 0 / 0`
- 判定：clean focused stochastic firing gate passes。

- artifact：
  `experiments_tmp/m3s2_fire_closure_validation_20260608_r1/stochastic_seed20260525_ep1_800_after_master_arm_fix.json`
- seed：`20260525`
- first release：step `283`
- requested / accepted / rejected：`1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment：`1 / 1 / 0 / 0`
- 判定：clean focused stochastic firing gate passes。

## 判定

当前模型加上 A5 武器保险动作帧修复后，可以证明一个更窄的事实：deterministic
learned-policy execution 与已检查 stochastic trajectories 都能发出一次合法、被接受、
授权的 `fire_once` release，并且没有 rejection、violation 或
repeat-before-assessment。

这清除了此前局部化的 `weapon_not_ready` 动作转换问题。但它仍不是正式 batch
closure result，因为本记录只围绕已知 release window 跑了单 episode 的 focused
deterministic/stochastic checks。下一道 gate 是有边界的多 episode / 多 seed validation。

Damage/effects observations 不属于本判定。它们仍归 A8/task evidence，而不是
firing-closure gate。

## 下一步验证

升级为 closure 前，应运行有边界的 batch validation，并要求所有被检查 episode 满足：

- exactly one accepted authorized release；
- zero violation releases；
- zero repeat-before-assessment releases；
- zero rejected `fire_once` requests，或存在显式接受的有界 reject 例外；
- 报告 first-release timing 与 event-mode support。

如果 batch validation 中 stochastic rejects 再次出现，下一步模型/runtime 工作应优先处理
request cleanliness 与 readiness alignment，而不是 kill-chain effects。
