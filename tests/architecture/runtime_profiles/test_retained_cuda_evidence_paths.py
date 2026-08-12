"""Production-path contract for retained CUDA-resident evidence manifests.

The CR2/RB manifests record their inputs and outputs under the pre-migration
`docs/plan/exact_runtime/` prefix. Those recorded strings are pinned by canonical
byte counts and SHA-256 digests, so they cannot be rewritten without
invalidating reviewed evidence; the retained packet itself now lives under
`tests/fixtures/runtime_profiles/cuda_resident_program_2/`.

The translation between the two therefore has exactly one owner,
`tools/diagnostics/cuda_resident_retained_evidence_paths`. This module pins the
part that regressed once already: the *production* collector resolved recorded
paths verbatim while only the tests translated them, so the collector failed on
its first manifest read and its parity output would have recreated the retired
`docs/plan/` tree.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.diagnostics.cuda_resident_retained_evidence_paths import (
    LOGICAL_EVIDENCE_PREFIX,
    PHYSICAL_EVIDENCE_PREFIX,
    logical_relative,
    physical_relative,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = ROOT / PHYSICAL_EVIDENCE_PREFIX
MATRIX_MANIFEST = (
    FIXTURE_ROOT / "cuda_resident_cr2_matrix_evidence_20260804" / "manifest.json"
)

# Descriptor groups whose recorded paths must resolve to a file on disk. Binary
# probe executables are deliberately excluded: they are build outputs that only
# exist in a GPU build tree, so requiring them here would make the contract
# unrunnable on a CPU-only checkout.
RESOLVABLE_GROUPS = ("source_inputs", "prior_evidence_inputs")


def _manifest() -> dict[str, object]:
    value = json.loads(MATRIX_MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _recorded_paths(value: object) -> list[str]:
    """Collect every `path` / `parity_output_path` string in a manifest tree."""
    found: list[str] = []
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, child in item.items():
                if key in {"path", "parity_output_path"} and isinstance(child, str):
                    found.append(child)
                else:
                    stack.append(child)
        elif isinstance(item, list):
            stack.extend(item)
    return found


def test_translation_is_an_exact_round_trip() -> None:
    logical = LOGICAL_EVIDENCE_PREFIX + "cuda_resident_cr2_closure_20260805.json"
    physical = PHYSICAL_EVIDENCE_PREFIX + "cuda_resident_cr2_closure_20260805.json"

    assert physical_relative(logical) == physical
    assert logical_relative(physical) == logical
    assert logical_relative(physical_relative(logical)) == logical


def test_translation_leaves_unrelated_paths_untouched() -> None:
    for path in (
        "src/runtime/contracts/cuda_resident_matrix_contract.h",
        "tools/diagnostics/cuda_resident_cr2_matrix_probe.py",
        "build-cr2-cpu-v1/Release/ef_cuda_resident_cr2_matrix_cpu_probe.exe",
    ):
        assert physical_relative(path) == path
        assert logical_relative(path) == path


def test_only_the_leading_prefix_occurrence_is_translated() -> None:
    # A recorded path that mentions the prefix twice must translate only the
    # leading one, matching the single-replacement behavior the manifests were
    # captured against.
    nested = LOGICAL_EVIDENCE_PREFIX + "nested/" + LOGICAL_EVIDENCE_PREFIX + "leaf.json"

    assert physical_relative(nested) == (
        PHYSICAL_EVIDENCE_PREFIX + "nested/" + LOGICAL_EVIDENCE_PREFIX + "leaf.json"
    )


def test_matrix_manifest_retains_the_logical_prefix() -> None:
    # If a future change rewrites the manifests instead of translating, this gate
    # should fail loudly rather than let the recorded hashes drift silently.
    recorded = _recorded_paths(_manifest())

    assert recorded
    assert any(path.startswith(LOGICAL_EVIDENCE_PREFIX) for path in recorded)


def test_every_resolvable_manifest_input_resolves_inside_the_fixture_tree() -> None:
    manifest = _manifest()
    fixture_root = FIXTURE_ROOT.resolve()
    repo_root = ROOT.resolve()

    checked = 0
    for group in RESOLVABLE_GROUPS:
        descriptors = manifest[group]
        assert isinstance(descriptors, dict)
        for name, descriptor in descriptors.items():
            assert isinstance(descriptor, dict)
            recorded = descriptor["path"]
            assert isinstance(recorded, str)
            resolved = (ROOT / physical_relative(recorded)).resolve()

            assert resolved.is_file(), f"{group}.{name} does not resolve: {recorded}"
            assert resolved.is_relative_to(repo_root)
            # A path recorded under the retired prefix must land in the fixture
            # tree; anything else (maintained source) stays where it is.
            if recorded.startswith(LOGICAL_EVIDENCE_PREFIX):
                assert resolved.is_relative_to(fixture_root), (
                    f"{group}.{name} escapes the fixture tree: {resolved}"
                )
            checked += 1

    assert checked


def test_every_campaign_report_resolves_inside_the_fixture_tree() -> None:
    manifest = _manifest()
    fixture_root = FIXTURE_ROOT.resolve()

    checked = 0
    campaigns = manifest["campaigns"]
    assert isinstance(campaigns, list)
    for campaign in campaigns:
        assert isinstance(campaign, dict)
        reports = campaign["reports"]
        assert isinstance(reports, dict)
        for lane, descriptor in reports.items():
            assert isinstance(descriptor, dict)
            resolved = (ROOT / physical_relative(str(descriptor["path"]))).resolve()

            assert resolved.is_file(), f"{campaign['campaign_id']}.{lane} is missing"
            assert resolved.is_relative_to(fixture_root)
            checked += 1

    assert checked


def test_parity_output_never_recreates_the_retired_tree() -> None:
    manifest = _manifest()
    recorded = manifest["parity_output_path"]
    assert isinstance(recorded, str)

    # The manifest still records the retired location as the logical identity.
    assert recorded.startswith(LOGICAL_EVIDENCE_PREFIX)

    resolved = (ROOT / physical_relative(recorded)).resolve()

    assert resolved.is_relative_to(FIXTURE_ROOT.resolve())
    assert not resolved.is_relative_to((ROOT / "docs").resolve())


def test_no_retired_evidence_directory_is_tracked() -> None:
    # The migration retired this tree; nothing in the repository should recreate
    # it, whether by a collector write or a new manifest.
    assert not (ROOT / LOGICAL_EVIDENCE_PREFIX).exists()


def test_collector_and_closure_validator_share_the_single_resolver() -> None:
    # Guard against the duplication that caused the original defect: each module
    # must call the shared helper rather than inline its own prefix replacement.
    for relative in (
        "tools/diagnostics/cuda_resident_cr2_matrix_evidence.py",
        "tools/diagnostics/cuda_resident_cr2_closure.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")

        assert "physical_relative" in source, f"{relative} bypasses the shared resolver"
        assert f'replace("{LOGICAL_EVIDENCE_PREFIX}"' not in source, (
            f"{relative} reintroduced an inline prefix translation"
        )
