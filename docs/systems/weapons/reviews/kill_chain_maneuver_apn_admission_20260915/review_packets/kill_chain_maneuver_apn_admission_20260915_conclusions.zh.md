# P10 机动目标 / APN 证据状态

- 证据准入状态：`held`；APN default promotion：`held`。
- 阻断原因：记录的生成提交不是当前分支祖先，生成时工作树不干净，AIM-120 输入 digest 已过期，原始运行包没有可检索的发布 URI。
- 历史运行记录的计算门状态为 `maneuver_apn_config_backed_admission_passed`，但这只是未通过来源复核的历史数值，不得用于 promotion。
- 历史 clean stage-4 structural admission：`True`；CVA 最大稳定加速度 RMSE 为 `0.000 m/s²`，末值最大误差 `0.000 m/s²`。
- 历史 noisy acceleration authority：`passed`；最大加速度 RMSE `4.053 m/s²`，最大估计加速度 `14.698 m/s²`。
- 历史 stage-5 APN selection：`True`；选定 gain 为 `0.125`，config-backed 复验记录为 `True`。

只有在干净最终修订上重新生成、发布可检索的原始包，并在 manifest 中记录输入/产物 digest 与保留责任人后，才能重新评估 promotion。该结果不构成真实 AIM-120 性能、Pk、默认武器参数或交战规则权威。
