from __future__ import annotations

import subprocess
from pathlib import Path

from tools.maintenance.internal_code_governance import audit as audit_module
from tools.maintenance.internal_code_governance import scan_text
from tools.maintenance.internal_code_governance.__main__ import exit_code


REPO_ROOT = Path(__file__).resolve().parents[3]
MAINTAINED_ENTRY_POINT_DOCUMENTS = (
  "README.md",
  "README.zh.md",
  "docs/README.md",
  "docs/README.zh.md",
  "docs/engineering/README.md",
  "docs/engineering/README.zh.md",
  "docs/engineering/documentation/README.md",
  "docs/engineering/documentation/README.zh.md",
  "tools/README.md",
)


def _initialize_git_repository(path: Path) -> None:
  subprocess.run(["git", "init", "-q"], cwd=path, check=True)
  subprocess.run(
    ["git", "config", "user.email", "governance-test@example.invalid"],
    cwd=path,
    check=True,
  )
  subprocess.run(
    ["git", "config", "user.name", "Governance Test"],
    cwd=path,
    check=True,
  )
  (path / "README.md").write_text("# Test\n", encoding="utf-8")
  subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
  subprocess.run(["git", "commit", "-qm", "baseline"], cwd=path, check=True)


def test_runtime_strings_reject_work_tracking_codes() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    'throw std::logic_error("CUDA RB7 supports only fixed-air setup");\n',
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("runtime-tracking-code", "RB7")
  ]


def test_production_identifiers_reject_work_tracking_codes() -> None:
  result = scan_text(
    "python/rl/runtime/backend.py",
    "rb8_replay_budget = load_budget()\n",
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("source-tracking-code", "rb8")
  ]


def test_camel_case_identifiers_reject_tracking_and_phase_codes() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    "class CudaResidentRB7Backend {};\nstruct CudaResidentPhaseBState {};\n",
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("source-tracking-code", "RB7"),
    ("opaque-phase-identifier", "PhaseB"),
  ]


def test_acronym_identifiers_reject_embedded_tracking_and_phase_codes() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    "class CUDARB7Backend {};\nstruct CUDAPHASEBState {};\n",
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("source-tracking-code", "RB7"),
    ("opaque-phase-identifier", "PHASEB"),
  ]


def test_technical_abbreviations_do_not_match_embedded_internal_codes() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    "I18nFormatter formatter;\nVectorI32 lanes;\nBROADPHASEBatch batch;\n",
  )

  assert result.findings == ()


def test_camel_and_pascal_identifiers_reject_issue_tracking_codes() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    "auto cudaResidentI94Backend = make_backend();\n"
    "class CudaResidentI94Backend {};\n",
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("source-tracking-code", "I94"),
    ("source-tracking-code", "I94"),
  ]


def test_production_paths_reject_issue_tracking_codes() -> None:
  findings = audit_module.scan_path_name(
    "src/runtime/CudaResidentI94Backend.cpp"
  )

  assert [(finding.code, finding.token) for finding in findings] == [
    ("source-tracking-code-path", "I94")
  ]


def test_production_paths_reject_tracking_and_camel_phase_codes() -> None:
  tracking = audit_module.scan_path_name(
    "src/CudaResidentRB7Backend/runtime.cpp"
  )
  phase = audit_module.scan_path_name(
    "src/runtime/CudaResidentPhaseBState.cpp"
  )

  assert [(finding.code, finding.token) for finding in tracking] == [
    ("source-tracking-code-path", "RB7")
  ]
  assert [(finding.code, finding.token) for finding in phase] == [
    ("opaque-phase-path", "PhaseB")
  ]


def test_broadphase_batch_is_not_a_lettered_phase_identifier() -> None:
  source = scan_text(
    "src/runtime/broadphase_batch.cpp",
    "auto broadphase_batch = build_interaction_broadphase_batch();\n",
  )
  path_findings = audit_module.scan_path_name(
    "src/runtime/broadphase_batch.cpp"
  )

  assert source.findings == ()
  assert path_findings == ()


def test_source_comments_warn_without_blocking() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    "// RB7 originally introduced this fixed-air projection.\n",
  )

  assert result.errors == ()
  assert [(finding.code, finding.token) for finding in result.warnings] == [
    ("source-tracking-code-comment", "RB7")
  ]


def test_cpp_block_comments_warn_without_becoming_source_errors() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    "/* RB7 originally introduced this path.\n"
    " * Phase B was the old local name. */\n"
    "run_semantic_stage();\n",
  )

  assert result.errors == ()
  assert [(finding.code, finding.token) for finding in result.warnings] == [
    ("source-tracking-code-comment", "RB7"),
    ("opaque-phase-comment", "Phase B"),
  ]


def test_selected_line_scan_preserves_multiline_block_comment_state() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    "/* historical note\n * RB7 introduced the old path.\n */\n",
    line_numbers={2},
  )

  assert result.errors == ()
  assert [(finding.code, finding.token) for finding in result.warnings] == [
    ("source-tracking-code-comment", "RB7")
  ]


def test_block_comment_markers_inside_strings_remain_runtime_text() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    'const char* message = "/* RB7 */";\n',
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("runtime-tracking-code", "RB7")
  ]


def test_python_triple_quoted_comment_markers_remain_runtime_text() -> None:
  result = scan_text(
    "python/rl/runtime/backend.py",
    'message = """\n# RB7 remains runtime text\n"""\n',
    line_numbers={2},
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("runtime-tracking-code", "RB7")
  ]
  assert result.warnings == ()


def test_cpp_raw_string_comment_markers_remain_runtime_text() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    'const char* message = R"tag(\n/* RB7 remains runtime text */\n)tag";\n',
    line_numbers={2},
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("runtime-tracking-code", "RB7")
  ]
  assert result.warnings == ()


def test_comment_markers_inside_strings_do_not_hide_runtime_codes() -> None:
  result = scan_text(
    "python/rl/runtime/backend.py",
    'raise RuntimeError("replay # RB8 is unavailable")\n',
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("runtime-tracking-code", "RB8")
  ]


def test_actual_comments_after_string_markers_remain_comments() -> None:
  result = scan_text(
    "python/rl/runtime/backend.py",
    'marker = "#"  # RB8 introduced the old replay path\n',
  )

  assert result.errors == ()
  assert [(finding.code, finding.token) for finding in result.warnings] == [
    ("source-tracking-code-comment", "RB8")
  ]


def test_phase_identifiers_require_an_explicit_compatibility_marker() -> None:
  blocked = scan_text(
    "src/runtime/contracts/schema.h",
    "const char* phase_b_schema = value;\n",
  )
  compatible = scan_text(
    "src/runtime/contracts/schema.h",
    "// internal-code: compatibility\nconst char* phase_b_schema = value;\n",
  )

  assert [(finding.code, finding.token) for finding in blocked.errors] == [
    ("opaque-phase-identifier", "phase_b_schema")
  ]
  assert compatible.findings == ()


def test_phase_runtime_text_and_uppercase_identifiers_are_blocked() -> None:
  result = scan_text(
    "src/runtime/contracts/schema.h",
    'const char* message = "supports only Phase A/B/D";\nint PHASE_B_STATE = 0;\n',
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("opaque-phase-runtime-string", "Phase A/B/D"),
    ("opaque-phase-identifier", "PHASE_B_STATE"),
  ]


def test_semantic_phase_words_do_not_match_lettered_phase_codes() -> None:
  result = scan_text(
    "src/runtime/contracts/schema.h",
    "int phaseBoundary = 0;\n"
    "int broadphase_batch = 0;\n"
    "int phase_bucket = 0;\n"
    "int phase_default = 0;\n"
    "int phase_command_expectations = 0;\n",
  )
  path_findings = audit_module.scan_path_name(
    "src/runtime/phase_bucket/phase_default/phase_command_expectations.inc"
  )

  assert result.findings == ()
  assert path_findings == ()


def test_hyphenated_phase_runtime_text_is_blocked() -> None:
  result = scan_text(
    "src/runtime/contracts/schema.h",
    'const char* message = "requires a committed Phase-D window";\n',
  )

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("opaque-phase-runtime-string", "Phase-D")
  ]


def test_new_phase_named_production_paths_are_blocked() -> None:
  findings = audit_module.scan_path_name(
    "src/runtime/cuda/cuda_world_store_phase_b.cu"
  )

  assert [(finding.code, finding.token) for finding in findings] == [
    ("opaque-phase-path", "phase_b")
  ]


def test_document_definitions_are_distinct_from_bare_references() -> None:
  result = scan_text(
    "docs/task/runtime/README.md",
    "RB7: fixed-air observation projection.\nRB7 is now complete.\n",
  )

  assert [(finding.line, finding.token) for finding in result.warnings] == [
    (2, "RB7")
  ]


def test_maintained_entry_points_have_no_bare_internal_codes() -> None:
  result = audit_module.audit_paths(REPO_ROOT, MAINTAINED_ENTRY_POINT_DOCUMENTS)

  assert result.findings == ()


def test_policy_documents_can_define_the_examples_they_govern() -> None:
  result = scan_text(
    "docs/engineering/documentation/standards/internal_code_policy.md",
    "Do not expose RB7 or phase_b.\n",
  )

  assert result.findings == ()


def test_added_line_parser_tracks_only_new_line_numbers() -> None:
  diff = """diff --git a/src/a.cpp b/src/a.cpp
--- a/src/a.cpp
+++ b/src/a.cpp
@@ -2,0 +3,2 @@
+clean();
+fail(\"RB7\");
@@ -8 +10 @@
-old();
+new_value();
"""

  assert audit_module.parse_added_line_numbers(diff) == {
    "src/a.cpp": {3, 4, 10}
  }


def test_name_status_parser_selects_added_and_rename_destinations() -> None:
  status = "A\0src/new.cpp\0R100\0src/phase_b.cu\0src/flight_dynamics.cu\0"

  assert audit_module.parse_added_or_renamed_paths(status) == {
    "src/new.cpp",
    "src/flight_dynamics.cu",
  }


def test_incremental_audit_includes_untracked_production_files(tmp_path: Path) -> None:
  _initialize_git_repository(tmp_path)
  source = tmp_path / "src/runtime/new_backend.cpp"
  source.parent.mkdir(parents=True)
  source.write_text('throw_error("RB7 leaked");\n', encoding="utf-8")

  result = audit_module.audit_changed_lines(tmp_path, "HEAD")

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("runtime-tracking-code", "RB7")
  ]


def test_incremental_audit_scans_changed_inc_source(tmp_path: Path) -> None:
  _initialize_git_repository(tmp_path)
  source = tmp_path / "src/runtime/detail/schema.inc"
  source.parent.mkdir(parents=True)
  source.write_text("EF_FIELD(int, semantic_budget)\n", encoding="utf-8")
  subprocess.run(["git", "add", source.relative_to(tmp_path)], cwd=tmp_path, check=True)
  subprocess.run(["git", "commit", "-qm", "add schema"], cwd=tmp_path, check=True)
  source.write_text("EF_FIELD(int, rb7_budget)\n", encoding="utf-8")

  result = audit_module.audit_changed_lines(tmp_path, "HEAD")

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("source-tracking-code", "rb7")
  ]
  assert result.files_checked == 1


def test_incremental_audit_scans_complete_renamed_inc_source(tmp_path: Path) -> None:
  _initialize_git_repository(tmp_path)
  source = tmp_path / "src/runtime/detail/schema.inc"
  source.parent.mkdir(parents=True)
  source.write_text("EF_FIELD(int, phase_b_state)\n", encoding="utf-8")
  subprocess.run(["git", "add", source.relative_to(tmp_path)], cwd=tmp_path, check=True)
  subprocess.run(["git", "commit", "-qm", "add legacy schema"], cwd=tmp_path, check=True)
  destination = source.with_name("renamed_schema.inc")
  subprocess.run(
    ["git", "mv", source.relative_to(tmp_path), destination.relative_to(tmp_path)],
    cwd=tmp_path,
    check=True,
  )

  result = audit_module.audit_changed_lines(tmp_path, "HEAD")

  assert [(finding.code, finding.token) for finding in result.errors] == [
    ("opaque-phase-identifier", "phase_b_state")
  ]
  assert result.files_checked == 1
  assert result.lines_checked == 1


def test_selected_line_scan_does_not_block_legacy_context() -> None:
  result = scan_text(
    "src/runtime/backend.cpp",
    'throw_error("RB7 legacy");\nrun_semantic_stage();\n',
    line_numbers={2},
  )

  assert result.findings == ()
  assert result.lines_checked == 1


def test_irrelevant_files_do_not_inflate_audit_counts() -> None:
  result = scan_text("tests/runtime/test_backend.py", "RB7\n")

  assert result.files_checked == 0
  assert result.lines_checked == 0
  assert result.findings == ()


def test_exit_threshold_keeps_document_warnings_non_blocking() -> None:
  result = scan_text("docs/task/README.md", "Continue RB7.\n")

  assert exit_code(result, "error") == 0
  assert exit_code(result, "warning") == 1
  assert exit_code(result, "never") == 0


def test_internal_code_governance_modules_stay_below_1000_lines() -> None:
  package = REPO_ROOT / "tools/maintenance/internal_code_governance"
  line_counts = {
    path.name: len(path.read_text(encoding="utf-8").splitlines())
    for path in package.glob("*.py")
  }

  assert line_counts
  assert {name: count for name, count in line_counts.items() if count >= 1000} == {}


def test_internal_code_policy_is_registered_and_indexed() -> None:
  standards = (REPO_ROOT / "docs/engineering/documentation/README.md").read_text(encoding="utf-8")
  standards_zh = (REPO_ROOT / "docs/engineering/documentation/README.zh.md").read_text(encoding="utf-8")
  policy = REPO_ROOT / "docs/engineering/documentation/standards/internal_code_policy.md"
  policy_zh = REPO_ROOT / "docs/engineering/documentation/standards/internal_code_policy.zh.md"

  assert policy.is_file()
  assert policy_zh.is_file()
  assert "standards/internal_code_policy.md" in standards
  assert "standards/internal_code_policy.zh.md" in standards_zh
