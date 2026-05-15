# US Marine Corps Profile

本文档定义项目在海空地一体 expeditionary 建模时采用的 US Marine Corps profile。

## 1. 官方现实基础

Marine Corps 官方 `MCDP 1-0` 明确强调 Marine Corps component 与 MAGTF 组织方式。

公开官方依据：

- [MCDP 1-0 w/ CH 1-3](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1323621/mcdp-1-0-w-ch-1-3/)

该文档官方页面明确指出：

- `MCDP 1-0` 关注 Marine Corps component 在 operational level 的作用
- 以及最大的 MAGTF 如何在 tactical level 组织行动

## 2. 建模结论

USMC 不是简单的：

- Army ground profile
- + Navy embarkation
- + Air Force air support

它的现实组织更接近：

- `Command Element`
- `Ground Combat Element`
- `Aviation Combat Element`
- `Logistics Combat Element`

因此，如果项目未来扩到两栖或 expeditionary 场景，
Marine Corps 应作为独立 service profile，而不是临时拼接。

## 3. 对项目通用模板的影响

USMC profile 说明 joint/core 层需要支持：

- 多 combat element 并存
- command element 统一调度
- 跨 air / ground / logistics 的任务关系

这进一步证明：

- 通用模板应以 `joint/common core + service profile` 架构为主
- 而不应从空战单域结构直接向外硬推
