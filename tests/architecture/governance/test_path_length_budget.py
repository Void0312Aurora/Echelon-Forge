"""Ratchet the repository's long relative paths downward.

Windows caps most Win32 file APIs at MAX_PATH (260 characters) for the whole
absolute path. `core.longpaths=true` lifts that cap for git and for nothing
else, and the host's `LongPathsEnabled` registry switch only helps a process
whose manifest declares `longPathAware`. Unmanifested consumers of the working
tree still fail at the limit, and they fail by reporting the file as missing
rather than as too long, which is why the symptom is usually misdiagnosed.
`docs/engineering/workspace/worktree_and_path_policy.md` records the measured
case: `findstr` opens a tracked file from the main checkout at 245 absolute
characters and reports it as unopenable from a worktree at 268, with both
settings already enabled.

The budget is set on the *relative* path so it survives being checked out
anywhere reasonable. MAX_PATH counts the terminating null, so 259 characters are
usable. On the reference workstation the main checkout root is 35 characters and
`.worktrees/merge-check/` is 58, so a 200-character relative path lands at 258
absolute characters inside that linked worktree -- inside the limit, with the
worktree case protected rather than only the main checkout.

Two nearby budgets were rejected. 180 protects deeper checkouts but starts the
baseline at 342 entries. 224, the widest budget that still keeps the main
checkout under MAX_PATH, cuts the baseline to 97 only by grandfathering 143
files that are already unopenable from every worktree in the repository.

The gate is a subset ratchet against `path_length_baseline.json`. Shortening,
renaming, or deleting a baselined path is always allowed; introducing a new
over-budget path is not. Tightening the budget later means regenerating the
baseline at the lower threshold, never widening `PATH_LENGTH_BUDGET`.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_PATH = Path(__file__).with_name("path_length_baseline.json")
POLICY_DOC = REPO_ROOT / "docs/engineering/workspace/worktree_and_path_policy.md"
PATH_LENGTH_BUDGET = 200


def _baseline() -> dict:
  return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _tracked_paths() -> list[str]:
  # -z avoids git's quoting of non-ASCII names, which would inflate lengths.
  result = subprocess.run(
    ["git", "ls-files", "-z"],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
    encoding="utf-8",
  )
  return [path for path in result.stdout.split("\0") if path]


def _over_budget(paths: list[str]) -> set[str]:
  return {path for path in paths if len(path) > PATH_LENGTH_BUDGET}


def test_no_new_tracked_path_exceeds_the_length_budget() -> None:
  baseline = set(_baseline()["paths"])
  current = _over_budget(_tracked_paths())
  introduced = sorted(current - baseline)

  assert not introduced, (
    f"{len(introduced)} tracked path(s) exceed the {PATH_LENGTH_BUDGET}-character "
    "relative-path budget and are not in "
    f"{BASELINE_PATH.relative_to(REPO_ROOT).as_posix()}. Shorten the path rather "
    "than extending the baseline; see "
    f"{POLICY_DOC.relative_to(REPO_ROOT).as_posix()}:\n"
    + "\n".join(f"  {len(path)}  {path}" for path in introduced)
  )


def test_path_length_baseline_is_normalized() -> None:
  baseline = _baseline()
  paths = baseline["paths"]

  assert baseline["budget"] == PATH_LENGTH_BUDGET
  assert paths == sorted(paths)
  assert len(paths) == len(set(paths))
  assert all(len(path) > PATH_LENGTH_BUDGET for path in paths)


def test_the_path_length_budget_is_documented() -> None:
  policy = POLICY_DOC.read_text(encoding="utf-8")

  assert str(PATH_LENGTH_BUDGET) in policy
  assert BASELINE_PATH.name in policy
  assert "core.longpaths" in policy
