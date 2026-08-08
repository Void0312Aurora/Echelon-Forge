# 操作文档

语言：英文为规范页；[中文配套](README.md)。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/operations/README.md`
Owner: `operations documentation`
Last verified: `2026-08-08`

面向开发者和用户的参考文档与操作指南，按类别组织。

## 目录

### 参考指南（"是什么"）

系统能力、代码结构、物理实现的当前状态说明。

| 文档 | 说明 |
|------|------|
| [引擎能力说明](reference/engine_capabilities.zh.md) | 当前引擎能做什么、关键局限、RL 接口 |
| [代码层地图](reference/src_layer_map.zh.md) | `src/` → `python/` → `gym_envs/` → `tests/` → `tools/` 的导航入口与推荐阅读顺序 |
| [物理引擎基础清单](reference/physics_engine_inventory.zh.md) | ECS 管线、运动积分、控制模型、环境模型、数据来源的代码入口 |

### 操作指南（"怎么做"）

| 文档 | 说明 |
|------|------|
| [场景配置指南](howto/scenario_configuration_guide.zh.md) | 维护中的场景 JSON 编写与 loader 映射；不拥有 doctrine 或 DTO |
| [远程可视化](howto/visualization_guide.zh.md) | SSH 端口转发 + Web 实时查看仿真 |

### 规划与开放问题

| 文档 | 说明 |
|------|------|
| [可视化技术栈演进](visualization/work/issues/viz_stack_evolution.zh.md) | 维护中的北极星计划；不是实施权威 |

### 已验收可视化评审

| 文档 | 说明 |
|------|------|
| [双语显示 P1](visualization/reviews/bilingual_display_20260606/README.zh.md) | 已验收的双语显示切片与有界证据 |
| [环境叠加 P1](visualization/reviews/environment_overlay_visual_elements_20260606/README.zh.md) | 已验收的环境叠加切片与 held 后续 |
| [仅地图 Viewer P1](visualization/reviews/map_only_viewer_mode_20260606/README.zh.md) | 已验收的仅地图切片与 held 后续 |

### 遗留归档

已过时的历史设计笔记。

| 文档 | 说明 |
|------|------|
| [起飞到巡航混合模式](../manual/archive/takeoff_to_cruise_mixedmode_notes.zh.md) | 冻结的历史 P3 实验基线；归档源不进入维护树迁移 |

着陆任务语义路由到当前
[Air 着陆 reference](../domains/air/reference/landing_task.zh.md)。

---

维护规则：reference 随代码变更更新，how-to 随工作流或工具变化更新。已完成的
操作工作应提升为维护 reference，或通过所属区域的归档路由收口。
