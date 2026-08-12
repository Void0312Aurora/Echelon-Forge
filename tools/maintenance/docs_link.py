#!/usr/bin/env python3
"""Shared Markdown inline-link scanning for documentation maintenance tools.

``document_link_audit``, ``wp_doc_closure_audit``, and ``translate_docs_batch``
each used to carry their own Markdown link regex, so the same document produced
three different link sets. This module is the single normative implementation.
The link shape and the non-prose masking are taken from the documentation link
audit because it had the most complete masking: fenced code blocks, HTML
comments, and inline code.

Consumers that only inspect links use :func:`iter_markdown_links`; consumers
that rewrite links in place use :func:`sub_markdown_links`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterator


MARKDOWN_LINK_RE = re.compile(r"(!?)\[([^\]\n]*)\]\(([^)\n]+)\)")
FENCED_CODE_RE = re.compile(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


@dataclass(frozen=True)
class MarkdownLink:
  """One Markdown inline link or image found in prose."""

  text: str
  raw_target: str
  target: str
  is_image: bool
  raw: str
  start: int
  end: int
  line: int

  def render(self, target: str | None = None) -> str:
    """Rebuild the link with a replacement destination, keeping the image mark."""

    prefix = "!" if self.is_image else ""
    return f"{prefix}[{self.text}]({self.raw_target if target is None else target})"


def _blank_preserving_lines(match: re.Match[str]) -> str:
  return re.sub(r"[^\n]", " ", match.group(0))


def mask_non_prose(text: str) -> str:
  """Blank out fenced code, HTML comments, and inline code.

  Masked regions keep their original length and line breaks, so offsets and
  line numbers computed on the masked text also address the original text.
  """

  masked = FENCED_CODE_RE.sub(_blank_preserving_lines, text)
  masked = HTML_COMMENT_RE.sub(_blank_preserving_lines, masked)
  return INLINE_CODE_RE.sub(_blank_preserving_lines, masked)


def extract_link_target(raw_target: str) -> str:
  """Normalize a raw destination into the bare target.

  Handles angle-bracket destinations and drops an optional link title.
  """

  value = raw_target.strip()
  if value.startswith("<"):
    end = value.find(">", 1)
    return value[1:end] if end >= 0 else value[1:]
  return value.split(maxsplit=1)[0] if value else ""


def iter_markdown_links(text: str, *, mask: bool = True) -> Iterator[MarkdownLink]:
  """Yield every inline link/image in ``text`` in source order."""

  scanned = mask_non_prose(text) if mask else text
  for match in MARKDOWN_LINK_RE.finditer(scanned):
    start, end = match.span()
    raw_target = text[match.start(3) : match.end(3)]
    yield MarkdownLink(
      text=text[match.start(2) : match.end(2)],
      raw_target=raw_target,
      target=extract_link_target(raw_target),
      is_image=match.group(1) == "!",
      raw=text[start:end],
      start=start,
      end=end,
      line=scanned.count("\n", 0, start) + 1,
    )


def sub_markdown_links(
  text: str,
  repl: Callable[[MarkdownLink], str],
  *,
  mask: bool = True,
) -> str:
  """Replace every scanned link with ``repl(link)``, leaving masked regions alone."""

  pieces: list[str] = []
  cursor = 0
  for link in iter_markdown_links(text, mask=mask):
    pieces.append(text[cursor : link.start])
    pieces.append(repl(link))
    cursor = link.end
  pieces.append(text[cursor:])
  return "".join(pieces)
