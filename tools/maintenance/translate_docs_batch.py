#!/usr/bin/env python3
"""Audit and batch-translate Markdown docs with an OpenAI-compatible API."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib import error, request

try:
  from tools.maintenance.docs_link import MarkdownLink, sub_markdown_links
  from tools.maintenance.document_scope import (
    classify_document,
    filter_paths,
    is_local_only_doc,
    is_strict_bilingual_doc,
  )
except ModuleNotFoundError:  # Direct script execution from tools/maintenance.
  from docs_link import MarkdownLink, sub_markdown_links
  from document_scope import (
    classify_document,
    filter_paths,
    is_local_only_doc,
    is_strict_bilingual_doc,
  )


DEFAULT_BASE_URL_ENV = "DOCS_TRANSLATE_BASE_URL"
DEFAULT_MODEL_ENV = "DOCS_TRANSLATE_MODEL"
DEFAULT_API_KEY_ENV = "DOCS_TRANSLATE_API_KEY"
FALLBACK_BASE_URL_ENVS = ("BASE_URL",)
FALLBACK_MODEL_ENVS = ("MODEL",)
FALLBACK_API_KEY_ENVS = ("API_KEY",)
DEFAULT_ENDPOINT = "/chat/completions"
DEFAULT_CLUSTER_REGISTRY = Path("docs/engineering/documentation/reference/bilingual_document_clusters.json")
LANGUAGE_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
LANGUAGE_LATIN_RE = re.compile(r"[A-Za-z]")
LEADING_DRAFT_NOTE_RE = re.compile(
  r"^\s*<!--\s*(?:Machine-translated draft|机器翻译草稿).*?-->\s*",
  re.DOTALL,
)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
FENCED_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
URL_RE = re.compile(r"https?://\S+")
WINDOWS_POSIX_ABS_RE = re.compile(r"^/[A-Za-z]:/")
DEFAULT_WORKSPACE_ROOT = "/home/void0312/Workshop/CMO"


@dataclass(frozen=True)
class TranslationTask:
  source: Path
  target: Path


def has_lang_suffix(path: Path, lang: str) -> bool:
  return path.name.endswith(f".{lang}.md")


def plain_from_lang_suffix(path: Path, lang: str) -> Path:
  suffix = f".{lang}.md"
  if not path.name.endswith(suffix):
    raise ValueError(f"Expected a {suffix} file, got: {path}")
  return path.with_name(path.name[: -len(suffix)] + ".md")


def suffixed_peer(path: Path, lang: str) -> Path:
  if has_lang_suffix(path, "zh") or has_lang_suffix(path, "en") or not path.name.endswith(".md"):
    raise ValueError(f"Expected a canonical .md file, got: {path}")
  return path.with_name(f"{path.stem}.{lang}.md")


def load_dotenv(path: Path) -> None:
  if not path.exists():
    return
  for raw_line in path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
      continue
    if value and value[0] == value[-1] and value[0] in {"'", '"'}:
      value = value[1:-1]
    os.environ.setdefault(key, value)


def env_first(names: tuple[str, ...]) -> str | None:
  for name in names:
    value = os.environ.get(name)
    if value:
      return value
  return None


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Audit bilingual coverage and translate Markdown docs in batches.",
  )
  subparsers = parser.add_subparsers(dest="command", required=True)

  audit = subparsers.add_parser("audit", help="Audit English/Chinese doc pairing coverage.")
  audit.add_argument("--root", default="docs", help="Root directory to scan.")
  audit.add_argument(
    "--show-missing",
    choices=("en", "zh", "all", "none"),
    default="all",
    help="Which missing peer lists to print.",
  )
  audit.add_argument(
    "--include-local-only",
    action="store_true",
    help="Include local-only or typically ignored documentation directories in the audit.",
  )
  audit.add_argument(
    "--registry",
    default=str(DEFAULT_CLUSTER_REGISTRY),
    help="Optional bilingual cluster registry JSON to compare against.",
  )
  audit.add_argument(
    "--full-tree",
    action="store_true",
    help="Audit the full shared docs tree instead of only the strict maintained bilingual surface.",
  )

  translate = subparsers.add_parser("translate", help="Translate Markdown docs into peer files.")
  translate.add_argument("--files", nargs="+", help="Explicit source files to translate.")
  translate.add_argument("--root", help="Directory to scan for source files.")
  translate.add_argument(
    "--pattern",
    help="Glob pattern for --root scans. Defaults to '*.zh.md' for zh->en and '*.md' for en->zh.",
  )
  translate.add_argument(
    "--include-local-only",
    action="store_true",
    help="Include local-only or typically ignored documentation directories when scanning by --root.",
  )
  translate.add_argument("--source-lang", choices=("en", "zh"), required=True)
  translate.add_argument("--target-lang", choices=("en", "zh"), required=True)
  translate.add_argument(
    "--only-missing",
    action="store_true",
    help="Skip files whose target peer already exists.",
  )
  translate.add_argument(
    "--force",
    action="store_true",
    help="Overwrite target files if they already exist.",
  )
  translate.add_argument(
    "--dry-run",
    action="store_true",
    help="Print planned work without writing files.",
  )
  translate.add_argument(
    "--chunk-chars",
    type=int,
    default=12000,
    help="Approximate maximum source characters per API chunk.",
  )
  translate.add_argument(
    "--sleep-seconds",
    type=float,
    default=0.0,
    help="Optional delay between API calls.",
  )
  translate.add_argument("--base-url", help=f"API base URL. Defaults to ${DEFAULT_BASE_URL_ENV}.")
  translate.add_argument("--model", help=f"Model id. Defaults to ${DEFAULT_MODEL_ENV}.")
  translate.add_argument("--api-key", help=f"API key. Defaults to ${DEFAULT_API_KEY_ENV}.")
  translate.add_argument(
    "--no-draft-note",
    dest="add_draft_note",
    action="store_false",
    help="Do not prepend the machine-translation draft comment.",
  )
  translate.set_defaults(add_draft_note=True)

  clusters = subparsers.add_parser(
    "clusters",
    help="Generate or audit the bilingual cluster registry JSON.",
  )
  clusters.add_argument("--root", default="docs", help="Root directory to scan.")
  clusters.add_argument(
    "--include-local-only",
    action="store_true",
    help="Include local-only or typically ignored documentation directories.",
  )
  clusters.add_argument(
    "--registry",
    default=str(DEFAULT_CLUSTER_REGISTRY),
    help="Registry JSON path to read or write.",
  )
  clusters.add_argument(
    "--write",
    action="store_true",
    help="Write the registry file after recomputing pairs.",
  )
  clusters.add_argument(
    "--dry-run",
    action="store_true",
    help="Show the registry path without writing changes.",
  )
  clusters.add_argument(
    "--full-tree",
    action="store_true",
    help="Build the registry from the full shared docs tree instead of only the strict maintained bilingual surface.",
  )
  clusters.add_argument(
    "--pair",
    dest="pair_ids",
    action="append",
    default=[],
    help=(
      "Refresh only the named pair_id while preserving every unselected registry "
      "entry. Repeat for multiple reviewed pairs."
    ),
  )

  rewrite = subparsers.add_parser(
    "rewrite-links",
    help="Rewrite workspace-absolute Markdown links into repo-relative links.",
  )
  rewrite.add_argument("--files", nargs="+", required=True, help="Markdown files to rewrite.")
  rewrite.add_argument(
    "--workspace-root",
    default=DEFAULT_WORKSPACE_ROOT,
    help="Workspace root prefix to rewrite out of Markdown links.",
  )
  rewrite.add_argument(
    "--dry-run",
    action="store_true",
    help="Print target files without writing changes.",
  )

  return parser.parse_args()


def map_target_path(path: Path, source_lang: str, target_lang: str) -> Path:
  if source_lang == target_lang:
    raise ValueError("source-lang and target-lang must differ")
  if source_lang == "zh" and target_lang == "en":
    if has_lang_suffix(path, "zh"):
      return plain_from_lang_suffix(path, "zh")
    if has_lang_suffix(path, "en"):
      raise ValueError(f"Expected a Chinese source, got an English companion: {path}")
    return suffixed_peer(path, "en")
  if source_lang == "en" and target_lang == "zh":
    if has_lang_suffix(path, "en"):
      return plain_from_lang_suffix(path, "en")
    if has_lang_suffix(path, "zh"):
      raise ValueError(f"Expected an English source, got a Chinese companion: {path}")
    return suffixed_peer(path, "zh")
  raise ValueError(f"Unsupported language pair: {source_lang}->{target_lang}")


def iter_markdown(root: Path) -> Iterable[Path]:
  return sorted(p for p in root.rglob("*.md") if p.is_file())


def classify_markdown_language(path: Path) -> str:
  text = normalize_for_language_detection(
    path.read_text(encoding="utf-8", errors="ignore")[:12000]
  )
  cjk = len(LANGUAGE_CJK_RE.findall(text))
  latin = len(LANGUAGE_LATIN_RE.findall(text))
  if cjk == 0 and latin == 0:
    return "en"
  if cjk == 0:
    return "en"
  if latin == 0:
    return "zh"
  return "zh" if cjk / max(latin, 1) >= 0.12 else "en"


def strip_leading_draft_notes(text: str) -> str:
  cleaned = text
  while True:
    updated = LEADING_DRAFT_NOTE_RE.sub("", cleaned, count=1)
    if updated == cleaned:
      return cleaned
    cleaned = updated


def normalize_doc_for_cluster_hash(text: str) -> str:
  cleaned = strip_leading_draft_notes(text)
  cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
  return cleaned


def unwrap_outer_markdown_fence(text: str) -> str:
  stripped = text.strip()
  lines = stripped.splitlines()
  if len(lines) < 2:
    return text

  opener = lines[0].strip().lower()
  if opener not in {"```markdown", "```md"}:
    return text
  if lines[-1].strip() != "```":
    return text

  fence_lines = [index for index, line in enumerate(lines) if line.strip().startswith("```")]
  if fence_lines != [0, len(lines) - 1]:
    return text

  inner = "\n".join(lines[1:-1]).strip("\n")
  return inner + "\n"


def normalize_translation_artifacts(text: str) -> str:
  cleaned = strip_leading_draft_notes(text)
  cleaned = unwrap_outer_markdown_fence(cleaned)
  cleaned = strip_leading_draft_notes(cleaned)
  return cleaned.strip() + "\n"


def normalize_for_language_detection(text: str) -> str:
  cleaned = strip_leading_draft_notes(text)
  cleaned = HTML_COMMENT_RE.sub(" ", cleaned)
  cleaned = FENCED_CODE_BLOCK_RE.sub(" ", cleaned)
  cleaned = INLINE_CODE_RE.sub(" ", cleaned)
  cleaned = URL_RE.sub(" ", cleaned)
  cleaned = sub_markdown_links(cleaned, lambda link: link.text)
  return cleaned


def expected_missing_peer(path: Path, missing_lang: str) -> Path:
  if missing_lang == "en":
    if has_lang_suffix(path, "zh"):
      return plain_from_lang_suffix(path, "zh")
    return suffixed_peer(path, "en")
  if missing_lang == "zh":
    if has_lang_suffix(path, "en"):
      return plain_from_lang_suffix(path, "en")
    return suffixed_peer(path, "zh")
  raise ValueError(f"Unsupported missing language: {missing_lang}")


def audit_tree(
  root: Path,
  show_missing: str,
  include_local_only: bool,
  registry_path: Path | None = None,
  *,
  full_tree: bool = False,
) -> int:
  files = filter_paths(
    iter_markdown(root),
    include_local_only=include_local_only,
    root=root,
    strict_bilingual_only=not full_tree,
  )
  zh_companions = [p for p in files if has_lang_suffix(p, "zh")]
  en_companions = [p for p in files if has_lang_suffix(p, "en")]
  canonical_files = [p for p in files if p.name.endswith(".md") and not has_lang_suffix(p, "zh") and not has_lang_suffix(p, "en")]

  missing_en: list[Path] = []
  missing_zh: list[Path] = []
  english_docs: list[Path] = []
  chinese_docs: list[Path] = []

  for path in zh_companions:
    if not plain_from_lang_suffix(path, "zh").exists():
      missing_en.append(path)
  for path in en_companions:
    if not plain_from_lang_suffix(path, "en").exists():
      missing_zh.append(path)

  for path in canonical_files:
    zh_peer = suffixed_peer(path, "zh")
    en_peer = suffixed_peer(path, "en")
    if zh_peer.exists() and not en_peer.exists():
      english_docs.append(path)
      continue
    if en_peer.exists() and not zh_peer.exists():
      chinese_docs.append(path)
      continue
    language = classify_markdown_language(path)
    if language == "zh":
      chinese_docs.append(path)
      if not en_peer.exists():
        missing_en.append(path)
    else:
      english_docs.append(path)
      if not zh_peer.exists():
        missing_zh.append(path)

  print(f"root: {root}")
  print(f"scope: {'full-tree' if full_tree else 'maintained-surface'}")
  print(f"markdown_total: {len(files)}")
  print(f"english_md_total: {len(english_docs) + len(en_companions)}")
  print(f"zh_md_total: {len(chinese_docs) + len(zh_companions)}")
  print(f"missing_english_peer: {len(missing_en)}")
  print(f"missing_chinese_peer: {len(missing_zh)}")

  if show_missing in {"en", "all"} and missing_en:
    print("\n[missing English peers]")
    for path in missing_en:
      print(f"{path} -> {expected_missing_peer(path, 'en')}")

  if show_missing in {"zh", "all"} and missing_zh:
    print("\n[missing Chinese peers]")
    for path in missing_zh:
      print(f"{path} -> {expected_missing_peer(path, 'zh')}")

  if registry_path is not None:
    print("")
    audit_cluster_registry(
      root,
      registry_path,
      include_local_only=include_local_only,
      full_tree=full_tree,
    )

  return 0


def audit_cluster_registry(
  root: Path,
  registry_path: Path,
  include_local_only: bool,
  *,
  full_tree: bool = False,
) -> int:
  records = build_cluster_records(
    root,
    include_local_only=include_local_only,
    strict_bilingual_only=not full_tree,
  )
  registry = load_cluster_registry(registry_path)

  if not registry_path.exists():
    print(f"registry: {registry_path} (missing, run `clusters --write` first)")
    return 0

  synced = 0
  needs_en = 0
  needs_zh = 0
  diverged = 0
  missing_en = 0
  missing_zh = 0

  for record in records:
    pair_id = record["pair_id"]
    english = Path(record["english"])
    chinese = Path(record["chinese"])
    current_state = "synced"
    if not english.exists():
      current_state = "missing-en"
      missing_en += 1
    elif not chinese.exists():
      current_state = "missing-zh"
      missing_zh += 1
    else:
      prev = registry.get(pair_id)
      if prev:
        english_changed = prev.get("english_hash") != record["english_hash"]
        chinese_changed = prev.get("chinese_hash") != record["chinese_hash"]
        if english_changed and chinese_changed:
          current_state = "diverged"
          diverged += 1
        elif english_changed:
          current_state = "needs-zh-update"
          needs_zh += 1
        elif chinese_changed:
          current_state = "needs-en-update"
          needs_en += 1
        else:
          synced += 1
      else:
        current_state = "unregistered"

    print(f"{pair_id}\t{current_state}\t{english.as_posix()}\t{chinese.as_posix()}")

  print(f"registry: {registry_path}")
  print(f"registry_scope: {'full-tree' if full_tree else 'maintained-surface'}")
  print(f"pair_count: {len(records)}")
  print(f"synced: {synced}")
  print(f"needs_en_update: {needs_en}")
  print(f"needs_zh_update: {needs_zh}")
  print(f"diverged: {diverged}")
  print(f"missing_en: {missing_en}")
  print(f"missing_zh: {missing_zh}")
  return 0


def file_sha256(path: Path) -> str:
  import hashlib

  normalized = normalize_doc_for_cluster_hash(
    path.read_text(encoding="utf-8", errors="ignore")
  )
  return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_cluster_registry(path: Path) -> dict[str, dict[str, str]]:
  if not path.exists():
    return {}
  data = json.loads(path.read_text(encoding="utf-8"))
  entries = data.get("pairs", []) if isinstance(data, dict) else []
  registry: dict[str, dict[str, str]] = {}
  for entry in entries:
    if isinstance(entry, dict) and entry.get("pair_id"):
      registry[str(entry["pair_id"])] = {
        "source_of_truth": str(entry.get("source_of_truth", "english")),
        "last_verified": str(entry.get("last_verified", "")),
        "english_hash": str(entry.get("english_hash", "")),
        "chinese_hash": str(entry.get("chinese_hash", "")),
      }
  return registry


def load_cluster_registry_payload(path: Path) -> dict[str, object]:
  if not path.exists():
    raise ValueError(f"Registry does not exist for selective refresh: {path}")
  data = json.loads(path.read_text(encoding="utf-8"))
  if not isinstance(data, dict) or not isinstance(data.get("pairs"), list):
    raise ValueError(f"Registry must be an object with a pairs list: {path}")
  return data


def merge_selected_cluster_records(
  existing_payload: dict[str, object],
  current_records: list[dict[str, str]],
  pair_ids: Iterable[str],
) -> dict[str, object]:
  selected = sorted(set(pair_ids))
  current_by_id = {record["pair_id"]: record for record in current_records}
  unknown = sorted(set(selected) - set(current_by_id))
  if unknown:
    raise ValueError(f"Unknown bilingual pair_id(s): {', '.join(unknown)}")

  existing_entries = existing_payload.get("pairs")
  if not isinstance(existing_entries, list):
    raise ValueError("Registry payload must contain a pairs list")

  merged_by_id: dict[str, dict[str, object]] = {}
  for entry in existing_entries:
    if not isinstance(entry, dict) or not entry.get("pair_id"):
      raise ValueError("Every registry pair entry must be an object with pair_id")
    merged_by_id[str(entry["pair_id"])] = dict(entry)
  for pair_id in selected:
    merged_by_id[pair_id] = dict(current_by_id[pair_id])

  merged = dict(existing_payload)
  merged["generated_at"] = date.today().isoformat()
  merged["pairs"] = [merged_by_id[pair_id] for pair_id in sorted(merged_by_id)]
  return merged


def build_cluster_records(
  root: Path,
  include_local_only: bool,
  previous_registry: dict[str, dict[str, str]] | None = None,
  *,
  strict_bilingual_only: bool = False,
) -> list[dict[str, str]]:
  files = filter_paths(
    iter_markdown(root),
    include_local_only=include_local_only,
    root=root,
    strict_bilingual_only=strict_bilingual_only,
  )
  canonical_files = [p for p in files if p.name.endswith(".md") and not has_lang_suffix(p, "zh") and not has_lang_suffix(p, "en")]
  records: list[dict[str, str]] = []
  for english in canonical_files:
    chinese = suffixed_peer(english, "zh")
    pair_id = english.relative_to(root).with_suffix("").as_posix()
    prev = (previous_registry or {}).get(pair_id, {})
    english_hash = file_sha256(english) if english.exists() else ""
    chinese_hash = file_sha256(chinese) if chinese.exists() else ""
    last_verified = str(prev.get("last_verified", "")) or date.today().isoformat()
    if (
      str(prev.get("english_hash", "")) != english_hash
      or str(prev.get("chinese_hash", "")) != chinese_hash
    ):
      last_verified = date.today().isoformat()
    record = {
      "pair_id": pair_id,
      "english": english.as_posix(),
      "chinese": chinese.as_posix(),
      "source_of_truth": "english",
      "last_verified": last_verified,
      "english_hash": english_hash,
      "chinese_hash": chinese_hash,
    }
    if not chinese.exists():
      record["source_of_truth"] = "english"
    elif not english.exists():
      record["source_of_truth"] = "chinese"
    records.append(record)
  return records


def run_clusters(args: argparse.Namespace) -> int:
  root = Path(args.root)
  if not root.exists():
    raise ValueError(f"Root does not exist: {root}")
  registry_path = Path(args.registry)
  previous_registry = load_cluster_registry(registry_path)
  records = build_cluster_records(
    root,
    args.include_local_only,
    previous_registry=previous_registry,
    strict_bilingual_only=not args.full_tree,
  )
  if args.pair_ids:
    payload = merge_selected_cluster_records(
      load_cluster_registry_payload(registry_path),
      records,
      args.pair_ids,
    )
  else:
    payload = {
      "generated_at": date.today().isoformat(),
      "root": root.as_posix(),
      "pairs": records,
    }
  print(f"cluster_registry: {registry_path}")
  print(f"scope: {'full-tree' if args.full_tree else 'maintained-surface'}")
  print(f"pair_count: {len(records)}")
  if args.pair_ids:
    print(f"selected_pair_count: {len(set(args.pair_ids))}")
  if args.dry_run:
    return 0
  if args.write:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
  return 0


def collect_source_files(args: argparse.Namespace) -> list[Path]:
  if args.files:
    return [Path(p) for p in args.files]

  if not args.root:
    raise ValueError("translate requires either --files or --root")

  root = Path(args.root)
  if not root.exists():
    raise ValueError(f"Root does not exist: {root}")

  if args.pattern:
    pattern = args.pattern
  elif args.source_lang == "zh":
    pattern = "*.zh.md"
  else:
    pattern = "*.md"

  files = sorted(p for p in root.rglob(pattern) if p.is_file())
  files = filter_paths(files, include_local_only=args.include_local_only, root=root)
  # Sealed dated evidence (Tier D) has no translation lane at all: its bytes
  # are routinely hash-pinned by retained-artifact manifests, so it stays
  # excluded even under --include-local-only.
  files = [p for p in files if classify_document(p, root) != "tier_d"]
  if args.source_lang == "en":
    files = [p for p in files if not has_lang_suffix(p, "zh") and not has_lang_suffix(p, "en")]
  if args.source_lang == "zh":
    files = [p for p in files if not has_lang_suffix(p, "en")]
  return files


def build_tasks(args: argparse.Namespace) -> list[TranslationTask]:
  tasks: list[TranslationTask] = []
  for source in collect_source_files(args):
    target = map_target_path(source, args.source_lang, args.target_lang)
    if args.only_missing and target.exists():
      continue
    if target.exists() and not args.force and not args.dry_run and not args.only_missing:
      raise FileExistsError(
        f"Target already exists: {target}. Use --force or --only-missing."
      )
    tasks.append(TranslationTask(source=source, target=target))
  return tasks


def split_markdown(text: str, max_chars: int) -> list[str]:
  if len(text) <= max_chars:
    return [text]

  blocks = text.split("\n# ")
  rebuilt: list[str] = []
  for index, block in enumerate(blocks):
    if index == 0:
      rebuilt.append(block)
    else:
      rebuilt.append("# " + block)

  chunks: list[str] = []
  current = ""

  for block in rebuilt:
    candidate = block if not current else current + "\n" + block
    if len(candidate) <= max_chars:
      current = candidate
      continue

    if current:
      chunks.append(current)
      current = ""

    if len(block) <= max_chars:
      current = block
      continue

    paragraphs = block.split("\n\n")
    para_chunk = ""
    for para in paragraphs:
      candidate = para if not para_chunk else para_chunk + "\n\n" + para
      if len(candidate) <= max_chars:
        para_chunk = candidate
        continue
      if para_chunk:
        chunks.append(para_chunk)
      para_chunk = para
    if para_chunk:
      current = para_chunk

  if current:
    chunks.append(current)

  return chunks


def mask_link_destinations(text: str) -> tuple[str, dict[str, str]]:
  replacements: dict[str, str] = {}
  counter = 0

  def repl(link: MarkdownLink) -> str:
    nonlocal counter
    placeholder = f"__DOC_LINK_{counter:04d}__"
    replacements[placeholder] = link.raw_target
    counter += 1
    return link.render(placeholder)

  return sub_markdown_links(text, repl), replacements


def unmask_link_destinations(text: str, replacements: dict[str, str]) -> str:
  restored = text
  for placeholder, target in replacements.items():
    restored = restored.replace(f"({placeholder})", f"({target})")
    restored = restored.replace(placeholder, target)
  return restored


def relativize_workspace_links(text: str, doc_path: Path, workspace_root: Path) -> str:
  workspace_root = workspace_root.resolve()
  doc_dir = doc_path.parent.resolve()

  def repl(link: MarkdownLink) -> str:
    target = link.raw_target
    stripped = target.split("#", 1)[0]
    suffix = target[len(stripped) :]

    if not stripped.startswith("/"):
      return link.raw

    line_suffix = ""
    candidate = stripped
    maybe_file, maybe_line = stripped.rsplit(":", 1) if ":" in stripped.rsplit("/", 1)[-1] else (stripped, "")
    if maybe_line.isdigit():
      candidate = maybe_file
      line_suffix = f":{maybe_line}"

    candidate_path = Path(candidate[1:] if WINDOWS_POSIX_ABS_RE.match(candidate) else candidate)
    try:
      resolved = candidate_path.resolve()
    except OSError:
      return link.raw

    try:
      rel_from_workspace = resolved.relative_to(workspace_root)
    except ValueError:
      return link.raw

    relative_target = os.path.relpath(workspace_root / rel_from_workspace, start=doc_dir)
    relative_target = Path(relative_target).as_posix()
    rewritten = relative_target + line_suffix + suffix
    return link.render(rewritten)

  return sub_markdown_links(text, repl)


def read_api_settings(args: argparse.Namespace) -> tuple[str, str, str]:
  load_dotenv(Path(".env"))

  base_url = args.base_url or env_first((DEFAULT_BASE_URL_ENV, *FALLBACK_BASE_URL_ENVS))
  model = args.model or env_first((DEFAULT_MODEL_ENV, *FALLBACK_MODEL_ENVS))
  api_key = args.api_key or env_first((DEFAULT_API_KEY_ENV, *FALLBACK_API_KEY_ENVS))
  if not base_url:
    raise ValueError(
      "Missing API base URL. Set --base-url, "
      f"${DEFAULT_BASE_URL_ENV}, or one of {FALLBACK_BASE_URL_ENVS}."
    )
  if not model:
    raise ValueError(
      "Missing model id. Set --model, "
      f"${DEFAULT_MODEL_ENV}, or one of {FALLBACK_MODEL_ENVS}."
    )
  if not api_key:
    raise ValueError(
      "Missing API key. Set --api-key, "
      f"${DEFAULT_API_KEY_ENV}, or one of {FALLBACK_API_KEY_ENVS}."
    )
  return base_url.rstrip("/"), model, api_key


def build_messages(source_lang: str, target_lang: str, chunk: str) -> list[dict[str, str]]:
  source_name = "Chinese" if source_lang == "zh" else "English"
  target_name = "English" if target_lang == "en" else "Chinese"
  system_prompt = (
    f"You translate repository Markdown from {source_name} to {target_name}. "
    "Preserve Markdown structure, headings, relative link destinations, code fences, "
    "tables, inline code, file paths, CLI flags, env vars, and identifiers. "
    "Translate prose, headings, captions, and human-readable link labels. "
    "Never wrap the entire response in triple backticks. "
    "If the input contains machine-translation draft comments, omit them instead of "
    "translating or duplicating them. "
    "If the Markdown contains placeholder link targets such as __DOC_LINK_0000__, "
    "keep them byte-for-byte unchanged. "
    "Do not invent facts. Return Markdown only."
  )
  return [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": chunk},
  ]


def request_translation(
  base_url: str,
  model: str,
  api_key: str,
  source_lang: str,
  target_lang: str,
  chunk: str,
) -> str:
  payload = {
    "model": model,
    "temperature": 0.2,
    "messages": build_messages(source_lang, target_lang, chunk),
  }
  body = json.dumps(payload).encode("utf-8")
  req = request.Request(
    base_url + DEFAULT_ENDPOINT,
    data=body,
    headers={
      "Authorization": f"Bearer {api_key}",
      "Content-Type": "application/json",
    },
    method="POST",
  )

  try:
    with request.urlopen(req) as resp:
      data = json.loads(resp.read().decode("utf-8"))
  except error.HTTPError as exc:
    detail = exc.read().decode("utf-8", errors="replace")
    raise RuntimeError(f"API request failed: {exc.code} {detail}") from exc

  try:
    content = data["choices"][0]["message"]["content"]
  except (KeyError, IndexError, TypeError) as exc:
    raise RuntimeError(f"Unexpected API response shape: {data}") from exc

  if isinstance(content, str):
    return content.strip() + "\n"
  if isinstance(content, list):
    parts = []
    for item in content:
      if isinstance(item, dict) and item.get("type") == "text":
        parts.append(item.get("text", ""))
    return "".join(parts).strip() + "\n"
  raise RuntimeError(f"Unsupported response content type: {type(content)!r}")


def translate_text(
  text: str,
  args: argparse.Namespace,
  base_url: str,
  model: str,
  api_key: str,
) -> str:
  text = normalize_translation_artifacts(text)
  chunks = split_markdown(text, args.chunk_chars)
  outputs: list[str] = []
  for index, chunk in enumerate(chunks, 1):
    masked_chunk, replacements = mask_link_destinations(chunk)
    print(f" chunk {index}/{len(chunks)}", file=sys.stderr)
    translated_chunk = request_translation(
      base_url=base_url,
      model=model,
      api_key=api_key,
      source_lang=args.source_lang,
      target_lang=args.target_lang,
      chunk=masked_chunk,
      ).rstrip()
    translated_chunk = normalize_translation_artifacts(translated_chunk).rstrip()
    outputs.append(
      unmask_link_destinations(translated_chunk, replacements)
    )
    if args.sleep_seconds > 0 and index != len(chunks):
      time.sleep(args.sleep_seconds)
  return "\n\n".join(outputs).strip() + "\n"


def draft_note(source: Path) -> str:
  return (
    f"<!-- Machine-translated draft generated on {date.today().isoformat()} "
    f"from {source.as_posix()}. Review before treating this file as authoritative. -->\n\n"
  )


def run_translate(args: argparse.Namespace) -> int:
  tasks = build_tasks(args)
  if not tasks:
    print("No translation tasks selected.")
    return 0

  print(f"translation_tasks: {len(tasks)}")
  for task in tasks:
    print(f"- {task.source} -> {task.target}")

  if args.dry_run:
    return 0

  base_url, model, api_key = read_api_settings(args)

  for task in tasks:
    text = task.source.read_text(encoding="utf-8")
    print(f"Translating {task.source} -> {task.target}", file=sys.stderr)
    translated = translate_text(text, args, base_url, model, api_key)
    translated = relativize_workspace_links(
      translated,
      doc_path=task.target,
      workspace_root=Path(DEFAULT_WORKSPACE_ROOT),
    )
    if args.add_draft_note:
      translated = draft_note(task.source) + translated
    task.target.write_text(translated, encoding="utf-8")

  return 0


def run_rewrite_links(args: argparse.Namespace) -> int:
  workspace_root = Path(args.workspace_root)
  files = [Path(p) for p in args.files]
  for path in files:
    text = path.read_text(encoding="utf-8")
    rewritten = relativize_workspace_links(text, path, workspace_root)
    if args.dry_run:
      print(path)
      continue
    if rewritten != text:
      path.write_text(rewritten, encoding="utf-8")
  return 0


def main() -> int:
  args = parse_args()
  if args.command == "audit":
    return audit_tree(
      Path(args.root),
      args.show_missing,
      args.include_local_only,
      Path(args.registry),
      full_tree=args.full_tree,
    )
  if args.command == "clusters":
    return run_clusters(args)
  if args.command == "translate":
    return run_translate(args)
  if args.command == "rewrite-links":
    return run_rewrite_links(args)
  raise ValueError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
  raise SystemExit(main())
