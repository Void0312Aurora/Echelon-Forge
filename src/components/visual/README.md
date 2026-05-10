# `src/components/visual` 边界

`components/visual` 保存视觉观测相关 ECS 状态和数据缓存。

## 允许

- visual sensor state。
- visual observation system 需要读写的轻量数据。

## 禁止

- 渲染器、图像编码、Python 视图绑定或 GPU kernel。
- 传感器扫描行为本身。
- mission/runtime 编排。

## 迁移备注

视觉系统行为放在 `systems/visual`，GPU 视觉 helper 放在 `gpu/`，本目录只保留 component 数据。
