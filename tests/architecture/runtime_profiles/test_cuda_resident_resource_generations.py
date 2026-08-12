"""Generation-supersession gates for the resource-evidence capture chain.

Split from test_cuda_resident_resource_evidence.py at CP-7b to keep both
modules under the 700-line soft target. Each generation's test pins the same
three claims: the new identity declares what it replaces, the structural
correspondence to its predecessor is a static assert in the contract, and the
frozen predecessors stay untouched so their tracked evidence keeps hashing.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_resource_evidence_contract.h"
PROBE = ROOT / "src/tools/experimental/cuda_resident/cuda_resident_resource_probe.cpp"


def test_v2_capture_supersedes_v1_without_reviving_the_retired_probe() -> None:
    """The v2 recapture must supersede v1, not revert its retirement.

    Since CP-5, v2 is itself frozen history: its catalog names the pre-fusion
    symbols, which the retained v2 static and counter evidence hashes against.
    The v2 identity, migration table, and static asserts must therefore stay in
    the contract untouched -- editing them to match the fused sources would
    invalidate that evidence exactly as relabeling v1 would have.
    """
    contract = CONTRACT.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")

    # v2 identity is distinct from v1 and declares what it replaces.
    assert "cuda_resident.cp.resource_capture_probe.v2" in contract
    assert "cuda_resident.cp.kernel_resource_evidence.v2" in contract
    assert "cp.resource.steady_full_window_body.sm86.v2" in contract
    assert "kProbeSchemaV2Predecessor = kProbeSchemaV1" in contract

    # The retirement marker survives: neither v2 nor v3 flips it back.
    assert "kCaptureProbeV1Retired = true" in contract
    assert "static_assert(evidence::kCaptureProbeV1Retired);" in probe

    # Compile-time enforcement that v2 describes the same graph as v1.
    for guard in (
        "static_assert(kKernelSpecsV2.size() == 10);",
        "static_assert(kLaunchSequenceV2.size() == 12);",
        "static_assert(kernel_catalog_v2_is_complete());",
        "static_assert(kernel_migration_is_total());",
        "static_assert(launch_sequences_correspond());",
    ):
        assert guard in contract

    # The frozen v2 catalog keeps naming the pre-fusion symbols.
    for symbol in (
        "flight_dynamics_forces_kernel",
        "flight_dynamics_aerodynamics_kernel",
        "flight_dynamics_integrate_kernel",
        "instrument_projection_kernel",
        "configuration_projection_kernel",
        "episode_projection_kernel",
    ):
        assert f'"{symbol}"' in contract, f"v2 catalog is missing {symbol}"


def test_v3_capture_supersedes_v2_against_the_fused_window_graph() -> None:
    """v3 is a deliberate execution-graph change, not a relabel.

    CP-5 fused the six window-commit launches into one kernel. That claim is
    checked structurally: the v3 catalog exists with a fold table that is total
    on v2 and surjective onto v3, launch correspondence across the fold is a
    static assert, every v3 symbol is emitted by the current .cu sources, and
    the probe aligns its rows against v3 while the workload digest stays the
    frozen one.
    """
    contract = CONTRACT.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")

    # v3 identity is distinct and declares what it replaces.
    assert "cuda_resident.cp.resource_capture_probe.v3" in contract
    assert "cuda_resident.cp.kernel_resource_evidence.v3" in contract
    assert "cp.resource.steady_full_window_body.sm86.v3" in contract
    assert "kProbeSchemaV3Predecessor = kProbeSchemaV2" in contract

    # Compile-time enforcement of the fold claim.
    for guard in (
        "static_assert(kKernelSpecsV3.size() == 5);",
        "static_assert(kLaunchSequenceV3.size() == 7);",
        "static_assert(kernel_catalog_v3_is_complete());",
        "static_assert(kernel_fold_is_total_and_surjective());",
        "static_assert(launch_sequences_correspond_v2_to_v3());",
    ):
        assert guard in contract

    # Since CP-7b, v3 is frozen history: its catalog symbols stay pinned in the
    # contract because the tracked v3 static evidence hashes against them.
    for symbol in (
        "apply_barrier_kernel",
        "control_preparation_kernel",
        "window_commit_body_kernel",
        "pack_device_observation_kernel",
        "device_observation_consumer_smoke_kernel",
    ):
        assert f'"{symbol}"' in contract, f"v3 catalog is missing {symbol}"
    assert probe  # the probe surface is asserted by the v4 test below


def test_v4_capture_supersedes_v3_against_the_folded_launch_graph() -> None:
    """v4 is a launch fold, not a kernel change, and says so structurally.

    CP-7b folded the stage_publish and window_commit barrier launches into
    their stage kernels. The v4 catalog must therefore name the same five
    kernels as v3 with apply_barrier down to one launch, the absorption walk
    must be a static assert, every v4 symbol must be emitted by the current
    .cu sources, and the probe must align fail-closed against v4 while the
    workload digest stays the frozen one.
    """
    contract = CONTRACT.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")

    # v4 identity is distinct and declares what it replaces.
    assert "cuda_resident.cp.resource_capture_probe.v4" in contract
    assert "cuda_resident.cp.kernel_resource_evidence.v4" in contract
    assert "cp.resource.steady_full_window_body.sm86.v4" in contract
    assert "kProbeSchemaV4Predecessor = kProbeSchemaV3" in contract

    # Compile-time enforcement of the launch-absorption claim.
    for guard in (
        "static_assert(kKernelSpecsV4.size() == 5);",
        "static_assert(kLaunchSequenceV4.size() == 5);",
        "static_assert(kernel_catalog_v4_is_complete());",
        "static_assert(kernel_sets_match_v3_to_v4());",
        "static_assert(launch_sequences_correspond_v3_to_v4());",
    ):
        assert guard in contract

    # Every v4 kernel must name the symbol the current sources actually emit,
    # and the folded stages must carry compound names so the barriers are
    # never read as removed.
    cuda_dir = ROOT / "src/runtime/facade/internal/cuda_resident"
    emitted_blob = "\n".join(
        source.read_text(encoding="utf-8") for source in cuda_dir.glob("*.cu")
    )
    for symbol in (
        "apply_barrier_kernel",
        "control_preparation_kernel",
        "window_commit_body_kernel",
        "pack_device_observation_kernel",
        "device_observation_consumer_smoke_kernel",
    ):
        assert f"{symbol}(" in emitted_blob, (
            f"v4 catalog names {symbol}, which no .cu source emits"
        )
    assert '"control_preparation_and_stage_publish"' in contract
    assert '"window_commit_body_and_window_commit"' in contract

    # The probe must fail closed on catalog drift rather than emit a plausible
    # report -- the exact gap that let the rename go unnoticed.
    assert "require_catalog_alignment" in probe
    assert "kKernelSpecsV4" in probe
    assert "absorption_json" in probe
    # A static capture must never be mistaken for a counter capture.
    assert '"achieved_counters_present", false' in probe
    # A recapture grants no new authority.
    for withheld in (
        "kMaintainedClaimAllowed",
        "kPublicSupportEnabled",
        "kPromotionAllowed",
        "kTuningAuthorized",
    ):
        assert withheld in probe
