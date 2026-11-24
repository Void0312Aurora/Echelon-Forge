"""Fixed native CPU comparison and replay probe; run with ``python -m``.

The script imports bindings only at execution. Outputs retain the existing
TraceManifest schema and clearly label this as a candidate diagnostic.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from python.experiment.contracts import FIXED_PROTOCOL_PROVENANCE, content_digest
from python.experiment.native_pilot import (
    FlightAction,
    RuntimePilotActionBackend,
    SpeedChangeEvaluator,
)
from python.experiment.runtime_candidate import RuntimeCandidateError, RuntimeCandidateSession
from python.experiment.runtime_facade_observation import RuntimeFacadeAgentObservationProvider
from python.experiment.numeric_observation_adapter import (
    build_numeric_exports,
    collect_agent_observation_sources_from_packets,
    write_episode_store,
)
from python.experiment.report_envelope import add_report_envelope_arg, apply_report_envelope
from python.experiment.trace import manifest_from_payload
from python.experiment.trace_projection import CONSUMERS, SeedSplit, project_manifests


SEEDS = (19, 83, 191)
HORIZON = 20
TRAINING_SEEDS = (19, 83)
EVALUATION_SEEDS = (191,)


def compare_seed(
    ef_py: object,
    candidate_py: object,
    seed: int,
    *,
    horizon: int = HORIZON,
    numeric_export_root: Path | None = None,
) -> dict:
    if type(horizon) is not int or not 1 <= horizon <= 100:
        raise ValueError("comparison horizon must be between 1 and 100")
    native = candidate_py.RuntimeKernelCandidate(0x5254422D50494C54, seed, True, seed)
    if not native.start():
        raise RuntimeCandidateError("native pilot comparison failed to start")
    try:
        spawn = ef_py.WorldSpawnRequest()
        spawn.type_name = "Aircraft"
        spawn.entity_name = "comparison_aircraft"
        spawn.z = 3000.0
        spawn.vx = 150.0
        entity = native.spawn_unit(spawn)
        if not entity or not native.set_time_step(0.05):
            raise RuntimeCandidateError("native pilot comparison setup rejected")
        evaluator = SpeedChangeEvaluator()

        def observation_ref_factory(handle: object | None, _agent_id: str) -> object:
            source = native if handle is None else handle
            entity_id = int(getattr(source, "resolve_entity")("comparison_aircraft"))
            if entity_id <= 0:
                raise RuntimeCandidateError("native pilot observation ref entity is unavailable")
            ref = ef_py.WorldEntityRef()
            ref.world_index = 0
            ref.entity_id = entity_id
            return ref

        observation_provider = RuntimeFacadeAgentObservationProvider(
            native, observation_ref_factory, ("pilot",)
        )
        backend = RuntimePilotActionBackend(
            native,
            entity_bindings=(("pilot", "comparison_aircraft"),),
            catalog=(("idle", FlightAction(0)), ("full", FlightAction(1000))),
            evaluator=evaluator,
            action_factory=ef_py.PilotAction,
            assignment_factory=ef_py.WorldPilotActionAssignment,
            observation_provider=observation_provider,
            protocol_context=(
                ("altitude_m", 3000),
                ("speed_mps", 150),
                ("time_step_ms", 50),
                ("horizon", horizon),
            ),
        )
        session = RuntimeCandidateSession(
            session_id="native_pilot_comparison",
            backend_id="runtime_candidate",
            scenario_ref="scenario:fixed_single_aircraft",
            config_digest=backend.config_digest,
            seed=seed,
            agent_ids=("pilot",),
            policy_ref="policy:fixed_open_loop_throttle",
            backend=backend,
        )
        # Native checkpoint qualification currently needs a nonzero boundary.
        session.step({"pilot": "idle"}, observation_provenance=FIXED_PROTOCOL_PROVENANCE)
        saved = session.checkpoint()
        source_trace = session.trace(session.baseline)
        initial_speed = evaluator.measure(native.observation(entity))
        branches = []
        branch_refs = []
        for symbol in ("idle", "full"):
            branch = session.restore(
                saved, intervention={"pilot": symbol}, label=symbol, horizon=horizon
            )
            branch_saved = session.checkpoint(branch)
            for _ in range(horizon):
                session.step_branch(
                    branch, {"pilot": symbol}, observation_provenance=FIXED_PROTOCOL_PROVENANCE
                )
            trace = session.trace(branch)
            # replay verifies complete transitions including per-step rewards,
            # state/RNG digests, action symbols, and coordinator sequence.
            replayed = session.replay(branch, branch_saved, label=f"replay_{symbol}")
            if session.head(branch) != session.head(replayed):
                raise RuntimeCandidateError("native pilot replay head changed")
            reward = sum(dict(item.rewards)["pilot"] for item in trace.transitions)
            branches.append(
                {
                    "action": symbol,
                    "initial_speed_mmps": initial_speed,
                    "final_speed_mmps": initial_speed + reward,
                    "reward_sum_mmps": reward,
                    "state_digest": session.head(branch).state_digest,
                    "branch_digest": branch.digest,
                    "replay_branch_digest": replayed.digest,
                    "replay_verified_steps": len(trace.transitions),
                    "agent_observation_ref_count": len(
                        session.agent_observation_ref_series("pilot", branch)
                    ),
                }
            )
            branch_refs.append(branch)
            if session.head() != saved or session.trace(session.baseline) != source_trace:
                raise RuntimeCandidateError("comparison mutated its source branch")
        if branches[0]["final_speed_mmps"] == branches[1]["final_speed_mmps"]:
            raise RuntimeCandidateError(
                "alternative controls produced no measured speed difference"
            )
        projection = project_manifests(
            (session.manifest(),),
            SeedSplit(training=TRAINING_SEEDS, evaluation=EVALUATION_SEEDS),
            consumer="ppo",
            selected_branch_digests=[branch.digest for branch in branch_refs],
        )
        packet_sources = collect_agent_observation_sources_from_packets(
            session.agent_observation_packet_sources("pilot", branch_refs),
            agent_id="pilot",
            fields=("speed", "health"),
            selected_branch_digests=[branch.digest for branch in branch_refs],
        )
        numeric_exports = build_numeric_exports(
            projection,
            packet_sources,
            agent_id="pilot",
            selected_branch_digests=[branch.digest for branch in branch_refs],
            action_encoder=lambda row: (1.0 if row.actions[0][1] == "full" else 0.0,),
            reward_encoder=lambda row: float(sum(value for _, value in row.rewards)),
        )
        numeric_export_receipt = None
        if numeric_export_root is not None:
            numeric_export_receipt = write_episode_store(
                numeric_exports,
                str(numeric_export_root / f"seed-{seed}"),
            )
        return {
            "seed": seed,
            "protocol": backend.protocol_payload(),
            "protocol_digest": backend.config_digest,
            "source_snapshot_digest": saved.digest,
            "source_isolation_verified": True,
            "agent_observation_refs": True,
            "numeric_export": {
                "consumer": projection.consumer,
                "projection_digest": projection.digest,
                "agent_id": "pilot",
                "persisted": numeric_export_receipt is not None,
                "metadata_digest": (
                    None
                    if numeric_export_receipt is None
                    else numeric_export_receipt.metadata_digest
                ),
                "episodes": [
                    {
                        "branch_digest": export.branch_digest,
                        "split": export.split,
                        "observation_count": int(export.observations.shape[0]),
                        "transition_count": int(export.actions.shape[0]),
                        "observation_dim": int(export.observations.shape[1]),
                        "action_dim": int(export.actions.shape[1]),
                        "packet_provenance": export.observation_provenance,
                    }
                    for export in numeric_exports
                ],
            },
            "branches": branches,
            "full_minus_idle_mmps": branches[1]["final_speed_mmps"]
            - branches[0]["final_speed_mmps"],
            "manifest": session.manifest().to_payload(),
        }
    finally:
        if not native.shutdown():
            raise RuntimeCandidateError("native pilot comparison shutdown failed")


def build_trace_projection_summary(runs: list[dict]) -> dict:
    """Regenerate audited consumer projections from the report manifests."""

    manifests = tuple(manifest_from_payload(run["manifest"]) for run in runs)
    split_spec = SeedSplit(training=TRAINING_SEEDS, evaluation=EVALUATION_SEEDS)
    # Project the compared alternatives only; replay and warmup branches repeat
    # or precede them and would double-count rows.
    compared = [branch["branch_digest"] for run in runs for branch in run["branches"]]
    consumers = {}
    for consumer in CONSUMERS:
        projection = project_manifests(
            manifests, split_spec, consumer=consumer, selected_branch_digests=compared
        )
        rows_by_split = {
            split: sum(row.split == split for row in projection.rows)
            for split in ("training", "evaluation")
        }
        consumers[consumer] = {
            "projection_digest": projection.digest,
            "rows": len(projection.rows),
            "rows_by_split": rows_by_split,
            "manifest_digests": list(projection.manifest_digests),
        }
    return {
        "schema": "echelon_forge.experiment_trace_projection_summary.v1",
        "split_spec": split_spec.to_payload(),
        "consumers": consumers,
    }


def summarize_runs(runs: list[dict]) -> list[dict]:
    """Replace each run's full TraceManifest payload with its digest.

    The summary keeps every per-seed result and branch identity, so it still
    shows what was compared and lets a regenerated full report be checked
    against it. The per-step manifests are reproducible with the same command
    without ``--summary``.
    """

    summarized = []
    for run in runs:
        compact = {key: value for key, value in run.items() if key != "manifest"}
        compact["manifest_digest"] = manifest_from_payload(run["manifest"]).digest
        summarized.append(compact)
    return summarized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--numeric-export-root",
        type=Path,
        help="write explicitly selected PPO episodes under seed-* directories",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="replace each run's TraceManifest payload with its digest",
    )
    add_report_envelope_arg(parser)
    args = parser.parse_args()
    import ef_py
    import ef_runtime_candidate_py

    protocol = {
        "seeds": list(SEEDS),
        "horizon": HORIZON,
        "evaluation": "speed_change_mmps_v1",
        "paired_controls": ["idle", "full"],
        "time_step_ms": 50,
        "altitude_m": 3000,
        "speed_mps": 150,
        "warmup_actions": ["idle"],
        "policy_observation": FIXED_PROTOCOL_PROVENANCE,
    }
    runs = [
        compare_seed(
            ef_py,
            ef_runtime_candidate_py,
            seed,
            numeric_export_root=args.numeric_export_root,
        )
        for seed in SEEDS
    ]
    report = {
        "schema": "echelon_forge.native_pilot_comparison.v1",
        "evidence_label": "runtime_candidate",
        "scope": "in_process_cpu_fixed_flight_control_diagnostic",
        "protocol": protocol,
        "protocol_digest": content_digest("experiment.native-pilot-comparison", protocol),
        "runs": summarize_runs(runs) if args.summary else runs,
        "trace_projection": build_trace_projection_summary(runs),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output = apply_report_envelope(
        report,
        enabled=args.report_envelope,
        tool_id="native_pilot_comparison",
        experiment_ref=report["protocol_digest"],
    )
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "seeds": list(SEEDS),
                "full_minus_idle_mmps": [run["full_minus_idle_mmps"] for run in report["runs"]],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
