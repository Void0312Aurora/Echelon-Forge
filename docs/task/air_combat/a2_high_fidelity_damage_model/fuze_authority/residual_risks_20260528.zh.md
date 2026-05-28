# residual risks

状态：`2026-05-28` 计划/标准文档。本文记录 deterministic fuze / P4 放行前后仍需跟踪的残余风险；它不是放行签核，不代表 deterministic fuze 已放行。

## 当前必须保持打开的风险

- **过确定风险**：若在 warhead / fuze / vulnerability / guidance 联合证据不足时移除 RNG hit gate，高机动规避可能无法通过 miss distance 或 signature 影响杀伤结果。
- **代理证据误升格风险**：RCS、laser 投影面积、surface distance、penetration depth、`delay_s` 等当前多为工程代理或诊断字段，不能被解释为校准引信性能。
- **vulnerability 混用风险**：vulnerability descriptor 可约束 effect scale、component failure probability 或 Pk 数据通路，但不是 fuze trigger authority。混用会让 P4 越权放行。
- **时序风险**：当前 proximity event 可能在最近点后一帧结算，`closure_mps` 可为 0；如果 admission 不固定 event ordering、dt 和 delayed detonation queue，回放会出现伪确定性。
- **scope 漏标风险**：一个窄域 weapon / target / aspect admission 被误用于其他武器、目标、姿态、闭合速度、高度或环境。
- **hitbox 几何风险**：contact / impact fuze 依赖 authored hitbox 表面；几何粗糙、组件重叠或父子 hitbox 不一致会改变触发判定。
- **signature 数据风险**：radar / laser fuze 对目标签名、姿态、遮蔽和环境敏感；缺少校准数据时，signature proxy 可能强化错误方向。
- **timed setting 风险**：`delay_s` 字段无法表达战术装定来源、漂移、保险逻辑和 safe separation；timed fuze 尤其容易被误当作简单定时炸点。
- **replay 漏洞风险**：branch replay、serialize/restore、不同 backend profile 或 dt 变化可能让 fuze state 丢失或重排。
- **训练消费层误读风险**：reward / combat_win smoke 可能把事件结果当作物理权威，反过来推动过早 deterministic admission。

## P4 前置缓解

放行前必须完成：

- 建立独立 `a2.fuze_authority.v1` manifest；
- 让 manifest 与 vulnerability descriptor 完全分离；
- 对四类 fuze type 分别定义 required evidence；
- 固定 replay/admission matrix；
- 对 out-of-scope case 强制回退 non-authoritative path；
- 在 event 中记录 authority manifest id、evidence refs、admission state；
- 给每个 admitted scope 建立 revocation policy；
- 由 residual risk review 明确哪些风险被接受、哪些风险仍阻塞。

## 放行后仍需监控

即使未来某一窄 scope 被 admission，仍需持续监控：

- 新增 aircraft / weapon JSON 是否意外继承 admitted scope；
- hitbox 或 component geometry 改动是否触发 admission 撤销；
- fuze profile、warhead profile、target signature profile 改动是否触发重放；
- backend scheduling、dt、serialization 或 event recorder 改动是否改变 event order；
- replay matrix 是否覆盖新出现的边界几何；
- synthetic / fixture 数据是否被误接入 production authority path；
- reward consumer 是否仍只消费 physical event，不反向定义 fuze authority。

## 当前 residual risk 判定

当前 residual risk 结论：`P4 blocked / deferred`。

主要阻塞项：

- 没有 admitted fuze authority manifest；
- radar / laser trigger 仍缺校准 signature / threshold 证据；
- contact / impact 仍缺接触物理、入射角、材料和失效模式证据；
- timed fuze 仍缺装定来源、漂移和安全逻辑证据；
- replay/admission matrix 尚未执行；
- vulnerability descriptor 与 P4 authority 仍必须保持分离。

因此 deterministic fuze 仍不得放行。
