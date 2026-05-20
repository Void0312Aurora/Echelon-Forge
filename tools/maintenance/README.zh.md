<!-- Machine-translated draft generated on 2026-05-18 from tools/maintenance/README.md. Review before treating this file as authoritative. -->

# 维护说明

`tools/maintenance/` 文件夹存放仓库清理、审计和本地维护辅助工具，这些工具不属于模型/运行时产品功能范围。

当前维护的辅助工具：

- [cmo_env.sh](cmo_env.sh)
  - Linux/macOS 仓库本地环境引导与验证，针对 `.venv`、`CMO_BUILD_DIR` 和 `PYTHONPATH`。
- [cmo_env.ps1](cmo_env.ps1)
  - Windows/PowerShell 仓库本地环境引导与验证，针对 `.venv`、`CMO_BUILD_DIR`、`PYTHONPATH` 以及 `ef_py*.pyd` 工件。
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

维护指南：

- 这里的脚本可以是 Shell 或 Python，但默认应面向工作空间且非破坏性。
- 维护的 Linux/macOS Shell 工作流应优先使用 `cmo_env.sh`，而非重复 `.venv` 和构建目录检测逻辑。
- 维护的 Windows 工作流应优先使用 `cmo_env.ps1`，而非假设 WSL、`.venv/bin/python` 或 Linux 扩展名 `.so` 的工件。
- 历史维护辅助工具应移至 `tools/archive/legacy_scripts/`，而非在此堆积。
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

推荐的双语文档审计：

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/standards/bilingual_document_clusters.json
```

默认情况下，这个审计只检查“严格维护的双语表面”
（入口/导航页、治理文档、manual、稳定计划权威层），而不是 `docs/`
下每一份历史任务长文。

如果你想有意检查更宽的共享文档树，请显式使用：

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/standards/bilingual_document_clusters.json \
  --full-tree
```

如果在一次大范围文档整理后结果看起来很嘈杂，先刷新注册表基线：

```bash
python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write
```

默认情况下，审计还会跳过仅在本地存在、通常不会进入共享远端的文档区域，包括：

- `docs/Archive/`
- `docs/**/archive/`
- `docs/temp/`
- `docs/plan/results/`
- `docs/plan/architecture/review/`

要明确包含它们，请使用：

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs --include-local-only
```

当前维护的 hash 比较会忽略文件开头的机器翻译草稿标记，并统一行尾风格，
因此单纯的 Windows `CRLF` checkout 噪音本身不应让整份注册表变成漂移。

针对一个活跃目录的推荐中译英回填：

```bash
python3 tools/maintenance/translate_docs_batch.py translate \
  --root docs/task/flight_dynamics \
  --pattern '*.zh.md' \
  --source-lang zh \
  --target-lang en \
  --only-missing
```

归一化现有 Markdown 文件中的仓库内部链接：

```bash
python3 tools/maintenance/translate_docs_batch.py rewrite-links \
  --files docs/task/flight_dynamics/program/*.md
```

翻译所需的 API 环境变量：

- `DOCS_TRANSLATE_BASE_URL`
- `DOCS_TRANSLATE_MODEL`
- `DOCS_TRANSLATE_API_KEY`

从仓库本地的 `.env` 加载的支持回退名称：

- `BASE_URL`
- `MODEL`
- `API_KEY`
