from __future__ import annotations

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


def test_python_facade_exports_explicit_host_and_realized_world_evidence() -> None:
    facade = ef_py.RuntimeFacade(1)

    result = facade.export_composition_evidence()

    assert result.available is True
    assert result.error_code == ""
    # Host identity records the runtime execution owner, not the caller language.
    assert result.evidence.host_mode == "native_cpp"
    assert result.evidence.binding_version == "native.v1"
    assert len(result.evidence.provider_versions) == 11
    assert len(result.evidence.world_instances) == 1
    assert len(result.evidence.world_instances[0].scope_generations) == 5
    assert len(result.evidence.evidence_sha256) == 64
    assert facade.compare_composition_evidence(result.evidence).compatible is True


def test_python_facade_comparison_rejects_unexplained_identity_changes() -> None:
    facade = ef_py.RuntimeFacade(1)
    original = facade.export_composition_evidence()
    assert original.available is True

    original.evidence.catalog_lock_sha256 = "0" * 64
    forged = facade.compare_composition_evidence(original.evidence)
    assert forged.compatible is False
    assert (
        "expected:evidence.canonical_bytes_mismatch@$.canonical_json" in forged.mismatches
    )
    assert "expected:evidence.identity_mismatch@$.evidence_sha256" in forged.mismatches

    before_resize = facade.export_composition_evidence()
    assert before_resize.available is True
    facade.resize(2)
    resized = facade.compare_composition_evidence(before_resize.evidence)
    assert resized.compatible is False
    assert "$.world_instances" in resized.mismatches


def test_python_shrink_regrow_changes_composition_incarnation() -> None:
    facade = ef_py.RuntimeFacade(1)
    before = facade.export_composition_evidence()
    assert before.available is True

    facade.resize(0)
    facade.resize(1)

    after = facade.export_composition_evidence()
    assert after.available is True
    assert after.evidence.evidence_sha256 != before.evidence.evidence_sha256
    comparison = facade.compare_composition_evidence(before.evidence)
    assert comparison.compatible is False
    assert "$.world_instances" in comparison.mismatches

    configured = ef_py.RuntimeFacade(1)
    configured_before = configured.export_composition_evidence()
    assert configured_before.available is True
    zero = ef_py.RuntimeBatchConfig()
    zero.world_count = 0
    zero.worker_threads = 0
    configured.configure_batch(zero)
    one = ef_py.RuntimeBatchConfig()
    one.world_count = 1
    one.worker_threads = 0
    configured.configure_batch(one)
    configured_after = configured.export_composition_evidence()
    assert configured_after.available is True
    assert (
        configured_after.evidence.evidence_sha256
        != configured_before.evidence.evidence_sha256
    )
    assert configured.compare_composition_evidence(configured_before.evidence).compatible is False


def test_python_zero_world_facade_fails_closed_with_named_reason() -> None:
    result = ef_py.RuntimeFacade(0).export_composition_evidence()

    assert result.available is False
    assert result.error_code == "composition_evidence.no_realized_worlds"
    assert result.evidence.evidence_sha256 == ""
