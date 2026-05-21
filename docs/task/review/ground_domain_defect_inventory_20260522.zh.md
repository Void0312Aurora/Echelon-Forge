# 陆军域缺陷清单与迁移差距分析

状态: `2026-05-22` 从 G0-G5 基线架构审计中编制。

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

### D-001: 缺少 C++ `command/ground/` 目录 — BLOCKER

`src/components/command/` 含 `air/` 和 `naval/` 但无 `ground/`。所有地面命令构造流经标为"兼容壳"的 `ground_profile.py::build_kernel_mission_command()`。

### D-002: 缺少 C++ `tasking/ground/` 目录 — BLOCKER

`src/components/tasking/` 含 air/naval 的领域枚举和 DTO，ground 无。需创建 `ground_tasking_enums.h`、`task_order_ground.h` 等。

### D-003: MissionCommand 聚合缺少 Ground — HIGH

`mission_command.h` 以平面继承聚合 Core+Air+Naval，无 Ground。勿将 `MissionCommandGround` 加入平面继承链，应采用能力组合。

### D-004: 阶段节点清单无 P2 节点 — HIGH

注册表仅 5 个节点（P7/P9/P10）。P2（TaskingIntent）为零。需注册 P2 节点清单。

### D-005: 时钟域仅定义战术节奏 — HIGH

仅声明 1 Hz 战术评估。运动/感知/火力/导出管线节奏未定义。需扩展时钟域表。

### D-006: C++ 中缺少地面特定枚举 — HIGH

对比 air（`LeaderPhase`、`TakeoffProcedureType` 等）和 naval（`NavalWarfareRole` 等），ground 无。需定义 `GroundEchelonLevel`、`GroundTacticalPosture`、`GroundSupportRelationship`。

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

### D-014: 无陆军域边界架构测试 — LOW

需添加 `tests/architecture/test_ground_domain_boundary.py`。

## 4. 汇总

| 级别 | 数量 | 项目 |
|------|------|------|
| BLOCKER | 2 | D-001, D-002 |
| HIGH | 4 | D-003-D-006 |
| MEDIUM | 4 | D-007-D-010 |
| LOW | 4 | D-011-D-014 |

## 5. 推荐解决顺序

1. 立即: D-013, D-014
2. G6前: D-005, D-009, D-011
3. G6前需C++工作: D-001, D-002, D-006
4. "maintained"前: D-004, D-007
5. 外部阻塞: D-003, D-008
6. 择机: D-010, D-012
