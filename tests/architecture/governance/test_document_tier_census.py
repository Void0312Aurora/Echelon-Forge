"""Every tracked document under `docs/` must belong to exactly one surface tier.

Before Tier D existed, 583 of 1211 tracked Markdown files (48%) matched none of
Tier A / Tier B / Tier C and therefore had no owner, no SLA, and no policy
answer for their Chinese-only pages. This census keeps that attribution vacuum
from reopening.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from tools.maintenance.document_scope import (
  DOCUMENT_TIERS,
  classify_document,
  is_retained_doc,
  is_sealed_evidence_doc,
  is_strict_bilingual_doc,
  requires_english_companion,
)

pytestmark = pytest.mark.governance_audit


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_ROOT = REPO_ROOT / "docs"
BASELINE_PATH = Path(__file__).with_name("document_tier_census_baseline.json")
BILINGUAL_REGISTRY = DOCS_ROOT / "engineering/documentation/reference/bilingual_document_clusters.json"
UPDATE_ENV = "EF_UPDATE_DOCUMENT_TIER_CENSUS"
A2_SEALED_PACKET = "docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/"


def _tracked_markdown() -> list[str]:
  result = subprocess.run(
    ["git", "ls-files", "--", "docs"],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )
  return sorted(line for line in result.stdout.splitlines() if line.endswith(".md"))


def _measure() -> dict[str, object]:
  tracked = _tracked_markdown()
  tiers = {relative: classify_document(REPO_ROOT / relative, DOCS_ROOT) for relative in tracked}
  chinese_only = [
    relative
    for relative in tracked
    if relative.endswith(".zh.md") and relative.removesuffix(".zh.md") + ".md" not in tiers
  ]
  counts = Counter(tiers.values())
  chinese_counts = Counter(tiers[relative] for relative in chinese_only)
  return {
    "tiers": tiers,
    "chinese_only": chinese_only,
    "snapshot": {
      "total_documents": len(tracked),
      "tiers": {tier: counts[tier] for tier in DOCUMENT_TIERS},
      "chinese_only_pages": {
        "total": len(chinese_only),
        "by_tier": {tier: chinese_counts[tier] for tier in DOCUMENT_TIERS},
      },
    },
  }


@pytest.fixture(scope="module")
def census() -> dict[str, object]:
  return _measure()


def _paths_in(census: dict[str, object], tier: str) -> list[str]:
  tiers: dict[str, str] = census["tiers"]  # type: ignore[assignment]
  return [relative for relative, value in tiers.items() if value == tier]


def test_every_tracked_document_resolves_to_exactly_one_tier(census: dict[str, object]) -> None:
  tiers: dict[str, str] = census["tiers"]  # type: ignore[assignment]
  snapshot: dict = census["snapshot"]  # type: ignore[assignment]

  assert tiers, "git ls-files returned no Markdown under docs/"
  unresolved = sorted(
    relative for relative, tier in tiers.items() if tier not in DOCUMENT_TIERS
  )
  assert unresolved == [], f"classify_document produced non-tier verdicts: {unresolved[:10]}"
  assert sum(snapshot["tiers"].values()) == snapshot["total_documents"]


def test_tier_predicates_agree_with_the_classifier(census: dict[str, object]) -> None:
  tiers: dict[str, str] = census["tiers"]  # type: ignore[assignment]
  violations: list[str] = []

  for relative, tier in tiers.items():
    path = REPO_ROOT / relative
    retained = is_retained_doc(path, DOCS_ROOT)
    strict = is_strict_bilingual_doc(path, DOCS_ROOT)
    sealed = is_sealed_evidence_doc(path, DOCS_ROOT)
    expected = {
      "tier_c": retained,
      "tier_a": not retained and strict,
      "tier_d": not retained and not strict and sealed,
      "tier_b": not retained and not strict and not sealed,
    }[tier]
    if not expected:
      violations.append(f"{relative} -> {tier}")

  assert violations == [], violations[:10]


def test_unmapped_path_shapes_still_land_in_a_tier(tmp_path: Path) -> None:
  docs_root = tmp_path / "docs"
  shapes = {
    "newowner/an_unregistered_page.md": "tier_b",
    "newowner/reviews/sealed_packet_20260813/README.md": "tier_d",
    "newowner/reviews/sealed_packet_20260813/evidence/source_ledger.zh.md": "tier_d",
    "newowner/reviews/sealed_packet_20260813/archive/superseded.md": "tier_c",
    "newowner/work/issues/draft.md": "tier_b",
    "newowner/temp/scratch_analysis.md": "tier_c",
    "README.md": "tier_a",
  }

  for relative, expected in shapes.items():
    path = docs_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Document\n", encoding="utf-8")
    assert classify_document(path, docs_root) == expected, relative


def test_tier_d_is_sealed_dated_evidence_under_a_reviews_subtree(
  census: dict[str, object],
) -> None:
  sealed = _paths_in(census, "tier_d")

  assert sealed
  assert all("/reviews/" in relative for relative in sealed)
  assert all(
    not any(part in {"Archive", "archive"} for part in Path(relative).parts)
    for relative in sealed
  )
  assert any(relative.startswith(A2_SEALED_PACKET) for relative in sealed)


def test_tier_d_chinese_pages_are_not_a_translation_backlog(census: dict[str, object]) -> None:
  chinese_only: list[str] = census["chinese_only"]  # type: ignore[assignment]
  tiers: dict[str, str] = census["tiers"]  # type: ignore[assignment]
  sealed_chinese = [relative for relative in chinese_only if tiers[relative] == "tier_d"]

  assert sealed_chinese, "expected sealed evidence packets to retain Chinese-only pages"
  assert any(relative.startswith(A2_SEALED_PACKET) for relative in sealed_chinese)
  queued = [
    relative
    for relative in sealed_chinese
    if requires_english_companion(REPO_ROOT / relative, DOCS_ROOT)
  ]
  assert queued == [], (
    "sealed evidence must not be queued for English companions; translating a "
    f"hash-pinned page invalidates its manifest pin: {queued[:5]}"
  )


def test_registered_bilingual_pairs_outrank_the_sealed_evidence_default(
  census: dict[str, object],
) -> None:
  tiers: dict[str, str] = census["tiers"]  # type: ignore[assignment]
  registry = json.loads(BILINGUAL_REGISTRY.read_text(encoding="utf-8"))
  registered = [entry[language] for entry in registry["pairs"] for language in ("english", "chinese")]
  under_reviews = [relative for relative in registered if "/reviews/" in relative]

  assert under_reviews, "expected the registry to still hold promoted review pairs"
  assert {tiers.get(relative) for relative in registered} == {"tier_a"}


def test_tier_census_matches_the_recorded_baseline(census: dict[str, object]) -> None:
  snapshot: dict = census["snapshot"]  # type: ignore[assignment]
  if os.environ.get(UPDATE_ENV):
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    baseline.update(snapshot)
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")

  baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
  recorded = {key: baseline[key] for key in snapshot}

  assert recorded == snapshot, (
    "Documentation tier census drifted from "
    f"{BASELINE_PATH.relative_to(REPO_ROOT).as_posix()}.\n"
    f"recorded: {json.dumps(recorded, sort_keys=True)}\n"
    f"measured: {json.dumps(snapshot, sort_keys=True)}\n"
    "If the change is intended (documents added, archived, or promoted), refresh "
    "the baseline in the same commit with:\n"
    f"  {baseline['update_command']}\n"
    "A rising tier_a count means new bilingual SLA; a rising tier_d count means "
    "new sealed evidence that must never be queued for translation."
  )


# ---------------------------------------------------------------------------
# The classifier and the maintained-selection filters must agree
# ---------------------------------------------------------------------------


def test_tier_c_scratch_stays_out_of_the_maintained_selection(tmp_path: Path) -> None:
  """A doc the classifier calls Tier C must not survive the default filter.

  ``docs/<owner>/temp/`` pages are retention (Tier C); letting them through
  ``filter_paths`` would feed scratch into the strict audit and the
  translation surface.
  """
  from tools.maintenance.document_scope import filter_paths

  docs = tmp_path / "docs"
  scratch = docs / "operations" / "temp" / "scratch.md"
  live = docs / "systems" / "standards" / "page.md"
  for page in (scratch, live):
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("# page\n", encoding="utf-8")

  assert classify_document(scratch, docs) == "tier_c"
  assert classify_document(live, docs) == "tier_a"

  selected = filter_paths([scratch, live], include_local_only=False, root=docs)
  assert live in selected
  assert scratch not in selected


def test_translation_collector_refuses_sealed_evidence(tmp_path: Path) -> None:
  """Tier D has no translation lane, not even under --include-local-only."""
  import argparse

  from tools.maintenance.translate_docs_batch import collect_source_files

  docs = tmp_path / "docs"
  sealed = docs / "systems" / "effects" / "reviews" / "packet_20260101" / "evidence.zh.md"
  work = docs / "learning" / "work" / "notes.zh.md"
  for page in (sealed, work):
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("# page\n", encoding="utf-8")

  assert classify_document(sealed, docs) == "tier_d"

  args = argparse.Namespace(
    files=None,
    root=str(docs),
    pattern=None,
    source_lang="zh",
    include_local_only=True,
  )
  files = collect_source_files(args)
  assert work in files
  assert sealed not in files
