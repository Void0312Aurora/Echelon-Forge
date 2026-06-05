# Environment Substrate G0-K Generator Catalog 任务簇

状态：`2026-06-06`，面向
[environment_substrate_g0_generator_catalog_20260605.zh.md](environment_substrate_g0_generator_catalog_20260605.zh.md)
的已接受有限 G0-K task-cluster plan。

## 边界决策

G0-K 可以定义并实现 generator request contracts、tile/seed partitioning、
catalog admission、deterministic fixture output 与 validation gates，范围限制在
shared Python environment-substrate package。它不得接入 runtime projection、编辑 C++
runtime、新增 scenarios，或声明 movement、LOS、cover、fires、damage、combat、
weather simulation、hydrodynamics、hydrology effects 或 dynamic environment
mutation。

## 有限任务簇

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `G0-K-A Request/Tiling Preflight` | Huygens read-only diagnostics | inherited parent / xhigh | 检查 generator/compiler surfaces，并定义 deterministic request、tile、seed 与 provenance contract requirements。 | none；仅 diagnostics packet | 不编辑、不写 generator code、不做 scenario/runtime integration、不做 derived products。 | worker packet 引用 inspected files，并列出 request fields、seed/tile rules、provenance、rejected shortcuts 与 implementation blockers。 | packet 返回 `pass`。 | 可与 G0-K-B/C 并行；依赖 accepted G0-J。 | 1 | pass |
| `G0-K-B Catalog Admission Preflight` | Pascal read-only diagnostics | inherited parent / xhigh | 为 terrain、buildings、vegetation、infrastructure、tactical areas、atmosphere/weather、wind、maritime 与 hydrology objects 定义 generic catalog descriptor/admission rules。 | none；仅 diagnostics packet | 不把 road/forest/building/village hardcode 成 schema root；不声明 runtime；不编辑。 | worker packet 将 catalog examples 映射到 branch/component/layer requirements 与 fail-closed admission rules。 | packet 返回 `pass`。 | 可与 G0-K-A/C 并行；依赖 accepted G0-J。 | 1 | pass |
| `G0-K-C Determinism And Validator Preflight` | Carson read-only diagnostics | inherited parent / xhigh | 定义 implementation 前需要的 focused tests、fixture determinism gates 与 validator failures。 | none；仅 diagnostics packet | 不实现、不接 runtime projection；不提交 generated fixture artifact。 | worker packet 命名 test files、assertions、validation reason codes 与 unstable randomness/provenance failure cases。 | packet 返回 `pass`。 | 可与 G0-K-A/B 并行；依赖 accepted G0-J。 | 1 | pass |
| `G0-K-D Integration Map` | main thread integration | n/a | 将 A/B/C packets 整合为有限 G0-K implementation plan。 | `docs/task/ground/environment_substrate_g0_architecture/*.md`、ground 父 README/progress/queue docs | 不做 runtime projection、C++ runtime、scenarios 或 derived products。 | 本地 review packets，并对 touched docs 跑 `git diff --check`。 | implementation write set 已命名，residuals 保持。 | G0-K-A/B/C 返回后串行。 | 1 | pass |
| `G0-K-E1 Request And Tile Contract` | main thread implementation | n/a | 实现 deterministic generator request、evidence refs、tile scheme、canonical bytes 与 seed derivation。 | `python/scenario/environment_substrate/generator.py`、`python/scenario/environment_substrate/__init__.py`、focused tests | 不复用 scenario compiler，不做 runtime projection，不使用 ambient randomness。 | request validation 与 deterministic output focused pytest。 | request/tile contract 使用 stable reason codes 验证并 fail closed。 | 依赖 G0-K-D。 | 1 | pass |
| `G0-K-E2 Catalog Admission Contract` | main thread implementation | n/a | 实现 catalog descriptors、catalog admission validation 与 default descriptor fixtures。 | `python/scenario/environment_substrate/catalog.py`、`python/scenario/environment_substrate/__init__.py`、focused tests | 不把 feature label 变成 schema root，不从 label 推导 runtime behavior。 | catalog refs、required components、branch/layer mismatch 与 held claims focused pytest。 | catalog admission 使用 stable reason codes 拒绝 invalid descriptors 与 generated manifests。 | 与 E1 文件上可并行，测试中串行集成。 | 1 | pass |
| `G0-K-E3 Deterministic Manifest Fixture` | main thread implementation | n/a | 从 request 加 catalog descriptors 构建 deterministic in-memory generated manifest fixture。 | `python/scenario/environment_substrate/generator.py`、`tests/scenario/test_environment_substrate_generator_catalog.py` | 不提交 generated data artifact，不输出 runtime setup payload。 | focused pytest 加现有 G0-J regressions。 | 同一 request 产生 byte-identical manifest metadata；不同 seed 改变 generated output 但保留 lineage。 | 依赖 E1/E2。 | 1 | pass |
| `G0-K-F Documentation And Acceptance` | main thread integration | n/a | 记录 G0-K implementation acceptance 并同步父级状态。 | G0 package docs 加 ground 父 README/progress/queue docs | 没有 maintained replacement 前不 archive；不释放 G0-L/G0-M。 | focused pytest 与 `git diff --check`。 | G0-K 只接受 Python generator/catalog contract；历史 G0-L/G0-M residuals 已由 G0 closure superseded。 | E1/E2/E3 验证后串行。 | 1 | accepted |

## 派发规则

- 只复用现有 agents；不得创建新的会话线程。
- 每个 worker packet 必须精确映射到一个 G0-K-A/B/C cluster。
- diagnostics workers 只读，不得编辑、stage、commit 或重排格式。
- Implementation write set 限于
  `python/scenario/environment_substrate/catalog.py`、
  `python/scenario/environment_substrate/generator.py`、
  `python/scenario/environment_substrate/__init__.py`、
  `tests/scenario/test_environment_substrate_generator_catalog.py` 与 status docs。
- 不把同一 normative table 拆给多个 worker。
- generator/catalog contracts 必须与 G0-L runtime projection、G0-M derived
  products 分离。
- 当前 `WorldZoneDefinition` projection 只作为 compatibility evidence。
- 保持 G0-J 是已接受 static contract input；不得把它改回 G1。

## Worker Packet 要求

每个 worker 必须返回：

```md
status: pass | partial | blocked | failed
touched files: none expected
files inspected:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

packet 还必须列出 rejected alternatives 与 explicit held capability claims。

## 验证计划

本 dispatch 的文档验证：

```bash
git diff --check -- docs/task/ground/environment_substrate_g0_architecture docs/task/ground/README.md docs/task/ground/README.zh.md docs/task/ground/ground_current_progress_20260524.md docs/task/ground/ground_current_progress_20260524.zh.md docs/task/ground/ground_subagent_dispatch_queue_20260521.md docs/task/ground/ground_subagent_dispatch_queue_20260521.zh.md
```

当前 G0-K focused validation 加 G0-J contract regression：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_manifest.py tests/scenario/test_environment_substrate_projection.py tests/scenario/test_environment_substrate_generator_catalog.py
# 22 passed
```

## 验收标准

G0-K implementation 只有因为以下条件成立才被接受：

- G0-K-A/B/C packet requirements 已集成；
- request/tile/seed/provenance contract 可验证并 fail closed；
- catalog descriptor/admission rules 拒绝 feature-label schema roots；
- generated fixture output deterministic 且只存在于内存；
- implementation write scope 有限，并与 runtime projection 分离；
- movement、LOS、cover、fires、damage、combat、weather simulation、hydrodynamics、
  hydrology effects 与 dynamic mutation claims 全部继续 held。

## Residual Map

- G0-K accepted implementation 仅限 Python request/tile/catalog contracts 与
  deterministic fixture generation。
- G0-K 历史 residual 中的 G0-L 已由 accepted G0-L projection setup plus compiler
  data ingestion 取代；runtime setup application 继续 held。
- G0-K 历史 residual 中的 G0-M 已由 accepted metadata-only derived products
  取代；runtime consumers 继续 held。
- Ground route movement 仍走单独 G6-D3/G6-F release path。
