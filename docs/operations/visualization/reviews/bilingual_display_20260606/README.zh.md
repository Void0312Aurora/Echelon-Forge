# 双语显示

状态：`2026-06-06` 已接受的 viz follow-on。`P1` 实现战术地图 UI 的显示层
中英切换。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/operations/visualization/reviews/bilingual_display_20260606/README.md`
Owner: `operations/visualization`
Last verified: `2026-08-08`

父级 owner：[Operations](../../../README.zh.md)

P1 验收：
[bilingual_display_p1_acceptance_20260606.zh.md](bilingual_display_p1_acceptance_20260606.zh.md)

## 目的

为 `examples/viz` 增加明确的 EN/ZH 显示层，让同一张战术地图可以在英文或中文
界面下检查，同时不改变 scenario、profile、地形或 runtime 语义。

`P1` 覆盖：

- 顶部 action bar 的语言切换按钮；
- 静态 UI 标签、按钮、dock 标题、控制提示和 ARIA 标签；
- 动态 workspace tab、图层控件、运行/会话控件、纯地图标签、速率文本、
  视图/相机模式文本和战术比例尺；
- generated terrain constructs 对应的 environment overlay callout；
- runtime 发出已知 task token 时的 C2 task、phase 和历史记录显示。

## 边界

本 follow-on 只做显示层，不新增或释放：

- scenario schema 变化；
- profile 或 object-binding 语义；
- 地形生成、地形 artifacts 或 runtime setup application；
- passability、movement cost、LOS、cover、concealment、combat、reward 或
  termination 行为；
- scenario 文件名、profile 名、unit ID 或 asset ID 的翻译。

scenario/profile/object 标识保持为稳定数据标签，按 runtime 原样显示。

## 验证

`P1` 已通过：

- JS module 语法检查；
- 覆盖 bilingual UI 契约的聚焦 viz pytest；
- browser smoke 确认语言按钮能把 `documentElement.lang` 和关键可见控件切到中文，
  再切回英文；
- browser console `Errors: 0`。

命令输出和浏览器观察状态见 P1 验收页。
