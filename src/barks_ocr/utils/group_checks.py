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

# Acknowledging this silences `ocr_check`'s ``text_does_not_fit`` for the group:
# the lettering overflows the box and always will, because the box is as drawn.
# Named for the judgement, not the check, since the check keeps firing —
# `ocr_check` is what stops reporting it.
TEXT_NEVER_FITS_ISSUE = "text-will-never-fit"

DISMISSABLE_ISSUE_TYPES: tuple[str, ...] = (
    "short_text",
    "error_notes",
    "page_number_notes",
    "dot_at_end_of_sentence",
    "em_dash_spacing",
    "double_hyphen",
    "unbalanced_quotes",
    "invalid_type",
    "invalid_markup",
    "whitespace",
    "florence-check",
    TEXT_NEVER_FITS_ISSUE,
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
    """Whether the text has stray whitespace: outer, per-line trailing, or doubled."""
    ai_text = _plain_text(group)
    if not ai_text:
        return False
    return (
        ai_text != ai_text.strip()
        or "  " in ai_text
        or any(line != line.rstrip() for line in ai_text.split("\n"))
    )


def cleaned_whitespace(ai_text: str) -> str:
    """Return ai_text with outer, trailing and doubled spaces removed.

    Line structure is preserved — the wrapping is meaningful and is what the
    line-height checks in ``ocr_check`` measure.
    """
    lines = [re.sub(r" {2,}", " ", line).rstrip() for line in ai_text.split("\n")]
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
    #   text-will-never-fit  -- ocr_check's text_does_not_fit, which needs the
    #                           rendered font and the page context.
    del group
    return False


DISMISSABLE_PREDICATES: dict[str, Callable[[dict], bool]] = {
    "short_text": is_short_text,
    "error_notes": is_ai_detected_error,
    "page_number_notes": has_page_number_notes,
    "dot_at_end_of_sentence": has_dot_at_end_of_sentence,
    "em_dash_spacing": has_em_dash_spacing_error,
    "double_hyphen": has_double_hyphen,
    "unbalanced_quotes": has_unbalanced_quotes,
    "invalid_type": has_invalid_type,
    "invalid_markup": has_invalid_markup,
    "whitespace": has_whitespace_error,
    "florence-check": _never_fires,
    TEXT_NEVER_FITS_ISSUE: _never_fires,
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
