# ruff: noqa: INP001

"""Quote-curlification helper shared by build and maintenance scripts.

The :func:`curlify` function turns straight ASCII ``"`` / ``'`` and any existing
curly quotes into typographically correct curly forms (U+201C/U+201D for double,
U+2018/U+2019 for single). It is idempotent on already-correct text and
self-corrects misoriented curlies emitted upstream.

HTML tags (``<...>``) are passed through unchanged except that any curly
quotes inside a tag are folded back to straight, so attribute quoting like
``style="..."`` survives even if a previous run mistakenly curlified it.
Markdown emphasis markers (``*`` / ``_``) are treated as transparent: they
neither open nor close a quote context, so quotes wrapped in or wrapping
emphasis (``"*foo*"`` or ``*"foo"*``) all resolve correctly.
"""

import re

_LEFT_DOUBLE = "“"
_RIGHT_DOUBLE = "”"
_LEFT_SINGLE = "‘"  # noqa: RUF001
_RIGHT_SINGLE = "’"  # noqa: RUF001
_DOUBLE_QUOTE_CHARS = frozenset(('"', _LEFT_DOUBLE, _RIGHT_DOUBLE))
_SINGLE_QUOTE_CHARS = frozenset(("'", _LEFT_SINGLE, _RIGHT_SINGLE))
_EMPHASIS_CHARS = frozenset("*_")
# Preceded by any of these → next quote is opening.
# Includes whitespace, opening brackets, em/en-dash, hyphen, ellipsis,
# and already-open curly quotes. Markdown emphasis markers are intentionally
# excluded; they are handled as transparent (see :func:`curlify`).
_OPEN_CONTEXT = frozenset(" \t\n\r\f\v([{<-—–…“‘")  # noqa: RUF001
_HTML_TAG_RE = re.compile(r"<[^>]*>")
_CURLY_TO_STRAIGHT = str.maketrans(
    {
        _LEFT_DOUBLE: '"',
        _RIGHT_DOUBLE: '"',
        _LEFT_SINGLE: "'",
        _RIGHT_SINGLE: "'",
    }
)


def curlify(text: str) -> str:
    """Return ``text`` with all quotes resolved to typographic curly forms.

    Existing curly quotes are folded to straight first, so misoriented quotes
    in the input get corrected on this pass. A quote is opening when preceded
    by start-of-string, whitespace, an opening bracket, an em/en-dash, a
    hyphen, an ellipsis, or an already-open curly; otherwise it is closing.

    HTML tags (``<...>``) are skipped — quotes inside a tag are folded back to
    straight so HTML attributes like ``style="..."`` are preserved. Markdown
    emphasis markers (``*`` / ``_``) are transparent: they do not change the
    surrounding quote context.

    Args:
        text: Source string that may contain straight or curly quotes.

    Returns:
        The text with every quote character resolved to its correct form.

    """
    parts: list[str] = []
    prev = ""
    pos = 0
    for match in _HTML_TAG_RE.finditer(text):
        segment, prev = _curlify_segment(text[pos : match.start()], prev)
        parts.append(segment)
        parts.append(match.group(0).translate(_CURLY_TO_STRAIGHT))
        pos = match.end()
    segment, _ = _curlify_segment(text[pos:], prev)
    parts.append(segment)
    return "".join(parts)


def _curlify_segment(text: str, prev: str) -> tuple[str, str]:
    """Curlify one tag-free segment, threading the previous-char context.

    Args:
        text: A run of text containing no HTML tags.
        prev: The previous character seen across earlier segments (empty string
            if at the start of the input). Used to decide opening vs. closing.

    Returns:
        ``(curlified, new_prev)`` where ``new_prev`` is the last non-emphasis
        character emitted, ready to be threaded into the next segment.

    """
    out: list[str] = []
    for ch in text:
        if ch in _DOUBLE_QUOTE_CHARS:
            opening = prev == "" or prev in _OPEN_CONTEXT
            replacement = _LEFT_DOUBLE if opening else _RIGHT_DOUBLE
            out.append(replacement)
            prev = replacement
        elif ch in _SINGLE_QUOTE_CHARS:
            opening = prev == "" or prev in _OPEN_CONTEXT
            replacement = _LEFT_SINGLE if opening else _RIGHT_SINGLE
            out.append(replacement)
            prev = replacement
        elif ch in _EMPHASIS_CHARS:
            out.append(ch)
        else:
            out.append(ch)
            prev = ch
    return "".join(out), prev
