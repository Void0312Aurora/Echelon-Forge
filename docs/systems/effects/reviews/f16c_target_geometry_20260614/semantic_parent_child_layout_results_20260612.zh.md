# F-16 语义父子部件布局结果（R14，2026-06-12）

## 结论

R14 把可视化主入口从 `26` 个孤立 receiver 视图改为 `14` 个基于几何建模的父外壳部件视图。

每个父部件对应一个模型区域/语义外壳体积；现有 `26` 个 receiver 先验不再作为主视图单独排开，而是按 `bound_region_id` 叠加到对应父外壳上。由于 `26 - 14 = 12`，当前总共有 `12` 个 extra receiver slot。

该层仍是 review-only 展示和审阅数据，不代表 runtime damage ownership 已经接受。

## 新增产物

- [review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json)
- [review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv)
- 中间 parent-child layout 视图已退役。
- 当前可视化结果：[whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html)

## 读图约定

- 蓝色：14 个父外壳/模型区域的 mesh-derived 几何背景。
- 绿色：该父部件的 primary 或 single receiver prior。
- 青色：同一父部件上的 extra receiver prior。
- 红色：跨区 held split segment；当前来自 `engine_core` 和
  `wing_spar_center`。

R14 最终预览图不再显示 source bounds、support bounds、旧 AABB、测试点或其他审阅辅助层。
它只保留父几何背景和子部件。R15 保持 receiver prior 的真实尺寸/先验尺寸，并在整机约束下
把两个红色 held receiver 画成更小的分段，而不是单一红色大块。

## 统计

- 父几何部件：`14`
- 叠加 receiver prior：`26`
- extra receiver slot：`12`
- 跨区 held receiver：`2`
- 跨区 held split segment：`8`
- active runtime component：`0`

## 边界

- R14 只是改变审阅主视图和数据分组，不激活 runtime damage model。
- 绿色/青色/红色都是 synthetic receiver prior，不是真实 F-16 内部工程结构。
- 红色 held 的 receiver 仍需先拆分或明确接受 ownership，不能因为已经画在父图上就视为通过。
