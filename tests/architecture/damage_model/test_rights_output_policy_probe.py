r"""Focused unit tests for the source-rights PDF text probe helpers.

These pin the fail-closed contract of
``tools/maintenance/source_governance/rights_output_policy.py`` at the helper
level, independent of any real ``pdftotext`` binary or retained payload. They
cover the I57 second-payoff-pack fix and its review-driven hardening: the
pre-I57 ``_pdf_text_probe`` ran with ``text=True``, so the console locale
codec (GBK on this host) decoded pdftotext's valid-UTF-8 output, died
mid-read on a multi-byte sequence (the en dash ``e2 80 93``), and handed
``None`` to ``re.sub`` (``TypeError``). The fixed probe captures raw bytes
and decodes them as *strict* UTF-8, failing closed (zero statement hits) on
undecodable output -- the interim ``errors="ignore"`` variant was fail-open:
a malformed byte inside a rights phrase (``RE\xffLEASE``) was silently
dropped and spliced back into ``RELEASE``, false-positively detecting a
public-release statement.

Test-nature accounting (corrected per the I57 review; the file's original
claim that every test here was red pre-fix was wrong): six tests pin new
post-fix behavior and are red against the pre-fix module --
``test_normalize_statement_text_tolerates_missing_text``,
``test_public_distribution_statement_none_is_fail_closed``,
``test_pdf_text_probe_decodes_utf8_multibyte_text``,
``test_pdf_text_probe_public_release_without_statement_a``,
``test_pdf_text_probe_malformed_bytes_fail_closed`` (also red against the
interim ``errors="ignore"`` variant, where it fails open),
``test_pdf_text_probe_none_stdout_is_fail_closed``. Three are regression
guards that already passed pre-fix and pin unchanged behavior --
``test_normalize_statement_text_collapses_whitespace_and_uppercases``,
``test_public_distribution_statement_detects_statement_a``,
``test_pdf_text_probe_missing_binary_is_fail_closed``.
"""

from __future__ import annotations

import subprocess

from tests.architecture.helpers import ensure_repo_root_on_sys_path

ensure_repo_root_on_sys_path()

from tools.maintenance.source_governance import (  # noqa: E402
  rights_output_policy as output_policy,
)


def _fake_pdftotext_run(stdout: bytes | None, returncode: int = 0):
  """Fake ``subprocess.run`` that also locks the probe to binary capture.

  The stub fails the test if the probe ever reverts to locale-text capture
  (``text=True`` / ``universal_newlines=`` / ``encoding=`` / ``errors=``):
  locale-text mode is the original defect (the GBK console codec killing the
  reader thread), and a stub that returned bytes regardless of kwargs would
  stay green while the real path regressed.
  """

  def _run(*args, **kwargs):
    assert kwargs.get("capture_output") is True, "probe must capture output"
    assert not kwargs.get("text"), "probe must not capture in locale-text mode"
    assert not kwargs.get("universal_newlines"), (
      "probe must not capture in locale-text mode"
    )
    assert kwargs.get("encoding") is None, "probe must not pass encoding="
    assert kwargs.get("errors") is None, "probe must not pass errors="
    return subprocess.CompletedProcess(
      args=args[0] if args else ["pdftotext"],
      returncode=returncode,
      stdout=stdout,
      stderr=b"",
    )

  return _run


def test_normalize_statement_text_tolerates_missing_text() -> None:
  # New-behavior pin -- red pre-fix: re.sub(pattern, " ", None) raised
  # TypeError; post-fix None/empty normalize to "" (fail-closed).
  assert output_policy._normalize_statement_text(None) == ""
  assert output_policy._normalize_statement_text("") == ""


def test_normalize_statement_text_collapses_whitespace_and_uppercases() -> None:
  # Regression guard -- green pre-fix: str normalization is unchanged.
  assert (
    output_policy._normalize_statement_text("Approved  for\npublic\trelease")
    == "APPROVED FOR PUBLIC RELEASE"
  )


def test_public_distribution_statement_none_is_fail_closed() -> None:
  # New-behavior pin -- red pre-fix (TypeError): None must report "no
  # statement detected", never crash and never hit.
  evidence = output_policy._public_distribution_statement(None)
  assert evidence["statement_detected"] is False
  assert evidence["statement_id"] == ""
  assert evidence["has_public_release_phrase"] is False
  assert evidence["has_unlimited_distribution_phrase"] is False


def test_public_distribution_statement_detects_statement_a() -> None:
  # Regression guard -- green pre-fix: phrase detection over str is unchanged.
  evidence = output_policy._public_distribution_statement(
    "DISTRIBUTION STATEMENT A. Approved for public release; distribution is unlimited."
  )
  assert evidence["statement_detected"] is True
  assert evidence["statement_id"] == "distribution_statement_a_public_release_unlimited"


def test_pdf_text_probe_decodes_utf8_multibyte_text(monkeypatch, tmp_path) -> None:
  # New-behavior pin -- red pre-fix. Mirrors the real TP-20 output shape:
  # pdftotext emits valid UTF-8 whose en dash (e2 80 93) carries the 0x93
  # byte the GBK console codec chokes on; the binary + strict-UTF-8 path
  # must decode it and detect the statement.
  payload = (
    b"TP\xe2\x80\x9320 \xe2\x80\x93 DISTRIBUTION STATEMENT A.\n"
    b"Approved for public release; distribution is unlimited.\n"
  )
  monkeypatch.setattr(output_policy.subprocess, "run", _fake_pdftotext_run(payload))

  evidence = output_policy._pdf_text_probe(tmp_path / "TP-20.pdf")

  assert evidence["extraction_status"] == "pdf_text_probe_ok"
  assert evidence["statement_detected"] is True
  assert evidence["statement_id"] == "distribution_statement_a_public_release_unlimited"


def test_pdf_text_probe_public_release_without_statement_a(monkeypatch, tmp_path) -> None:
  # New-behavior pin -- red pre-fix: TP-21-style id (public release without
  # the Statement A label).
  payload = b"Approved for public release; distribution is unlimited.\n"
  monkeypatch.setattr(output_policy.subprocess, "run", _fake_pdftotext_run(payload))

  evidence = output_policy._pdf_text_probe(tmp_path / "TP-21.pdf")

  assert evidence["statement_detected"] is True
  assert evidence["statement_id"] == "public_release_distribution_unlimited"


def test_pdf_text_probe_malformed_bytes_fail_closed(monkeypatch, tmp_path) -> None:
  # New-behavior pin -- I57 review scenario. A malformed byte splitting a
  # rights phrase must fail the probe closed with zero hits. The interim
  # errors="ignore" decode silently dropped the byte, spliced b"RE\xffLEASE"
  # back into "RELEASE" and failed open with
  # statement_id="public_release_distribution_unlimited".
  payload = b"Approved for public RE\xffLEASE; distribution is unlimited.\n"
  monkeypatch.setattr(output_policy.subprocess, "run", _fake_pdftotext_run(payload))

  evidence = output_policy._pdf_text_probe(tmp_path / "TP-20.pdf")

  assert evidence["extraction_status"] == "pdf_text_probe_decode_error_fail_closed"
  assert evidence["statement_detected"] is False
  assert evidence["statement_id"] == ""
  assert evidence["has_distribution_statement_a_label"] is False
  assert evidence["has_public_release_phrase"] is False
  assert evidence["has_unlimited_distribution_phrase"] is False


def test_pdf_text_probe_none_stdout_is_fail_closed(monkeypatch, tmp_path) -> None:
  # New-behavior pin -- red pre-fix: reproduces the original crash surface
  # directly (a dead reader thread leaves result.stdout as None). Post-fix
  # None decodes as empty text: no crash, zero hits.
  monkeypatch.setattr(output_policy.subprocess, "run", _fake_pdftotext_run(None))

  evidence = output_policy._pdf_text_probe(tmp_path / "TP-20.pdf")

  assert evidence["extraction_status"] == "pdf_text_probe_ok"
  assert evidence["statement_detected"] is False
  assert evidence["statement_id"] == ""


def test_pdf_text_probe_missing_binary_is_fail_closed(monkeypatch, tmp_path) -> None:
  # Regression guard -- green pre-fix: the FileNotFoundError branch is
  # unchanged by the I57 fix.
  def _raise_missing(*args, **kwargs):
    raise FileNotFoundError("pdftotext")

  monkeypatch.setattr(output_policy.subprocess, "run", _raise_missing)

  evidence = output_policy._pdf_text_probe(tmp_path / "TP-20.pdf")

  assert evidence["extraction_status"] == "pdftotext_missing_fail_closed"
  assert evidence["statement_detected"] is False
