<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/marine_corps.md. Review before treating this file as authoritative. -->

# 美国海军陆战队概况

本文档定义项目在海空地一体远征建模时采用的美国海军陆战队配置文件。

## 1. 官方现实基础

海军陆战队官方 `MCDP 1-0` 明确强调海军陆战队组成部分与 MAGTF 组织方式。

公开官方依据：

- [MCDP 1-0 含第1-3修改](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1323621/mcdp-1-0-w-ch-1-3/)

该文档官方页面明确指出：

- `MCDP 1-0` 关注海军陆战队组成部分在作战层级的作用
- 以及最大的 MAGTF 如何在战术层级组织行动

## 2. 建模结论

USMC 不是简单的：

- 陆军地面配置文件
- + 海军登舰
- + 空军空中支援

它的现实组织更接近：

- `指挥单元`
- `地面作战单元`
- `航空作战单元`
- `后勤作战单元`

因此，如果项目未来扩到两栖或远征场景，
海军陆战队应作为独立服务配置文件，而不是临时拼接。

## 3. 对项目通用模板的影响

USMC 配置文件说明联合/核心层需要支持：

- 多作战单元并存
- 指挥单元统一调度
- 跨空中/地面/后勤的任务关系

这进一步证明：

- 通用模板应以 `联合/通用核心 + 服务配置文件` 架构为主
- 而不应从空战单域结构直接向外硬推
