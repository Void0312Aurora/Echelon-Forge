Review this pull request for correctness, regressions, missing tests, and security risks.

Apply the severity ladder, blocking semantics, threat-model boundary, and
convergence protocol defined in `.github/codex/review-boundaries.md`. That
file is the shared contract for every review round; read it before writing
findings.

Review discipline:

- Only report high-confidence issues. Avoid style-only comments, broad
  refactors, speculative suggestions, and duplicate findings.
- If prior review context is provided, read it first. Do not re-raise
  findings that were fixed, answered with an accepted-risk rationale, or
  recorded as accepted residual risks. Focus on commits pushed since the
  last review round; treat the accumulated diff as context, not as the
  primary search space.
- When reviewing a defense or validation mechanism, evaluate its complete
  boundary in one round (what it defends, what it does not, where the
  sensible stopping point is). Do not go one layer deeper per round.

For each finding:

- assign a severity from the ladder (P0-P3);
- cite the relevant file and line or diff hunk;
- explain the impact;
- suggest a concrete fix.

Output format:

1. A `## Blocking findings` section listing only P0/P1 items (or "none").
2. A `## Follow-up suggestions` section listing P2/P3 items (or "none").
3. A one-line verdict: either "Blocking issues found: N" or
   "No blocking issues; N follow-up suggestions."

Only P0/P1 findings may justify requesting changes. A review whose only
findings are P2/P3 is an approval with suggestions.
