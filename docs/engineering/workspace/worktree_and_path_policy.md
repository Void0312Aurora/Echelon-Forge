# Worktree and Path Policy

Language:
- English canonical: `worktree_and_path_policy.md`
- Chinese companion: [worktree_and_path_policy.zh.md](worktree_and_path_policy.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/workspace/worktree_and_path_policy.md`
Owner: `engineering`
Last verified: `2026-08-13`

Status: `2026-08-13` authoritative policy for linked-worktree placement,
worktree file ownership, and the repository-relative path-length budget.

This policy governs the shape of a checkout rather than its contents. It exists
because both failure modes it covers present as something else: a worktree whose
directory is owned by another principal fails as `fatal: detected dubious
ownership`, and a path past the Windows limit fails as "the file does not
exist". Neither symptom names its cause.

## Worktree Placement

Every linked worktree of this repository lives at `<repo>/.worktrees/<name>`.

```powershell
git -C D:\workshop\Research\Echelon-Forge worktree add .worktrees/<name> -b <branch>
```

One directory keeps the inventory discoverable, keeps every worktree on the same
volume as the main checkout, and keeps the added path prefix short and
predictable. `.worktrees/` is ignored by the main checkout, so a worktree never
appears as untracked residue in its parent.

Worktrees scattered across other parents are out of policy even when they work.
As of 2026-08-13 this repository had seven linked worktrees across three
parents, including one under `<repo>/.codex/worktrees/` and one under
`C:\Users\<user>\.codex\visualizations\<date>\<uuid>\`. The second is on a
different volume and adds a 101-character prefix, which by itself puts 419
tracked files past the Windows path limit.

`tools/maintenance/audit_worktrees.py` reports any worktree outside the main
root or `.worktrees/`. Genuine exceptions are passed explicitly with
`--allow-path`; the allowlist is empty by default so an exception has to be
argued each time it is used.

### Name Length Is Part of the Budget

The worktree name lands in front of every relative path in that checkout. Keep
it to roughly twelve characters. The arithmetic is in
[Path Length Budget](#path-length-budget); `merge-check` and `governance` fit,
`wp2-bilingual-contraction` does not.

## Never Create a Worktree From an Elevated Shell

`git worktree add` run from an elevated PowerShell creates the worktree
directory owned by `BUILTIN\Administrators` rather than by the invoking user.
Git's ownership check then refuses to operate on that directory from an ordinary
session:

```text
fatal: detected dubious ownership in repository at 'D:/.../.worktrees/governance'
'D:/.../.worktrees/governance' is owned by:
	BUILTIN/Administrators (S-1-5-32-544)
```

Four of the seven worktrees present on 2026-08-13 were in this state. The
trigger is the ownership of the worktree's own top-level directory: in all four
cases the `.git` pointer file inside the worktree and the main repository's
`.git/worktrees/<name>/` administrative directory were still owned by the user.
Check the directory first, and only widen the search if that one is clean.

The failure is not confined to git. Every tool that consults the file owner, and
every later process running as the ordinary user, inherits the same restriction,
so an elevated `git worktree add` reliably produces a checkout that only an
elevated shell can maintain.

Create worktrees from an ordinary shell. If an elevated shell is unavoidable for
some other reason, repair the ownership afterwards using
[Repairing Worktree Ownership](#repairing-worktree-ownership) before handing the
tree to normal tooling.

## Worktree Lifecycle

- A worktree is created for one branch and one piece of work.
- Its untracked file count stays at zero. Scratch files, generated reports, and
  probe scripts either get committed, get ignored repository-wide, or get
  written outside the source tree.
- Build output goes to a build directory outside the checkout, selected through
  `CMO_BUILD_DIR`. A worktree is not a build root: object files under a source
  tree defeat the untracked-residue check, and the deeper prefix makes the
  Windows path limit bite compiler temporaries first.
- When the branch merges or is abandoned, the worktree is removed:

```powershell
git -C D:\workshop\Research\Echelon-Forge worktree remove .worktrees/<name>
git -C D:\workshop\Research\Echelon-Forge worktree prune
```

A worktree left behind after its branch merges is not free. It keeps a full copy
of the tree on disk, it keeps appearing in `git worktree list`, and if it was
created from an elevated shell it keeps failing for everyone who tries to clean
it up.

## Path Length Budget

**A tracked repository-relative path must not exceed 200 characters.**

The budget is enforced as a ratchet by
`tests/architecture/governance/test_path_length_budget.py` against
`tests/architecture/governance/path_length_baseline.json`. Paths already over
budget are grandfathered in the baseline; new ones are rejected. Removing a
baselined path is always allowed, and pruning the baseline as paths shorten is
encouraged. The budget is never widened to admit a new file.

The budget sits on the relative path because that is the part the repository
controls. What actually fails is the absolute path, and the absolute path
depends on where the checkout lives:

| Checkout root | Prefix | Tracked files at or past 260 characters |
| --- | --- | --- |
| `D:\workshop\Research\Echelon-Forge\` | 35 | 97 |
| `...\.worktrees\governance\` | 57 | 224 |
| `...\.worktrees\merge-check\` | 58 | 232 |
| `...\.codex\worktrees\cuda-promotion\` | 67 | 294 |
| `...\.worktrees\wp2-bilingual-contraction\` | 72 | 321 |
| `C:\Users\<user>\.codex\visualizations\<date>\<uuid>\ground-worktree\` | 101 | 419 |

Measured 2026-08-13 over 3679 tracked files; the longest relative path is 267
characters, which is already past the limit before any prefix is added.

The Win32 limit is `MAX_PATH` = 260 including the terminating null, so 259
usable characters. A 200-character relative path therefore stays inside the
limit for any checkout root plus worktree name totalling 59 characters or fewer
— on the reference workstation, `<repo>\.worktrees\<name>\` with a name of about
twelve characters. That is the case the budget is sized for.

Two nearby budgets were considered and rejected. 180 protects deeper checkouts
but starts the baseline at 342 entries. 224, the widest budget that still
protects the main checkout, would cut the baseline to 97 only by grandfathering
files that are already unopenable from every worktree. 200 leaves a 240-entry
baseline, all of it dated evidence packets under `docs/systems/effects/`,
`docs/domains/air/`, and `docs/systems/weapons/`.

### Keeping New Paths Short

The baseline is almost entirely evidence packets whose directory names repeat
the packet name at three or four levels. When adding an evidence directory:

- do not repeat the parent directory's name in the child's name;
- do not repeat the packet date at more than one level;
- put the distinguishing token in the leaf file name, not in every ancestor.

## Why `core.longpaths` Is Not Enough

This repository sets `core.longpaths=true`, and the host has
`HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1`. Neither
setting makes long paths safe.

`core.longpaths` changes how git itself builds Win32 calls. It says nothing
about any other program. The registry switch only makes the OS *permit* long
paths for a process whose application manifest declares `longPathAware`;
processes without that manifest entry keep the 260-character behaviour whatever
the registry says. Most of the toolchain that touches a working tree — legacy
console utilities, older MSVC components, many PDF and archive tools — is not
manifested.

Measured on this repository with both settings already enabled, using a tracked
file whose relative path is 210 characters:

| Access path | Absolute length | Result |
| --- | --- | --- |
| `findstr` in the main checkout | 245 | opens the file |
| `findstr` in `.worktrees\merge-check` | 268 | `FINDSTR: cannot open <path>` |
| Python `open()` in `.worktrees\merge-check` | 268 | reads the file |

Same repository, same file, same commit. Python succeeds because CPython ships a
`longPathAware` manifest; `findstr` does not.

## Diagnosing a Long-Path Failure

The characteristic symptom is a tool reporting a file as missing, unreadable, or
"cannot open" when the file is plainly there. Work through this order:

1. Measure the absolute path. Anything at or past 260 characters is a suspect
   regardless of what the error says.
2. Retry from a shallower checkout. If the main checkout works and a worktree
   does not, the path length is the cause and nothing else needs investigating.
3. Retry the same file through a long-path-aware reader, for example
   `python -c "import sys; open(sys.argv[1],'rb').read()" <path>`. Success there
   plus failure in the original tool confirms the tool is not manifested.
4. Only then look for permissions, locking, or antivirus.

`\\?\`-prefixed paths bypass the limit for APIs that accept them, but most
command-line tools do not parse the prefix. Treat it as a diagnostic, not a fix.

## Repairing Worktree Ownership

Run from an **elevated** PowerShell. Replace `<name>` with the worktree
directory name and `<DOMAIN\user>` with the account that should own it.

```powershell
$repo = "D:\workshop\Research\Echelon-Forge"

# 1. Confirm what is actually mis-owned before changing anything.
(Get-Acl "$repo\.worktrees\<name>").Owner
(Get-Acl "$repo\.worktrees\<name>\.git").Owner
(Get-Acl "$repo\.git\worktrees\<name>").Owner

# 2. Reset the owner of whichever of the three is wrong, recursively.
icacls "$repo\.worktrees\<name>" /setowner "<DOMAIN\user>" /T /C
icacls "$repo\.git\worktrees\<name>" /setowner "<DOMAIN\user>" /T /C
```

`takeown /F "$repo\.worktrees\<name>" /R /D Y` is the alternative when the
target owner is the elevated user itself. Do not add `/A`: it assigns ownership
to the Administrators group, which is the state being repaired.

Verify from an **ordinary** shell — the elevated one will succeed either way:

```powershell
(Get-Acl "$repo\.worktrees\<name>").Owner
git -C "$repo\.worktrees\<name>" status --porcelain
```

### What Not To Do

```powershell
git config --global --add safe.directory "D:/workshop/Research/Echelon-Forge/.worktrees/<name>"
```

This silences git and changes nothing on disk. The directory stays owned by
another principal, every non-git tool keeps hitting the same wall, the
suppression is per-user so it does not travel, and it accumulates one stale
global entry per abandoned worktree. Use it only to read a tree you are about to
delete.

## Audit Commands

```powershell
# Worktree placement, status reachability, and untracked residue.
python tools/maintenance/audit_worktrees.py
python tools/maintenance/audit_worktrees.py --format json

# Relative-path budget ratchet.
python -m pytest tests/architecture/governance/test_path_length_budget.py
```

`audit_worktrees.py` is read-only: it reports and exits non-zero, and never
creates, moves, prunes, or repairs anything. Its status probe retries with
`git -c safe.directory=*` so that a mis-owned worktree is reported as a finding
instead of aborting the audit; the finding records what an ordinary session
sees.

## Reverification Triggers

Update this policy when the worktree inventory changes shape, when the
path-length baseline is regenerated at a different budget, when the repository's
`core.longpaths` or the host's long-path configuration changes, or when a new
class of tool is found to fail at the Windows limit.
