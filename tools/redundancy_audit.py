#!/usr/bin/env python3
import argparse
import hashlib
import os
from collections import defaultdict
from pathlib import Path


TEMP_DIR_PREFIXES = (
    "_tmp",
    "tmp",
    "_debug",
    "debug",
    "backup",
    "old",
    "smoke",
)


def iter_files(root: Path):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            yield Path(dirpath) / name


def dir_size_and_count(root: Path):
    total = 0
    count = 0
    for fp in iter_files(root):
        try:
            total += fp.stat().st_size
            count += 1
        except OSError:
            continue
    return total, count


def human_size(num):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}PB"


def collect_temp_like_dirs(root: Path):
    out = []
    for dirpath, dirnames, _ in os.walk(root):
        for dn in dirnames:
            low = dn.lower()
            if low.startswith(TEMP_DIR_PREFIXES) or any(p in low for p in TEMP_DIR_PREFIXES):
                out.append(Path(dirpath) / dn)
    return sorted(out)


def sha256_file(path: Path, block_size=1024 * 1024):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(block_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(roots, min_size):
    size_groups = defaultdict(list)
    for root in roots:
        for fp in iter_files(root):
            try:
                sz = fp.stat().st_size
            except OSError:
                continue
            if sz < min_size:
                continue
            size_groups[sz].append(fp)

    dup_hash_groups = defaultdict(list)
    for _, files in size_groups.items():
        if len(files) < 2:
            continue
        for fp in files:
            try:
                h = sha256_file(fp)
            except OSError:
                continue
            dup_hash_groups[h].append(fp)

    return {h: v for h, v in dup_hash_groups.items() if len(v) > 1}


def main():
    parser = argparse.ArgumentParser(description="Audit redundancy in workspace directories.")
    parser.add_argument(
        "--roots",
        nargs="+",
        default=["experiments", "tests", "tools", "scenarios", "datasets"],
        help="Directories to audit",
    )
    parser.add_argument(
        "--min_dup_size_mb",
        type=float,
        default=8.0,
        help="Only hash files >= this size for duplicate check",
    )
    args = parser.parse_args()

    roots = [Path(r).resolve() for r in args.roots if Path(r).exists()]
    if not roots:
        print("No valid roots found.")
        return

    print("=== Redundancy Audit Summary ===")
    total_size = 0
    total_files = 0
    for r in roots:
        sz, cnt = dir_size_and_count(r)
        total_size += sz
        total_files += cnt
        print(f"- {r.name:<12} files={cnt:>7} size={human_size(sz):>10}")
    print(f"- {'TOTAL':<12} files={total_files:>7} size={human_size(total_size):>10}")

    print("\n=== Temp/Debug-like Directories ===")
    temp_total = 0
    for r in roots:
        candidates = collect_temp_like_dirs(r)
        if not candidates:
            continue
        print(f"[{r.name}] {len(candidates)} candidates")
        for d in candidates[:50]:
            print(f"  {d}")
        if len(candidates) > 50:
            print(f"  ... ({len(candidates) - 50} more)")
        temp_total += len(candidates)
    if temp_total == 0:
        print("No temp/debug-like directories detected by naming pattern.")

    print("\n=== Exact Duplicate Files (Hash) ===")
    min_size_bytes = int(args.min_dup_size_mb * 1024 * 1024)
    dup = find_duplicates(roots, min_size=min_size_bytes)
    if not dup:
        print(f"No exact duplicate files >= {args.min_dup_size_mb} MB found.")
        return

    reclaimed = 0
    for h, files in sorted(dup.items(), key=lambda kv: len(kv[1]), reverse=True):
        try:
            size = files[0].stat().st_size
        except OSError:
            size = 0
        reclaimed += size * (len(files) - 1)
        print(f"hash={h[:12]}... count={len(files)} size_each={human_size(size)}")
        for fp in files:
            print(f"  {fp}")

    print(f"\nPotential reclaim (if dedup by hardlink/delete): {human_size(reclaimed)}")


if __name__ == "__main__":
    main()
