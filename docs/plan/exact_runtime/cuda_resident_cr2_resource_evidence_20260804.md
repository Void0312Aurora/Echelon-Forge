# CUDA-resident CR2-5a resource evidence (2026-08-04)

## Scope

This record covers static kernel resources and the achieved launch/API topology
of one production-shaped full-window body. It does not contain Nsight Compute
hardware counters and does not authorize tuning, support, promotion, or a
maintained-backend claim. The machine-readable artifact is
`cuda_resident_cr2_resource_evidence_20260804.json`.

The CUDA-only Release/SM86 probe configures and sets up 256 fixed-air worlds
before `cudaProfilerStart`. Its single capture range contains:

`inject → evaluate(empty) → advance(WorldBatch) → public export → acquire
device lease → consumer submit → event await`.

Resource queries and object destruction are outside the range. Diagnostic
consumer materialization is never called.

## Captured topology

Nsight Systems 2025.3.2 captured exactly 12 launch instances and 10 unique
kernel symbols. Every launch used grid `2×1×1` and block `128×1×1`. The ordered
instances were three barrier launches around Phase A/B/D, seven phase kernels
(one Phase A, three Phase B, and three Phase D), observation pack, and device
consumer.

The captured CUDA API/memory tables contained:

| Fact | Achieved value |
| --- | ---: |
| kernel launches | 12 |
| `cudaDeviceSynchronize` | 5 |
| `cudaMalloc` / `cudaFree` inside capture | 4 / 0 |
| event create / record | 2 / 2 |
| `cudaEventSynchronize` | 1 |
| `cudaStreamWaitEvent` | 1 |
| `cudaMemset` / `cudaMemcpy` | 5 / 13 |
| H2D copies / bytes | 3 / 14,080 |
| D2H copies / bytes | 7 / 229,908 |
| D2D copies / bytes | 3 / 677,376 |

The seven D2H copies are the five existing barrier-status transfers plus the
two public export transfers. The two diagnostic consumer readbacks are absent.
CUDA memcpy bytes are API-transfer evidence, not achieved kernel global-memory
traffic.

## Static resources

The collector cross-checked ptxas, runtime attributes, and cuobjdump for each
kernel. All ten ptxas entries explicitly reported zero spill stores and zero
spill loads. The build used `-maxrregcount=0`, which means no register cap.

| Kernel | Registers | Stack bytes/thread | Theoretical occupancy | SASS LDL / STL |
| --- | ---: | ---: | ---: | ---: |
| apply barrier | 30 | 0 | 100% | 0 / 0 |
| Phase A controls | 34 | 0 | 100% | 0 / 0 |
| Phase B forces | 66 | 40 | 58.33% | 3 / 2 |
| Phase B aerodynamics | 66 | 40 | 58.33% | 3 / 2 |
| Phase B integrate | 64 | 40 | 66.67% | 3 / 2 |
| Phase D instruments | 64 | 40 | 66.67% | 3 / 2 |
| Phase D configuration | 34 | 0 | 100% | 0 / 0 |
| Phase D projection | 40 | 0 | 100% | 0 / 0 |
| Phase D pack | 16 | 0 | 100% | 0 / 0 |
| Phase D consumer | 14 | 0 | 100% | 0 / 0 |

The four 40-byte stack kernels each contain three `LDL.64` and two `STL.64`
instructions. Those instructions are stack/local operations; they are not
relabeled as compiler spills. Nsight Systems reported zero in its
`localMemoryPerThread` launch-metadata field for all launches, so that field is
retained but treated as non-authoritative for static stack size and unavailable
as an achieved traffic counter. It also reported 16 registers for the consumer
launch while ptxas, runtime attributes, and cuobjdump agreed on 14; the launch
metadata value is retained without overriding the three-source static result.

## Fail-closed status

Achieved occupancy, divergence, and kernel global/local/shared traffic remain
null with status `pending_cr2_5b`. The collector rejects missing kernel or
ptxas fields, source disagreement, wrong launch order/count/shape, a second
window, distinct-symbol drift, a conflicting register cap, invalid runtime
occupancy metadata, extra diagnostic D2H, support flags set true, or any
theoretical value inserted into an achieved-counter field. CR2-5b owns the
separate Nsight Compute attempt and external-blocker record.

Source-file SHA-256 values use an explicitly declared UTF-8/LF canonical form,
so Windows checkout newline conversion cannot change the provenance guard.
Binary, probe-output, SQLite, and build-log hashes remain hashes of raw bytes.
