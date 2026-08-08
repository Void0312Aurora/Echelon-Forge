# CUDA-resident CR2-5b achieved-counter evidence (2026-08-04)

## Scope

This record covers the separate Nsight Compute attempt required after CR2-5a.
It uses the same Release/SM86 resource-probe binary and the same one-window,
256-world `cudaProfilerApi` body. The machine-readable artifact is
`cuda_resident_cr2_counter_evidence_20260804.json`.

CR2-5b changes no CUDA kernel, launch shape, allocation path, runtime selection,
or public support flag. It attempts to collect achieved occupancy, branch
divergence, and kernel global/local/shared-memory traffic. Missing hardware
counters cannot be replaced by zero, CR2-5a theoretical occupancy, Nsight
Systems launch metadata, or CUDA API transfer bytes.

## Real profiler attempt

Nsight Compute 2025.3.1.0 launched the frozen probe with application-only
targeting, `cudaProfilerApi` range control, kernel replay, demangled names, the
`full` counter set, and a 12-launch limit. The collector itself constructed and
executed the command. The compact artifact records hashes of the absolute
argument vector, NCU executable, resource-probe binary, attempt log, probe
output, parent CR2-5a evidence, collector, and contract. Absolute machine paths
are redacted from the readable command template.

The profiler connected to one process, reported exactly one error, and
disconnected from the same process. Its exit code was 1 and the error was:

`ERR_NVGPUCTRPERM` — the process did not have permission to access NVIDIA GPU
performance counters.

No `.ncu-rep` was created. The application nevertheless completed the full
profile body, awaited the device consumer, and wrote the same frozen probe
payload hash used by CR2-5a. Therefore the failure is outside the kernel result
and is classified as `external_blocked`, not as a successful zero-valued
measurement.

## Fail-closed result

| Counter family | Result |
| --- | --- |
| achieved occupancy | null |
| branch divergence | null |
| kernel global-memory traffic | null |
| kernel local-memory traffic | null |
| kernel shared-memory traffic | null |

The required counter-launch count is 12; the collected hardware-counter record
count is 0. `cr2_5b_counter_attempt_complete` is true because the required real
attempt and external blocker are documented. `cr2_5_achieved_counter_gate_complete`
remains false and the disposition is `documented_external_blocker`. Tuning,
promotion, public support, and maintained-backend claims remain disabled.

The raw log and probe output remain outside the repository. Their raw-byte
SHA-256 values are retained in the compact artifact; tracked source hashes use
the declared UTF-8/LF canonical form. Enabling GPU performance counters is an
external host-policy change and is not performed by this iteration.
