from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

import pytest

from tools.maintenance import document_link_audit as audit
from tools.maintenance import document_scope
from tools.maintenance import translate_docs_batch

pytestmark = pytest.mark.governance_audit


REPO_ROOT = Path(__file__).resolve().parents[3]


def _write(path: Path, text: str = "# Document\n") -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(text, encoding="utf-8")


def test_translate_docs_batch_reexports_shared_scope_helpers(tmp_path: Path) -> None:
  docs_root = tmp_path / "docs"
  readme = docs_root / "README.md"
  architecture_reference = docs_root / "architecture/reference/t8_g4_truth_leak_inventory.md"
  authority_map = docs_root / "engineering/automation/rules/document_authority_map.md"
  examples_readme = docs_root / "engineering/documentation/structure_examples.md"
  reference_artifacts = docs_root / "reference_artifacts.md"
  retired_migration_path = docs_root / "plan/documentation_bilingual_migration_plan_20260518.md"
  _write(readme)
  _write(architecture_reference)
  _write(authority_map)
  _write(examples_readme)
  _write(reference_artifacts)

  assert translate_docs_batch.is_strict_bilingual_doc(readme, docs_root)
  assert translate_docs_batch.is_strict_bilingual_doc(architecture_reference, docs_root)
  assert translate_docs_batch.is_strict_bilingual_doc(authority_map, docs_root)
  assert translate_docs_batch.is_strict_bilingual_doc(examples_readme, docs_root)
  assert translate_docs_batch.is_strict_bilingual_doc(reference_artifacts, docs_root)
  assert not translate_docs_batch.is_strict_bilingual_doc(retired_migration_path, docs_root)
  assert not translate_docs_batch.is_local_only_doc(readme)


def test_selective_cluster_refresh_preserves_unreviewed_registry_entries(
  tmp_path: Path,
) -> None:
  docs_root = tmp_path / "docs"
  _write(docs_root / "README.md", "# Current English\n")
  _write(docs_root / "README.zh.md", "# 当前中文\n")
  _write(docs_root / "operations/README.md", "# Changed English\n")
  _write(docs_root / "operations/README.zh.md", "# 已更新中文\n")
  current = translate_docs_batch.build_cluster_records(
    docs_root,
    include_local_only=False,
    strict_bilingual_only=True,
  )
  existing = {
    "generated_at": "2026-01-01",
    "root": "docs",
    "review_note": "preserve top-level metadata",
    "pairs": [
      {
        "pair_id": "README",
        "english": "docs/README.md",
        "chinese": "docs/README.zh.md",
        "source_of_truth": "english",
        "last_verified": "2026-01-01",
        "english_hash": "unreviewed-en",
        "chinese_hash": "unreviewed-zh",
      },
      {
        "pair_id": "operations/README",
        "english": "docs/operations/README.md",
        "chinese": "docs/operations/README.zh.md",
        "source_of_truth": "english",
        "last_verified": "2026-01-01",
        "english_hash": "stale-en",
        "chinese_hash": "stale-zh",
      },
    ],
  }

  merged = translate_docs_batch.merge_selected_cluster_records(
    existing,
    current,
    ["operations/README"],
  )
  by_id = {entry["pair_id"]: entry for entry in merged["pairs"]}

  assert merged["generated_at"] == date.today().isoformat()
  assert merged["review_note"] == "preserve top-level metadata"
  assert by_id["README"]["english_hash"] == "unreviewed-en"
  assert by_id["README"]["chinese_hash"] == "unreviewed-zh"
  assert by_id["operations/README"]["english_hash"] != "stale-en"
  assert by_id["operations/README"]["chinese_hash"] != "stale-zh"


def test_selective_cluster_refresh_rejects_unknown_pair(tmp_path: Path) -> None:
  docs_root = tmp_path / "docs"
  _write(docs_root / "README.md")
  _write(docs_root / "README.zh.md")
  current = translate_docs_batch.build_cluster_records(
    docs_root,
    include_local_only=False,
    strict_bilingual_only=True,
  )

  with pytest.raises(ValueError, match="Unknown bilingual pair_id"):
    translate_docs_batch.merge_selected_cluster_records(
      {"pairs": []},
      current,
      ["missing/pair"],
    )


def test_repository_bilingual_registry_matches_the_maintained_surface() -> None:
  docs_root = REPO_ROOT / "docs"
  registry_path = docs_root / "engineering/documentation/reference/bilingual_document_clusters.json"
  entries = json.loads(registry_path.read_text(encoding="utf-8"))["pairs"]
  registered = {
    entry["pair_id"]: entry
    for entry in entries
  }
  records = translate_docs_batch.build_cluster_records(
    docs_root,
    include_local_only=False,
    strict_bilingual_only=True,
  )

  assert len(entries) == len(registered)
  assert set(registered) == {record["pair_id"] for record in records}
  for record in records:
    entry = registered[record["pair_id"]]
    for language in ("english", "chinese"):
      path = Path(record[language]).resolve()
      assert path.is_file()
      assert entry[language] == path.relative_to(REPO_ROOT).as_posix()
      assert entry[f"{language}_hash"] == record[f"{language}_hash"]

  for path in translate_docs_batch.filter_paths(
    translate_docs_batch.iter_markdown(docs_root),
    include_local_only=False,
    root=docs_root,
    strict_bilingual_only=True,
  ):
    if translate_docs_batch.has_lang_suffix(path, "zh"):
      assert translate_docs_batch.plain_from_lang_suffix(path, "zh").exists()
    elif translate_docs_batch.has_lang_suffix(path, "en"):
      assert translate_docs_batch.plain_from_lang_suffix(path, "en").exists()


def test_audit_accepts_relative_files_directories_fragments_and_external_links(tmp_path: Path) -> None:
  _write(tmp_path / "README.md", "[docs](docs/README.md)\n")
  _write(
    tmp_path / "docs/README.md",
    "\n".join(
      (
        "[file](guide.md#section)",
        "[dir](operations/README.md)",
        "[encoded](space%20name.md?view=1)",
        "[web](https://example.com/missing)",
        "[anchor](#local-heading)",
        "```md",
        "[example only](missing-example.md)",
        "```",
      )
    ),
  )
  _write(tmp_path / "docs/guide.md")
  _write(tmp_path / "docs/operations/README.md")
  _write(tmp_path / "docs/space name.md")

  result = audit.audit_repository(tmp_path)

  assert result.documents_checked == 3
  assert result.links_checked == 4
  assert result.issues == []


def test_audit_reports_missing_escape_and_machine_absolute_targets(tmp_path: Path) -> None:
  _write(
    tmp_path / "README.md",
    "\n".join(
      (
        "[missing](docs/missing.md)",
        "[escape](../outside.md)",
        "[unix](/home/example/project/doc.md)",
        r"[windows](C:\Users\example\project\doc.md)",
        "[docs directory](docs/)",
      )
    ),
  )
  _write(tmp_path / "docs/README.md")

  result = audit.audit_repository(tmp_path)

  assert [issue.code for issue in result.issues] == [
    "missing-target",
    "path-escapes-repository",
    "machine-absolute-path",
    "machine-absolute-path",
    "documentation-directory-target",
  ]


def test_archive_sources_are_excluded_but_maintained_archive_targets_are_validated(tmp_path: Path) -> None:
  _write(tmp_path / "README.md")
  _write(
    tmp_path / "docs/README.md",
    "[retained history](task/archive/closed/README.md)\n",
  )
  _write(
    tmp_path / "docs/task/archive/closed/README.md",
    "[stale historical link](missing.md)\n",
  )

  clean = audit.audit_repository(tmp_path)
  assert clean.issues == []
  assert all(
    "archive" not in path.relative_to(tmp_path).parts
    for path in audit.select_documents(tmp_path)
  )

  (tmp_path / "docs/task/archive/closed/README.md").unlink()
  broken = audit.audit_repository(tmp_path)
  assert [(issue.code, issue.target) for issue in broken.issues] == [
    ("missing-target", "task/archive/closed/README.md")
  ]


def test_full_tree_adds_non_strict_docs_without_adding_archive_sources(tmp_path: Path) -> None:
  _write(tmp_path / "README.md")
  _write(tmp_path / "docs/README.md")
  _write(tmp_path / "docs/project/notes/draft.md", "[missing](missing.md)\n")
  _write(tmp_path / "docs/archive/old.md", "[missing](missing.md)\n")

  assert audit.audit_repository(tmp_path).issues == []
  full = audit.audit_repository(tmp_path, full_tree=True)
  assert [(issue.source, issue.code) for issue in full.issues] == [
    ("docs/project/notes/draft.md", "missing-target")
  ]


def test_default_scope_link_audits_maintained_english_work_documents(tmp_path: Path) -> None:
  _write(tmp_path / "README.md")
  _write(tmp_path / "docs/README.md")
  _write(
    tmp_path / "docs/systems/effects/work/issues/gap/README.md",
    "[missing](missing.md)\n",
  )
  _write(
    tmp_path / "docs/systems/effects/work/issues/gap/README.zh.md",
    "[也缺失](missing-zh.md)\n",
  )
  _write(tmp_path / "docs/learning/work/archive/old.md", "[missing](missing.md)\n")

  result = audit.audit_repository(tmp_path)

  assert [(issue.source, issue.code) for issue in result.issues] == [
    ("docs/systems/effects/work/issues/gap/README.md", "missing-target")
  ]
  selected = {
    path.relative_to(tmp_path).as_posix()
    for path in audit.select_documents(tmp_path)
  }
  assert "docs/systems/effects/work/issues/gap/README.md" in selected
  assert "docs/systems/effects/work/issues/gap/README.zh.md" not in selected
  assert "docs/learning/work/archive/old.md" not in selected


def test_promoted_work_pair_reenters_the_strict_bilingual_surface(
  tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
  docs_root = tmp_path / "docs"
  promoted_en = docs_root / "learning/work/issues/temporal_policy_roadmap.md"
  promoted_zh = docs_root / "learning/work/issues/temporal_policy_roadmap.zh.md"
  sibling = docs_root / "learning/work/issues/rl_selfplay.md"
  _write(promoted_en, "# Promoted Plan\n")
  _write(promoted_zh, "# 已提升计划\n")
  _write(sibling, "# English-only Plan\n")

  assert not translate_docs_batch.is_strict_bilingual_doc(promoted_en, docs_root)

  monkeypatch.setattr(
    document_scope,
    "PROMOTED_WORK_DOCUMENTS",
    frozenset(
      {
        "learning/work/issues/temporal_policy_roadmap.md",
        "learning/work/issues/temporal_policy_roadmap.zh.md",
      }
    ),
  )

  assert translate_docs_batch.is_strict_bilingual_doc(promoted_en, docs_root)
  assert translate_docs_batch.is_strict_bilingual_doc(promoted_zh, docs_root)
  assert not translate_docs_batch.is_strict_bilingual_doc(sibling, docs_root)

  records = translate_docs_batch.build_cluster_records(
    docs_root,
    include_local_only=False,
    strict_bilingual_only=True,
  )
  pair_ids = {record["pair_id"] for record in records}
  assert "learning/work/issues/temporal_policy_roadmap" in pair_ids
  assert "learning/work/issues/rl_selfplay" not in pair_ids

  merged = translate_docs_batch.merge_selected_cluster_records(
    {"pairs": []},
    records,
    ["learning/work/issues/temporal_policy_roadmap"],
  )
  refreshed = {entry["pair_id"] for entry in merged["pairs"]}
  assert refreshed == {"learning/work/issues/temporal_policy_roadmap"}


def test_json_cli_is_strict_and_machine_readable(tmp_path: Path) -> None:
  _write(tmp_path / "README.md", "[missing](missing.md)\n")
  output = io.StringIO()
  with redirect_stdout(output):
    exit_code = audit.main(["--repo-root", str(tmp_path), "--format", "json"])

  payload = json.loads(output.getvalue())
  assert exit_code == 1
  assert payload["documents_checked"] == 1
  assert payload["issues"][0]["code"] == "missing-target"


def test_repository_maintained_document_links_are_clean() -> None:
  result = audit.audit_repository(REPO_ROOT)

  assert result.issues == []


def test_retired_plan_and_task_roots_are_outside_maintained_link_scope() -> None:
  selected = {
    path.relative_to(REPO_ROOT).as_posix()
    for path in audit.select_documents(REPO_ROOT)
  }

  assert not any(path.startswith("docs/plan/") for path in selected)
  assert not any(path.startswith("docs/task/") for path in selected)
