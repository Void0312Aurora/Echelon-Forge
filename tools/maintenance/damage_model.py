#!/usr/bin/env python3
"""Unified damage-model maintenance CLI.

Consolidated entrypoint replacing the eight previously separate
``damage_model_*.py`` dispatch routers. Every sub-command is namespaced
under a domain prefix so the surface stays discoverable::

  damage_model.py benchmark-evidence mechanism-evidence
  damage_model.py candidate-artifacts validation-scaffold
  damage_model.py external-evidence intake-contract
  damage_model.py independent-review effect-scale-review
  damage_model.py release-governance package-provenance-identity
  damage_model.py retained-artifacts manifest-integrity
  damage_model.py scope-provenance row-provenance
  damage_model.py source-governance admission-audit
"""

from __future__ import annotations

try:
    from ._dispatch import dispatch, ensure_path
except ImportError:
    from _dispatch import dispatch, ensure_path

ensure_path()

from tools.maintenance.benchmark_evidence import ( # noqa: E402
  benchmark_execution_admission,
  comparison_hashes,
  debris_admission,
  mechanism_evidence,
  selected_debris_case_admission,
  selected_debris_case_packet,
  spreadsheet_lineage_tolerance_packet,
  spreadsheet_recalculation_admission,
  spreadsheet_replacement_tolerance,
)
from tools.maintenance.candidate_artifacts import ( # noqa: E402
  component_fragility_benchmark,
  component_fragility_review_gate,
  component_fragility_validation_prep,
  component_probability_result_pack,
  component_probability_retained_pack,
  component_probability_review_readiness,
  component_probability_snapshot,
  component_probability_surface_probe,
  effect_scale_result_pack,
  effect_scale_retained_pack,
  effect_scale_snapshot,
  package_bundle,
  runtime_authority_exercise,
  scope_boundary_probe,
  validation_scaffold,
)
from tools.maintenance.external_signoff_evidence import ( # noqa: E402
  admission_preflight,
  intake_contract,
  packet_template,
  signoff_request,
)
from tools.maintenance.independent_review import ( # noqa: E402
  effect_scale_review,
  review_closeout,
  scope_bucket_review,
  uncertainty_review,
)
from tools.maintenance.release_governance import ( # noqa: E402
  effect_scale_release_closeout,
  effect_scale_release_readiness,
  package_provenance_identity,
  provenance_closeout,
  provenance_identity_review,
  scoped_release_identity,
  source_release_signoff,
)
from tools.maintenance.retained_artifacts import manifest_integrity # noqa: E402
from tools.maintenance.scope_provenance import ( # noqa: E402
  geometry_warhead_row_provenance,
  mechanism_source_closeout,
  target_geometry_closeout,
  warhead_scope_closeout,
)
from tools.maintenance.source_governance import ( # noqa: E402
  admission_audit,
  payload_pack,
  rights_output_policy,
)

# Command registry.
# Keys use a "domain command" convention so related operations sort together.

COMMANDS = {
  # -- benchmark-evidence ---------------------------------------------------
  "benchmark-evidence mechanism-evidence": (
    "Generate the mechanism benchmark evidence manifest.",
    mechanism_evidence.main,
  ),
  "benchmark-evidence comparison-hashes": (
    "Generate hash-only mechanism comparison evidence.",
    comparison_hashes.main,
  ),
  "benchmark-evidence benchmark-execution-admission": (
    "Evaluate benchmark execution admission evidence.",
    benchmark_execution_admission.main,
  ),
  "benchmark-evidence debris-admission": (
    "Evaluate debris criteria admission evidence.",
    debris_admission.main,
  ),
  "benchmark-evidence selected-debris-case-admission": (
    "Evaluate selected debris case admission evidence.",
    selected_debris_case_admission.main,
  ),
  "benchmark-evidence selected-debris-case-packet": (
    "Build the selected debris case candidate packet.",
    selected_debris_case_packet.main,
  ),
  "benchmark-evidence spreadsheet-recalculation-admission": (
    "Evaluate spreadsheet recalculation admission evidence.",
    spreadsheet_recalculation_admission.main,
  ),
  "benchmark-evidence spreadsheet-replacement-tolerance": (
    "Evaluate spreadsheet replacement/tolerance admission evidence.",
    spreadsheet_replacement_tolerance.main,
  ),
  "benchmark-evidence spreadsheet-lineage-tolerance-packet": (
    "Build the spreadsheet lineage/tolerance review packet.",
    spreadsheet_lineage_tolerance_packet.main,
  ),
  # -- candidate-artifacts --------------------------------------------------
  "candidate-artifacts validation-scaffold": (
    "Generate the non-authoritative validation scaffold artifact.",
    validation_scaffold.main,
  ),
  "candidate-artifacts scope-boundary-probe": (
    "Generate Stage B scope boundary probe results.",
    scope_boundary_probe.main,
  ),
  "candidate-artifacts effect-scale-snapshot": (
    "Generate the Stage B effect-scale candidate snapshot.",
    effect_scale_snapshot.main,
  ),
  "candidate-artifacts effect-scale-result-pack": (
    "Generate the Stage B effect-scale validation result pack.",
    effect_scale_result_pack.main,
  ),
  "candidate-artifacts effect-scale-retained-pack": (
    "Write retained Stage B effect-scale candidate artifacts.",
    effect_scale_retained_pack.main,
  ),
  "candidate-artifacts runtime-authority-exercise": (
    "Generate the test-local runtime authority exercise pack.",
    runtime_authority_exercise.main,
  ),
  "candidate-artifacts package-bundle": (
    "Assemble the current candidate package bundle.",
    package_bundle.main,
  ),
  "candidate-artifacts component-probability-surface-probe": (
    "Generate the Stage C component-probability surface probe.",
    component_probability_surface_probe.main,
  ),
  "candidate-artifacts component-probability-snapshot": (
    "Generate the Stage C component-probability candidate snapshot.",
    component_probability_snapshot.main,
  ),
  "candidate-artifacts component-probability-result-pack": (
    "Generate the Stage C component-probability result pack.",
    component_probability_result_pack.main,
  ),
  "candidate-artifacts component-probability-retained-pack": (
    "Write retained Stage C component-probability artifacts.",
    component_probability_retained_pack.main,
  ),
  "candidate-artifacts component-probability-review-readiness": (
    "Evaluate Stage C component-probability review readiness.",
    component_probability_review_readiness.main,
  ),
  "candidate-artifacts component-fragility-validation-prep": (
    "Generate Stage C component-fragility validation review inputs.",
    component_fragility_validation_prep.main,
  ),
  "candidate-artifacts component-fragility-review-gate": (
    "Evaluate the Stage C component-fragility review gate.",
    component_fragility_review_gate.main,
  ),
  "candidate-artifacts component-fragility-benchmark": (
    "Generate blocked Stage C component-fragility benchmark evidence.",
    component_fragility_benchmark.main,
  ),
  # -- external-evidence ----------------------------------------------------
  "external-evidence intake-contract": (
    "Generate the fail-closed external signoff intake contract.",
    intake_contract.main,
  ),
  "external-evidence packet-template": (
    "Generate a reviewer-fillable external signoff packet template.",
    packet_template.main,
  ),
  "external-evidence admission-preflight": (
    "Generate the signoff admission preflight packet.",
    admission_preflight.main,
  ),
  "external-evidence signoff-request": (
    "Generate the source-rights allowed-output signoff request packet.",
    signoff_request.main,
  ),
  # -- independent-review ---------------------------------------------------
  "independent-review effect-scale-review": (
    "Evaluate bounded Stage B effect-scale independent review evidence.",
    effect_scale_review.main,
  ),
  "independent-review review-closeout": (
    "Evaluate RES-011/012 independent review closeout evidence.",
    review_closeout.main,
  ),
  "independent-review scope-bucket-review": (
    "Evaluate scope-bucket independent review evidence.",
    scope_bucket_review.main,
  ),
  "independent-review uncertainty-review": (
    "Evaluate uncertainty review evidence.",
    uncertainty_review.main,
  ),
  # -- release-governance ---------------------------------------------------
  "release-governance package-provenance-identity": (
    "Evaluate package provenance and surrogate identity boundaries.",
    package_provenance_identity.main,
  ),
  "release-governance provenance-identity-review": (
    "Evaluate retained provenance identity review evidence.",
    provenance_identity_review.main,
  ),
  "release-governance provenance-closeout": (
    "Evaluate release provenance closeout evidence.",
    provenance_closeout.main,
  ),
  "release-governance source-release-signoff": (
    "Evaluate source release signoff evidence.",
    source_release_signoff.main,
  ),
  "release-governance scoped-release-identity": (
    "Evaluate scoped release identity evidence.",
    scoped_release_identity.main,
  ),
  "release-governance effect-scale-readiness": (
    "Evaluate Stage B effect-scale release readiness.",
    effect_scale_release_readiness.main,
  ),
  "release-governance effect-scale-closeout": (
    "Evaluate Stage B effect-scale release closeout.",
    effect_scale_release_closeout.main,
  ),
  # -- retained-artifacts ---------------------------------------------------
  "retained-artifacts manifest-integrity": (
    "Check retained artifact manifest hashes and authority guards.",
    manifest_integrity.main,
  ),
  # -- scope-provenance -----------------------------------------------------
  "scope-provenance row-provenance": (
    "Evaluate geometry and warhead row provenance boundaries.",
    geometry_warhead_row_provenance.main,
  ),
  "scope-provenance target-geometry-closeout": (
    "Evaluate target-geometry scope closeout evidence.",
    target_geometry_closeout.main,
  ),
  "scope-provenance warhead-scope-closeout": (
    "Evaluate warhead-family scope closeout evidence.",
    warhead_scope_closeout.main,
  ),
  "scope-provenance mechanism-source-closeout": (
    "Evaluate mechanism source closeout evidence.",
    mechanism_source_closeout.main,
  ),
  # -- source-governance ----------------------------------------------------
  "source-governance admission-audit": (
    "Audit source ledgers and candidate docs for fail-closed admission.",
    admission_audit.main,
  ),
  "source-governance payload-pack": (
    "Build or inspect the retained source payload pack.",
    payload_pack.main,
  ),
  "source-governance rights-output-policy": (
    "Evaluate the source rights and allowed-output policy gate.",
    rights_output_policy.main,
  ),
}


def main(argv=None):
  return dispatch(
    prog="damage_model.py",
    description="Damage-model maintenance commands (use <domain> <command>):",
    commands=COMMANDS,
    argv=argv,
  )


if __name__ == "__main__":
  raise SystemExit(main())
