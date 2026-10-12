# `src/models/systems` 边界

`models/systems` 保存平台系统相关模型实现，例如 sensor 和 acoustic model 默认实现。

本目录在 sensing/contact 侧是 multi-domain aware，包括 air/visual sensor
行为和 naval/acoustic helper。ship-specific maritime sensor state 通过
`models/domains/naval/naval_sensor_maritime_adapter.h` 路由，不由 generic sensor model
直接拥有。它不拥有 full ground sensing 或 land C2 runtime 行为。

## 允许

- sensor、acoustic/sonar、track、data-link 等平台系统的可替换计算模型。
- 只依赖 `core/interfaces` 和 component 数据的纯 C++ 逻辑。

## 禁止

- Flecs system tick。
- component 定义。
- Python binding 或 facade。
- full ground sensing、terrain-control 或 fires runtime。

## 默认 acoustic provider 的能力

内容加载器解析 Passive、Active 声呐声明，包括 inline 和 mounted 模块；解析成功
不代表 provider 支持该模式。默认 acoustic provider 仅支持 Passive：
`IAcousticModel::scan` 对 Active 返回 `UnsupportedMode`，对受支持的扫描返回
`Completed`，包括零检测结果。`SonarSystem` 仅在 `Completed` 时接收新接触，
将结果保存到 `Sonar::last_scan_status`，并在模块进入不支持状态时输出
`runtime.acoustic.unsupported_mode` 诊断。`last_scan_time_s` 表示最近一次尝试，
消费者必须同时读取状态。inline 和 mounted 状态均参与迁移；缺少该字段的旧快照
默认恢复为 `NotScanned`，不会推断历史扫描成功。未来 provider 可以通过同一接口
实现 Active；本次变更不提供主动声呐传播或回波模型。

## 迁移备注

目录名与 `systems/systems` 相近，新增文件必须用具体业务名表达模型类型，避免泛化扩张。
