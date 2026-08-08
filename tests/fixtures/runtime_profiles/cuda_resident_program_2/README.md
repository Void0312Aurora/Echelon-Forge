# CUDA Resident Program 2 Test Fixture

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This directory preserves the byte-stable evidence, decisions, and phase-freeze
records consumed by the CUDA-resident runtime-profile tests. It is a test
fixture, not an active planning or documentation authority.

Recommended reading order:

1. [cuda_resident_backend_program_20260729.md](cuda_resident_backend_program_20260729.md)
2. [cuda_resident_backend_iteration_log_20260729.md](cuda_resident_backend_iteration_log_20260729.md)
3. [cuda_resident_rb10_hold_decision_20260731.md](cuda_resident_rb10_hold_decision_20260731.md)
4. [cuda_resident_rb11_closure_20260731.md](cuda_resident_rb11_closure_20260731.md)
5. [cuda_resident_runtime_program_2_20260731.md](cuda_resident_runtime_program_2_20260731.md)
6. [cuda_resident_runtime_program_2_iteration_log_20260731.md](cuda_resident_runtime_program_2_iteration_log_20260731.md)
7. [cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)
8. [cuda_resident_cr2_resource_evidence_20260804.md](cuda_resident_cr2_resource_evidence_20260804.md)
9. [cuda_resident_cr2_resource_evidence_20260804.json](cuda_resident_cr2_resource_evidence_20260804.json)
10. [cuda_resident_cr2_counter_evidence_20260804.md](cuda_resident_cr2_counter_evidence_20260804.md)
11. [cuda_resident_cr2_counter_evidence_20260804.json](cuda_resident_cr2_counter_evidence_20260804.json)
12. [cuda_resident_cr2_matrix_evidence_20260804.md](cuda_resident_cr2_matrix_evidence_20260804.md)
13. [cuda_resident_cr2_matrix_evidence_20260804.json](cuda_resident_cr2_matrix_evidence_20260804.json)
14. [cuda_resident_cr2_closure_20260805.md](cuda_resident_cr2_closure_20260805.md)
15. [cuda_resident_cr2_closure_20260805.json](cuda_resident_cr2_closure_20260805.json)
16. [gpu_execution_phase4_rollout_hot_path_freeze.md](gpu_execution_phase4_rollout_hot_path_freeze.md)

Usage rules:

- The CUDA-resident second-backend program is the single frozen execution plan
  for that new workline. The companion iteration log records accepted branch
  evidence and the RB10 hold decision/RB11 closure record the no-promotion
  boundary. The plan is complete; future work requires a new explicit program.
- The CR2 continuation program completed those full-window, size-governance,
  consumer, parity, resource, and small-batch gates and then closed without
  promotion in CR2-7. Its retained advisory is not a runtime selector; future
  CUDA-resident work requires another explicit program and user authorization.
- The fixture preserves historical paths and hashes where validators require
  byte-stable provenance. Current architecture authority remains under
  `docs/architecture/`.
- Relative links embedded in frozen evidence may describe the historical
  layout and are not current repository routes.
- Do not add new planning material here. New runtime work must use the current
  owner-local work structure.
