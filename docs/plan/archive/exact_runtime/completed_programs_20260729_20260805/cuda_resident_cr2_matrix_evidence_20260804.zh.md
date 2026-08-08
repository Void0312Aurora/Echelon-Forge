# CR2-6b production matrix 证据

日期：2026-08-04

source commit：`0c24a07549e238222741da6b20100537e7a9be22`

状态：**matrix evidence 与 experimental selection advisory 已完整；maintained
support、tuning 与 promotion 继续关闭。**

## 范围

本证据以完整 `1/4/16/64/256` world protocol，各运行两次 CR2-6a Release CPU/CUDA
probe。campaign 1 顺序为 CPU→CUDA，campaign 2 为 CUDA→CPU；lane 从不并发。比较仅覆盖
两个共同 mode，以及 warmed end-to-end p50/p95、rollout-per-window p50/p95 四项指标。
CUDA-only device-consumer mode 只记录 availability，不伪造 CPU 比较。

advisory 面向 steady window，因此 setup/cold family 虽保留在 raw report 中，但不作为
routing 输入。rollout 只有 10 个 sample，所以 nearest-rank p95 实际是观测最大 rollout，
不是高样本量 tail estimate。

主机为 AMD Ryzen 7 8845H（8 core/16 logical processor）、约 32 GiB RAM、Windows 11
build 26200 与 RTX 3090。active power scheme 为 balanced；未固定 affinity、未使用 GPU
exclusive mode，也未控制 background load。因此结论仅是本机 experimental routing
advice，不是 tuning 或 production support claim。

## 内容寻址输入

| 输入 | Bytes | SHA-256 |
|---|---:|---|
| CPU campaign 1 | 103,773 | `ef7484bb431595836e388b57112e8123b17baf016752f198dbefc5a79b88f0cf` |
| CUDA campaign 1 | 194,834 | `5dd5f89c32b4dc7336e56fbe6d67042cbe0d4127e054f3f0c5e6b73f0e1b902a` |
| CUDA campaign 2 | 194,684 | `9cfc14ac3dccdc629b6378958a0c5631487c34d172df41502165b1138b34fa84` |
| CPU campaign 2 | 103,948 | `e3791164ae64b2a28fb56a8a543991e95d7973e2df317b46e274bc126fd9281b` |

四份 report 均通过 CR2-6a production validator。同 lane 的跨 campaign 非 timing 字段
完全一致，CPU/CUDA master trace signature 一致。fresh CR2-4b full-window comparison 的
12 个 release field 与 same-backend exact reset 全部通过。CR2-5a static/topology evidence
保持完整，但 CR2-5b achieved counter 仍被 `ERR_NVGPUCTRPERM` 阻断，因此不授权 tuning。

raw、manifest、parity 与 summary JSON path 标记为 `-text`，checkout 不会改变其 byte
hash；source 与 prior-evidence descriptor 显式使用 `utf8_lf` canonicalization，
不依赖平台换行表示。

## 观测方向

ratio 定义为 CPU ms / CUDA ms；大于 1 表示 CUDA 更快。除非单独指出 metric，range
覆盖两个 order-balanced campaign 与该 row 的全部命名指标。

| Worlds | 共同 mode | 结果 |
|---:|---|---|
| 1 | no export | CPU 赢得全部指标；ratio `0.028–0.151`。 |
| 1 | host export | CPU 赢得全部指标；ratio `0.048–0.096`。 |
| 4 | no export | CUDA 赢得全部指标；最小 ratio `1.332`。 |
| 4 | host export | CUDA 赢得两个 p50，但 rollout p95 按 campaign 反转（`0.508–6.057`）。 |
| 16 | 两者 | CUDA 赢得全部指标；最小 ratio `6.539`。 |
| 64 | 两者 | CUDA 赢得全部指标；最小 ratio `5.651`。 |
| 256 | 两者 | CUDA 赢得全部指标；最小 ratio `4.954`。 |

world-4 host-export tail 不会被平均值掩盖。campaign 1 的 CUDA rollout p95 约为
4.82 ms/window，CPU 为 2.45；campaign 2 的 CUDA 为 0.89，CPU 为 5.41。该顺序敏感
反转阻止对这一 row 给出无条件 CUDA 规则。

## Experimental selection advisory

- world 1 的共同 mode：使用 Flecs CPU reference。
- world 4、no export：使用 CUDA。
- world 4、host export：保守 tail 默认 CPU；只在调用方明确追求 median throughput 时
  opt in CUDA。
- world 16/64/256 的共同 mode：使用 CUDA。
- device-consumer mode：CPU 无 comparator，必须使用 CUDA；这不是比较性能 claim。
- 其他 world count：不外推、不提供 recommendation。

maintained default 继续是 Flecs CPU。该 advisory 不启用 public backend selector，也不改变
runtime behavior。

## Gates

`cr2_6_matrix_evidence_complete=true`，
`cr2_6_selection_advisory_complete=true`。achieved counter、maintained claim、public
support、tuning 与 promotion 均继续为 false。CR2-7 必须另行审阅 closure 或 promotion
decision；本证据不替代该决策。
