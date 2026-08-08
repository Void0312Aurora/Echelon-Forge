# CUDA-resident Runtime Program 2 收口记录

- Closure ID：`cr2_7.closed_without_promotion.cuda_resident.20260805`
- 日期：`2026-08-05`
- 机器可读记录：[cuda_resident_cr2_closure_20260805.json](cuda_resident_cr2_closure_20260805.json)
- 英文规范版：[cuda_resident_cr2_closure_20260805.md](cuda_resident_cr2_closure_20260805.md)
- 计划：[cuda_resident_runtime_program_2_20260731.zh.md](cuda_resident_runtime_program_2_20260731.zh.md)
- 收口前 HEAD：`356bcd56a61e40f1327d16b6a2dda335d7fdd553`

## 决策

CR2-7 将 Runtime Program 2 无晋级关闭。CUDA-resident 实现作为未维护的研究型
第二后端保留；RuntimeFacade 不选择它，维护中的 CPU 默认不变，也不因此获得公开
support、ABI、tuning、merge 或 push 授权。

这不是“第二后端失败”的判断。CR2 已完成结构拆分、common-SPI full-window 路径、
device-consumer boundary、selected-slice parity、静态资源与 launch topology 采集，以及
production-shaped 小批量矩阵。关闭是以下两个相互独立条件的机械结果：

1. 真实 Nsight Compute 尝试返回 `ERR_NVGPUCTRPERM`，achieved occupancy、divergence
   与 global/local/shared traffic 仍不可用；
2. 没有记录显式 promotion 授权或 integration plan。

不能用 theoretical occupancy、零值 counter 或 timing matrix 推断来替代任一条件。

## 保留证据

closure 绑定精确的 CR2-6b matrix summary 与 fresh parity output，并以规范化
`utf8_lf` descriptor 绑定较早的 CR2-5a/5b 证据。矩阵包含两轮 order-balanced
campaign，并保留 host-specific 限制。其 advisory 为：

- world 1 的共同 mode：`flecs_cpu_reference`；
- world 4 无 host export：`cuda_resident`；
- world 4 有 host export：保守默认 CPU；由于 rollout p95 在两轮间反转，CUDA 仅作
  median-throughput opt-in；
- world 16/64/256 的共同 mode：`cuda_resident`；
- device-consumer mode：要求 CUDA，不作 CPU 比较性能声明；
- 未测 world count：不分类、不外推。

该 advisory 是保留的研究证据，不是 runtime selector 或 maintained performance
contract。

## 仓库与维护边界

在最终 pre-commit topology 快照中：

- 原 maintained baseline 与 candidate/main merge base 均为
  `395e02b7dfeaa87baedb2611ec503d14ab137ce3`；
- maintained `main` 已由独立的 PR #21 推进至
  `a4365cf673cb7995413168cb1e1439c183566268`；
- main 与 candidate 分别有 4 和 24 个独有提交，其中保留的 RB11 parent closure 之后有
  12 个线性 CR2 提交；
- 在未 fetch 的本地 remote-tracking ref 范围内，没有 ref 包含收口前 HEAD；
- candidate branch 与 worktree 均保留；
- 未执行 merge、push、删除、清理、profiler 权限修改或 maintained rollback。

观测到的 main、remote ref、branch 与 worktree 值是有日期的 pre-commit snapshot，
不是未来 architecture test 的永久 pin。实时比对属于显式 acceptance check；持久 guard
只校验冻结记录、不可变提交图、证据与 maintained code boundary。

维护中的 CPU backend 继续为默认。`compiled_experimental_backend`、
`supports_resident_state` 与 `supports_device_observation_view` 均保持 false。
CR2-7 不修改 runtime、contract、probe、CMake、kernel、launch 或 C++ test。
既有 143 行 RB11 architecture guard 从可变 live ref 收窄为冻结快照与不可变的
`BASELINE → RB10` 提交图。

## 规模与工件评估

CR2-7 新增 546 行 validator 与 232 行 architecture guard；调整后的 RB11 guard 为
143 行。三者均低于 700 行 soft target 和 1000 行 hard ceiling；closure JSON 与两份
说明文档均为小型工件。

保留的四份 CR2-6b raw report 合计 597,239 bytes，最大单件 194,834 bytes。其格式化
JSON 行数虽超过 1000，但属于证据工件而非代码模块；每件均低于 512 KiB artifact
soft cap 与 1 MiB hard cap。保留 raw sample 是独立重算两轮 order-balanced campaign
所必需的。CR2-7 不新增大型 raw artifact。

## 验证与未来工作

持久 closure 校验与独立 pre-commit live check 命令：

```powershell
python tools/diagnostics/cuda_resident_cr2_closure.py
python tools/diagnostics/cuda_resident_cr2_closure.py --check-live-snapshot
```

validator 检查精确 JSON type、hash、先验证据规范化、线性提交链、maintained flag
与 evidence-only 写边界；显式 flag 额外把可变的本地 ref/worktree 与有日期快照比较。
architecture test 有意不永久 pin 未来 `main` 或 worktree 状态；它拒绝 gate、type、
scope、hash、链接、不可变提交图与规模漂移。最终暂存快照仍必须通过既有 CR2 focused
与 CUDA-on/off runtime 套件。

精确 staged CR2-7 snapshot 必须先获得新的独立 `FINAL APPROVE`，才能形成唯一 closure
commit。该批准不授权 merge、push、promotion、tuning、host 权限修改或破坏性清理。

未来 CUDA-resident 工作必须建立新的显式计划并取得用户授权。新计划可以在 host
permission 可用后重试 achieved counter，也可以提出 integration；本已关闭计划不隐式
授权任何一项。
