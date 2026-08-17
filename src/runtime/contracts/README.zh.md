# `src/runtime/contracts` 边界

`runtime/contracts` 保存 runtime/facade 与 lower-level runtime owner 之间共享的稳定 DTO。这里的类型可以被 facade、engine、Python bindings 和测试共同引用，但不能拥有 world state、ECS registry 或系统调度逻辑。

当前 contract surface 是 multi-domain/common-first。`world_batch_contracts.h`
承载 typed platform setup、terrain/wind/zones，以及带 shared、air、naval
slice 的 maintained mission-command 与 tasking batch contract。
`engagement_contracts.h` 承载 N4 pre-fire/contact 加受限 engagement-evidence
路径使用的 track/contact evidence、launch request/event、munition lifecycle、
effects、damage 和 diagnostics trace DTO。ground 在这里仅是
setup/evidence-aware；full ground movement、sensing、fires、damage 或 runtime
contract 尚未维护。

`simulation_composition_contract.h` 与生成的
`composition/simulation_composition_manifest.v1.schema.json` 定义 host-neutral composition
value contract。它们命名 version、scope、service、provider/system contribution、backend
request、evidence policy 与 stable validation error；不构造 provider、不持有 scope resource、
不解析 Cordis object，也不注册 Flecs system。Executable schema source 与 canonical fixture
位于 `tools/maintenance/simulation_composition_contract.py` 和
`tests/architecture/composition/fixtures/`。

## 允许

- `WorldEntityRef` 这类轻量引用。
- batch setup / command / tasking / episode step request DTO。
- 只由 value types、component DTO 和 mission runtime DTO 组成的 request/result 类型。
- 保持纯 contract、不执行业务逻辑的 engagement/tasking evidence DTO。
- Host-neutral composition manifest、stable service key 与纯 validation/result value。

## 禁止

- `SimulationKernel`、`WorldBatchRuntime` 或其他 owner class。
- Flecs system 注册、step 调度、GPU helper 实现。
- Python/nanobind 绑定逻辑。
- 为了方便 include 而引入 `core/engine/*`。
- 在维护中的 ground owner 与 schema 存在前扩张 ground-specific runtime 语义。
- Provider construction、lifecycle effect、service locator state 或 composition-time Flecs registration。

## 生成 detail 布局

`detail/` 下生成的 X-macro 列表按 contract 领域放入 `damage`、
`engagement`、`kill_chain`、`learning`、`platform`、`scenario` 与 `tasking`。
新增列表必须进入对应 contract 目录，并同步维护
`tools/maintenance/dto_schema/schemas/<domain>/` 下的声明源；schema 领域名与
输出领域名不要求完全相同。不得再向 `detail/` 根层直接添加 `.inc` 文件。

## 迁移备注

本目录是后续 `ef_contracts` target 的候选起点。新增 facade-facing 类型应优先放在这里，再由 facade 或 engine implementation 消费。新增领域字段时，优先采用 `common` 加显式 domain slice，而不是把 air/naval/ground-only 语义扩进共享 contract。
