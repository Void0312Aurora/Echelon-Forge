# P4-B 状态转移与 Episode Candidate

状态：`2026-08-30` 实现快照；**repair-required，尚未验收**。本文记录隔离的
`codex/long-horizon-governance-architecture` 分支上的 dark/shadow contract 工作。
它不授权 production truth 发布、caller 迁移或现有 runtime 路径退役。

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/p4b_state_transfer_candidate_20260830.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-30`

## Purpose

P4-B 让 P4-A host lifecycle 使用显式 native episode barrier 与 owner-directed
state-transfer 协议。长期目标是具备 source-bound provenance、typed schema bytes、
事务化 target import、replay evidence、N/N-1 解码和 fail-closed recovery 的可执行
状态转移。fixture 或 mirror 测试变绿不能单独构成验收。

## 已实现的 candidate surface

- `RuntimeEpisodeCoordinatorCandidate` 负责 episode phase、step、reset generation、
  barrier sequence、幂等 receipt 与 native mutation 串行化。
- `RuntimeHostCandidate` 签发 host-bound episode capability，并从 slot-owned
  `RuntimeNativeEpisodeControl` 获取控制器；submit 不再接受任意 caller control。
- replacement quiescence 分离绑定 active slot 的 source owner registry 与 candidate
  slot 的 target owner registry。source registry 输出 census 与 typed
  `RuntimeStateOwnerArtifact` payload；target registry 接收该 export，返回 observations
  与可回滚 import transaction。
- validator 在 owner callback 前固定 host transfer，校验完整类别集合、schema 窗口、
  artifact digest、source census equality、target observation equality、native barrier
  identity 与 host revalidation。
- import transaction 在每条验证失败路径都有 abort guard，并在 transfer/host mutex 外
  commit。host/native/state-transfer in-flight counter 阻止 reclaim、shutdown、timeout、
  fault 或 abort 竞争。
- 当前 contract 只接受 N=2 与 N-1=1，candidate entry hash 归一到 N；在 per-world
  transfer protocol 被 admission 前，multi-world replacement 明确拒绝。
- Python `NativeEpisodeMirror` 只做 receipt mirror，reset 与 episode truth 仍由 native
  持有。

## 验证证据

隔离的 Windows/MSVC target 当前通过：

```text
ef_runtime_host_candidate_test：37 test cases，925 assertions
focused Python architecture/mirror tests：23 passed
```

CMake target 保持 static 且只链接 `ef_runtime_contracts`。CI smoke workflow 已显式构建、
运行 native host boundary，以及 state-transfer 和 Python mirror contract gates。

## 尚未验收的架构阻塞

当前实现仍是 contract candidate，不是 production state-transfer implementation：

1. 没有 maintained production owner adapter 把 ECS、RNG、clock、queue、pending command、
   episode、device、in-flight、side-effect 或 mirror state 解码成 typed artifact payload。
   现有 test registry 仍合成确定性 bytes 与 observations。
2. `RuntimeInstanceControl` 及其 registry 仍在 candidate construction 时由 caller 提供。
   host 已分离 source/target，但 production admission 仍需要 opaque host-issued owner
   handle 或等价的 authenticated binding，不能由 caller DTO 替代。
3. import commit/abort 仍是同步 callback。production 实现需要 durable one-shot transaction
   state、有界 cancellation/deadline、显式 commit/abort outcome，以及进程中断后的 recovery。
4. artifact envelope 已承载 typed bytes 与 digest，但仍缺少每类别 decoder/migration matrix、
   unknown-field policy 与 exact N/N-1 所需的 durable replay log。
5. Multi-world transfer、durable journal admission、RunReceipt binding、storage/authenticity
   与 production canary/backout 仍属于 P5 gate。

这些是架构阻塞，不是把计划缩短为 fixture 或 cleanup wave 的理由。

## 长期完成路线

只有在每个类别 owner 提供 maintained source exporter 与 target importer，并具备 opaque host
binding、exact payload decoder、replay/rollback、interruption recovery 和 versioned
compatibility matrix 后，P4-B 才能转为 accepted。随后 P4-C 可集成 candidate kernel seam，
但仍保持 dark/shadow。P5-B/P5-D 还必须完成 durable RunReceipt、ArtifactLedger、authenticity、
canary/backout、supported topology 与唯一 production cutover，之后才能改变 maintained
caller 的 authority。

本迭代之后必须执行独立 review。reviewer 可以替换机制，但不能通过删除 typed transfer、
provenance、durability、compatibility 或 recovery 义务来关闭 P4-B。
