"""Which emphasis tag a group's lettering takes: `[b]` for emphasis, `[i]` only for a face.

The shared markup vocabulary (`barks_fantagraphics.speech_markup.EMPHASIS_TAGS`)
allows both `[b]` and `[i]`, and the vision roster used to offer them as equal
options for emphasis. Batches then drifted: measured 2026-09-17, the corpus held
35,706 `[b]` tags against 2,540 `[i]`, with whole recent batches written in `[i]`
and their neighbours in `[b]`.

The rule this module enforces:

* **Emphasis is `[b]`.** Barks's letterer varies the weight of a word; the corpus
  records that as bold, whatever the face happens to slant.
* **`[i]` marks a SLANTED FACE, and only when it covers the whole group** -- a
  caption or balloon set entirely in italic, which is what `speech_markup` keeps
  `[i]` for. Emphasis inside such a face is still `[b]`. The face may be written
  as one run or as one run per line, which is the form the retired
  `emphasis_spans` migration produced; what matters is that the `[i]` runs
  together leave no letter or digit outside them.
"""

import re

_TAG_RE = re.compile(r"\[(/?)([bi])\]")


def _italic_runs(text: str) -> list[tuple[int, int, int, int]]:
    """Return ``(open_start, open_end, close_start, close_end)`` for each ``[i]`` run."""
    runs: list[tuple[int, int, int, int]] = []
    stack: list[tuple[int, int]] = []
    for match in _TAG_RE.finditer(text):
        if match.group(2) != "i":
            continue
        if match.group(1):
            if stack:
                start, end = stack.pop()
                runs.append((start, end, match.start(), match.end()))
        else:
            stack.append((match.start(), match.end()))
    return runs


def _lettering_count(text: str) -> int:
    """Count the letters and digits once every tag is removed; punctuation does not count."""
    return sum(ch.isalnum() for ch in _TAG_RE.sub("", text))


def is_slanted_face(text: str) -> bool:
    """Whether the ``[i]`` runs in ``text`` together cover all of its lettering.

    Args:
        text: A group's marked-up ``ai_text``.

    Returns:
        True when there is at least one ``[i]`` run and no letter or digit lies
        outside every one of them. Quote marks and other punctuation outside the
        runs are ignored, since a quoted caption often keeps its quotes untagged.

    """
    runs = _italic_runs(text)
    if not runs:
        return False
    outside = text
    for open_start, _open_end, _close_start, close_end in sorted(runs, reverse=True):
        outside = outside[:open_start] + outside[close_end:]
    return _lettering_count(outside) == 0


def italic_emphasis_problem(text: str) -> str | None:
    """Explain why ``text`` uses ``[i]`` for emphasis, or return None if it does not.

    Args:
        text: A group's marked-up ``ai_text`` or a result's ``emphasis_markup``.

    Returns:
        A human-readable problem when ``[i]`` appears but does not cover the whole
        group; None when there is no ``[i]`` or it marks a whole slanted face.

    """
    if "[i]" not in text or is_slanted_face(text):
        return None
    return (
        "[i] is used for emphasis; emphasis is always [b]. [i] is allowed only when"
        " it covers the whole group's lettering -- a caption or balloon set entirely"
        " in a slanted face -- and emphasis inside such a face is still [b]"
    )


def normalize_emphasis(text: str) -> str:
    """Rewrite ``[i]`` emphasis in ``text`` as ``[b]``, leaving a whole slanted face alone.

    Handles the shapes found in the corpus: plain ``[i]`` emphasis, a ``[b]`` and
    an ``[i]`` run on the same words, a partial ``[i]`` run wrapping a ``[b]`` word
    (whose ``[i]`` is dropped rather than doubled), and runs left abutting once
    converted (``[/b][b]``), which are merged. The lettering itself never changes.

    Args:
        text: A group's marked-up ``ai_text``.

    Returns:
        The rewritten text; ``text`` unchanged when it has no ``[i]`` or is a
        whole slanted face.

    """
    if "[i]" not in text or is_slanted_face(text):
        return text
    out = text
    for pattern in (r"\[b\]\[i\](.*?)\[/i\]\[/b\]", r"\[i\]\[b\](.*?)\[/b\]\[/i\]"):
        out = re.sub(pattern, r"[b]\1[/b]", out, flags=re.DOTALL)
    changed = True
    while changed:
        changed = False
        for open_start, open_end, close_start, close_end in _italic_runs(out):
            inner = out[open_end:close_start]
            if "[b]" in inner:
                out = out[:open_start] + inner + out[close_end:]
                changed = True
                break
    out = out.replace("[i]", "[b]").replace("[/i]", "[/b]")
    return out.replace("[/b][b]", "")
