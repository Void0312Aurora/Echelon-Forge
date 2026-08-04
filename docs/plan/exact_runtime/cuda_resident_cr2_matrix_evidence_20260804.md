# CR2-6b production-matrix evidence

Date: 2026-08-04

Source commit: `0c24a07549e238222741da6b20100537e7a9be22`

Status: **matrix evidence and an experimental selection advisory are complete;
maintained support, tuning, and promotion remain closed.**

## Scope

This evidence runs the CR2-6a Release CPU and CUDA probes twice under the full
`1/4/16/64/256`-world protocol. Campaign 1 uses CPU then CUDA; campaign 2 uses
CUDA then CPU. Lanes never run concurrently. Comparisons cover only the two
common modes and four metrics: warmed end-to-end p50/p95 and rollout-per-window
p50/p95. CUDA-only device-consumer modes are availability evidence, not fake CPU
comparisons.

The advisory targets steady windows, so setup and cold families remain recorded
but are not routing inputs. With 10 rollout samples, nearest-rank p95 is the
maximum observed rollout, not a high-sample tail estimate.

The host is an AMD Ryzen 7 8845H (8 cores/16 logical processors), 32 GiB-class
RAM, Windows 11 build 26200, and an RTX 3090. The active power scheme was
balanced. Affinity was not pinned, GPU exclusive mode was not used, and
background load was not controlled. Conclusions are therefore host-specific
experimental routing advice, not a tuning or production-support claim.

## Content-addressed inputs

| Input | Bytes | SHA-256 |
|---|---:|---|
| CPU campaign 1 | 103,773 | `ef7484bb431595836e388b57112e8123b17baf016752f198dbefc5a79b88f0cf` |
| CUDA campaign 1 | 194,834 | `5dd5f89c32b4dc7336e56fbe6d67042cbe0d4127e054f3f0c5e6b73f0e1b902a` |
| CUDA campaign 2 | 194,684 | `9cfc14ac3dccdc629b6378958a0c5631487c34d172df41502165b1138b34fa84` |
| CPU campaign 2 | 103,948 | `e3791164ae64b2a28fb56a8a543991e95d7973e2df317b46e274bc126fd9281b` |

Every report passes the CR2-6a production validator. Non-timing fields are exact
across campaigns within each lane, and the CPU/CUDA master trace signatures
match. A fresh CR2-4b full-window comparison passes all 12 released fields and
same-backend exact resets. CR2-5a static/topology evidence remains complete, but
CR2-5b achieved counters remain blocked by `ERR_NVGPUCTRPERM`; tuning remains
unauthorized.

Raw, manifest, parity, and summary JSON paths are marked `-text`, so their byte
hashes survive checkout unchanged. Source and prior-evidence descriptors use
explicit `utf8_lf` canonicalization instead of depending on a platform newline
representation.

## Observed direction

Ratios are CPU milliseconds divided by CUDA milliseconds. Above one means CUDA
is faster. Ranges cover both order-balanced campaigns and all named metrics for
the row unless a metric is called out separately.

| Worlds | Common mode | Result |
|---:|---|---|
| 1 | no export | CPU wins every metric; ratios `0.028–0.151`. |
| 1 | host export | CPU wins every metric; ratios `0.048–0.096`. |
| 4 | no export | CUDA wins every metric; minimum ratio `1.332`. |
| 4 | host export | CUDA wins both p50 metrics, but rollout p95 reverses by campaign (`0.508–6.057`). |
| 16 | both | CUDA wins every metric; minimum ratio `6.539`. |
| 64 | both | CUDA wins every metric; minimum ratio `5.651`. |
| 256 | both | CUDA wins every metric; minimum ratio `4.954`. |

The world-4 host-export tail is intentionally not averaged away. Campaign 1
records CUDA rollout p95 at about 4.82 ms/window versus CPU at 2.45; campaign 2
records CUDA at 0.89 versus CPU at 5.41. That order-sensitive reversal prevents
an unconditional CUDA rule for this row.

## Experimental selection advisory

- World 1, common modes: use the Flecs CPU reference.
- World 4, no export: use CUDA.
- World 4, host export: default to CPU for conservative tail behavior; CUDA is
  an explicit opt-in for median throughput.
- Worlds 16/64/256, common modes: use CUDA.
- Device-consumer modes: CUDA is required because CPU has no comparator; this is
  not a comparative performance claim.
- Other world counts: no extrapolation and no recommendation.

The maintained default remains Flecs CPU. The advisory does not enable a public
backend selector or change runtime behavior.

## Gates

`cr2_6_matrix_evidence_complete=true` and
`cr2_6_selection_advisory_complete=true`. Achieved counters, maintained claim,
public support, tuning, and promotion remain false. CR2-7 must make a separately
reviewed closure or promotion decision; this evidence does not decide it.
