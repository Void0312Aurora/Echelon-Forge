"""Opt-in report envelope: end-to-end demonstration on two real CLIs.

Track T5 second slice. Covers the two adopting tools named in the iteration
scope: ``tools/eval/naval_station_policy_eval.py`` and
``tools/diagnostics/calibration_admission_audit.py``. Every test here pins
the ``--report-envelope`` default (disabled -> byte-identical to the
pre-envelope output shape) as a negative test, then checks the opt-in
enabled shape against the same disabled-run payload.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

NAVAL_SCENARIO = REPO_ROOT / "scenarios" / "naval" / "ddg51_take1_screen_threat_roe_v1.json"
NAVAL_TRAIN_CONFIG = (
    REPO_ROOT
    / "examples"
    / "config"
    / "training"
    / "active"
    / "naval"
    / "naval_screen_station_hold_threat_aware_smoke_v1.json"
)

ENVELOPE_KEYS = {
    "envelope_schema_version",
    "tool_id",
    "generated_at",
    "git_rev",
    "experiment_ref",
    "payload",
}


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *argv],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


class TestNavalStationPolicyEvalReportEnvelope:
    BASE_ARGV = [
        "tools/eval/naval_station_policy_eval.py",
        "--scenario",
        str(NAVAL_SCENARIO),
        "--train_config",
        str(NAVAL_TRAIN_CONFIG),
        "--steps",
        "32",
        "--seed",
        "20260525",
    ]

    def test_default_disabled_output_keeps_the_original_top_level_shape(self) -> None:
        proc = _run(self.BASE_ARGV)
        assert proc.returncode in (0, 1), proc.stdout + proc.stderr
        payload = json.loads(proc.stdout)
        assert ENVELOPE_KEYS.isdisjoint(payload)
        assert {"mode", "scenario", "train_config", "passed"} <= set(payload)

    def test_default_disabled_json_out_file_matches_stdout_byte_for_byte(self, tmp_path: Path) -> None:
        json_out = tmp_path / "report.json"
        proc = _run([*self.BASE_ARGV, "--json_out", str(json_out)])
        assert proc.returncode in (0, 1), proc.stdout + proc.stderr
        file_text = json_out.read_text(encoding="utf-8")
        # The CLI writes the file without a trailing newline captured by
        # print(); the stdout capture strips the process's own trailing
        # newline, so compare the parsed payloads rather than raw text.
        assert json.loads(file_text) == json.loads(proc.stdout)

    def test_enabled_flag_wraps_the_disabled_runs_payload_unchanged(self) -> None:
        plain = _run(self.BASE_ARGV)
        enveloped = _run([*self.BASE_ARGV, "--report-envelope"])

        assert enveloped.returncode == plain.returncode
        plain_payload = json.loads(plain.stdout)
        envelope = json.loads(enveloped.stdout)

        assert set(envelope) == ENVELOPE_KEYS
        assert envelope["tool_id"] == "tools.eval.naval_station_policy_eval"
        assert envelope["envelope_schema_version"] == "1"
        assert envelope["payload"] == plain_payload

    def test_help_advertises_the_opt_in_flag_disabled_by_default(self) -> None:
        proc = _run(["tools/eval/naval_station_policy_eval.py", "--help"])
        assert proc.returncode == 0
        assert "--report-envelope" in proc.stdout


def _calibration_manifest() -> dict[str, object]:
    non_claims = [
        "real_world_pk",
        "deterministic_fuze_reliability",
        "reward_authority",
        "entity_deletion_authority",
        "out_of_scope_weapon_truth",
        "out_of_scope_target_truth",
    ]
    record = {
        "schema_version": "mlf10.calibration_evidence.v1",
        "evidence_id": "ENVELOPE-DEMO-001",
        "evidence_class": "engineering_proxy",
        "source_kind": "engineering_runtime_proxy",
        "source_ref": "repo://retained/example/manifest.json",
        "provenance": "report-envelope integration fixture",
        "rights_status": "repository_local",
        "source_gate_status": "not_applicable",
        "validation_status": "regression_passed",
        "scope": {
            "target_type": "F-16C_Block50",
            "weapon_family": "AIM-120C-class",
            "mechanism_family": "blast_fragmentation",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss_0_35m",
        },
        "population": {
            "identity": "unit test population v1",
            "denominator_name": "validated_case_count",
            "sample_count": 8,
            "filters": "scope axes exactly match",
            "independence_assumption": "fixture inputs are independent",
        },
        "uncertainty": {
            "method": "bootstrap_interval",
            "coverage": "95 percent interval over admitted cases",
            "residuals": [],
        },
        "independent_review": {"status": "passed", "reviewer_ref": "repo://retained/example/reviewer_signoff.json"},
        "authority_requests": {},
        "non_claims": non_claims,
        "residuals": [],
    }
    return {
        "schema_version": "mlf10.calibration_evidence_manifest.v1",
        "manifest_id": "report_envelope_integration_manifest",
        "non_claims": non_claims,
        "evidence_records": [record],
    }


class TestCalibrationAdmissionAuditReportEnvelope:
    def _write_manifest(self, tmp_path: Path) -> Path:
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(_calibration_manifest()), encoding="utf-8")
        return manifest_path

    def test_default_disabled_output_keeps_the_original_top_level_shape(self, tmp_path: Path) -> None:
        manifest_path = self._write_manifest(tmp_path)
        proc = _run(
            [
                "tools/diagnostics/calibration_admission_audit.py",
                "--manifest_json",
                str(manifest_path),
            ]
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        payload = json.loads(proc.stdout)
        assert ENVELOPE_KEYS.isdisjoint(payload)
        assert {"schema_version", "report_surface", "decision_counts", "decisions"} <= set(payload)
        assert payload["schema_version"] == "mlf10.calibration_admission_report.v1"

    def test_json_out_default_disabled_matches_stdout_default_shape(self, tmp_path: Path) -> None:
        manifest_path = self._write_manifest(tmp_path)
        json_out = tmp_path / "report.json"
        proc_stdout = _run(
            ["tools/diagnostics/calibration_admission_audit.py", "--manifest_json", str(manifest_path)]
        )
        proc_file = _run(
            [
                "tools/diagnostics/calibration_admission_audit.py",
                "--manifest_json",
                str(manifest_path),
                "--json_out",
                str(json_out),
            ]
        )
        assert proc_file.returncode == 0, proc_file.stdout + proc_file.stderr
        assert proc_file.stdout == ""
        assert json.loads(json_out.read_text(encoding="utf-8")) == json.loads(proc_stdout.stdout)

    def test_enabled_flag_wraps_the_disabled_runs_payload_unchanged(self, tmp_path: Path) -> None:
        manifest_path = self._write_manifest(tmp_path)
        plain = _run(["tools/diagnostics/calibration_admission_audit.py", "--manifest_json", str(manifest_path)])
        enveloped = _run(
            [
                "tools/diagnostics/calibration_admission_audit.py",
                "--manifest_json",
                str(manifest_path),
                "--report-envelope",
            ]
        )

        assert enveloped.returncode == plain.returncode == 0
        plain_payload = json.loads(plain.stdout)
        envelope = json.loads(enveloped.stdout)

        assert set(envelope) == ENVELOPE_KEYS
        assert envelope["tool_id"] == "tools.diagnostics.calibration_admission_audit"
        assert envelope["envelope_schema_version"] == "1"
        assert envelope["payload"] == plain_payload

    def test_help_advertises_the_opt_in_flag_disabled_by_default(self) -> None:
        proc = _run(["tools/diagnostics/calibration_admission_audit.py", "--help"])
        assert proc.returncode == 0
        assert "--report-envelope" in proc.stdout
