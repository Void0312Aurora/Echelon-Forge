"""Opt-in report envelope: a uniform metadata wrapper for tool JSON outputs.

Unified-architecture program T5, second slice. Track T5's scope names an
"opt-in report envelope" alongside the typed Experiment definition frozen by
I30; this module supplies the envelope *vocabulary* only, deliberately
leaving trace/ancestry mechanics (packet ids, replay gates, provenance
graphs) to the T10 evidence-and-replay spine so this slice does not
encroach on that track's write set.

Design contract:

1. **Opt-in, not automatic.** Nothing here runs unless a caller explicitly
   builds an envelope. Adopting tools gate the call behind their own CLI
   flag (see :func:`add_report_envelope_arg`); with the flag unset (the
   default), a tool's output is byte-identical to before this module
   existed. :func:`apply_report_envelope` makes this the only code path a
   caller needs: it returns the payload untouched when disabled.
2. **Payload travels verbatim.** The envelope never inspects, validates, or
   mutates the wrapped payload (no JSON-safety checks, no key rewriting) so
   it stays usable for the same payloads tools already emit today,
   including ones containing ``NaN``/``Infinity`` floats.
3. **Metadata is generic, not tool-specific.** Only identity/provenance
   fields that make sense for *any* tool are included: a tool id, the
   envelope's own schema version (distinct from any ``schema_version`` a
   payload already carries internally), a generation timestamp, the
   current git revision (best effort; ``None`` when unavailable), and an
   optional free-form experiment reference. The envelope does not resolve
   ``experiment_ref`` against :class:`python.experiment.definition.
   ExperimentRegistry`; it is an opaque tag today, by design (see point
   above about staying out of T10's territory).
4. **Zero bootstrap side effects.** Standard library only: no ``ef_py``,
   ``gymnasium``, or SB3 imports, and no import-time IO or subprocess
   calls. ``git_revision`` only shells out when a caller actually invokes
   it.
"""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENVELOPE_SCHEMA_VERSION = "1"

# python/experiment/report_envelope.py -> python/experiment -> python -> repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]


def git_revision(repo_root: str | Path | None = None, *, timeout: float = 5.0) -> str | None:
    """Best-effort current git ``HEAD`` hash; ``None`` when unavailable.

    Never raises. A missing ``git`` binary, a directory outside any git
    work tree, or any other subprocess failure all resolve to ``None`` so
    envelope generation stays robust in minimal or CI environments that
    lack a git checkout.
    """

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root) if repo_root is not None else str(_REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    rev = result.stdout.strip()
    return rev or None


def build_report_envelope(
    payload: Any,
    *,
    tool_id: str,
    experiment_ref: str | None = None,
    generated_at: datetime | None = None,
    git_rev: str | None = None,
    autodetect_git_rev: bool = True,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Wrap *payload* in the shared opt-in report envelope.

    ``payload`` is embedded verbatim under the ``payload`` key: this
    function does not copy, freeze, or validate it. ``git_rev`` lets a
    caller supply an already-known revision (for example to avoid one
    subprocess call per report in a batch); when omitted (``None``) and
    ``autodetect_git_rev`` is true (the default), the current ``HEAD`` is
    resolved via :func:`git_revision`. Passing ``autodetect_git_rev=False``
    keeps ``git_rev`` as ``None`` without shelling out, which is what tests
    should do for determinism.
    """

    if not isinstance(tool_id, str) or not tool_id.strip():
        raise ValueError(f"tool_id must be a non-empty string, got {tool_id!r}")
    if experiment_ref is not None and (not isinstance(experiment_ref, str) or not experiment_ref.strip()):
        raise ValueError(f"experiment_ref must be a non-empty string or None, got {experiment_ref!r}")

    resolved_git_rev = git_rev
    if resolved_git_rev is None and autodetect_git_rev:
        resolved_git_rev = git_revision(repo_root)

    timestamp = generated_at if generated_at is not None else datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return {
        "envelope_schema_version": ENVELOPE_SCHEMA_VERSION,
        "tool_id": tool_id,
        "generated_at": timestamp.astimezone(timezone.utc).isoformat(),
        "git_rev": resolved_git_rev,
        "experiment_ref": experiment_ref,
        "payload": payload,
    }


def apply_report_envelope(
    payload: Any,
    *,
    enabled: bool,
    tool_id: str,
    **envelope_kwargs: Any,
) -> Any:
    """Return *payload* unchanged when ``enabled`` is false, else its envelope.

    This is the single call adopting tools need at their serialization
    boundary: ``payload = apply_report_envelope(payload, enabled=args.
    report_envelope, tool_id="...")``. Because the disabled branch returns
    ``payload`` itself (same object, no copy), a tool that never sets the
    flag has an identically-shaped, identically-ordered output to before
    this module existed.
    """

    if not enabled:
        return payload
    return build_report_envelope(payload, tool_id=tool_id, **envelope_kwargs)


def add_report_envelope_arg(
    parser: argparse.ArgumentParser,
    *,
    default: bool = False,
    help: str | None = None,
) -> None:
    """Add the shared ``--report-envelope`` opt-in flag.

    Default is disabled (``False``); adopting tools must not flip this
    default, since the whole point of the envelope is that existing
    automation and byte-parity fixtures see no change until a caller asks
    for it.
    """

    parser.add_argument(
        "--report-envelope",
        dest="report_envelope",
        action="store_true",
        default=default,
        help=help
        or (
            "Wrap the JSON output in the opt-in report envelope (tool id, "
            "schema version, timestamp, git rev, optional experiment ref). "
            "Default: disabled, output unchanged."
        ),
    )


__all__ = [
    "ENVELOPE_SCHEMA_VERSION",
    "add_report_envelope_arg",
    "apply_report_envelope",
    "build_report_envelope",
    "git_revision",
]
