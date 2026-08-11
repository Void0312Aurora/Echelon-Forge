# 损伤模型校准残差

语言：
- 英文规范版：[damage_model_calibration_residuals.md](damage_model_calibration_residuals.md)
- 中文伴随版：`damage_model_calibration_residuals.zh.md`

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/effects/work/issues/damage_model_calibration_residuals.md`
Owner: `systems/effects/damage-calibration`
Last verified: `2026-08-08`
Content status: 从已完成的 T6 残差账本抽取的所有者本地页面；这些条目是被保留的校准/产品预期，不是已接受行为。

## 范围

本文负责当前二进制行为与命名的损伤模型或空战校准预期间的残差。不负责
测试工具缺陷、来源权利准入或 C++ include-direction 决策。

## 当前残差

- 保留的 weapon-guidance realism 测试包含 6 类、33 个已裁定方法：主响应选择、
  近炸投影扩散、跨子系统溢出、损失状态升级/饱和、气动/引信响应和机理校准。
  其中 25 个由严格 `xfail` 管理，8 个使用 `expectedFailure`，因为混合子测试不能安全使用严格 xfail。
- I97 聚焦修复记录 7 个二进制残差：直接命中部件身份、起爆结果、破片能量、
  爆压、空间采样数、非空部件来源行以及 synthetic fragility 向量。当前标记是告警，
  不是新的基线。

## 证据边界

来源账本和日期化验证记录保留在
[已完成的 T6 账本](../../../../plan/archive/unified_architecture_program_completed_20260727/t6_residual_ledger.zh.md)。
账本记录 I65/I97 校准组的双二进制继承证据和精确测试节点；本文是当前路由，
不替代这些历史测量。

## 晋级门槛

只有在 effects 所有者提供新的校准权威、在当前匹配构建上重现预期行为、更新受影响
测试契约并完成独立评审后，才能移除或改变残差。严格 xfail 意外通过只能触发复核，
不能自动晋级。

## 非目标

- 不得为使测试变绿而弱化或删除残差标记。
- 不得把被保留的数值解释为维护中的 effects 标准。
- 不修改归档证据或无关的运行时/文档所有者。
