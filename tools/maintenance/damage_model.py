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

Producer modules are bound lazily (see :func:`_producer`): a single
invocation only pays for the one module it routes to.
"""

from __future__ import annotations

from importlib import import_module

try:
  from ._dispatch import dispatch, ensure_path
except ImportError:
  from _dispatch import dispatch, ensure_path

ensure_path()


def _producer(module_path: str):
  """Bind a sub-command to its producer without importing it up front.

  Importing all ~47 producers at router import cost ~14s per interpreter
  start, which every ``--help``, every sub-command and every pytest session
  paid regardless of which domain it needed. The returned shim resolves the
  module on the dispatch path instead, so only the invoked domain is loaded.
  """

  def run(argv: list[str] | None = None) -> int:
    return import_module(module_path).main(argv)

  # Lets audits enumerate the routed producers without importing any of them.
  run.producer_module = module_path
  return run


# Command registry.
# Keys use a "domain command" convention so related operations sort together.

COMMANDS = {
  # -- benchmark-evidence ---------------------------------------------------
  "benchmark-evidence mechanism-evidence": (
    "Generate the mechanism benchmark evidence manifest.",
    _producer("tools.maintenance.benchmark_evidence.mechanism_evidence"),
  ),
  "benchmark-evidence comparison-hashes": (
    "Generate hash-only mechanism comparison evidence.",
    _producer("tools.maintenance.benchmark_evidence.comparison_hashes"),
  ),
  "benchmark-evidence benchmark-execution-admission": (
    "Evaluate benchmark execution admission evidence.",
    _producer("tools.maintenance.benchmark_evidence.benchmark_execution_admission"),
  ),
  "benchmark-evidence debris-admission": (
    "Evaluate debris criteria admission evidence.",
    _producer("tools.maintenance.benchmark_evidence.debris_admission"),
  ),
  "benchmark-evidence selected-debris-case-admission": (
    "Evaluate selected debris case admission evidence.",
    _producer("tools.maintenance.benchmark_evidence.selected_debris_case_admission"),
  ),
  "benchmark-evidence selected-debris-case-packet": (
    "Build the selected debris case candidate packet.",
    _producer("tools.maintenance.benchmark_evidence.selected_debris_case_packet"),
  ),
  "benchmark-evidence spreadsheet-recalculation-admission": (
    "Evaluate spreadsheet recalculation admission evidence.",
    _producer("tools.maintenance.benchmark_evidence.spreadsheet_recalculation_admission"),
  ),
  "benchmark-evidence spreadsheet-replacement-tolerance": (
    "Evaluate spreadsheet replacement/tolerance admission evidence.",
    _producer("tools.maintenance.benchmark_evidence.spreadsheet_replacement_tolerance"),
  ),
  "benchmark-evidence spreadsheet-lineage-tolerance-packet": (
    "Build the spreadsheet lineage/tolerance review packet.",
    _producer("tools.maintenance.benchmark_evidence.spreadsheet_lineage_tolerance_packet"),
  ),
  # -- candidate-artifacts --------------------------------------------------
  "candidate-artifacts validation-scaffold": (
    "Generate the non-authoritative validation scaffold artifact.",
    _producer("tools.maintenance.candidate_artifacts.validation_scaffold"),
  ),
  "candidate-artifacts scope-boundary-probe": (
    "Generate Stage B scope boundary probe results.",
    _producer("tools.maintenance.candidate_artifacts.scope_boundary_probe"),
  ),
  "candidate-artifacts effect-scale-snapshot": (
    "Generate the Stage B effect-scale candidate snapshot.",
    _producer("tools.maintenance.candidate_artifacts.effect_scale_snapshot"),
  ),
  "candidate-artifacts effect-scale-result-pack": (
    "Generate the Stage B effect-scale validation result pack.",
    _producer("tools.maintenance.candidate_artifacts.effect_scale_result_pack"),
  ),
  "candidate-artifacts effect-scale-retained-pack": (
    "Write retained Stage B effect-scale candidate artifacts.",
    _producer("tools.maintenance.candidate_artifacts.effect_scale_retained_pack"),
  ),
  "candidate-artifacts runtime-authority-exercise": (
    "Generate the test-local runtime authority exercise pack.",
    _producer("tools.maintenance.candidate_artifacts.runtime_authority_exercise"),
  ),
  "candidate-artifacts package-bundle": (
    "Assemble the current candidate package bundle.",
    _producer("tools.maintenance.candidate_artifacts.package_bundle"),
  ),
  "candidate-artifacts component-probability-surface-probe": (
    "Generate the Stage C component-probability surface probe.",
    _producer("tools.maintenance.candidate_artifacts.component_probability_surface_probe"),
  ),
  "candidate-artifacts component-probability-snapshot": (
    "Generate the Stage C component-probability candidate snapshot.",
    _producer("tools.maintenance.candidate_artifacts.component_probability_snapshot"),
  ),
  "candidate-artifacts component-probability-result-pack": (
    "Generate the Stage C component-probability result pack.",
    _producer("tools.maintenance.candidate_artifacts.component_probability_result_pack"),
  ),
  "candidate-artifacts component-probability-retained-pack": (
    "Write retained Stage C component-probability artifacts.",
    _producer("tools.maintenance.candidate_artifacts.component_probability_retained_pack"),
  ),
  "candidate-artifacts component-probability-review-readiness": (
    "Evaluate Stage C component-probability review readiness.",
    _producer("tools.maintenance.candidate_artifacts.component_probability_review_readiness"),
  ),
  "candidate-artifacts component-fragility-validation-prep": (
    "Generate Stage C component-fragility validation review inputs.",
    _producer("tools.maintenance.candidate_artifacts.component_fragility_validation_prep"),
  ),
  "candidate-artifacts component-fragility-review-gate": (
    "Evaluate the Stage C component-fragility review gate.",
    _producer("tools.maintenance.candidate_artifacts.component_fragility_review_gate"),
  ),
  "candidate-artifacts component-fragility-benchmark": (
    "Generate blocked Stage C component-fragility benchmark evidence.",
    _producer("tools.maintenance.candidate_artifacts.component_fragility_benchmark"),
  ),
  # -- external-evidence ----------------------------------------------------
  "external-evidence intake-contract": (
    "Generate the fail-closed external signoff intake contract.",
    _producer("tools.maintenance.external_signoff_evidence.intake_contract"),
  ),
  "external-evidence packet-template": (
    "Generate a reviewer-fillable external signoff packet template.",
    _producer("tools.maintenance.external_signoff_evidence.packet_template"),
  ),
  "external-evidence admission-preflight": (
    "Generate the signoff admission preflight packet.",
    _producer("tools.maintenance.external_signoff_evidence.admission_preflight"),
  ),
  "external-evidence signoff-request": (
    "Generate the source-rights allowed-output signoff request packet.",
    _producer("tools.maintenance.external_signoff_evidence.signoff_request"),
  ),
  # -- independent-review ---------------------------------------------------
  "independent-review effect-scale-review": (
    "Evaluate bounded Stage B effect-scale independent review evidence.",
    _producer("tools.maintenance.independent_review.effect_scale_review"),
  ),
  "independent-review review-closeout": (
    "Evaluate RES-011/012 independent review closeout evidence.",
    _producer("tools.maintenance.independent_review.review_closeout"),
  ),
  "independent-review scope-bucket-review": (
    "Evaluate scope-bucket independent review evidence.",
    _producer("tools.maintenance.independent_review.scope_bucket_review"),
  ),
  "independent-review uncertainty-review": (
    "Evaluate uncertainty review evidence.",
    _producer("tools.maintenance.independent_review.uncertainty_review"),
  ),
  # -- release-governance ---------------------------------------------------
  "release-governance package-provenance-identity": (
    "Evaluate package provenance and surrogate identity boundaries.",
    _producer("tools.maintenance.release_governance.package_provenance_identity"),
  ),
  "release-governance provenance-identity-review": (
    "Evaluate retained provenance identity review evidence.",
    _producer("tools.maintenance.release_governance.provenance_identity_review"),
  ),
  "release-governance provenance-closeout": (
    "Evaluate release provenance closeout evidence.",
    _producer("tools.maintenance.release_governance.provenance_closeout"),
  ),
  "release-governance source-release-signoff": (
    "Evaluate source release signoff evidence.",
    _producer("tools.maintenance.release_governance.source_release_signoff"),
  ),
  "release-governance scoped-release-identity": (
    "Evaluate scoped release identity evidence.",
    _producer("tools.maintenance.release_governance.scoped_release_identity"),
  ),
  "release-governance effect-scale-readiness": (
    "Evaluate Stage B effect-scale release readiness.",
    _producer("tools.maintenance.release_governance.effect_scale_release_readiness"),
  ),
  "release-governance effect-scale-closeout": (
    "Evaluate Stage B effect-scale release closeout.",
    _producer("tools.maintenance.release_governance.effect_scale_release_closeout"),
  ),
  # -- retained-artifacts ---------------------------------------------------
  "retained-artifacts manifest-integrity": (
    "Check retained artifact manifest hashes and authority guards.",
    _producer("tools.maintenance.retained_artifacts.manifest_integrity"),
  ),
  # -- scope-provenance -----------------------------------------------------
  "scope-provenance row-provenance": (
    "Evaluate geometry and warhead row provenance boundaries.",
    _producer("tools.maintenance.scope_provenance.geometry_warhead_row_provenance"),
  ),
  "scope-provenance target-geometry-closeout": (
    "Evaluate target-geometry scope closeout evidence.",
    _producer("tools.maintenance.scope_provenance.target_geometry_closeout"),
  ),
  "scope-provenance warhead-scope-closeout": (
    "Evaluate warhead-family scope closeout evidence.",
    _producer("tools.maintenance.scope_provenance.warhead_scope_closeout"),
  ),
  "scope-provenance mechanism-source-closeout": (
    "Evaluate mechanism source closeout evidence.",
    _producer("tools.maintenance.scope_provenance.mechanism_source_closeout"),
  ),
  # -- source-governance ----------------------------------------------------
  "source-governance admission-audit": (
    "Audit source ledgers and candidate docs for fail-closed admission.",
    _producer("tools.maintenance.source_governance.admission_audit"),
  ),
  "source-governance payload-pack": (
    "Build or inspect the retained source payload pack.",
    _producer("tools.maintenance.source_governance.payload_pack"),
  ),
  "source-governance rights-output-policy": (
    "Evaluate the source rights and allowed-output policy gate.",
    _producer("tools.maintenance.source_governance.rights_output_policy"),
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
