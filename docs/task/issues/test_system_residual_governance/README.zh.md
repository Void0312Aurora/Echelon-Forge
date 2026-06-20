# 测试系统残余治理

状态：`2026-06-21` 活跃保留 issue，用于追踪
[测试系统治理](../../review/test_system_governance/README.zh.md)
当前切片验收后仍必须可见的残余项。

负责线程：测试系统治理线和后续 runtime/test 负责人。

首次观察：`2026-06-21`，`docs/task/review/test_system_governance/`
收口期间。

问题类别：跨任务测试治理残余。这些问题会阻塞“整体测试健康”“行为保持”
或“覆盖充分”等宽口径声明，但不阻塞当前审计、精简、分层切片的验收。

## 摘要

测试系统治理切片已经建立可复跑的 active-test 审计，澄清 coverage 语义，
拆分部分超长测试，同步 smoke membership，并为 `weapon_guidance_realism`
wrapper/mixin collection 面补充文档。

以下四类残余应从已验收切片中保留下来：

- airframe geometry 行为保持仍需要依赖完整机器验证，因为本地 focused run
  通过既有 optional `scipy` / `shapely` gate 跳过；
- `tests/architecture/damage_model/` 已不再出现 `oversized_test_item`，
  但若干文件仍存在文件级 literal-heavy 或 source-scan-heavy 模式；
- `tests/runtime/air_combat/weapon_guidance_realism/` 已有显式 wrapper 和文档，
  但包级 focused run 仍失败；
- coverage 表述仍只能限定在已测量的 Python root，不能推出 C++ 或全项目覆盖充分。

## 当前证据

- 测试系统验收记录：
  [test_system_governance_acceptance_20260620.md](../../review/test_system_governance/test_system_governance_acceptance_20260620.md)
- 当前状态：
  [test_system_governance_current_status_20260620.md](../../review/test_system_governance/test_system_governance_current_status_20260620.md)
- 审计 runner：
  [tools/runners/audit_test_system.py](../../../../tools/runners/audit_test_system.py)
- 测试系统 README：
  [tests/README.md](../../../../tests/README.md)
- weapon-guidance wrapper README：
  [tests/runtime/air_combat/weapon_guidance_realism/README.md](../../../../tests/runtime/air_combat/weapon_guidance_realism/README.md)

`2026-06-21` 收口时的测量事实：

| 表面 | 证据 | 边界 |
| --- | --- | --- |
| 活跃审计 | 343 个已追踪活跃 test 文件、256 个已追踪活跃 Python 文件、1990 个修正后静态 test item、152 个风险标记 Python 文件。 | 仅为静态审计，不能证明语义冗余或覆盖充分。 |
| Pytest collection | `tests --ignore=tests/archive` 下 `2000 tests collected`。 | 仅 collection；仍有既有 Eventlet 与 nanobind side-effect 诊断。 |
| 当前验收 focused 批次 | runner、拆分 tools、拆分 damage-model 与 suite-manifest 测试为 `205 passed, 30 skipped`。 | skip 来自既有 optional airframe dependency 边界。 |
| Smoke suite | `340 passed, 41 subtests passed`。 | 不包含失败的 `weapon_guidance_realism` 包。 |
| Python coverage | 本地 `.coverage` 为 `34376` statements、`11916` missed、`65%` covered。 | 仅 Python roots；不接受 C++ `src/` 或 branch coverage。 |
| Weapon-guidance 包 | `192 tests collected`；focused 包级运行 `45 failed, 167 passed, 221 subtests passed`。 | 仅 local/focused 表面；不能提升 smoke。 |

## 影响

- 阻塞“整个测试系统健康”或“覆盖充分”的声明。
- 在依赖完整环境真正执行前，阻塞已拆分 airframe geometry 测试的行为保持验收。
- 阻塞 `weapon_guidance_realism` 的 smoke 提升。
- 虽然 damage-model oversized single-test-item 清理已完成，但仍不能把剩余
  literal/source-scan 文件视为完全精简。
- 后续 coverage 报告必须写明测量 root，并区分 Python、C++、smoke、focused
  和 full-suite 证据。

## 不能宣称

- 本 issue 不重开已验收的审计 runner、suite manifest 或结构拆分工作。
- 本 issue 不授权在测试系统治理子项目内重写 runtime/model 行为。
- 本 issue 不允许在没有替代证据时删除 literal-heavy 测试。
- 本 issue 不判断失败的 `weapon_guidance_realism` 期望到底正确还是错误；
  它只把失败状态保留为 gate。

## 假设

1. Airframe 拆分大概率保留了行为，但本地机器缺少证明这一点所需的 optional
   geometry 依赖。
2. Damage-model 剩余 source-scan 和 literal-heavy 检查可能需要数据 contract
   抽取，或明确记录为 focused/local guard。
3. `weapon_guidance_realism` 失败更像是当前空战 lethality/guidance 表面的
   行为或期望漂移，而不是 collection 问题。
4. Coverage 混乱来自把静态审计数、pytest collection、本地 Python coverage、
   C++ coverage 工具链和 smoke-suite 执行混在同一叙述中。

## 下一步门槛

1. **Airframe 行为门**：在依赖完整机器上运行已拆分的 `tests/tools`
   airframe geometry 检查，并记录通过/失败证据。
2. **Damage-model data-contract 门**：决定剩余 literal-heavy 与
   source-scan-heavy 检查应转为共享 data contract、helper，还是记录为
   focused/local guard。
3. **Weapon-guidance 行为门**：将失败的 `weapon_guidance_realism` 期望与当前
   runtime 行为对齐，包级运行转绿后再考虑 suite promotion。
4. **Coverage 门**：产出区分 Python 与 C++ 的 coverage 记录，写明测量 root、
   工具链前提，并避免跨表面过度声明。

## 关闭标准

当上述活跃 blocker 都有新的通过证据，或已经拆成更窄的领域 issue 且有明确验收门时，
本 issue 可从 active 转为 retained/closed。
