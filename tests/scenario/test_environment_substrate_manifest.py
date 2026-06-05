from __future__ import annotations

from copy import deepcopy

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.scenario.environment_substrate import (  # noqa: E402
    DEFAULT_BRANCH_IDS,
    EnvironmentManifest,
    build_deterministic_environment_fixture,
    validate_environment_manifest,
)


def _manifest_from_metadata(metadata: dict) -> EnvironmentManifest:
    return EnvironmentManifest(**deepcopy(metadata))


def test_g0_j_static_environment_fixture_validates_deterministically() -> None:
    fixture_a = build_deterministic_environment_fixture()
    fixture_b = build_deterministic_environment_fixture()

    validation = validate_environment_manifest(fixture_a)

    assert validation.valid
    assert not validation.fail_closed
    assert validation.rejection_reason == ""
    assert fixture_a.to_metadata() == fixture_b.to_metadata()
    branch_ids = {
        branch["branch_id"] for branch in fixture_a.to_metadata()["branch_registry"]
    }
    assert set(DEFAULT_BRANCH_IDS) <= branch_ids
    assert fixture_a.to_metadata()["objects"][1]["components"][0]["family"] == "structure"


def test_g0_j_manifest_requires_the_shared_environment_branch_registry() -> None:
    metadata = build_deterministic_environment_fixture().to_metadata()
    metadata["branch_registry"] = [
        branch
        for branch in metadata["branch_registry"]
        if branch["branch_id"] != "hydrology"
    ]
    manifest = _manifest_from_metadata(metadata)

    validation = validate_environment_manifest(manifest)

    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "environment_substrate_required_branch_missing"
    assert "hydrology" in validation.errors[0]


def test_g0_j_manifest_rejects_behavior_semantics_in_untyped_properties() -> None:
    metadata = build_deterministic_environment_fixture().to_metadata()
    metadata["objects"][0]["properties"]["speed_multiplier"] = 0.8
    manifest = _manifest_from_metadata(metadata)

    validation = validate_environment_manifest(manifest)

    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "environment_substrate_untyped_behavior_property"


def test_g0_j_manifest_rejects_held_runtime_capability_claims() -> None:
    metadata = build_deterministic_environment_fixture().to_metadata()
    metadata["capability_claims"] = ["movement"]
    manifest = _manifest_from_metadata(metadata)

    validation = validate_environment_manifest(manifest)

    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "environment_substrate_held_capability_claim"


def test_g0_j_manifest_rejects_missing_required_component_attributes() -> None:
    metadata = build_deterministic_environment_fixture().to_metadata()
    del metadata["objects"][0]["components"][0]["attributes"]["surface"]
    manifest = _manifest_from_metadata(metadata)

    validation = validate_environment_manifest(manifest)

    assert not validation.valid
    assert validation.fail_closed
    assert (
        validation.rejection_reason
        == "environment_substrate_missing_required_component_attribute"
    )
