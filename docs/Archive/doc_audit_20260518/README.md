# Documentation Audit — 2026-05-18

Status: **Complete**. Six parallel sub-agents audited all documentation domains against actual code.

## Files

| File | Content |
|------|---------|
| [CONSOLIDATED_ISSUES.md](CONSOLIDATED_ISSUES.md) | **Start here** — all issues merged, sorted by severity |
| [forward_vs_code.md](forward_vs_code.md) | Domain R1: `docs/forward/` vs `src/` |
| [manual_vs_code.md](manual_vs_code.md) | Domain R2: `docs/manual/` vs engine/code |
| [standards_vs_code.md](standards_vs_code.md) | Domain R3: `docs/standards/` vs code conventions |
| [plan_vs_code.md](plan_vs_code.md) | Domain R4: `docs/plan/` vs implementation status |
| [src_readme_vs_code.md](src_readme_vs_code.md) | Domain R5: `src/**/README.md` vs directory contents |
| [python_layer_vs_code.md](python_layer_vs_code.md) | Domain R6: Python layer READMEs vs code |

## Quick Stats

| Severity | Count |
|----------|-------|
| P0 | 17 |
| P1 | 32 |
| P2 | 36 |
| **Total** | **85** |

### Top 5 Most Critical

1. **`air/act.md`** — `stick_pitch` sign inverted (P0)
2. **`visualization_guide.md`** — references nonexistent script (P0)
3. **5 GPU exact-runtime plans** — zero implementation for documented backends (P0)
4. **`rl_selfplay.md`** — claims implemented files that don't exist (P1)
5. **`engagement_termination.md`** — claims implemented fields that don't exist (P1)

## Methodology

Each domain report was produced by an independent sub-agent (haiku model) that:
1. Read every document in the domain
2. Extracted all factual claims (file paths, types, features, status)
3. Verified each claim against actual code via grep/find/ls
4. Recorded verified claims and mismatches with code evidence
