# 维护说明

`tools/maintenance/` 文件夹存放仓库清理、审计和本地维护辅助工具，这些工具不属于模型/运行时产品功能范围。

通用维护辅助工具：

- [cmo_env.sh](cmo_env.sh)
  - Linux/macOS 仓库本地环境引导与验证，针对 `.venv`、`CMO_BUILD_DIR` 和 `PYTHONPATH`。
- [cmo_env.ps1](cmo_env.ps1)
  - Windows/PowerShell 仓库本地环境引导与验证，针对 `.venv`、`CMO_BUILD_DIR`、`PYTHONPATH` 以及 `ef_py*.pyd` 工件。
- [cmo_env_validate_rl.py](cmo_env_validate_rl.py)
  - `cmo_env.sh validate-rl` 与 `cmo_env.ps1 validate-rl` 共用的 RL import 探针，
    两个 shell 因此报告相同的模块与相同的退出码。
- [docs_link.py](docs_link.py)
  - 文档链接审计、WP closure 审计和文档翻译批次共用的 Markdown 行内链接扫描器。
    扫描前会屏蔽代码围栏、HTML 注释和行内代码，使三个工具对同一文档给出相同的
    链接集合。
- [redundancy_audit.py](redundancy_audit.py)
  - 审计重复/临时性质的仓库内容。
- [cleanup_redundancy.py](cleanup_redundancy.py)
  - 预检或执行清理缓存/临时工件。
- [isolate_repro_workspace.sh](isolate_repro_workspace.sh)
  - 将选定的实验/数据集目录移开，以创建一个更小的复现工作空间。
- [translate_docs_batch.py](translate_docs_batch.py)
  - 审计中英文文档配对覆盖率，并通过兼容 OpenAI 的 API 批量翻译 Markdown 对等文件。
  - 通过在翻译前屏蔽 Markdown 链接目标并在翻译后恢复它们，来保持 Markdown 链接目标不变。
  - 将仓库工作空间绝对路径的文件链接重写为相对 Markdown 目标。
  - 生成并审计双语 cluster registry，使单边编辑后的 paired docs 可被漂移检查覆盖。
- [wp_doc_closure_audit.py](wp_doc_closure_audit.py)
  - 审计 simulation-architecture WP task/review closure，包括必需伴生文件、
    acceptance review 链接和 WP 作用域内 Markdown 链接健康度。
  - 输出只读清单或生成 closure 摘要供 closure subagent 使用，而不是让主
    实现路径手工重写 README 或 review index。
维护指南：

- 这里的脚本可以是 Shell 或 Python，但默认应面向工作空间且非破坏性。
- 维护的 Linux/macOS Shell 工作流应优先使用 `cmo_env.sh`，而非重复 `.venv` 和构建目录检测逻辑。
- 维护的 Windows 工作流应优先使用 `cmo_env.ps1`，而非假设 WSL、`.venv/bin/python` 或 Linux 扩展名 `.so` 的工件。
- 历史维护辅助工具应直接删除并在 `tools/README.md` 的退役登记中留一行（git 历史即归档），而非在此堆积。
- 文档翻译批次应优先使用 `translate_docs_batch.py`，而非临时一次性脚本，以保持文件配对和草稿注释行为的一致性。

推荐的 Linux/macOS 用法：

```bash
python -m pip install pytest numpy
cmake -S . -B build-workshop -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j2
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q tests/runtime/core/test_env_config.py
```

这与 CI 烟雾边界测试一致：安装小的烟雾依赖集，用 CMake 构建 `ef_core` / `ef_py`，然后使用 `cmo_env.sh` 暴露本地扩展。除非目标特别在于测试 scikit-build 可编辑安装行为，否则不要用 `pip install -e .` 替换此快速循环。

也支持直接脚本模式入口：

```bash
bash tools/maintenance/cmo_env.sh summary
bash tools/maintenance/cmo_env.sh validate
bash tools/maintenance/cmo_env.sh validate-rl
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/core/test_env_config.py
```

`validate` 有意只检查烟雾/运行时工作流需要的仓库虚拟环境与本地
`ef_py` 构建产物。运行会导入 RL 栈的回归测试前，请使用 `validate-rl`；它会导入
`ef_py`、`gymnasium`、`stable_baselines3` 和 `torch`，并报告被选中的模块位置。

推荐的 Windows/PowerShell 用法：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pytest numpy

cmake -S . -B build-local-win -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-local-win --target ef_core ef_py -j2

.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 validate-rl
.\tools\maintenance\cmo_env.ps1 summary
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\core\test_env_config.py
```

Windows 范围：

- PowerShell 辅助工具旨在用于本地开发烟雾测试、结构测试和聚焦的运行时回归测试。
- 它不定义本地工作站的 RL 训练能力；默认 `validate` 只检查构建/运行时烟雾前提。
  当某个聚焦回归会导入 RL 栈时，请在安装 `.[rl]` 或等价直接依赖后运行
  `validate-rl`。
- 它有意与 `cmo_env.sh` 并存运行，不应替代 Linux CI 工作流。

推荐的维护文档链接审计：

```bash
python3 tools/maintenance/document_link_audit.py
python3 tools/maintenance/document_link_audit.py --format json
```

默认命令检查仓库根中英文 README 与严格维护文档面。archive、scratch、results
和本地 review 文档不会作为扫描源，但维护页面指向保留 archive 的链接仍必须真实
可解析。使用 `--full-tree` 可检查上述排除源之外的全部共享 Markdown 文档。缺失
目标、逃出仓库的路径或本机绝对路径都会让命令以非零状态退出。

推荐的双语文档审计：

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
```

默认情况下，这个审计只检查“严格维护的双语表面”：入口/导航页、owner-local
工程标准、维护中的旧 standards、operations 指引、research 来源和稳定计划权威层，
而不是 `docs/` 下每一份历史任务长文。

如果你想有意检查更宽的共享文档树，请显式使用：

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/engineering/documentation/reference/bilingual_document_clusters.json \
  --full-tree
```

独立核对某轮实际修改的文档对后，只刷新这些记录，避免把无关的历史分歧整体
重置：

```bash
python3 tools/maintenance/translate_docs_batch.py clusters --root docs \
  --registry docs/engineering/documentation/reference/bilingual_document_clusters.json --write \
  --pair README --pair engineering/documentation/standards/document_lifecycle_policy
```

省略 `--pair` 会重建完整登记表。只有完成整个维护面双语审阅后才能这样做，否则
未经审阅的遗留分歧也会被写入新哈希并显示为已同步。

默认情况下，审计还会跳过仅在本地存在、通常不会进入共享远端的文档区域，包括：

- `docs/Archive/`
- `docs/**/archive/`
- `docs/**/temp/`

要明确包含它们，请使用：

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs --include-local-only
```

当前维护的 hash 比较会忽略文件开头的机器翻译草稿标记，并统一行尾风格，
因此单纯的 Windows `CRLF` checkout 噪音本身不应让整份注册表变成漂移。

针对一个活跃目录的推荐中译英回填：

```bash
python3 tools/maintenance/translate_docs_batch.py translate \
  --root docs/architecture/work/issues \
  --pattern '*.zh.md' \
  --source-lang zh \
  --target-lang en \
  --only-missing
```

归一化现有 Markdown 文件中的仓库内部链接：

```bash
python3 tools/maintenance/translate_docs_batch.py rewrite-links \
  --files docs/architecture/work/issues/*.md
```

分配或验收 closure lane 前，审计一个 WP closure package：

```bash
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP9
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP9 --json
```

当 error-level closure gap 应导致命令失败时使用 `--strict`。warning 应被视为
closure subagent 的工作项，而不是主实现流 blocker。

翻译所需的 API 环境变量：

- `DOCS_TRANSLATE_BASE_URL`
- `DOCS_TRANSLATE_MODEL`
- `DOCS_TRANSLATE_API_KEY`

从仓库本地的 `.env` 加载的支持回退名称：

- `BASE_URL`
- `MODEL`
- `API_KEY`
