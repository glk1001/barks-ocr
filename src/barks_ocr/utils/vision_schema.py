"""The vocabulary the vision pass writes, and that the editor offers back.

``vision_apply`` validates a Claude Code vision result against these names
before writing anything; ``kivy_editor``'s speaker popup offers the same names
for review. They live here so the two cannot drift — a roster entry the editor
offers but the validator rejects would be a silent trap.

See ``docs/vision-pass.md`` for what each field means.
"""

import re
from collections.abc import Iterable, Mapping
from enum import StrEnum

from barks_fantagraphics.speech_markup import EMPHASIS_TAGS

# Ordered, because the editor lays the roster out in this order. Free-form
# speakers are allowed only behind ``OTHER_PREFIX``, so a typo in a main-cast
# name is caught rather than silently becoming a new character.
#
# "nephews" is not a fourth nephew: it is the honest answer when the line is one
# of the three but the art will not say which. The Huey-red / Dewey-blue /
# Louie-green convention was not firmly fixed in the early years, and 085 p3 of
# the pilot gives two nephews the same green. It also covers a line the three
# speak together. Prefer it to guessing a name; it is not the same as "unknown",
# which means the speaker could not be placed at all.
SPEAKER_OPTIONS: tuple[str, ...] = (
    "Donald",
    "Huey",
    "Dewey",
    "Louie",
    "nephews",
    "Daisy",
    "Gladstone",
    "Scrooge",
    "Gyro",
    "narrator",
    "none",
    "unknown",
)
ROSTER: frozenset[str] = frozenset(SPEAKER_OPTIONS)
OTHER_PREFIX = "other:"

# Database character tags that name somebody the roster already carries, under a
# fuller form. Mapped rather than offered alongside: a closed set holding both
# "Daisy" and "Daisy Duck" would make one character into two speakers, which is
# the exact drift the closed set exists to prevent.
#
# The two "not in ... series" entries are not names at all -- they tag where a
# story sits in the Fantagraphics series, and only look like cast because they
# live in the character groups. They map to the character they are about.
DB_CHARACTER_ALIASES: dict[str, str] = {
    "Daisy Duck": "Daisy",
    "Gladstone Gander": "Gladstone",
    "Gyro Gearloose": "Gyro",
    "Gyro not in GG series": "Gyro",
    "Uncle Scrooge not in US series": "Scrooge",
}

# Glosses for the entries that are easy to use wrongly, rendered into the
# roster file the vision pass is handed. The named cast needs no explanation.
SPEAKER_NOTES: dict[str, str] = {
    "nephews": "one of the three but the art will not say which, or all three at once",
    "narrator": "a caption box, not a character",
    "none": "nobody speaks it: a sound effect, a sign, background lettering",
    "unknown": "the speaker could not be placed at all",
}

CONFIDENCE_OPTIONS: tuple[str, ...] = ("high", "medium", "low")
CONFIDENCES: frozenset[str] = frozenset(CONFIDENCE_OPTIONS)

# The three nephews by name, as distinct from the `nephews` collective.
NEPHEW_NAMES: frozenset[str] = frozenset({"Huey", "Dewey", "Louie"})

# Naming an individual nephew rests entirely on the cap-colour convention, so
# being unsure *which* nephew is exactly the case `nephews` exists for. The
# combination is therefore refused rather than merely discouraged.
#
# Measured, not assumed: reviewing the pilot's 18 low-confidence calls found 10
# wrong, and **9 of those 10 were a named nephew that should have been the
# collective** -- three clean triples on 079, 080 and 083. The pass had the rule
# already ("prefer it to guessing a name; a guess is unrecoverable, a collective
# is not") and its own `vision_note`s said the tails were ambiguous. It named one
# anyway. A rule the model states and then breaks needs enforcing, not rewording.
NEPHEW_GUESS_CONFIDENCE = "low"


def nephew_needs_collective(speaker: str, confidence: str) -> bool:
    """Return whether this call must be the collective rather than a name.

    Args:
        speaker: The speaker value.
        confidence: The stated ``speaker_confidence``.

    Returns:
        True when an individual nephew is named at a confidence that does not
        support naming one.

    """
    return speaker in NEPHEW_NAMES and confidence == NEPHEW_GUESS_CONFIDENCE


CAP_COLOUR_OPTIONS: tuple[str, ...] = ("red", "blue", "green")
CAP_COLOUR_SET: frozenset[str] = frozenset(CAP_COLOUR_OPTIONS)

# What the speaker call actually rests on. `cap_colour` records the evidence
# behind a *nephew* call and is what makes one reversible; the five-title trial
# found three separate populations with no equivalent, and every one of them is
# unrecoverable without this field:
#
#   - adults told apart only by hat and shirt colour, where the single confirmed
#     colour-override error in the trial lives (Sheriff 168 g5, whose
#     contradiction with g3 would have been mechanical to catch);
#   - eleven high-confidence calls made from pyjamas and shirt colour, which
#     `cap_colour` has nowhere to put (Plenty of Pets 204, 208);
#   - a call made from the previous balloon rather than from the art at all
#     (Plenty of Pets 208 g20, Sheriff 165 g0).
#
# A list rather than one value, because a real call usually rests on more than
# one thing -- a tail that lands on a figure *and* the cap that figure wears --
# and separating them is what lets a later check ask whether two calls in one
# panel disagree about the same evidence.
IDENTIFIED_BY_OPTIONS: tuple[str, ...] = (
    "balloon-tail",
    "cap-colour",
    "costume",
    "hat",
    "sole-figure",
    "dialogue",
    "caption",
    "off-panel",
)
IDENTIFIED_BY_SET: frozenset[str] = frozenset(IDENTIFIED_BY_OPTIONS)

IDENTIFIED_BY_NOTES: dict[str, str] = {
    "balloon-tail": "the tail lands on this figure",
    "cap-colour": "a nephew's cap, recorded in cap_colour",
    "costume": "pyjamas, shirt or other clothing colour",
    "hat": "an adult's hat -- colour or shape",
    "sole-figure": "the only character who could be speaking",
    "dialogue": "what the line says, or what the previous balloon said",
    "caption": "a narration box, not a character",
    "off-panel": "the speaker is not drawn in this panel",
}

# Emphasis is written inline, as `[b]WORD[/b]`, into the group's `ai_text`
# itself; `EMPHASIS_TAGS` in `barks_fantagraphics.speech_markup` is the
# vocabulary and the only definition of it. It used to be a separate
# `emphasis_spans` field of character offsets, which drifted the moment anything
# else edited the text -- see that module for the full argument.
EMPHASIS_MARKUP_KEY = "emphasis_markup"

# Broad, unambiguous categories only. A specific named place -- the Money Bin,
# Plain Awful, Grandma Duck's farm -- arrives behind OTHER_PREFIX exactly as a
# one-off character does, and is promoted here once the census shows it recurs.
# Seeding this list with guesses would be worse than leaving it short: a wrong
# category gets used, and then has to be unpicked across the corpus.
SETTING_OPTIONS: tuple[str, ...] = (
    "indoors",
    "outdoors",
    "street",
    "countryside",
    "wilderness",
    "at sea",
    "underground",
    "unknown",
)
SETTINGS: frozenset[str] = frozenset(SETTING_OPTIONS)

# Separate from `setting` on purpose. Folded into one field, every place would
# need a value per lighting condition -- street-by-day, street-by-night -- and
# the pilot showed time of day carries its own signal anyway: the unreadable cap
# colours on 079 are unreadable *because* it is a night scene. Recorded here, a
# low speaker confidence on a night page is explained rather than just observed.
TIME_OF_DAY_OPTIONS: tuple[str, ...] = ("day", "night", "dusk-or-dawn", "indoors-or-unclear")
TIMES_OF_DAY: frozenset[str] = frozenset(TIME_OF_DAY_OPTIONS)

# Keys written onto a prelim group by `vision_apply` and read back by the editor.
SPEAKER_KEY = "speaker"
SPEAKER_CONFIDENCE_KEY = "speaker_confidence"
CAP_COLOUR_KEY = "cap_colour"
IDENTIFIED_BY_KEY = "identified_by"
VISION_NOTE_KEY = "vision_note"

# Written by the editor only. `speaker_confidence` alone cannot tell a human's
# confirmation from the model's own confident guess, and the difference is the
# whole point of the review pass.
SPEAKER_REVIEWED_KEY = "speaker_reviewed"

# Also written by the editor only, and only when a review *changes* the call:
# the pass's own answer, kept beside the reviewer's.
#
# A review outcome is an event, not a state, and `speaker_reviewed` records only
# that somebody looked. Every speaker error rate in `docs/vision-pass.md` -- the
# pilot's 10 in 14, Sheriff's 1 in 14, Plenty of Pets' 2 in 6, the 5 in 50 audit,
# Big Bin's 0 in 8 -- was reconstructed by diffing scratch files in
# `~/barks-vision` against the corpus, and vanishes with that directory. Storing
# the superseded call on the group makes a per-title error rate computable from
# the corpus alone: a reviewed group carrying `speaker_was` is a correction, one
# without it is a confirmation.
#
# Deliberately not a ledger. The datum belongs with the thing it describes, it
# survives any scratch directory, and a second record of what is on disk could
# only drift away from the disk.
SPEAKER_WAS_KEY = "speaker_was"
CAP_COLOUR_WAS_KEY = "cap_colour_was"
SPEAKER_REVIEWED_DATE_KEY = "speaker_reviewed_date"

# The reviewer's own reasoning, and the only field that can hold it.
#
# `vision_note` is the *pass's* reasoning and nothing supersedes it, so after a
# correction it is left asserting something the data now contradicts -- and it
# reads as authoritative while doing so. The one correction in the `other:` audit
# still says "Both balloons in this panel are hers; Donald and Scrooge are
# silent" on a group whose speaker is now Donald.
#
# Deliberately a *second* note rather than an edit of the first. Overwriting
# `vision_note` would destroy the evidence of how the pass went wrong, which is
# the raw material every finding in `docs/vision-pass.md` was derived from --
# the pilot's ambiguous tails, the 2x enlargements recorded in false precision.
# Both notes are kept and `speaker_was` says which one the data agrees with.
SPEAKER_REVIEW_NOTE_KEY = "speaker_review_note"

# The confidence a reviewed group carries: a human looked at the art.
REVIEWED_CONFIDENCE = "high"

# Queue issue types, shared between the queues `vision_apply` writes and the
# editor's info bar.
VISION_TEXT_ISSUE = "vision-text"
VISION_SPEAKER_ISSUE = "vision-speaker"

# Keys of the per-page capture file, written beside the prelim JSON rather than
# into it: `final_groups.py` copies only the `groups` key and would silently
# drop a new top-level section.
CHARACTERS_KEY = "characters"
SETTING_KEY = "setting"
TIME_OF_DAY_KEY = "time_of_day"
VISIBLE_TEXT_KEY = "visible_text"
OBJECTS_KEY = "objects"
BEATS_KEY = "beats"
PANELS_OF_NOTE_KEY = "panels_of_note"

# `objects` has no closed vocabulary and cannot have one -- a fly swatter, a
# legless chair and a goldfish bowl are not enumerable in advance. It is free
# text, normalized for whitespace and surfaced by the census like any other
# free-form value.
#
# It exists because the retrieval queries specified it. Sixty-odd of them ask
# for background props, and `beats` is three sentences that must also carry the
# plot: "Roscoe the Robot" is four pages and its queries name ten distinct
# objects. Beats could never have held that, and raising its cap would not have
# helped -- a prop only reaches a beat sentence if it is plot-relevant, and the
# useful queries are deliberately about props that are not.
#
# The cap is here for a different reason than `MAX_BEATS`. That one guards
# against retelling; this one guards against an inventory. A page listing thirty
# objects matches every query and discriminates nothing.
MAX_OBJECTS = 12

# Provenance. The capture layer is a cache -- a better model should be able to
# rebuild it -- so every record says what built it and when.
#
# These three were declared here, rendered into `vision_prep`'s stub and written
# up in the docs from the beginning, and **never actually written**: they were
# absent from `vision_apply`'s allowed capture keys, so a result that set them
# was rejected, and nothing else filled them in.  All 56 capture records written
# before 2026-08-03 carry nulls.  Fixed that day, which is why the version below
# starts at 2 -- version 1 is the unstamped cohort, identifiable only by the
# nulls it left behind.
CAPTURE_MODEL_KEY = "capture_model"
CAPTURE_PROMPT_VERSION_KEY = "capture_prompt_version"
CAPTURED_KEY = "captured"
CAPTURE_RULES_KEY = "capture_rules"

# Bumped whenever a change alters what the pass is asked to produce or what the
# tooling will accept, so a page can be told apart from one read under older
# rules.  `CAPTURE_RULES` spells the same thing out in names, because a bare
# integer tells a future reader nothing about what changed.
CAPTURE_PROMPT_VERSION = 3

# The rules in force that change what the pass does, newest last.  Add an entry and bump the version
# above in the same commit.
CAPTURE_RULES: tuple[str, ...] = (
    # An individual nephew may not be named at low confidence; if the cap cannot
    # be read the answer is the collective.  Added after the pilot's 10-in-14.
    "collective-nephew",
    # Emphasis is inline `[b]`/`[i]` markup inside ai_text, not stored offsets.
    "inline-emphasis",
    # Annotations are copied onto the other engine's groups, so a pass does not
    # widen the gap the two-engine reconciliation is closing.
    "mirror-engines",
    # An individual nephew named on a cap colour with no sibling nephew in the
    # panel is queued for review whatever confidence the pass gave it.  Added
    # after the 50-call audit found that configuration 24% wrong.
    "lone-panel-queue",
    # Every speaker call records what evidence it rests on, so a call made from
    # a hat, a costume or the previous balloon is as reversible as a nephew call
    # made from a cap already was.
    "identified-by",
    # `panels_of_note` names the shot where the framing is the point. The five-
    # title trial's only *not recorded* misses were both queries asking for one.
    "framing-vocabulary",
)


class PublicationClass(StrEnum):
    """What a field is, for the purpose of deciding whether it may be published.

    The Barks comics are in US copyright until roughly 2038-2062, so the corpus
    permanently splits in two.  Recording that split per field, in code, is
    deliberate: the sibling wiki states "never reproduce" in four separate
    places and still emits verbatim prose, because the rule lived in prose and
    the generator underneath it did not follow it.
    """

    #: Measurements, identifiers and closed-vocabulary labels. Not expression.
    FACT = "fact"
    #: Our own words *about* the work. Ours to license, but it is what starts to
    #: resemble an abridgment if it ever grows into a page-by-page retelling.
    DERIVED = "derived"
    #: Text copied out of the comic, or inseparable from it. Never published.
    VERBATIM = "verbatim"


# Every key any of these tools writes or reads, and what it is. Deliberately
# exhaustive: `classify` raises on anything absent rather than defaulting, so a
# new field cannot reach an exporter without someone having said what it is.
FIELD_CLASS: dict[str, PublicationClass] = {
    # -- existing prelim group fields ------------------------------------
    "panel_num": PublicationClass.FACT,
    "panel_id": PublicationClass.FACT,
    "text_box": PublicationClass.FACT,
    "type": PublicationClass.FACT,
    "style": PublicationClass.FACT,
    "use_as_final": PublicationClass.FACT,
    "florence_passed": PublicationClass.FACT,
    "ai_text": PublicationClass.VERBATIM,
    "ocr_text": PublicationClass.VERBATIM,
    "cleaned_box_texts": PublicationClass.VERBATIM,
    "notes": PublicationClass.DERIVED,
    # -- written by the vision pass onto a group -------------------------
    SPEAKER_KEY: PublicationClass.FACT,
    SPEAKER_CONFIDENCE_KEY: PublicationClass.FACT,
    SPEAKER_REVIEWED_KEY: PublicationClass.FACT,
    CAP_COLOUR_KEY: PublicationClass.FACT,
    # Closed-vocabulary labels about the art, exactly as `cap_colour` is.
    IDENTIFIED_BY_KEY: PublicationClass.FACT,
    # The superseded call and when it was superseded. Same class as the fields
    # they shadow -- a wrong closed-set label is still a closed-set label.
    SPEAKER_WAS_KEY: PublicationClass.FACT,
    CAP_COLOUR_WAS_KEY: PublicationClass.FACT,
    SPEAKER_REVIEWED_DATE_KEY: PublicationClass.FACT,
    VISION_NOTE_KEY: PublicationClass.DERIVED,
    # Our own words about the work, exactly as `vision_note` is.
    SPEAKER_REVIEW_NOTE_KEY: PublicationClass.DERIVED,
    "vision_text_ok": PublicationClass.FACT,
    "vision_corrected_text": PublicationClass.VERBATIM,
    # The marked-up `ai_text`: the comic's own words, so it is classed exactly
    # as `ai_text` is. (The retired `emphasis_spans` was classed VERBATIM too,
    # on the reasoning that offsets encode the shape of the text they index.
    # Inline markup makes that literal rather than an inference.)
    EMPHASIS_MARKUP_KEY: PublicationClass.VERBATIM,
    # -- the per-page capture file ---------------------------------------
    CHARACTERS_KEY: PublicationClass.FACT,
    SETTING_KEY: PublicationClass.FACT,
    TIME_OF_DAY_KEY: PublicationClass.FACT,
    OBJECTS_KEY: PublicationClass.FACT,
    VISIBLE_TEXT_KEY: PublicationClass.VERBATIM,
    BEATS_KEY: PublicationClass.DERIVED,
    PANELS_OF_NOTE_KEY: PublicationClass.DERIVED,
    CAPTURE_MODEL_KEY: PublicationClass.FACT,
    CAPTURE_PROMPT_VERSION_KEY: PublicationClass.FACT,
    CAPTURED_KEY: PublicationClass.FACT,
    CAPTURE_RULES_KEY: PublicationClass.FACT,
}


_WHITESPACE_RE = re.compile(r"\s+")
_ROSTER_BY_CASEFOLD: dict[str, str] = {name.casefold(): name for name in SPEAKER_OPTIONS}
_SETTINGS_BY_CASEFOLD: dict[str, str] = {name.casefold(): name for name in SETTING_OPTIONS}


def classify(key: str) -> PublicationClass:
    """Return what kind of thing *key* holds.

    Args:
        key: A field name written or read by these tools.

    Returns:
        Its :class:`PublicationClass`.

    Raises:
        KeyError: If the field has no declared class. This is the point of the
            table -- a field nobody has classified must stop an export rather
            than be guessed at, since guessing wrong in the permissive
            direction publishes someone else's copyright.

    """
    try:
        return FIELD_CLASS[key]
    except KeyError:
        msg = (
            f"Field {key!r} has no publication class."
            " Add it to FIELD_CLASS in utils/vision_schema.py before exporting it."
        )
        raise KeyError(msg) from None


def publishable(keys: Iterable[str]) -> list[str]:
    """Return only the keys that may leave this machine.

    Args:
        keys: Field names to filter.

    Returns:
        Those classed :attr:`PublicationClass.FACT`, in the order given.

    Raises:
        KeyError: If any key has no declared class.

    """
    return [key for key in keys if classify(key) is PublicationClass.FACT]


def verbatim_keys(keys: Iterable[str]) -> list[str]:
    """Return the keys that hold comic text and must never be published.

    Args:
        keys: Field names to check.

    Returns:
        Those classed :attr:`PublicationClass.VERBATIM`, in the order given.

    Raises:
        KeyError: If any key has no declared class.

    """
    return [key for key in keys if classify(key) is PublicationClass.VERBATIM]


def collapse_whitespace(value: str) -> str:
    """Return *value* with outer and repeated whitespace collapsed.

    The only drift that can be fixed mechanically in a free-text field with no
    vocabulary behind it. ``"fly  swatter"`` and ``"fly swatter "`` name one
    object; anything subtler is for the census and a human.

    Args:
        value: The value as written.

    Returns:
        The value to store.

    """
    return _WHITESPACE_RE.sub(" ", value.strip())


def _normalize_vocab_value(value: str, canonical: Mapping[str, str]) -> str:
    """Collapse whitespace and unwrap a prefixed value that is really canonical.

    Case is deliberately left alone: "McFiendy" has no safe automatic casing,
    and title-casing it would be a different kind of wrong. Case variants are
    surfaced by ``barks-ocr-speaker-census`` for a human to merge instead.
    """
    value = _WHITESPACE_RE.sub(" ", value.strip())
    if not value.startswith(OTHER_PREFIX):
        return value
    name = value[len(OTHER_PREFIX) :].strip()
    if not name:
        return value  # Names nothing; the `is_valid_*` check rejects it anyway.
    return canonical.get(name.casefold(), OTHER_PREFIX + name)


def normalize_speaker(speaker: str) -> str:
    """Return the canonical stored form of *speaker*.

    Free-form names are where drift gets in. ``"other: Argus  McFiendy"`` and
    ``"other:Argus McFiendy"`` name one character but are two distinct speakers,
    and nothing downstream would ever reconcile them, so outer and repeated
    whitespace is collapsed. A roster name written behind the prefix
    (``"other:Donald"``) is unwrapped to the roster entry it already is.

    Args:
        speaker: The speaker value as written.

    Returns:
        The value to store. Unchanged if it is already canonical.

    """
    return _normalize_vocab_value(speaker, _ROSTER_BY_CASEFOLD)


def normalize_setting(setting: str) -> str:
    """Return the canonical stored form of *setting*.

    The same drift applies as to speakers, and for the same reason: a named
    place recorded as free text is only text until the census promotes it.

    Args:
        setting: The setting value as written.

    Returns:
        The value to store. Unchanged if it is already canonical.

    """
    return _normalize_vocab_value(setting, _SETTINGS_BY_CASEFOLD)


def speaker_key(speaker: str) -> str:
    """Return a key that collapses the spellings of one speaker onto one value.

    Case-insensitive, unlike :func:`normalize_speaker`, so the census can group
    ``other:crows`` with ``other:Crows`` and show them side by side.

    Args:
        speaker: The speaker value as stored.

    Returns:
        A grouping key. Not a storable speaker value.

    """
    return normalize_speaker(speaker).casefold()


def roster_text(story_characters: Iterable[str] = (), story_things: Iterable[str] = ()) -> str:
    """Render the vocabulary as the ``roster.txt`` handed to the vision pass.

    Generated rather than written by hand: the names the pass is told and the
    names ``vision_apply`` will accept are then the same names by construction.

    Args:
        story_characters: This story's database character tags, which extend the
            main-cast roster for the run in hand. Passing them makes the answer
            a closed-set choice rather than an open one, so a name outside the
            set is an error signal instead of silent drift.
        story_things: This story's database thing tags. Not a vocabulary --
            ``objects`` cannot have one -- but naming anchors, so a recurring
            prop is written the same way each time it appears.

    Returns:
        The full text of the roster file, newline-terminated.

    """
    extra = sorted(set(story_characters) - ROSTER)
    lines = [
        "# Vision pass vocabulary — generated from barks_ocr/utils/vision_schema.py.",
        "# `vision_apply` validates every result.json against exactly these values,",
        "# and anything else aborts the run once the reading work is already done.",
        "",
        "speaker — one of:",
    ]
    width = max(len(name) for name in SPEAKER_OPTIONS)
    lines += [
        f"  {name.ljust(width)}  {SPEAKER_NOTES.get(name, '')}".rstrip() for name in SPEAKER_OPTIONS
    ]
    if extra:
        lines += [
            "",
            "  and, tagged in the database as appearing in THIS story:",
            *[f"    {name}" for name in extra],
        ]
    lines += [
        f'  anyone else goes behind the prefix: "{OTHER_PREFIX}the shopkeeper".',
        "  The name after the colon must not be empty.",
        "",
        f"speaker_confidence — one of: {', '.join(CONFIDENCE_OPTIONS)}",
        (
            f"  Naming one nephew at {NEPHEW_GUESS_CONFIDENCE} confidence is REFUSED."
            " If you cannot tell which"
        ),
        "  of the three it is, the answer is `nephews` — and you are not unsure of that,",
        "  so it is not a low-confidence call. Being unsure which nephew is exactly what",
        "  `nephews` is for; a guess at a name is unrecoverable, a collective is not.",
        f"cap_colour — one of: {', '.join(CAP_COLOUR_OPTIONS)}, or null when no cap is visible",
        f"{IDENTIFIED_BY_KEY} — what the call actually rests on. A list, because a real",
        "  call usually rests on more than one thing. One or more of:",
        *[
            f"  {kind.ljust(max(len(k) for k in IDENTIFIED_BY_OPTIONS))}  "
            f"{IDENTIFIED_BY_NOTES.get(kind, '')}".rstrip()
            for kind in IDENTIFIED_BY_OPTIONS
        ],
        "  Record it even when the answer seems obvious: this is what makes a call",
        "  reversible later. cap_colour already does that for a nephew, and nothing",
        "  did it for an adult identified by a hat, for a call made from what a",
        "  character was wearing, or for a speaker named by the previous balloon",
        "  rather than by the art. Omit only for `none`.",
        (
            f"{EMPHASIS_MARKUP_KEY} — the group's ai_text with emphasis marked"
            f" inline: {', '.join(f'[{t}]WORD[/{t}]' for t in EMPHASIS_TAGS)}."
        ),
        "  Copy the ai_text exactly and add only the tags; it is checked against",
        "  the stored text and the run is refused if anything else changed.",
        "  A literal [ ] or & in the lettering must be written &bl; &br; &amp;.",
        "  Omit the field when nothing on the page is emphasized.",
        "",
        "Per page, in the page capture file:",
        "",
        f"  {CHARACTERS_KEY} — who is DEPICTED on the page, from the speaker list above.",
        "    Not who speaks: a character in frame and silent still belongs here.",
        f"  {SETTING_KEY} — one of: {', '.join(SETTING_OPTIONS)}",
        f'    a specific named place goes behind the prefix: "{OTHER_PREFIX}the Money Bin".',
        f"  {TIME_OF_DAY_KEY} — one of: {', '.join(TIME_OF_DAY_OPTIONS)}",
        f"  {VISIBLE_TEXT_KEY} — lettering that is NOT speech: signs, posters, newspapers,",
        "    labels, sound effects painted into the art. Transcribe exactly; omit if none.",
        f"  {OBJECTS_KEY} — notable things visible on the page, at most {MAX_OBJECTS}.",
        "    Short noun phrases: 'fly swatter', 'goldfish bowl', 'sheriff's badge'.",
        "    Include a prop even when it carries no plot -- that is exactly what this",
        "    field is for, and what the sentences below will not mention. But do not",
        "    inventory the scenery: a page listing everything matches everything.",
        *(
            [
                "    The database records these notable things in THIS story --",
                "    name them this way so they stay findable:",
                *[f"      {name}" for name in sorted(set(story_things))],
            ]
            if story_things
            else []
        ),
        f"  {BEATS_KEY} — 1 to 3 plain sentences saying what happens on the page.",
        "    Describe only what is shown. No mood, no significance, no interpretation.",
        f"  {PANELS_OF_NOTE_KEY} — [[panel_num, phrase], ...] for panels worth addressing",
        "    on their own: the splash, the gag, the reveal. Most pages need none, and",
        "    listing every panel defeats the point.",
        "    Name the SHOT as well as its contents where the framing is the point --",
        "    'establishing shot', 'close-up', 'wide', 'silhouette', 'from above',",
        "    'no characters in frame'. This is the one gap five titles of capture",
        "    found: the pages were described in detail and the framing never was, so",
        "    a query asking for an establishing shot reached nothing. Do not label",
        "    every panel; only where the framing is what makes the panel notable.",
    ]
    return "\n".join(lines) + "\n"


def is_valid_speaker(speaker: str, story_characters: Iterable[str] = ()) -> bool:
    """Return whether *speaker* is an allowed name for this story.

    A bare ``"other:"`` with nothing after it is not valid — it names no one.

    Args:
        speaker: The speaker value to check.
        story_characters: Extra exact-matched names for the story in hand,
            supplied from its database character tags. These cover the long
            tail — Bolivar, Magica, Argus McFiendy — which the main-cast roster
            deliberately omits, and which would otherwise drift as free text.

    Returns:
        True if the value is acceptable for the ``speaker`` field.

    """
    if speaker in ROSTER or speaker in set(story_characters):
        return True
    return speaker.startswith(OTHER_PREFIX) and bool(speaker[len(OTHER_PREFIX) :].strip())


def is_valid_setting(setting: str) -> bool:
    """Return whether *setting* is a vocabulary entry or a prefixed free-form place.

    Args:
        setting: The setting value to check.

    Returns:
        True if the value is acceptable for the ``setting`` field.

    """
    if setting in SETTINGS:
        return True
    return setting.startswith(OTHER_PREFIX) and bool(setting[len(OTHER_PREFIX) :].strip())


def invalid_identified_by(kinds: Iterable[str]) -> list[str]:
    """Return the evidence kinds that are not in the vocabulary.

    Closed with no ``other:`` escape, unlike ``speaker`` and ``setting``. The
    point of the field is to make calls comparable across a corpus -- to ask
    whether two calls in one panel rest on the same evidence, or whether the
    costume-based calls are the ones that turn out wrong -- and free text cannot
    be counted. A kind genuinely missing from the list is a reason to add one
    here, deliberately, rather than to let it arrive unannounced.

    Args:
        kinds: The ``identified_by`` values from one group.

    Returns:
        The unrecognized values, in the order given. Empty when all are valid.

    """
    return [kind for kind in kinds if kind not in IDENTIFIED_BY_SET]
