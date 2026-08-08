# 陆军域缺陷清单与迁移差距分析

语言：[英文主文](ground_domain_defect_inventory_20260522.md)；中文配套。

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/reviews/ground_domain_defect_inventory_20260522.md`
Owner: `domains/ground/reviews`
Last verified: `2026-08-08`
Review basis：`2026-05-22` 清单与 `2026-06-09` 收口更新；不是当前缺陷权威。

状态：保留 review；来自 `2026-05-22` G0-G5 基线审计，并含
`2026-06-09` 收口更新。新缺陷必须进入当前 issue 或 review。

## 1. 目的

记录截至 G5 MVP 场景壳验收时，陆军域中所有已知的缺陷、差距和架构不完整性。

## 2. 严重级别

| 级别 | 含义 |
|------|------|
| **BLOCKER** | 阻止在 P2 任务层外声明 "maintained" |
| **HIGH** | 限制领域完整性的结构性差距 |
| **MEDIUM** | 随时间累积风险的架构债务 |
| **LOW** | 文档/命名/一致性问题 |

## 3. 缺陷账本

### D-001: 缺少 C++ `command/ground/` 目录 — ~~BLOCKER~~ **CLOSED 2026-06-09**

`src/components/domains/ground/command/` 已存在，含 `mission_command_ground.h` + README（中/英）。

### D-002: 缺少 C++ `tasking/ground/` 目录 — ~~BLOCKER~~ **CLOSED 2026-06-09**

`src/components/domains/ground/tasking/` 已存在，含完整结构：`ground_tasking_enums.h`、`leader_intent_ground.h`、`pilot_report_ground.h`、`task_order_ground.h` + README（中/英）。

### D-003: MissionCommand 聚合缺少 Ground — ~~HIGH~~ **CLOSED 2026-06-09**

`mission_command.h` 现在通过 `MissionCommandGround` 继承和 `mission_command_ground_owner_slice()` / `mission_command_ground_static_task_directive()` 访问器提供 Ground 投影。

### D-004: 阶段节点清单无 P2 节点 — HIGH

注册表仅 5 个节点（P7/P9/P10）。P2（TaskingIntent）为零。需注册 P2 节点清单。

### D-005: 时钟域仅定义战术节奏 — HIGH

仅声明 1 Hz 战术评估。运动/感知/火力/导出管线节奏未定义。需扩展时钟域表。

### D-006: C++ 中缺少地面特定枚举 — ~~HIGH~~ **PARTIAL 2026-06-09**

基础枚举已存在：`GroundTaskMode`、`GroundStatusPhase`（`ground_tasking_enums.h`）。仍缺失：`GroundEchelonLevel`、`GroundTacticalPosture`、`GroundSupportRelationship` 等战术语义枚举。降级为 MEDIUM。

### D-007: 未对地面评估保真度 — MEDIUM

无后台配置、无奇偶预算、无保真度准入请求。G6 前需定义。

### D-008: WP21 依赖 — MEDIUM

反事实恢复被 WP21-B 阻塞。跟踪 WP21-B，按 WP21 契约词汇设计 ground 反事实参与。

### D-009: common_core 回退默认 Air — MEDIUM

`common_core_profile.py:76` 返回 `"air"`。配置错误的 ground 场景静默获得空中语义。

### D-010: `build_kernel_mission_command` 是兼容壳 — MEDIUM

`ground_profile.py:253-276`，推断函数全部返回 0。G6+ 前勿扩展，届时实现正确版本。

### D-011: Ground Adapter 重新导出 Air 的 Leader Phase Manager — LOW

导入 `leader_tasking.py` 中空中特定的阶段推断。

### D-012: `.seed` 模式非永久方案 — LOW

需定义 seed → runtime JSON 升级标准。

### D-013: `scenarios/README.md` 中无 Ground 场景 — LOW

验证并更新。

### D-014: 无陆军域边界架构测试 — ~~LOW~~ **CLOSED 2026-06-09**

`tests/architecture/ground/` 已存在，含 `test_realism_gradient_guardrails.py` 和 `test_tasking_component_boundary.py`。

## 4. 汇总

| 级别 | 数量 | 项目 |
|------|------|------|
| ~~BLOCKER~~ | ~~2~~ 0 | ~~D-001, D-002~~ (均已闭合) |
| HIGH | ~~4~~ 2 | D-004, D-005 |
| MEDIUM | ~~4~~ 5 | D-006(降级), D-007-D-010 |
| LOW | ~~4~~ 3 | D-011-D-013 |
| **CLOSED** | **5** | D-001, D-002, D-003, D-006(partial→降级), D-014 |

## 5. 推荐解决顺序

1. 立即: D-013, D-014
2. G6前: D-005, D-009, D-011
3. G6前需C++工作: D-001, D-002, D-006
4. "maintained"前: D-004, D-007
5. 外部阻塞: D-003, D-008
6. 择机: D-010, D-012
