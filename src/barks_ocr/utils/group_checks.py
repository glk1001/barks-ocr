"""Heuristic OCR-group checks that the user can dismiss per-group.

`ocr_check.py` raises these issue types as warnings, and the Kivy editor
lets the user mark any subset of them as acknowledged on the group's prelim
JSON. Once acknowledged, future `ocr_check` runs skip them for that group.

Adding a check means adding a predicate and one entry to
`DISMISSABLE_PREDICATES` — both `ocr_check` and the editor's acknowledge popup
read the registry, so neither needs touching.
"""

import re
from collections.abc import Callable

from barks_fantagraphics.speech_markup import strip_markup, validate_markup

from barks_ocr.utils.vision_schema import GROUP_TYPES

# Acknowledging this silences every layout check `ocr_check` runs on the group
# -- `text_does_not_fit` and both `too_many_lines` bands. They are two symptoms
# of one fault, a box that cannot hold its lettering as drawn, and which one
# fires is an accident of the wrapping. Named for the judgement, not for either
# check, since the checks keep firing -- `ocr_check` is what stops reporting.
TEXT_NEVER_FITS_ISSUE = "text-will-never-fit"

# Acknowledging this silences `ocr_check`'s `box_too_big` bands on the group.
# The layout checks read one number -- box height per text line -- against the
# page norm, and TEXT_NEVER_FITS_ISSUE covers the reading from below: a box too
# small for its lettering. This is the reading from above, and it is a different
# judgement rather than the same one restated: the box is RIGHT, and the
# lettering inside it is simply large -- a shout, a display caption, the carol
# relayed through the loudspeakers on vol 3 page 257. Named for that judgement,
# as the others are.
LETTERING_IS_LARGE_ISSUE = "lettering-is-large"

# Acknowledging this silences the other route into `ocr_check`'s `box_too_big`:
# the box measured against the lettering the two OCR engines boxed inside it,
# which is how a box of the right height with blank space beside its lettering
# is caught. The judgement is again that the box is RIGHT -- the fragments stop
# short of a drop capital or a trailing dash that is plainly lettering, or the
# box was drawn round a sound-effect burst on purpose -- and it is kept apart
# from LETTERING_IS_LARGE_ISSUE because the two readings fail independently: a
# group can carry either or both.
BOX_IS_WIDE_ISSUE = "box-is-deliberately-wide"

# Acknowledging this silences `ocr_check`'s `panel_nums_not_contiguous` for the
# page/engine it is set on. Named for the judgement -- "the skipped panel really
# has no lettering" -- and not for the check, following TEXT_NEVER_FITS_ISSUE.
#
# It is unlike every other type here in that it is not about the group carrying
# it. The finding is about a panel with *no* group, so there is nothing in that
# panel to mark; `ocr_check` anchors the issue on the first group of the next
# populated panel, and reads the acknowledgement back off that same group. Two
# consequences worth knowing before setting it:
#
#   - It is anchor-bound. Delete or add a group and the ids shift, the anchor
#     may become a different group, and the acknowledgement stops being found.
#     The issue then re-fires, which is the safe direction to fail in.
#   - It is per page/engine, not per panel. A page skipping two panels is one
#     issue naming both, so acknowledging it covers both -- including a panel
#     that later turns out to have had lettering all along.
PANEL_HAS_NO_TEXT_ISSUE = "panel-has-no-text"

# Acknowledging this silences `ocr_check`'s `box_outside_panel` for the group it
# is set on. Named for the judgement -- "the lettering really does sit out
# there" -- following the two above.
#
# The two classes it exists for, both measured over vols 1-29: splash-page
# mastheads, where the title logo and the "Walt Disney" byline are drawn above
# panel 1 and belong to no panel at all (vol 27 page 146 is three such groups);
# and a sound effect the art deliberately bursts through a panel border. Both
# are correct as drawn and would otherwise re-fire on every run.
BOX_OUTSIDE_PANEL_ISSUE = "box-outside-panel"

# Acknowledging this on either engine's group silences `ocr_check`'s
# `box_mismatch` for the pair and, more to the point, stops `--fix-boxes`
# merging it. It is the only way a reviewer can keep a box they tightened by
# hand on one engine: the fixer would otherwise re-inflate it to the other
# engine's box on the next run, with no report, because a tightened box still
# overlaps its counterpart well above the reporting threshold. It used to be
# honoured by the fixer without being offered by the editor's Mark OK popup,
# so no group in the corpus carried it.
BOX_MISMATCH_ISSUE = "box_mismatch"


def panels_with_no_groups(json_groups: dict, panel_count: int) -> list[int]:
    """Return the panels a page skips: 1..max-with-text, minus those that have text.

    The page's groups should occupy panels 1..n with nothing skipped. A hole is
    either lettering that was never grouped or groups filed under the wrong
    panel -- or, often enough, a genuinely wordless panel, which is why
    `PANEL_HAS_NO_TEXT_ISSUE` exists.

    Bounded above by the highest panel that *has* text rather than by
    `panel_count`: ending on a wordless panel is ordinary Barks and is not a
    hole. A `panel_num` past `panel_count` is ignored entirely, so one group
    claiming panel 99 cannot invent 90-odd empty panels -- that claim is
    `ocr_check`'s `panel_num_out_of_range` to report, not this function's.

    Returns nothing for a page holding an unassigned (-1) group: that group's
    text may belong to the empty panel, so the hole would just restate
    `panel_unassigned` and resolves itself once that is worked.

    Shared so that `ocr_check` and the Kivy editor agree on which panels are
    empty -- the editor widens its crop to show them, and a second copy of this
    arithmetic drifting from the first would point the reviewer at the wrong
    panel.

    Args:
        json_groups: One page/engine's groups, as stored.
        panel_count: How many panels the page's segments file defines.

    Returns:
        The skipped panel numbers, ascending. Empty when there is no hole.

    """
    texted = [
        group for group in json_groups.values() if strip_markup(group.get("ai_text") or "").strip()
    ]
    if any(int(group.get("panel_num", -1)) == -1 for group in texted):
        return []

    used = {int(group.get("panel_num", -1)) for group in texted}
    used = {panel for panel in used if 1 <= panel <= panel_count}
    if not used:
        return []

    return sorted(set(range(1, max(used) + 1)) - used)


DISMISSABLE_ISSUE_TYPES: tuple[str, ...] = (
    "short_text",
    "error_notes",
    "page_number_notes",
    "dot_at_end_of_sentence",
    "em_dash_spacing",
    "ellipsis_spacing",
    "double_hyphen",
    "unbalanced_quotes",
    "invalid_type",
    "invalid_markup",
    "whitespace",
    "florence-check",
    TEXT_NEVER_FITS_ISSUE,
    LETTERING_IS_LARGE_ISSUE,
    BOX_IS_WIDE_ISSUE,
    PANEL_HAS_NO_TEXT_ISSUE,
    BOX_OUTSIDE_PANEL_ISSUE,
    BOX_MISMATCH_ISSUE,
)

# The `type` vocabulary Gemini is asked for. Anything else is a mis-labelled
# group: the corpus carries 27, as "caption", "speech", "dialogtext",
# "dialogtext_bubble_id" and "symbol".
#
# Re-exported from `vision_schema` rather than restated. It used to be spelled
# out here and again in `kivy_editor`, which is exactly the drift the schema
# module exists to prevent -- and the vision pass now writes this field too.
VALID_GROUP_TYPES: frozenset[str] = GROUP_TYPES

# Word-uppercased forms (e.g. "MR", "PROF") that, when followed by ".", should
# NOT be flagged as a sentence end. Add common comic abbreviations as needed.
_SENTENCE_END_ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "MR",
        "MRS",
        "MS",
        "DR",
        "PROF",
        "ST",
        "JR",
        "SR",
        "SGT",
        "LT",
        "CAPT",
        "COL",
        "GEN",
        "MAJ",
        "REV",
        "GOV",
        "M.D",
        "PRES",
        "SEN",
        "REP",
        "HON",
        "INC",
        "LTD",
        "CO",
        "U.S",
        "VS",
        "ETC",
    }
)

_SENTENCE_END_RE = re.compile(r"((?:\w+\.)*\w*)(?<!\.)\.(?=\s*$|\s+[A-Z])", re.MULTILINE)

EM_DASH = "—"
# What may sit next to an em-dash. A line break or either edge of the text
# counts, so the wrapped and interrupted forms both pass.
_EM_DASH_BREAK_CHARS = frozenset({" ", "\n"})
# What may hug the dash on its right: the punctuation ending an interrupted
# utterance ("BUT —!"), and the closing quote, apostrophe or paren when the
# interruption ends a quotation or an aside ('GET SICK —"', "AD INFINITUM —)").
_EM_DASH_HUGGING_CHARS = frozenset({"!", "?", '"', ")", "'"})
# A *space* between the dash and its punctuation is a slip; a line break is not.
# "WELL, I'LL BE —\n!!!" is the art's own wrapping, 8 times in the corpus, and
# joining the lines to satisfy the rule would edit what the transcription saw.
_ADRIFT_PUNCTUATION_RE = re.compile(r" +[!?]")
_HYPHEN_RUN_RE = re.compile(r"-{2,}")
# A space between a word and the "!" or "?" ending its sentence: "SCARE !",
# "HAIRY HARRY ???". Part of the whitespace rule rather than the dash one --
# `_ADRIFT_PUNCTUATION_RE` above covers the same slip after an EM_DASH, which
# `with_dash_fixes` already repairs, and the two must not both claim a group.
#
# Spaces and tabs only, never a newline: "SCARE\n!" is the art's own wrapping,
# 10 times in the corpus, and joining those lines would edit what the
# transcription saw -- the same reasoning that keeps the dash rule off it.
_SPACED_END_PUNCT_RE = re.compile(r"(?<=[0-9A-Za-z])[ \t]+(?=[!?])")
# The three rewrites that make ``with_dash_fixes`` output text
# ``has_em_dash_spacing_error`` accepts. The left-hand one takes any non-break
# character, EM_DASH excepted so that "——" is never split into "— —" — the
# doubled dash is the one class left for a human.
_ADRIFT_HUGGING_RE = re.compile(rf"{EM_DASH} +(?=[!?])")
_LEFT_HUGGING_DASH_RE = re.compile(rf"(?<=[^\s{EM_DASH}]){EM_DASH}")
_RIGHT_HUGGING_DASH_RE = re.compile(rf"{EM_DASH}(?=\w)")
# The checks whose acknowledgement silences the whole dash fixer for a group.
_DASH_ISSUES: tuple[str, ...] = ("em_dash_spacing", "double_hyphen")


def _plain_text(group: dict) -> str:
    """Return the group's text with emphasis markup removed.

    Every check below is about the lettering, not its presentation, so all of
    them go through here.  Reading ``group["ai_text"]`` directly would measure
    the tags too: ``[b]X[/b]`` is eight characters, so ``is_short_text`` would
    no longer recognize a one-character group, and the em-dash rule would read
    the ``]`` before a dash as the character preceding it.
    """
    return strip_markup(group.get("ai_text") or "")


def is_short_text(group: dict) -> bool:
    ai_text = _plain_text(group).strip().lower()
    return (len(ai_text) == 1) and (ai_text not in ("?", "!"))


def is_ai_detected_error(group: dict) -> bool:
    notes = (group.get("notes") or "").strip().lower()
    return "error" in notes and "art" in notes and "background" in notes


def has_page_number_notes(group: dict) -> bool:
    notes = (group.get("notes") or "").strip().lower()
    return "page number" in notes


def has_dot_at_end_of_sentence(group: dict) -> bool:
    ai_text = _plain_text(group)
    for match in _SENTENCE_END_RE.finditer(ai_text):
        word_before = match.group(1).upper()
        if word_before not in _SENTENCE_END_ABBREVIATIONS:
            return True
    return False


def has_em_dash_spacing_error(group: dict) -> bool:
    """Whether any em-dash is spaced against the corpus convention.

    An em-dash needs a space, a line break or a text edge before it. After
    it: one of those, the end of the text, or the punctuation of an
    interrupted utterance hugging it — "BUT —!", "WHAT IS YOUR —?", the
    closing quote in 'GET SICK —"', and the closing apostrophe or paren in
    "AD INFINITUM —)". What it may not do is drift away from that punctuation
    by a space ("WHAT GEEFS — ?"): standard typography binds the dash and its
    punctuation as one unit, so the space is a transcription slip. A *line
    break* between them is not — that is the art's own wrapping.

    Settled 2026-08-03 after a brief flip to requiring the space, reverted
    the same day against typographic convention and the art (the reviewed
    vols 1-18 hug 80 to 16). The quote exception is the one change kept from
    that episode — the original rule wrongly flagged all 30 corpus cases.

    Widened 2026-08-08 so that ``with_dash_fixes`` can satisfy it outright:
    ``)`` and ``'`` joined the hugging set (3 corpus cases with no sensible
    fix — spacing them would be worse), and the adrift rule narrowed from any
    whitespace to spaces only. What remains flagged with no fixer behind it is
    the doubled dash "——", 34 occurrences over 16 spots, kept as a hand edit.
    """
    ai_text = _plain_text(group)
    for match in re.finditer(EM_DASH, ai_text):
        # Either edge of the text reads as a break, so a leading dash is fine.
        before = ai_text[match.start() - 1] if match.start() else "\n"
        if before not in _EM_DASH_BREAK_CHARS:
            return True

        rest = ai_text[match.end() :]
        if not rest:
            continue  # the dash ends the text: interrupted speech
        if rest[0] in _EM_DASH_HUGGING_CHARS:
            continue  # hugging its punctuation: "BEHIND —!", 'SICK —"'
        if rest[0] not in _EM_DASH_BREAK_CHARS:
            return True  # runs straight into a word, or another dash
        if _ADRIFT_PUNCTUATION_RE.match(rest):
            return True  # "WHAT GEEFS — ?"

    return False


ELLIPSIS_SPACING_ISSUE = "ellipsis_spacing"
# What an ellipsis may hug. Ruled 2026-10-08: a run of two or more dots takes a
# space on each side, except at either end of a line -- and except that it hugs
# a closing `?`, `!`, `)` or quote after it, and an opening `(` or quote before
# it: `WORD ... WORD`, `HOME! ... UNCLE`, `DICKENS ...?`, `(YAWN! ...)`,
# `"... THE ISLAND`. The rule is the reviewer's; the corpus was split on it,
# 1,902 runs of which 1,138 broke it, the seed volumes worst.
_ELLIPSIS_OPENERS = frozenset({"("})
_ELLIPSIS_CLOSERS = frozenset({"?", "!", ")"})
_QUOTES = frozenset({'"', "'"})
_EMPHASIS_TAG_RE = re.compile(r"\[/?[bi]\]")


def _visible_chars(raw: str) -> list[tuple[str, int]]:
    """Return (character, index into *raw*) for every character outside a markup tag.

    The ellipsis rule is about the lettering, but its fixer has to edit the stored
    string, tags and all. Pairing each visible character with its raw index lets
    it insert or delete a plain space at an exact position without ever touching a
    tag -- which is why, unlike the whitespace and dash fixers, it is safe on a
    group carrying ``[b]``/``[i]``.
    """
    out: list[tuple[str, int]] = []
    i = 0
    while i < len(raw):
        tag = _EMPHASIS_TAG_RE.match(raw, i)
        if tag:
            i = tag.end()
            continue
        out.append((raw[i], i))
        i += 1
    return out


def _quote_opens(chars: list[tuple[str, int]], at: int) -> bool:
    """Whether the quote at *at* opens: it starts a line or follows a space or `(`."""
    return at == 0 or chars[at - 1][0] in (" ", "\n", "(")


def _quote_closes(chars: list[tuple[str, int]], at: int) -> bool:
    """Whether the quote at *at* closes: nothing alphanumeric follows it."""
    return at + 1 >= len(chars) or not chars[at + 1][0].isalnum()


def _hugs_before(chars: list[tuple[str, int]], at: int) -> bool:
    """Whether the character at *at*, just before an ellipsis, may touch it."""
    char = chars[at][0]
    return char in _ELLIPSIS_OPENERS or (char in _QUOTES and _quote_opens(chars, at))


def _hugs_after(chars: list[tuple[str, int]], at: int) -> bool:
    """Whether the character at *at*, just after an ellipsis, may touch it."""
    char = chars[at][0]
    return char in _ELLIPSIS_CLOSERS or (char in _QUOTES and _quote_closes(chars, at))


def _left_edit(chars: list[tuple[str, int]], start: int) -> tuple[int, bool] | None:
    """Return the edit the ellipsis starting at *start* needs on its left, if any."""
    if start == 0 or chars[start - 1][0] == "\n":
        return None  # starts a line
    if chars[start - 1][0] != " ":
        return None if _hugs_before(chars, start - 1) else (chars[start][1], True)
    if start >= 2 and _hugs_before(chars, start - 2):  # noqa: PLR2004 -- the char before the space
        return chars[start - 1][1], False
    return None


def _right_edit(chars: list[tuple[str, int]], end: int) -> tuple[int, bool] | None:
    """Return the edit the ellipsis ending before *end* needs on its right, if any."""
    if end >= len(chars) or chars[end][0] == "\n":
        return None  # ends a line
    if chars[end][0] != " ":
        return None if _hugs_after(chars, end) else (chars[end - 1][1] + 1, True)
    if end + 1 < len(chars) and _hugs_after(chars, end + 1):
        return chars[end][1], False
    return None


def _ellipsis_space_edits(raw: str) -> list[tuple[int, bool]]:
    """Return the edits that space every ellipsis in *raw* by the rule.

    Each edit is ``(raw index, insert)``: insert a space before that index, or
    delete the space at it. A deletion is a space between an ellipsis and a
    character it should hug (`DICKENS ... ?`, `( ...`).
    """
    chars = _visible_chars(raw)
    edits: list[tuple[int, bool]] = []
    start = 0
    while start < len(chars):
        if chars[start][0] != "." or start + 1 >= len(chars) or chars[start + 1][0] != ".":
            start += 1
            continue
        end = start
        while end < len(chars) and chars[end][0] == ".":
            end += 1
        edits += [e for e in (_left_edit(chars, start), _right_edit(chars, end)) if e is not None]
        start = end
    return edits


def ellipsis_spacing_ok(text: str) -> bool:
    """Whether every run of two or more dots in *text* is spaced by the rule.

    For callers holding a string rather than a group: ``vision-seed build`` and
    ``vision-apply`` refuse text that fails it. See ``ELLIPSIS_SPACING_ISSUE``.
    """
    return not _ellipsis_space_edits(text)


def has_ellipsis_spacing_error(group: dict) -> bool:
    """Whether the group's ai_text has an ellipsis spaced against the rule."""
    return not ellipsis_spacing_ok(group.get("ai_text") or "")


def with_ellipsis_fixes(text: str) -> str:
    """Return *text* with every ellipsis spaced by the rule, markup untouched.

    Only ever inserts or deletes a single plain space next to a run of dots, so
    the tags, the line breaks and every other character survive as they were,
    and the result passes ``ellipsis_spacing_ok`` on one pass.
    """
    for index, insert in sorted(_ellipsis_space_edits(text), reverse=True):
        text = f"{text[:index]} {text[index:]}" if insert else text[:index] + text[index + 1 :]
    return text


def has_double_hyphen(group: dict) -> bool:
    """Whether the text has a run of hyphens, almost always an unconverted em-dash."""
    return bool(_HYPHEN_RUN_RE.search(_plain_text(group)))


def has_unbalanced_quotes(group: dict) -> bool:
    """Whether the text has an odd number of double-quote characters."""
    return (_plain_text(group).count('"') % 2) == 1


def has_invalid_type(group: dict) -> bool:
    """Whether the group's ``type`` is outside the expected vocabulary."""
    return (group.get("type") or "").strip().lower() not in VALID_GROUP_TYPES


def has_invalid_markup(group: dict) -> bool:
    """Whether the group's stored ai_text carries malformed emphasis markup.

    Unbalanced or mis-nested ``[b]``/``[i]``, a disallowed tag, or an
    unescaped ``&``/``[``/``]`` — everything ``validate_markup`` reports.
    Reads the raw string, not ``_plain_text``: markup validity is a property
    of what is on disk, and ``strip_markup`` would remove the evidence.
    """
    return bool(validate_markup(group.get("ai_text") or ""))


def has_whitespace_error(group: dict) -> bool:
    """Whether the text has stray whitespace: outer, per-line trailing, doubled, or before !/?."""
    ai_text = _plain_text(group)
    if not ai_text:
        return False
    return (
        ai_text != ai_text.strip()
        or "  " in ai_text
        or any(line != line.rstrip() for line in ai_text.split("\n"))
        or _SPACED_END_PUNCT_RE.search(ai_text) is not None
    )


def cleaned_whitespace(ai_text: str) -> str:
    """Return ai_text with outer, trailing and doubled spaces removed.

    Also closes up a space before the "!" or "?" ending a sentence. Applied per
    line, so it can only ever delete a space or tab — a sentence whose
    punctuation the art wrapped onto the next line keeps its line break.

    Line structure is preserved — the wrapping is meaningful and is what the
    line-height checks in ``ocr_check`` measure.
    """
    lines = [
        re.sub(r" {2,}", " ", _SPACED_END_PUNCT_RE.sub("", line)).rstrip()
        for line in ai_text.split("\n")
    ]
    return "\n".join(lines).strip()


def with_dash_fixes(ai_text: str, group: dict) -> str:
    """Return ai_text with the dash rewrites *group* has not dismissed.

    The rule is the one ``has_em_dash_spacing_error`` enforces: a break (space,
    line break or text edge) on the dash's left, and a break, a text edge, or
    its own hugging punctuation on its right. Everything here is a mechanical
    step towards that, so the output passes the check — the sole exception is
    the doubled dash "——", which is left alone deliberately.

    A group that has accepted **either** dash issue is returned untouched, the
    same way the checks stay quiet on it. Acknowledging one but not the other
    is not a licence to apply the rest: vol 7 page 135 group 6 is the case that
    settled it — the reviewer accepted ``dash_wrong_space`` and hand-restored
    "SPUT! — --", and per-rewrite gating would have converted the hyphen run
    straight back to "— —" on the next run, undoing that by a rule the reviewer
    had just overruled. The old ``dash_wrong_space``/``dash_no_spaces`` names
    count, since ``is_acknowledged`` honours them.

    What is left wrong in an accepted group stays reported — the checks are
    dismissed per group, not per corpus — so nothing goes missing; it just
    waits for a hand that has already looked at it once.

    The text is passed separately from the group because the whitespace fixer
    runs first and the two compose on one string; the group is read only for
    its acknowledgements.

    Four ordered rewrites:

    1. Hyphen runs, not pairs: the corpus has 221 of them and 70 are three
       hyphens or more, so a plain "--" swap would leave a stray hyphen behind.
    2. Punctuation pulled back against the dash ("CAME ASHORE — !" → "—!").
       Standard typography binds the two as one unit. This must run before the
       left-hand spacing so "WAY— !" lands on "WAY —!", not "WAY — !".
    3. A space in front of any dash hugging the character before it — the ones
       step 1 just made ("HOW ARE--"), the 490 the AI wrote that way itself,
       and the closing quote form ("'EXPECT'— AIR"). The corpus puts a break
       before the dash 10,699 times against 490.
    4. A space after any dash running straight into the next word ("IN—AND
       HOW", "WHAT'S THIS —FLY SPRAY?").

    Step 4 reverses a carve-out made on 2026-08-08, when the closed-up
    "IN—AND HOW" form was spared on a 71-to-9 corpus count. That count measured
    the AI's habit, not the art, and it left 67 occurrences flagged with no
    fixer able to touch them; the same reasoning had already spaced the other
    490. The result is idempotent, so the ``MAX_FIX_PASSES`` loop converges on
    the first pass.
    """
    if any(is_acknowledged(group, issue) for issue in _DASH_ISSUES):
        return ai_text

    text = _HYPHEN_RUN_RE.sub(EM_DASH, ai_text)
    text = _ADRIFT_HUGGING_RE.sub(EM_DASH, text)
    text = _LEFT_HUGGING_DASH_RE.sub(f" {EM_DASH}", text)
    return _RIGHT_HUGGING_DASH_RE.sub(f"{EM_DASH} ", text)


def _never_fires(group: dict) -> bool:
    # For the issues whose check lives outside this module, so there is nothing
    # to evaluate here. The acknowledge popup shows them as "not firing" and
    # never auto-checks them; the user toggles them by hand to opt the group out
    # of the check that does own them:
    #
    #   florence-check       -- florence_check.py, an external model run.
    #   text-will-never-fit  -- ocr_check's layout checks, which need the
    #                           rendered font and the page context.
    #   lettering-is-large   -- ocr_check's box_too_big, the same page context
    #                           read from the other end.
    #   box-is-deliberately-wide -- box_too_big's width reading, which needs
    #                           the other engine's fragments for the pair.
    #   box-outside-panel    -- ocr_check's overhang check, which needs the
    #                           page's panel boxes.
    del group
    return False


DISMISSABLE_PREDICATES: dict[str, Callable[[dict], bool]] = {
    "short_text": is_short_text,
    "error_notes": is_ai_detected_error,
    "page_number_notes": has_page_number_notes,
    "dot_at_end_of_sentence": has_dot_at_end_of_sentence,
    "em_dash_spacing": has_em_dash_spacing_error,
    ELLIPSIS_SPACING_ISSUE: has_ellipsis_spacing_error,
    "double_hyphen": has_double_hyphen,
    "unbalanced_quotes": has_unbalanced_quotes,
    "invalid_type": has_invalid_type,
    "invalid_markup": has_invalid_markup,
    "whitespace": has_whitespace_error,
    "florence-check": _never_fires,
    TEXT_NEVER_FITS_ISSUE: _never_fires,
    LETTERING_IS_LARGE_ISSUE: _never_fires,
    BOX_IS_WIDE_ISSUE: _never_fires,
    # Like the two above it: `ocr_check` decides when this fires and consults
    # `is_acknowledged` itself, because the judgement needs the whole page and
    # its panel boxes, which a predicate over one group cannot see.
    PANEL_HAS_NO_TEXT_ISSUE: _never_fires,
    # Same again: the group carries its text_box, but not the panel box it has
    # to be measured against.
    BOX_OUTSIDE_PANEL_ISSUE: _never_fires,
    # And again: it is a verdict on a pair of groups, one per engine, which
    # `ocr_check` alone has in hand.
    BOX_MISMATCH_ISSUE: _never_fires,
}

# Issue types that were renamed or merged. 75 groups carry an acknowledgement
# under "dash_wrong_space" from when the em-dash rule was two narrower checks;
# honouring the old name keeps those dismissals alive without rewriting any
# prelim file.
_ACKNOWLEDGEMENT_ALIASES: dict[str, tuple[str, ...]] = {
    "em_dash_spacing": ("dash_wrong_space", "dash_no_spaces"),
}


def get_fired_dismissable_issues(group: dict) -> list[str]:
    """Return the dismissable issue types currently firing on *group*."""
    return [t for t, pred in DISMISSABLE_PREDICATES.items() if pred(group)]


def is_acknowledged(group: dict, issue_type: str) -> bool:
    """Return True if *issue_type*, or a name it superseded, is acknowledged."""
    acknowledged = group.get("acknowledged_issues") or []
    if issue_type in acknowledged:
        return True
    return any(alias in acknowledged for alias in _ACKNOWLEDGEMENT_ALIASES.get(issue_type, ()))
