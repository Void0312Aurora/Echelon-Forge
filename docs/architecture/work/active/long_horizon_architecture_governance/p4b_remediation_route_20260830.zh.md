# P4-B 修正路线：来源证明与持久化迁移

状态：`2026-08-30` 规划工件；P4-B 仍为 `repair-required`。

本路线闭合 caller 可伪造 owner provenance 与非持久化 import transaction 两个长期
阻塞。fixture 兼容性只能作为证据，不能满足验收。

1. **Host 签发 capability**：通过 host-owned factory 构造 owner，返回绑定 host boot、
   slot、resource、generation 和 authenticator 的 opaque single-use handle，拒绝复制、
   重放、跨 host/slot 及 reclaim 后使用。
2. **持久化 transaction**：以具备单调状态、deadline、取消、幂等 commit/abort 和中断
   恢复的 durable transaction 替换同步 `void noexcept` hook；写入 mutation 前记录和终态，
   歧义记录 fail-closed 并 quarantine。
3. **Typed decoder/replay matrix**：十二类状态均提供维护中的 exporter/importer，明确
   N/N-1、unknown-field、migration hash、replay vector 与 rollback 语义。
4. **验收**：每个工作包后独立审查；补齐 native、Python、boundary、中断恢复与 replay
   证据。P4-C 保持 dark/shadow，P5 durability/authenticity/canary 单独设门。

不授权 caller migration、production publication、rebuild retirement、multi-world enablement
或缩小为 fixture-only。只有 handles 可认证、transaction 有持久终态和恢复、decoder matrix
全绿且独立审查无 Critical/High 阻塞时才可 accepted。
