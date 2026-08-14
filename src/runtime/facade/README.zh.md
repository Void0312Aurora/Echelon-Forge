# `src/runtime/facade` 边界

`runtime/facade` 是维护中的 C++ 应用层 API。它面向训练环境、Python 绑定和后续前端主线，提供 typed request/result，而不是暴露底层 world owner 的全部细节。

facade 应以 multi-domain/common-first 口径描述平台，而不是 air-only。
它可以暴露 common setup、air execution、naval tasking/engagement evidence
以及 ground-aware typed setup evidence 的维护中 request/result。它不应暗示
ground movement、sensing、fires、damage 或 full ground runtime 已可用。

## 允许

- `RuntimeFacade`。
- facade request/result/capability 类型。
- 批量 reset、setup、step、command、tasking 和 observation 操作。
- 承载 common、air、naval evidence contract 的 tasking packet 与 engagement-event export。
- 面向早期 ground-aware admission 的 typed platform setup/capability evidence。
- 专用 diagnostics-trace query/export 操作。
- 对 `WorldBatchRuntime` 的受控包装。
- public header 只暴露 facade / contracts 类型；底层 `WorldBatchRuntime` owner 应留在 implementation 中。

## 禁止

- 实现 ECS system 或物理模型。
- 内联 Python 绑定逻辑。
- 把 `WorldBatchRuntime` 的所有低层 API 无选择复制为 facade API。
- 新增未设计 request/result 的主线入口。
- 在 `*_types.h` 或 facade public header 中直接 include `core/engine/*`。
- 通过 facade 命名或 capability flag 宣称仍 held 的 ground-domain runtime 行为。

## 生成 detail 布局

`detail/` 下生成的 facade X-macro 列表分为 `batch`、`runtime` 与 `window`。
新增列表必须进入对应 facade 目录，并同步维护
`tools/maintenance/dto_schema/schemas/<domain>/` 下的声明源；schema 领域名与
输出领域名不要求完全相同。不得再向 `detail/` 根层直接添加 `.inc` 文件。

## 逃逸口退休

`RuntimeFacade` 不再公开 raw `WorldBatchRuntime` 逃逸口。维护前端必须使用 facade-level request/result API；低层 diagnostics 或能力验证如果确实需要 raw runtime，应在 diagnostics/test scope 直接实例化 `WorldBatchRuntime`，而不是从 facade 向下钻。

主线前端不得缓存 raw `WorldBatchRuntime`、不得从 adapter 重新暴露 compatibility runtime，也不得根据 raw runtime 是否可用分叉。新增长期能力时，应补充设计过的 facade request/result，并在 Python 层绑定 facade 方法。

新增长期 API 时，应优先补充 facade request/result，并在 Python 层绑定 facade，而不是直接暴露新的底层 runtime 方法。

## Diagnostics Surface

`DiagnosticsTrace` 本身就是维护中的 facade surface。它可以与 engagement
export 共享 kernel evidence，但 facade 必须提供独立的 diagnostics query path，
不能要求使用者为了读取 trace 只能 piggyback 到
`export_engagement_event_packet()`。

engagement export 也是 N4 pre-fire/contact 与受限 engagement-evidence DTO 的维护中
facade 路径，例如 track packet、launch request/event、effects、damage 和
diagnostics trace。保持它们作为导出的 evidence surface；不要把 engagement
ownership 搬到 facade。

## Split Threshold

`RuntimeFacade` 的治理计数规则如下：

- 只统计维护中的 public request/result 方法。
- 不统计 constructor 和简单 accessor。
- 当维护中的方法数接近约 40 个时，应先围绕 Session、Setup、Execution、
  Observation、Diagnostics、Engagement 与 Capability groups 规划拆分，再继续扩张主线 surface。
