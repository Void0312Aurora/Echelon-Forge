# Worktree 与路径策略

语言：
- 英文规范页：[worktree_and_path_policy.md](worktree_and_path_policy.md)
- 中文配套：`worktree_and_path_policy.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/workspace/worktree_and_path_policy.md`
Owner: `engineering`
Last verified: `2026-08-13`

Status: `2026-08-13` 链接 worktree 放置、worktree 文件属主与仓库相对路径长度预算的
权威策略。

本策略管的是检出的形状而不是内容。之所以需要它，是因为它覆盖的两类故障都以别的
面貌出现：目录属主不对的 worktree 报的是 `fatal: detected dubious ownership`，
而超过 Windows 长度上限的路径报的是"文件不存在"。两个症状都没有指向真正的原因。

## Worktree 放置

本仓库的每棵链接 worktree 都放在 `<repo>/.worktrees/<name>`。

```powershell
git -C D:\workshop\Research\Echelon-Forge worktree add .worktrees/<name> -b <branch>
```

集中在一个目录下可以让清单可发现、让所有 worktree 与主检出同卷、并让附加的路径
前缀既短又可预测。`.worktrees/` 已被主检出忽略，因此 worktree 不会在父仓库里表现为
未跟踪残留。

散落在其他父目录下的 worktree 即使能用也属于越界。截至 2026-08-13，本仓库有 7 棵
链接 worktree 分布在 3 个父目录，其中一棵位于 `<repo>/.codex/worktrees/`，另一棵位于
`C:\Users\<user>\.codex\visualizations\<date>\<uuid>\`。后者不但跨卷，还带来 101 字符
前缀——仅此一项就让 419 个已跟踪文件越过 Windows 路径上限。

`tools/maintenance/audit_worktrees.py` 会报出任何不在主仓库根或 `.worktrees/` 下的
worktree。真正的例外用 `--allow-path` 显式传入；白名单默认为空，因此每次使用例外都
必须被论证。

### 名字长度也是预算的一部分

worktree 名字会加在该检出中每一条相对路径之前，请控制在 12 个字符左右。计算方式见
[路径长度预算](#路径长度预算)；`merge-check` 和 `governance` 合格，
`wp2-bilingual-contraction` 不合格。

## 不要在提权 shell 里创建 worktree

在提权 PowerShell 中执行 `git worktree add`，创建出的 worktree 目录属主是
`BUILTIN\Administrators` 而不是调用者本人。此后 git 的属主检查会拒绝在普通会话中
操作该目录：

```text
fatal: detected dubious ownership in repository at 'D:/.../.worktrees/governance'
'D:/.../.worktrees/governance' is owned by:
	BUILTIN/Administrators (S-1-5-32-544)
```

2026-08-13 存在的 7 棵 worktree 中有 4 棵处于该状态。触发点是 worktree 自身顶层目录的
属主：这 4 例中，worktree 内的 `.git` 指针文件与主仓库的 `.git/worktrees/<name>/`
管理目录属主都仍是当前用户。先查目录，只有在目录干净时才扩大排查范围。

故障不止影响 git。任何会查看文件属主的工具、以及之后以普通用户身份运行的每个进程，
都会继承同样的限制；所以提权执行的 `git worktree add` 必然产出一棵只有提权 shell 才
维护得了的检出。

请在普通 shell 中创建 worktree。若因其他原因不得不使用提权 shell，请在把这棵树交给
常规工具之前，按[修复 worktree 属主](#修复-worktree-属主)先修好属主。

## Worktree 生命周期

- 一棵 worktree 只服务一个分支、一件事。
- 其未跟踪文件数保持为 0。抓痕文件、生成的报告、探针脚本，要么提交、要么在全仓
  ignore、要么写到源树之外。
- 构建产物写到检出之外的构建目录，通过 `CMO_BUILD_DIR` 指定。worktree 不是构建根：
  源树下的目标文件会让未跟踪残留检查失效，而更深的前缀会让编译器临时文件率先撞上
  Windows 路径上限。
- 分支合并或废弃后，移除 worktree：

```powershell
git -C D:\workshop\Research\Echelon-Forge worktree remove .worktrees/<name>
git -C D:\workshop\Research\Echelon-Forge worktree prune
```

分支合并后仍留着的 worktree 并不免费：它在磁盘上保留一份完整的树、持续出现在
`git worktree list` 中；如果它是提权创建的，还会对每个试图清理它的人持续报错。

## 路径长度预算

**已跟踪的仓库相对路径不得超过 200 字符。**

该预算由 `tests/architecture/governance/test_path_length_budget.py` 以棘轮方式针对
`tests/architecture/governance/path_length_baseline.json` 执行。已超限的路径在基线中
获得豁免，新增的则被拒绝。从基线中移除条目永远允许，路径缩短后主动裁剪基线值得
鼓励。预算不会为了容纳新文件而放宽。

预算落在相对路径上，因为那是仓库能控制的部分。真正失败的是绝对路径，而绝对路径
取决于检出位置：

| 检出根 | 前缀长度 | 绝对路径 ≥260 的已跟踪文件数 |
| --- | --- | --- |
| `D:\workshop\Research\Echelon-Forge\` | 35 | 97 |
| `...\.worktrees\governance\` | 57 | 224 |
| `...\.worktrees\merge-check\` | 58 | 232 |
| `...\.codex\worktrees\cuda-promotion\` | 67 | 294 |
| `...\.worktrees\wp2-bilingual-contraction\` | 72 | 321 |
| `C:\Users\<user>\.codex\visualizations\<date>\<uuid>\ground-worktree\` | 101 | 419 |

2026-08-13 对 3679 个已跟踪文件实测；最长相对路径为 267 字符——在加任何前缀之前就
已越限。

Win32 上限 `MAX_PATH` = 260 且包含结尾的 null，即可用 259 字符。因此 200 字符的相对
路径，在"检出根 + worktree 名"合计不超过 59 字符的任何位置都仍在限内——在参考工作站
上即 `<repo>\.worktrees\<name>\` 且名字约 12 字符。这正是该预算所针对的场景。

另外两个候选预算被否决。180 能保护更深的检出，但基线一上来就是 342 条。224 是仍能
保住主检出的最宽预算，它把基线降到 97 条，靠的却是豁免那些在本仓库任何 worktree 下
都已经打不开的文件。200 留下 240 条基线，全部是 `docs/systems/effects/`、
`docs/domains/air/`、`docs/systems/weapons/` 下带日期的证据包。

### 让新路径保持短

基线几乎全是证据包，其目录名在三到四层上重复了包名。新增证据目录时：

- 不要在子目录名里重复父目录名；
- 不要在多于一层的位置重复包日期；
- 把区分性的词放在叶子文件名里，而不是每一级祖先目录里。

## 为什么 `core.longpaths` 不够

本仓库设置了 `core.longpaths=true`，宿主也设置了
`HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1`。这两项都
不能让长路径变安全。

`core.longpaths` 改变的是 git 自己如何构造 Win32 调用，它对其他任何程序不作任何
承诺。注册表开关只是让操作系统**允许**长路径给那些在应用程序清单（manifest）中声明
了 `longPathAware` 的进程；没有该清单项的进程，无论注册表怎么设，仍是 260 字符行为。
接触工作树的工具链里大多数——老式控制台工具、较旧的 MSVC 组件、许多 PDF 与压缩
工具——都没有该清单声明。

在两项设置均已开启的前提下，用一个相对路径 210 字符的已跟踪文件实测：

| 访问方式 | 绝对路径长度 | 结果 |
| --- | --- | --- |
| 主检出下的 `findstr` | 245 | 正常打开 |
| `.worktrees\merge-check` 下的 `findstr` | 268 | `FINDSTR: 无法打开 <path>` |
| `.worktrees\merge-check` 下的 Python `open()` | 268 | 正常读取 |

同一仓库、同一文件、同一提交。Python 能成功是因为 CPython 自带 `longPathAware`
清单，而 `findstr` 没有。

## 诊断长路径故障

典型症状是：文件明明在，工具却报告它缺失、不可读或"无法打开"。按以下顺序排查：

1. 量一下绝对路径长度。达到或超过 260 就是嫌疑对象，不管报错说的是什么。
2. 换一个更浅的检出重试。若主检出能行而 worktree 不行，原因就是路径长度，无需再查。
3. 用长路径感知的读取器重试同一文件，例如
   `python -c "import sys; open(sys.argv[1],'rb').read()" <path>`。它成功而原工具失败，
   即可确认原工具没有该清单声明。
4. 到这一步才去查权限、文件锁与杀毒软件。

`\\?\` 前缀路径能让接受它的 API 绕过上限，但多数命令行工具并不解析该前缀。把它当作
诊断手段，不要当作修复方案。

## 修复 worktree 属主

在**提权** PowerShell 中执行。把 `<name>` 换成 worktree 目录名，把 `<DOMAIN\user>`
换成应当拥有它的账户。

```powershell
$repo = "D:\workshop\Research\Echelon-Forge"

# 1. 改动之前先确认到底哪一处属主不对。
(Get-Acl "$repo\.worktrees\<name>").Owner
(Get-Acl "$repo\.worktrees\<name>\.git").Owner
(Get-Acl "$repo\.git\worktrees\<name>").Owner

# 2. 对三者中错误的那个递归重设属主。
icacls "$repo\.worktrees\<name>" /setowner "<DOMAIN\user>" /T /C
icacls "$repo\.git\worktrees\<name>" /setowner "<DOMAIN\user>" /T /C
```

当目标属主就是提权用户本人时，也可以用
`takeown /F "$repo\.worktrees\<name>" /R /D Y`。不要加 `/A`：它会把属主设成
Administrators 组，而那正是要修复的状态。

在**普通** shell 中验证——提权 shell 无论如何都会成功，验不出问题：

```powershell
(Get-Acl "$repo\.worktrees\<name>").Owner
git -C "$repo\.worktrees\<name>" status --porcelain
```

### 不要这样做

```powershell
git config --global --add safe.directory "D:/workshop/Research/Echelon-Forge/.worktrees/<name>"
```

这只让 git 闭嘴，磁盘上什么都没变。目录属主仍属于别的主体，所有非 git 工具照撞同一
堵墙；这条抑制是按用户生效的，不会随仓库传播；而且每废弃一棵 worktree 就会在全局
配置里积一条陈旧条目。只有在你即将删除某棵树、仅需读一下它时才用它。

## 审计命令

```powershell
# worktree 位置、status 可达性与未跟踪残留。
python tools/maintenance/audit_worktrees.py
python tools/maintenance/audit_worktrees.py --format json

# 相对路径预算棘轮。
python -m pytest tests/architecture/governance/test_path_length_budget.py
```

`audit_worktrees.py` 是只读的：它只报告并以非零退出，绝不创建、移动、prune 或修复
任何东西。它的 status 探测会用 `git -c safe.directory=*` 重试一次，好让属主异常的
worktree 被记为 finding 而不是中断整个审计；finding 中记录的是普通会话真正看到的
报错。

## 复核触发条件

worktree 清单形态变化、路径长度基线以不同预算重新生成、仓库 `core.longpaths` 或宿主
长路径配置变化、或发现新一类工具在 Windows 上限处失败时，更新本策略。
