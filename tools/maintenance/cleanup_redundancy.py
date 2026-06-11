#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path


SAFE_DELETE_DIR_NAMES = {"__pycache__", ".pytest_cache"}
SAFE_DELETE_FILE_SUFFIXES = {".pyc", ".pyo", ".tmp", ".bak", "~"}
SAFE_TMP_PREFIXES = ("_tmp", "tmp", "_debug", "debug")


def should_delete_dir(path: Path, include_named_tmp_dirs: bool):
  name = path.name.lower()
  if name in SAFE_DELETE_DIR_NAMES:
    return True
  if include_named_tmp_dirs and name.startswith(SAFE_TMP_PREFIXES):
    return True
  return False


def should_delete_file(path: Path):
  name = path.name.lower()
  if name.endswith("~"):
    return True
  for suffix in SAFE_DELETE_FILE_SUFFIXES:
    if suffix == "~":
      continue
    if name.endswith(suffix):
      return True
  return False


def find_cleanup_targets(root: Path, include_named_tmp_dirs: bool):
  delete_dirs = []
  delete_files = []
  for p in root.rglob("*"):
    if p.is_dir() and should_delete_dir(p, include_named_tmp_dirs):
      delete_dirs.append(p)
    elif p.is_file() and should_delete_file(p):
      delete_files.append(p)
  return sorted(delete_dirs), sorted(delete_files)


def human_size(num):
  for unit in ["B", "KB", "MB", "GB", "TB"]:
    if num < 1024.0:
      return f"{num:.1f}{unit}"
    num /= 1024.0
  return f"{num:.1f}PB"


def estimate_bytes(paths):
  total = 0
  for p in paths:
    try:
      if p.is_file():
        total += p.stat().st_size
      elif p.is_dir():
        for fp in p.rglob("*"):
          if fp.is_file():
            total += fp.stat().st_size
    except OSError:
      continue
  return total


def main():
  parser = argparse.ArgumentParser(description="Safely cleanup redundant cache/temp artifacts.")
  parser.add_argument(
    "--roots",
    nargs="+",
    default=["experiments", "tests", "tools", "scenarios", "datasets"],
    help="Directories to clean",
  )
  parser.add_argument(
    "--include_named_tmp_dirs",
    action="store_true",
    help="Also delete dirs whose names start with tmp/_tmp/debug/_debug.",
  )
  parser.add_argument(
    "--apply",
    action="store_true",
    help="Apply cleanup. Without this flag, only prints dry-run plan.",
  )
  args = parser.parse_args()

  roots = [Path(r).resolve() for r in args.roots if Path(r).exists()]
  if not roots:
    print("No valid roots found.")
    return

  all_dirs = []
  all_files = []
  for root in roots:
    dirs, files = find_cleanup_targets(root, args.include_named_tmp_dirs)
    all_dirs.extend(dirs)
    all_files.extend(files)

  bytes_est = estimate_bytes(all_dirs + all_files)

  print("=== Cleanup Plan ===")
  print(f"dirs: {len(all_dirs)}")
  print(f"files: {len(all_files)}")
  print(f"estimated reclaim: {human_size(bytes_est)}")

  for p in all_dirs[:80]:
    print(f"DIR {p}")
  if len(all_dirs) > 80:
    print(f"... {len(all_dirs) - 80} more dirs")

  for p in all_files[:120]:
    print(f"FILE {p}")
  if len(all_files) > 120:
    print(f"... {len(all_files) - 120} more files")

  if not args.apply:
    print("\nDry-run only. Re-run with --apply to execute cleanup.")
    return

  removed = 0
  for p in all_files:
    try:
      p.unlink(missing_ok=True)
      removed += 1
    except OSError:
      pass

  # Remove deeper dirs first
  for p in sorted(all_dirs, key=lambda x: len(str(x)), reverse=True):
    try:
      shutil.rmtree(p, ignore_errors=True)
      removed += 1
    except OSError:
      pass

  print(f"\nCleanup complete. Removed entries: {removed}")


if __name__ == "__main__":
  main()
