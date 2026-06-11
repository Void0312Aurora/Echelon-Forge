# A2 目标几何建模派发队列

状态：`2026-06-11` TG-P5-R1 complete / first dispatch queue。当前记录第一轮进展；本轮由 main thread 完成，
未派发 worker。

英文辅文：[missile_lethality_target_geometry_dispatch_queue_20260611.md](missile_lethality_target_geometry_dispatch_queue_20260611.md)。

## 第一轮建议

| Packet | Cluster | 建议 Owner | 目标 | 写入范围 | 验证 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| `TG-P1-R1` | `TG-P1` | main thread | 解析 F-16 glTF，输出 manifest 和尺度/轴向摘要 | `tools/geometry/airframe_geometry_review.py`; `review_packets/f16c_20260611/manifest.json`; `tests/tools/test_airframe_geometry_review.py` | JSON parse; registry/glTF path existence; public-dimension check; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P2-R1` | `TG-P2` | main thread | 基于 glTF 外包、位置规则和人工映射生成第一版外壳区域候选 | `review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json`; `top.svg`; `side.svg`; `front.svg`; focused tests | region schema; bounds check; SVG smoke; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P3-R1` | `TG-P3` | main thread | 读取现有 F-16 部件盒，绑定外壳区域并标出异常 | `component_binding_report_20260611.json`; `component_binding_report_20260611.csv`; focused tests | every component has region or `needs_review`; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P4-R1` | `TG-P4` | main thread | 生成第一版 HTML/SVG 审阅包 | `review_packets/f16c_20260611/scene.html`; `top.svg`; `side.svg`; `front.svg` | local file existence; no external network dependency; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P5-R1` | `TG-P5` | main thread | 对鼻向 4 m / 6 m 等测试点输出距离诊断 | `review_point_diagnostics_20260611.json`; `review_point_diagnostics_20260611.csv`; focused tests | nearest outer/component distance and candidate count present; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P6-R1` | `TG-P6` | main thread | 设计第一版精细几何代理候选 | `fine_geometry_proxy_design_20260611.zh.md`; `fine_geometry_proxy_design_20260611.md` | markdown links; `git diff --check` | pass as design draft; proxy JSON implementation remains queued |
| `TG-P6-R2` | `TG-P6` | main thread | 生成第一版精细几何代理 JSON 和叠加审阅 | `fine_geometry_proxy_candidate_20260611.json`; optional SVG overlay; focused tests | proxy schema check; distance sanity; visual smoke | queued after `TG-P6-R1` |

## Main Thread 合并检查

- 确认 worker 没有保存 token、signed URL 或 Authorization header。
- 确认生成物不声称真实 F-16 工程结构或真实武器杀伤率。
- 确认审阅包能解释 4 m 鼻向样例，而不是仅复述“非直接命中”。
- 确认父级 README 只由 main thread 同步状态。

## 暂缓项

- Runtime 近炸投影接入：等 `TG-P4`/`TG-P5`/`TG-P6` 验收后再决定。
- MQ-9 几何：等 F-16 工具链可复用后再展开。
- 结构解体、残骸和 Pk：另建后续子项目。
