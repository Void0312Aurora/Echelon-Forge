# `src/models/ground` 边界

`models/ground` 保存共享 default model 使用的 ground-owned placeholder model route。

## 允许

- 保持 legacy 行为的显式 ground placeholder routing。
- 防止 ground 概念藏回 generic model 文件的小型 owner-shell helper。

## 禁止

- ECS system registration。
- 定义 ground component。
- 宣称完整 ground movement、sensing、fires 或 damage runtime 成熟度。

## 当前文件

- [default_effects_ground_domain.h](default_effects_ground_domain.h)
  - 保持 finalize-only 行为的 placeholder ground effects routing。
