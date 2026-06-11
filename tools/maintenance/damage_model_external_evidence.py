#!/usr/bin/env python3
"""Unified external signoff evidence CLI for damage-model maintenance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.external_signoff_evidence import (  # noqa: E402
    admission_preflight,
    intake_contract,
    packet_template,
    signoff_request,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _run_intake_contract(args: argparse.Namespace) -> int:
    artifact = intake_contract.write_retained_artifacts(
        retained_dir=args.retained_dir,
        source_rights_signoff_request_packet_path=args.source_rights_signoff_request_packet,
        candidate_signoff_packet_path=args.candidate_signoff_packet,
    )
    if args.output:
        _write_json(args.output, artifact)
    return 0


def _run_packet_template(args: argparse.Namespace) -> int:
    template = packet_template.write_retained_artifacts(
        retained_dir=args.retained_dir,
        source_rights_signoff_request_packet_path=args.source_rights_signoff_request_packet,
    )
    if args.output:
        _write_json(args.output, template)
    return 0


def _run_admission_preflight(args: argparse.Namespace) -> int:
    artifact = admission_preflight.write_retained_artifacts(
        retained_dir=args.retained_dir,
        signoff_intake_contract_path=args.signoff_intake_contract,
        candidate_signoff_packet_path=args.candidate_signoff_packet,
    )
    if args.output:
        _write_json(args.output, artifact)
    return 0


def _run_signoff_request(args: argparse.Namespace) -> int:
    artifact = signoff_request.write_retained_artifacts(
        retained_dir=args.retained_dir,
        source_rights_output_policy_gate_path=args.source_rights_output_policy_gate,
        source_payload_pack_manifest_path=args.source_payload_pack_manifest,
        res005_selected_case_gate_path=args.res005_selected_case_gate,
        res006_replacement_tolerance_gate_path=args.res006_replacement_tolerance_gate,
    )
    if args.output:
        _write_json(args.output, artifact)
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate damage-model external signoff evidence artifacts without "
            "granting approval, admission, or runtime authority."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    intake = subparsers.add_parser(
        "intake-contract",
        help="Generate the fail-closed external signoff intake contract.",
    )
    intake.add_argument(
        "--output",
        type=Path,
        help="Optional path for a copy of the generated contract JSON.",
    )
    intake.add_argument(
        "--retained-dir",
        type=Path,
        default=intake_contract.DEFAULT_RETAINED_DIR,
        help="Directory for retained signoff intake contract artifacts.",
    )
    intake.add_argument(
        "--source-rights-signoff-request-packet",
        type=Path,
        default=intake_contract.SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH,
        help="Current source-rights signoff request packet JSON.",
    )
    intake.add_argument(
        "--candidate-signoff-packet",
        type=Path,
        help="Optional external signoff packet to shape-check without consuming it.",
    )
    intake.set_defaults(func=_run_intake_contract)

    template = subparsers.add_parser(
        "packet-template",
        help="Generate a reviewer-fillable external signoff packet template.",
    )
    template.add_argument(
        "--output",
        type=Path,
        help="Optional path for a copy of the generated template JSON.",
    )
    template.add_argument(
        "--retained-dir",
        type=Path,
        default=packet_template.DEFAULT_RETAINED_DIR,
        help="Directory for retained external signoff packet template artifacts.",
    )
    template.add_argument(
        "--source-rights-signoff-request-packet",
        type=Path,
        default=intake_contract.SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH,
        help="Current source-rights signoff request packet JSON.",
    )
    template.set_defaults(func=_run_packet_template)

    preflight = subparsers.add_parser(
        "admission-preflight",
        help="Generate the signoff admission preflight packet.",
    )
    preflight.add_argument(
        "--output",
        type=Path,
        help="Optional path for a copy of the generated preflight packet JSON.",
    )
    preflight.add_argument(
        "--retained-dir",
        type=Path,
        default=admission_preflight.DEFAULT_RETAINED_DIR,
        help="Directory for retained signoff admission preflight artifacts.",
    )
    preflight.add_argument(
        "--signoff-intake-contract",
        type=Path,
        default=admission_preflight.DEFAULT_SIGNOFF_INTAKE_CONTRACT_PATH,
        help="Current retained signoff intake contract JSON.",
    )
    preflight.add_argument(
        "--candidate-signoff-packet",
        type=Path,
        help="Optional external signoff packet to shape-check without consuming.",
    )
    preflight.set_defaults(func=_run_admission_preflight)

    request = subparsers.add_parser(
        "signoff-request",
        help="Generate the source-rights allowed-output signoff request packet.",
    )
    request.add_argument(
        "--output",
        type=Path,
        help="Optional path for a copy of the generated request packet JSON.",
    )
    request.add_argument(
        "--retained-dir",
        type=Path,
        default=signoff_request.DEFAULT_RETAINED_DIR,
        help="Directory for retained source-rights signoff request artifacts.",
    )
    request.add_argument(
        "--source-rights-output-policy-gate",
        type=Path,
        default=signoff_request.SOURCE_RIGHTS_OUTPUT_POLICY_GATE_PATH,
        help="Existing source-rights output policy gate JSON.",
    )
    request.add_argument(
        "--source-payload-pack-manifest",
        type=Path,
        default=signoff_request.SOURCE_PAYLOAD_PACK_MANIFEST_PATH,
        help="Existing source payload pack manifest JSON.",
    )
    request.add_argument(
        "--res005-selected-case-gate",
        type=Path,
        default=signoff_request.RES005_SELECTED_CASE_GATE_PATH,
        help="Optional current RES-005 TP-21 selected-case packet JSON.",
    )
    request.add_argument(
        "--res006-replacement-tolerance-gate",
        type=Path,
        default=signoff_request.RES006_REPLACEMENT_TOLERANCE_GATE_PATH,
        help="Optional current RES-006 BEC-O replacement/tolerance packet JSON.",
    )
    request.set_defaults(func=_run_signoff_request)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
