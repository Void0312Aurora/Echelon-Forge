# Issue 板块

状态：活跃的跨领域问题板块。

本目录用于追踪不只属于单一领域目录的具体问题，或需要在领域、runtime、
模型、训练与评估工作线之间保持可见的问题。

以下情况适合放入这里：

- 问题可能在首次出现的领域之外复现；
- 问题会阻塞验收或正式训练结论；
- 问题暴露了运行行为、训练证据和评估基础设施之间的缺口；
- 修复路径可能跨多个任务领域。

`naval/`、`air_combat/`、`ground/` 等领域目录仍然承载领域路线图和
场景特定任务簇。本板块用于沉淀可被其他工作线复用的问题证据和修复路径。

## 活跃问题

- [A6 发射窗口标签密度失衡](./a6_launch_window_label_imbalance/README.zh.md)：
  L contract 下 deterministic `fire_once` argmax 不 crossing，尽管 open-window
  event probability 达到 `34.6%`。它仍是 live symptom 与 balancing requirement，但
  A6 root-cause re-scope 已将更深 blocker 归属为 first-event censoring 与缺失
  counterfactual hold/fire credit；下一修复路径由 A7 承载。
- [HMoE 层级化计算断裂](./hmoe_hierarchical_computation_gap/README.zh.md)：
  subexpert head 接收与 family head 相同的原始 latent，而非 family-head 输出；
  空战 C2/ROE 布局下五家族塌缩为单家族。A7 必须在 head placement 与 diagnostics
  中考虑该风险，但该 issue 仍不授权活跃 HMoE redesign。

## 保留跟踪项

- [RL 策略保持基线漂移](./rl_policy_hold_baseline_drift/README.zh.md)：
  N4 确定性保持探针已闭合，但 stochastic-policy acceptance 与 off-station
  curricula 仍需要这份记录作为可复用证据。

## 问题记录形态

每个 issue 子项目通常应包含：

- 当前状态与负责线程；
- 首次观察到的上下文；
- 带命令或测量事实的证据摘要；
- 影响与不能宣称的内容；
- 可能原因或假设；
- 下一步行动门；
- 指向依赖该问题的领域任务簇链接。
