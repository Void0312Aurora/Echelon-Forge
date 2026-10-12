# `src/models/systems` 边界

`models/systems` 保存平台系统相关模型实现，例如 sensor 和 acoustic model 默认实现。

本目录在 sensing/contact 侧是 multi-domain aware，包括 air/visual sensor
行为和 naval/acoustic helper。ship-specific maritime sensor state 通过
`models/domains/naval/naval_sensor_maritime_adapter.h` 路由，不由 generic sensor model
直接拥有。它不拥有 full ground sensing 或 land C2 runtime 行为。

## 允许

- sensor、acoustic/sonar、track、data-link 等平台系统的可替换计算模型。
- 只依赖 `core/interfaces` 和 component 数据的纯 C++ 逻辑。

## Passive 声学源强代理

`default_acoustic_model.cpp` 对没有已接纳 acoustic signature 的目标使用
`passive_target_source_proxy.v1`：118 dB 参考值加每 m/s 1.6 dB，并叠加潜艇
stealth bias + 10 dB、舰船 + 16 dB、飞机 + 18 dB 的平台偏置（当前扫描仅接纳
舰船/潜艇目标，所以飞机 helper 分支不生效）。这是用于确定性
运行时的工程代理，不是经过校准的频率相关特征、实测部署距离或源数据替代品。
接收方遗留的 `Sonar::source_level_*` 字段不再选择目标发射源强。

维护中的 C++ 归属基线是 `src/tests/test_acoustic_model.cpp` 中的
`passive target source level is invariant to receiver source settings` 和
`passive target source level follows target speed` 两个用例；历史上使用接收方
源强字段生成的 detection、SNR、概率或距离报告，必须按该代理版本重新计算后再
比较。具体包括 `tests/runtime/naval/test_naval_asw_helo_runtime.py` 中的接触和
海况噪声用例：它们过去消费 `DDG-51_Flight_I_ASW_Helo_MVP` 接收方的
118 dB / 每 m/s 1.7 dB 设置，现在目标速度项使用代理的 1.6 系数。使用
Virginia passive 模块（0 / 0 源强字段），或曾将 DDG Active 的 235 dB 字段
当作 passive 目标发射源强的历史 CSG trace，同样需要重算。
在有已接纳且具备校准证据的 signature provider 替换代理前，不作运行部署
能力声明。

## 禁止

- Flecs system tick。
- component 定义。
- Python binding 或 facade。
- full ground sensing、terrain-control 或 fires runtime。

## 迁移备注

目录名与 `systems/systems` 相近，新增文件必须用具体业务名表达模型类型，避免泛化扩张。
