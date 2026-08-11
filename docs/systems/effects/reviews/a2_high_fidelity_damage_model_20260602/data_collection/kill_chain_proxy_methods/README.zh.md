# G5 Kill-Chain Proxy Methods 数据收集入口

状态：`2026-06-02 / G5-R-A / research_source_collection / non_authoritative`。

本目录只整理 `G5-R` Pk / fuze proxy 研究线可用的方法、边界和候选输入。它不授予
`pk_authority` 或 `deterministic_fuze_authority`，不创建 runtime descriptor，不替换现有
RNG-compatible hit / fuze gate。

## Scope

本包关注：

- kill-chain proxy 的事件分解方法；
- miss-distance、fuze proxy、mechanism-load、component response 和 consequence flags
  之间的研究级连接；
- `G4-R-B` / `G4-R-C` 输出如何作为 downstream research input；
- 哪些公开、第三方、社区或 repo-internal 方法只能作为 sanity / proxy，而不是 Pk 真值。

不关注：

- Pk calibration claim；
- deterministic fuze trigger threshold、delay、reliability 或 target signature truth；
- mission-kill probability；
- stock database row、runtime descriptor 或训练 reward authority。

## 当前 packet

| packet | role | status |
|---|---|---|
| [G5-R source scan](g5_r_source_scan_20260602.zh.md) | 整理 G5 research proxy 的第一波方法输入、拒绝项和 replacement rule | `pass` |
| [G5-R event-chain map](../../g5_research_event_chain_map_20260602.zh.md) | 将 proxy source / boundary 连接为 research event chain | `pass` |
| [G5-R uncertainty audit](../../g5_research_uncertainty_independence_audit_20260602.zh.md) | 审查 source/model/scope/result uncertainty 和独立性 | `pass` |

## 使用规则

- 每条 method / input row 必须标注 source tier、scope、rights、uncertainty、confidence
  和 replacement rule；
- repo-internal docs 可以作为 boundary / method input，但不能被写成外部独立真值；
- community / simulation / game-like material 最多作为 rejected 或 sanity-only；
- 任何单点 Pk、kill radius、fuze radius、damage value 或 trigger threshold 都不得进入
  research surface，除非另有 source admission、rights 和 explicit non-authoritative 标注。
