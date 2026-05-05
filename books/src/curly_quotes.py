# ruff: noqa: INP001

"""Quote-curlification helper shared by build and maintenance scripts.

The :func:`curlify` function turns straight ASCII ``"`` / ``'`` and any existing
curly quotes into typographically correct curly forms (U+201C/U+201D for double,
U+2018/U+2019 for single). It is idempotent on already-correct text and
self-corrects misoriented curlies emitted upstream.
"""

_LEFT_DOUBLE = "“"
_RIGHT_DOUBLE = "”"
_LEFT_SINGLE = "‘"  # noqa: RUF001
_RIGHT_SINGLE = "’"  # noqa: RUF001
_DOUBLE_QUOTE_CHARS = frozenset(('"', _LEFT_DOUBLE, _RIGHT_DOUBLE))
_SINGLE_QUOTE_CHARS = frozenset(("'", _LEFT_SINGLE, _RIGHT_SINGLE))
# Preceded by any of these → next quote is opening.
# Includes whitespace, opening brackets, em/en-dash, hyphen, ellipsis,
# Markdown emphasis markers, and already-open curly quotes.
_OPEN_CONTEXT = frozenset(" \t\n\r\f\v([{<-—–…*_“‘")  # noqa: RUF001


def curlify(text: str) -> str:
    """Return ``text`` with all double and single quotes set to curly quotes.

    Existing curly quotes are folded to straight first, so misoriented quotes
    in the input get corrected on this pass. A ``"`` or ``'`` is opening when
    preceded by start-of-string, whitespace, an opening bracket, an em/en-dash,
    a hyphen, an ellipsis, a Markdown emphasis marker, or an already-open
    curly; otherwise it is closing.

    Args:
        text: Source string that may contain straight or curly quotes.

    Returns:
        The text with every quote character resolved to its correct curly form.

    """
    out: list[str] = []
    prev = ""
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
        else:
            out.append(ch)
            prev = ch
    return "".join(out)
