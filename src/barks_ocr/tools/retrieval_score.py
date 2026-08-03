# ruff: noqa: T201
"""Score the retrieval queries in ``docs/retrieval-queries.md`` against page capture.

The queries are the acceptance test for the vision pass's page-capture layer, and
their hit rate is measurement 2 of the five the trial is running.  That number is
only meaningful against the *previous* title's number, so the scorer has to be the
same one -- which is exactly what went wrong after trial 1, where the scoring was
done with a throwaway script and the write-up had to record the tool itself as a
variable in the measurement.  This module exists so that cannot happen again.

``--validate`` re-scores *Roscoe the Robot* and checks the result against the
recorded trial-1 outcome (15 hits of 16, #93 the only *not retrieved* miss).  Run
it before trusting a new title's number: if the calibration has drifted, the two
titles are no longer being measured the same way.

**Two matcher generations, and both stay runnable.** ``--matcher lexical`` is the
one the five-title trial was scored with, and every number in
``docs/vision-pass.md`` is its; it is frozen. ``--matcher v2`` (the default) adds
a Porter stemmer, compound joining and IDF-weighted ranking, each earned by a
documented miss. Replacing the old matcher rather than keeping it would have made
the trial's recorded results unverifiable the moment the scorer moved on, which
is the very failure this module was written to prevent -- so ``--validate``
carries one calibration per generation and checks whichever is selected.

The ``lexical`` rules, which ``v2`` inherits except where noted:

* parentheticals are dropped, so "a fly (the insect)" searches for "a fly";
* function words are dropped, and so are one-character tokens, since the ``s``
  that falls out of every possessive would otherwise match everything;
* a query token matches a record token when they are equal, when one is a prefix
  of the other and the shorter is at least 4 characters ("alley" / "alleyway"),
  or when they are within one edit and at least 6 characters, which is what
  carries the query set's own typo in #91 ("dumbells" / "dumbbells");
* a page scores the number of *distinct* query tokens it matches, and the result
  is the highest-scoring band, capped at ``TOP_BAND``.

``v2`` changes three of those and the tally moves 81 hits to 85 across the five
titles -- five queries fixed, one lost:

* **stemming** fixes ``sneeze``/``sneezing`` (#38) and ``hide``/``hiding`` (#70),
  and retrieves #79 on ``falling``/``fall`` where the noun still misses;
* **compound joining** fixes #103, ``flypaper`` against the art's own
  ``FLY PAPER``. Compounds match by equality only and are formed within one
  string, both learnt the hard way: left open to the prefix rule, a query's
  "down" reached a junk join starting with it and scored pages on nothing;
* **IDF weighting** fixes #29, where nine pages tied at the top score and the cap
  truncated the tie by page number. It costs #82, and that is worth reading
  rather than regretting: #82's ``lexical`` hit was *also* a tie artifact -- seven
  pages tied at 1.0 and alphabetical truncation happened to keep two correct ones.
  The same mechanism produced one lucky hit and one unlucky miss in one title.

The fuzzy rule was measured while it was being reasoned about, since the trial
recorded a suspicion that it cost more than it earned. Under ``v2`` its **only**
effect across all five titles is #91, where it carries the query set's own typo
(``dumbells``). It buys one hit and no longer changes any other result, because
the stemmer took over the morphology it was compensating for.

Note what is **not** stripped: "character", "panel", "page" and "story" stay in
the query.  They look like noise but they are load-bearing -- #30 ("the story's
splash page") reaches Roscoe 175 only through the word "story" in its
``panels_of_note`` phrase "the story's title logo".  Removing them is a change to
the measurement, not a cleanup.

Two layers are indexed separately so every hit can be attributed:

``capture``
    ``characters``, ``setting``, ``time_of_day``, ``visible_text``, ``objects``,
    ``beats`` and ``panels_of_note``, read from the ``-page-capture.json``
    sidecars ``vision_apply`` writes beside the prelim OCR JSON.
``speech``
    the stored ``ai_text`` of every group on the page, markup stripped.

A ``capture`` query the speech layer could have answered on its own is still
reported as a hit, but it is *not* a hit the vision pass earned, and the tally
keeps the two apart.  Trial 1's honest figure was 11 capture-only of 15.
"""

import json
import math
import re
from dataclasses import dataclass
from itertools import pairwise
from typing import Annotated, Any

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from barks_fantagraphics.speech_markup import strip_markup, unescape_markup
from loguru import logger
from whoosh.lang.porter import stem as porter_stem

from barks_ocr.utils.vision_schema import (
    BEATS_KEY,
    CHARACTERS_KEY,
    OBJECTS_KEY,
    OTHER_PREFIX,
    PANELS_OF_NOTE_KEY,
    SETTING_KEY,
    TIME_OF_DAY_KEY,
    VISIBLE_TEXT_KEY,
)

app = typer.Typer()

CAPTURE_FILE_SUFFIX = "-page-capture.json"

CAPTURE_FIELDS: tuple[str, ...] = (
    CHARACTERS_KEY,
    SETTING_KEY,
    TIME_OF_DAY_KEY,
    VISIBLE_TEXT_KEY,
    OBJECTS_KEY,
    BEATS_KEY,
    PANELS_OF_NOTE_KEY,
)

# Function words only. "character", "panel", "page" and "story" are deliberately
# absent -- see the module docstring.
_STOP_WORD_TEXT = """
    a an the of in on at to for with and or is are was were be being been
    it its that this these those his her their there here from by as into
    some any no not one two what which who whom whose how why when where
    has have had do does did will would can could
"""
STOP_WORDS: frozenset[str] = frozenset(_STOP_WORD_TEXT.split())

TOP_BAND = 3  # "the right page is in the top few results"
MIN_PREFIX = 4  # shortest token allowed to match as a prefix
MIN_FUZZY = 6  # shortest token allowed to match within one edit
MIN_TOKEN = 2  # a bare "s" off a possessive would match every possessive

_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Matcher:
    """One generation of the matching rules, named so a result can cite it.

    The five-title trial was scored entirely by ``LEXICAL``, and every number in
    ``docs/vision-pass.md`` is that matcher's.  Improving the matcher is a change
    to the measurement, so the old one is kept runnable rather than replaced:
    otherwise the trial's recorded results become unverifiable the moment the
    scorer moves on, which is the exact failure this module was written to
    prevent.

    ``rules`` is listed for the same reason ``capture_rules`` is stamped on a
    capture record -- a bare version number tells a later reader nothing about
    what changed.
    """

    name: str
    rules: tuple[str, ...]
    stem: bool = False
    compounds: bool = False
    idf: bool = False
    fuzzy: bool = True
    semantic: bool = False
    # LEXICAL keeps only the pages tied at the maximum score, capped at TOP_BAND,
    # which is what truncated Sheriff's #29 alphabetically. Graded scores make
    # exact ties vanishingly rare, so a max-only band would collapse to a single
    # page; ranked_band takes the top TOP_BAND by score instead, which is the
    # ordinary recall@3 the cap was always reaching for.
    ranked_band: bool = False


LEXICAL = Matcher(
    name="lexical",
    rules=("exact", "prefix>=4", "fuzzy>=6", "count-distinct-tokens", "max-score-band"),
)

V2 = Matcher(
    name="v2",
    rules=(
        "exact",
        "prefix>=4",
        "fuzzy>=6",
        "porter-stem",
        "compound-join",
        "idf-weighted",
        "ranked-band",
    ),
    stem=True,
    compounds=True,
    idf=True,
    ranked_band=True,
)

V3 = Matcher(
    name="v3",
    rules=(
        "exact",
        "prefix>=4",
        "fuzzy>=6",
        "porter-stem",
        "compound-join",
        "idf-weighted",
        "ranked-band",
        "semantic-rrf",
    ),
    stem=True,
    compounds=True,
    idf=True,
    ranked_band=True,
    semantic=True,
)

MATCHERS = {m.name: m for m in (LEXICAL, V2, V3)}
DEFAULT_MATCHER = V2

# Sentence embeddings for the semantic half of `v3`. Chosen for quality rather
# than speed: the whole corpus is 66 captured pages and about a hundred queries,
# so throughput is irrelevant and the larger model is free.
EMBED_MODEL = "all-mpnet-base-v2"  # cspell:disable-line

# Reciprocal rank fusion, the standard way to combine a lexical and a dense
# retriever. Deliberately parameter-light: k is the conventional 60 and NOTHING
# is tuned against the query set. That restraint is the point -- the queries are
# the acceptance test for the capture layer, so fitting a weight to them would
# make the test grade its own answer, which is the same error as scoring expected
# pages from the capture records instead of from the art.
RRF_K = 60

# A dense retriever always returns a ranking -- a cosine is never zero -- so it
# has no natural notion of "nothing here". Left unbounded it proposes TOP_BAND
# pages for every query, which on a four-page title means three of the four come
# back whatever was asked, and the capture-only/speech-answerable split collapses
# to nothing. That split is one of the numbers the trial reports, so this matters
# more than the hit rate.
#
# The gate is deliberately **relative to the query's own spread** rather than a
# fixed cosine: a page must stand out from the other pages of its title by this
# many standard deviations to be proposed at all. A fixed threshold would have to
# be picked by looking at which value made the expected pages pass, and the
# queries are the acceptance test -- fitting to them is the same error as taking
# expected pages from the capture records instead of from the art. One sigma is
# the conventional outlier mark, not a tuned value.
SEMANTIC_SIGMA = 1.0

# A spread needs at least two pages to mean anything.
MIN_PAGES_FOR_SPREAD = 2


# --------------------------------------------------------------------------- #
# The query sets, per title.
#
# Each entry is (number, query text, expected pages).  The numbers are those in
# `docs/retrieval-queries.md`; the expected pages are filled in from the trial
# and are what the scorer counts against.  `None` means no page was committed
# in advance, so the query can only ever be a miss here -- which is itself the
# finding for a state the capture layer never records.
# --------------------------------------------------------------------------- #

# Sheriff of Bullet Valley runs 32 pages, so several of its queries are true of
# most of the story.  Those lists are pulled out here rather than inlined, both to
# keep the table readable and to make the breadth visible: a query whose expected
# list is nearly the whole title cannot discriminate, and that is a finding about
# the query rather than about the capture.
SHERIFF_ALL_PAGES: list[str] = [str(p) for p in range(144, 176)]

SHERIFF_COWBOY_PAGES = SHERIFF_ALL_PAGES  # every page has someone in cowboy dress

# fmt: off
SHERIFF_HANDGUN_PAGES = [
    "144", "147", "148", "149", "151", "152", "153", "155", "156", "157", "163",
    "164", "165", "166", "167", "168", "169", "170", "171", "172", "173", "175",
]
SHERIFF_HORSE_PAGES = [
    "146", "147", "148", "149", "150", "151", "152", "153", "154", "155", "156",
    "157", "160", "162", "164", "165", "169", "170", "171", "174", "175",
]
SHERIFF_BADGE_PAGES = [
    "145", "146", "147", "148", "149", "150", "151", "152", "153", "154", "155",
    "156", "157", "162", "164", "165", "166", "167", "168", "169", "170", "171",
    "172", "173", "174", "175",
]
SHERIFF_BADLANDS_PAGES = [
    "144", "147", "148", "149", "154", "155", "156", "157", "162", "165", "166",
    "167", "169", "170", "171", "172", "173", "174", "175",
]
SHERIFF_SILHOUETTE_PAGES = [
    "146", "147", "148", "149", "154", "155", "158", "161", "164", "165", "168",
    "169", "171", "175",
]
SHERIFF_SUB_MACHINEGUN_PAGES = [
    "149", "151", "155", "156", "160", "163", "166", "169", "170",
]
SHERIFF_RANCH_PAGES = [
    "149", "150", "151", "152", "153", "154", "158", "159", "160",
]
# fmt: on

# Every page of Plenty of Pets after the nephews get home has the pets loose on it.
POP_ANIMAL_PAGES: list[str] = [str(p) for p in range(200, 209)]


QUERIES: dict[str, list[tuple[int, str, list[str] | None]]] = {
    "Roscoe the Robot": [
        (16, "Gyro's Little Helper", ["175", "176", "177", "178"]),
        (30, "the story's splash page", ["175"]),
        (43, "a panel containing silhouettes", ["177", "178"]),
        (84, "a robot", ["175", "176", "177", "178"]),
        (85, "a character being electrocuted", ["175"]),
        (86, "a hammer", ["175"]),
        (87, "a fly swatter", ["176"]),
        (88, "a gold fish in a bowl", ["176"]),
        (89, "a medical kit", ["176"]),
        (90, "a fly (the insect)", ["175", "176"]),
        (91, "a dumbells", ["176"]),
        (92, "a legless chair", ["175", "176"]),
        (93, "a character being hit", ["176"]),
        (94, "a character that is a postman", ["177"]),
        (96, "an alleyway", ["177", "178"]),
        (97, "a character fainting", ["178"]),
    ],
    "Billions to Sneeze At": [
        (11, "Scrooge diving into his money bin", ["046"]),
        (26, "an establishing shot with no characters in frame", None),
        (30, "the story's splash page", ["044"]),
        (33, "a character that is sick", ["049", "050"]),
        (34, "a character that is sad", ["044", "047", "048", "052"]),
        (35, "a character that is smiling", None),
        (36, "a character that is using a machine", ["045", "047"]),
        (37, "a character that is crying", ["044", "047", "048", "052"]),
        (38, "a character that is sneezing", ["048", "049", "050"]),
        (39, "a character kissing", ["048"]),
        (40, "a character that is a doctor", ["050"]),
        (41, "a cave", ["050", "052"]),
        (42, "a character that has a halo", ["051", "052"]),
        (43, "a panel containing silhouettes", ["044", "045", "050", "051"]),
        (44, "a panel containing a campfire", ["050", "052"]),
        (45, "a character pointing", ["047"]),
        (46, "a sound effect", ["048", "049", "052"]),
        (115, "a fire hydrant", ["049"]),
    ],
    # 27 of the queries in `docs/retrieval-queries.md` name this title (#22, #29,
    # #31 and the whole run #59-#82), plus three that any title can answer.  The
    # expected pages were taken from the ART while reading, not from what the
    # capture records happen to say -- that is what lets a miss be split into
    # "not recorded" and "not retrieved".
    "Sheriff of Bullet Valley": [
        (22, "a wanted poster or reward notice", ["144", "145", "175"]),
        (29, "a chase or pursuit across several panels", ["164", "174"]),
        (30, "the story's splash page", ["144"]),
        (31, "the nephews driving a car", ["154", "155", "157"]),
        (43, "a panel containing silhouettes", SHERIFF_SILHOUETTE_PAGES),
        (59, "car 313", ["144", "146", "154", "155", "157"]),
        # True of nearly every page in the story -- kept honest and reported as
        # non-discriminating rather than trimmed to flatter the hit rate.
        (60, "a character that is a cowboy", SHERIFF_COWBOY_PAGES),
        (61, "a handgun", SHERIFF_HANDGUN_PAGES),
        (62, "a river or creek", ["146", "147", "149", "150", "155", "161"]),
        (63, "a brand on cattle", ["147", "151", "152", "154", "160"]),
        (64, "a character riding a horse", SHERIFF_HORSE_PAGES),
        (65, "a character wearing a sheriff's badge", SHERIFF_BADGE_PAGES),
        (66, "a character cutting a wire fence", ["151"]),
        (67, "a character being tied up", ["153", "158", "159", "160", "174", "175"]),
        (68, "a gunshot", ["155", "157", "163", "166", "170", "172", "173"]),
        (69, "a walkie talkie", ["156"]),
        (70, "a character hiding", ["159", "160", "165"]),
        (71, "a rifle", ["150", "157", "163", "164"]),
        (72, "a sub-machinegun", SHERIFF_SUB_MACHINEGUN_PAGES),
        (73, "a character sleeping", ["162"]),
        (74, "an antenna", ["156", "163", "164"]),
        (75, "a character yelling", ["150", "151", "152", "158", "165"]),
        (76, "a character feeling pain", ["157", "166", "167", "171", "174"]),
        (77, "badlands", SHERIFF_BADLANDS_PAGES),
        (78, "a hand grenade", ["172"]),
        (79, "a character's pants falling down", ["173", "174"]),
        (80, "an empty handgun", ["173"]),
        (81, "a sunset", ["175"]),
        (82, "a character smoking a pipe", ["145", "150", "151", "164", "167", "168", "175"]),
        (83, "a cattle ranch", SHERIFF_RANCH_PAGES),
    ],
    # 13 of the queries in `docs/retrieval-queries.md` name this title (#47-#58 and
    # #95), plus two any title can answer.  Expected pages taken from the ART while
    # reading, before any capture record existed for the page.
    "Plenty of Pets": [
        (30, "the story's splash page", ["199"]),
        (43, "a panel containing silhouettes", ["200", "204", "205"]),
        (47, "a character that is a policeman", ["199"]),
        (48, "a character carrying something", ["199", "204", "208"]),
        # True of nine of the ten pages -- this is a pet-shop story.  Recorded at its
        # real breadth and reported as non-discriminating rather than trimmed.
        (49, "non-speaking animals", POP_ANIMAL_PAGES),
        (50, "a radio", ["202"]),
        (51, "a character colliding with something", ["200", "203", "206"]),
        (52, "a character collapsed", ["203", "206"]),
        (53, "a character in bed", ["204", "205", "207", "208"]),
        (54, "a character that is a burglar", ["204", "205", "206", "207"]),
        (55, "a burglar putting objects in bag", ["205"]),
        (56, "a telephone", ["205", "208"]),
        (57, "a character that is scared", ["199", "205", "206", "207"]),
        (58, "a character eating food", ["208"]),
        (95, "a letterbox", ["199"]),
    ],
    # 19 of the queries in `docs/retrieval-queries.md` name this title (#98-#116),
    # plus five any title can answer (#11, #17, #26, #30, #43).  Expected pages
    # taken from the ART while reading, before any capture record existed.
    #
    # This is the only title in the trial with a non-empty `story_cast`, which is
    # what #17 is here to exercise: the Beagle Boys have to come back from the
    # closed set rather than from an `other:` free-text name.
    "The Big Bin on Killmotor Hill": [
        (11, "Scrooge diving into his money bin", ["041"]),
        (17, "the Beagle Boys in their masks", ["042", "047"]),
        # The one panel in the story with no character in frame at all: the burst
        # fire hydrant in the empty night street, and the bin splitting from outside.
        (26, "an establishing shot with no characters in frame", ["046"]),
        (30, "the story's splash page", ["038"]),
        (43, "a panel containing silhouettes", ["046"]),
        (98, "an establishing shot", ["038", "047"]),
        (99, "an acid moat", ["040"]),
        (100, "a microphone", ["040"]),
        (101, "a cannon", ["040", "044"]),
        (102, "a portcullis", ["040"]),
        (103, "flypaper", ["040"]),
        (104, "a beartrap", ["040"]),
        (105, "a drawbridge", ["040", "043", "044"]),
        (106, "an alarm bell", ["041"]),
        # Drawn as hearts round Scrooge's head, never named. Committed because the
        # art plainly shows it; if it misses, that is the emotion result again.
        (107, "love", ["041"]),
        (108, "a periscope", ["042", "043"]),
        (109, "a pickaxe", ["042"]),
        (110, "a spade", ["042"]),
        # Same shape as #107: drawn as sobbing, tears and clutched head, never
        # named as worry.
        (111, "worry", ["043", "044", "046"]),
        (112, "wall painting", ["045"]),
        (113, "a water hose", ["045"]),
        (114, "character kicking another character", ["045"]),
        (115, "a fire hydrant", ["046"]),
        (116, "making a fire with books", ["046"]),
    ],
}

# The trial-1 result recorded in `docs/vision-pass.md`, which `--validate` holds
# the scorer to.  `capture_only` is not asserted: the write-up's 11 counts #16 as
# earned by capture, where a purely lexical speech layer credits it to the
# dialogue, because 176 happens to call Roscoe "a strong, alert HELPER".
TRIAL_1_TITLE = "Roscoe the Robot"

# One calibration per matcher generation. The `lexical` entry is the trial-1
# result every number in `docs/vision-pass.md` was measured against and must
# never change; a later matcher gets its own entry rather than overwriting it,
# so a drift in either is still caught.
TRIAL_1_RESULTS: dict[str, dict[str, object]] = {
    "lexical": {"hit": 15, "miss": 1, "missed": [93]},
    "v2": {"hit": 15, "miss": 1, "missed": [93]},
    # v3 does not move Roscoe: #93 is a four-page title's only miss, and the
    # semantic gate asks a page to stand a sigma clear of its siblings, which
    # four pages rarely manage. The calibration is unchanged rather than absent.
    "v3": {"hit": 15, "miss": 1, "missed": [93]},
}


def _tokens(text: str, matcher: Matcher = LEXICAL) -> set[str]:
    """Return the searchable word tokens of a record field."""
    found = set(_WORD_RE.findall(text.lower()))
    if matcher.stem:
        found |= {_stem(word) for word in found}
    return found


def _compound_tokens(parts: list[str]) -> set[str]:
    """Return the join of each adjacent word pair, so an open compound is reachable.

    This is trial 5's ``flypaper`` miss: the art letters ``FLY PAPER``, the
    capture rightly used the comic's own two words, and obeying the
    prefer-the-source rule is therefore what caused the miss. Neither a stemmer
    nor an embedding over single words closes it -- the split is in how the text
    divides into tokens at all.

    Two constraints, both learnt by getting it wrong first. Pairs are formed
    **within one string**, never across the join of a field's separate values,
    or the last word of one object phrase and the first of the next fuse into a
    word neither of them contains. And a compound is only ever matched
    **exactly** (see ``_page_score``): left open to the prefix rule, every
    compound becomes a magnet for the word that starts it, so a query's "down"
    reached a junk join beginning "down" and scored the page on nothing.
    """
    found: set[str] = set()
    for part in parts:
        words = _WORD_RE.findall(part.lower())
        found |= {a + b for a, b in pairwise(words)}
    return found


def _stem(token: str) -> str:
    """Return the Porter stem, or the token itself if stemming would empty it."""
    return porter_stem(token) or token


def _query_tokens(query: str) -> list[str]:
    query = re.sub(r"\([^)]*\)", " ", query)
    seen: set[str] = set()
    out: list[str] = []
    for tok in _WORD_RE.findall(query.lower()):
        if len(tok) < MIN_TOKEN or tok in STOP_WORDS or tok in seen:
            continue
        seen.add(tok)
        out.append(tok)
    return out


def _within_one_edit(a: str, b: str) -> bool:
    """Return whether ``a`` and ``b`` differ by at most one insertion or substitution."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = j = 0
    slack = True
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
            j += 1
            continue
        if not slack:
            return False
        slack = False
        if len(a) == len(b):
            i += 1
        j += 1
    return True


def _token_matches(query_token: str, record_token: str, matcher: Matcher = LEXICAL) -> bool:
    if query_token == record_token:
        return True
    if matcher.stem and _stem(query_token) == _stem(record_token):
        # Morphology: sneeze/sneezing and hide/hiding, the two misses that made
        # the strongest case for a stemmer. Prefix matching cannot reach either,
        # because the silent e is dropped before the suffix.
        return True
    short, long_ = sorted((query_token, record_token), key=len)
    if len(short) >= MIN_PREFIX and long_.startswith(short):
        return True
    if not matcher.fuzzy:
        return False
    return len(short) >= MIN_FUZZY and _within_one_edit(query_token, record_token)


def _flatten_parts(value: Any) -> list[str]:  # noqa: ANN401 -- capture values are free-form JSON.
    """Return every string anywhere in a capture field, kept separate.

    ``panels_of_note`` is a list of ``[panel, phrase]`` pairs and ``vision_apply``
    stamps each field with its publication class, so this has to walk both lists
    and the ``{"value": ..., "class": ...}`` wrapper rather than assume a shape.

    The values stay **unjoined** because compound tokens must not straddle two of
    them -- ``objects`` is a list of separate noun phrases, and joining it first
    makes a compound out of the last word of one and the first word of the next.
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return _flatten_parts(value["value"] if "value" in value else list(value.values()))
    if isinstance(value, list):
        return [part for item in value for part in _flatten_parts(item)]
    return [str(value)]


def _flatten(value: Any) -> str:  # noqa: ANN401 -- capture values are free-form JSON.
    """Return every string anywhere in a capture field, space-joined."""
    return " ".join(_flatten_parts(value))


def _readable(part: str) -> str:
    """Return a capture phrase as plain language, for encoding.

    Strips the ``other:`` prefix, which marks a value as outside the closed
    vocabulary and means nothing to a language model, and flattens newlines.
    """
    return " ".join(part.strip().removeprefix(OTHER_PREFIX).split())


def _index_title(
    title_str: str, engine: OcrTypes, matcher: Matcher = LEXICAL
) -> dict[str, dict[str, Any]]:
    """Return the capture and speech token sets for every captured page of a title."""
    title = STR_TITLE_TO_ENUM[title_str]
    speech_groups = SpeechGroups(ComicsDatabase())

    index: dict[str, dict[str, Any]] = {}
    for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True):
        if page_group.ocr_index != engine:
            continue
        page = page_group.fanta_page
        ocr_file = page_group.ocr_prelim_groups_json_file
        capture_file = ocr_file.parent / (page + CAPTURE_FILE_SUFFIX)
        if not capture_file.is_file():
            continue

        capture = json.loads(capture_file.read_text())
        field_parts = {f: _flatten_parts(capture.get(f)) for f in CAPTURE_FIELDS}
        per_field = {f: _tokens(" ".join(parts), matcher) for f, parts in field_parts.items()}
        groups = page_group.speech_page_json.get("groups", {})
        speech_parts = [
            strip_markup(unescape_markup(g.get("ai_text", ""))) for g in groups.values()
        ]
        index[page] = {
            "capture": set().union(*per_field.values()) if per_field else set(),
            "per_field": per_field,
            "speech": _tokens(" ".join(speech_parts), matcher),
            "capture_compounds": (
                _compound_tokens([p for parts in field_parts.values() for p in parts])
                if matcher.compounds
                else set()
            ),
            "speech_compounds": _compound_tokens(speech_parts) if matcher.compounds else set(),
            # Kept as separate phrases for the dense retriever, which scores a
            # page by its best-matching phrase rather than by one page vector.
            # `characters` and `setting` carry an `other:` prefix that is schema
            # bookkeeping rather than language, so it is dropped before encoding.
            "capture_parts": (
                [_readable(p) for parts in field_parts.values() for p in parts if _readable(p)]
                if matcher.semantic
                else []
            ),
            "speech_parts": (
                [p.replace("\n", " ").strip() for p in speech_parts if p.strip()]
                if matcher.semantic
                else []
            ),
        }
    return dict(sorted(index.items()))


def _idf(index: dict[str, dict[str, Any]], layer: str) -> dict[str, float]:
    """Return an inverse-document-frequency weight per token, over this title's pages.

    Counting matched tokens equally is what produced Sheriff's #29: nine pages
    tied at the top score and the cap truncated the tie by page number, dropping
    both correct pages. The tie is an artifact of every token being worth one --
    "character", "panel" and "chase" all score the same on a 32-page western.
    Weighting by rarity separates them, and the longer the title the more it
    matters, which is the direction the corpus is going.
    """
    pages = max(len(index), 1)
    seen: dict[str, int] = {}
    for blobs in index.values():
        for token in blobs[layer]:
            seen[token] = seen.get(token, 0) + 1
    # Smoothed, so a token on every page still counts a little rather than zero.
    return {token: math.log(1.0 + pages / count) for token, count in seen.items()}


def _page_score(
    query_tokens: list[str],
    record: set[str],
    weights: dict[str, float],
    matcher: Matcher,
    compounds: frozenset[str] | set[str] = frozenset(),
) -> float:
    """Score one page: matched query tokens, weighted by rarity under ``idf``.

    A compound is matched by equality only -- never by prefix or edit distance --
    so that indexing "fly paper" as "flypaper" cannot also make every word a
    prefix of some junk join.
    """
    total = 0.0
    for q in query_tokens:
        hits = [r for r in record if _token_matches(q, r, matcher)]
        if q in compounds:
            hits.append(q)
        if not hits:
            continue
        # The rarest record token this query token reached: a query word that
        # lands on a distinctive phrase should count for more than one that
        # lands on a word every page carries.
        total += max(weights.get(r, 1.0) for r in hits) if matcher.idf else 1.0
    return total


_MODEL: Any = None


def _model() -> Any:  # noqa: ANN401 -- SentenceTransformer, imported lazily.
    """Return the sentence-embedding model, loading it once.

    Imported and loaded lazily so ``lexical`` and ``v2`` -- which is the default
    and needs none of this -- pay neither the import nor the several seconds of
    model load.
    """
    global _MODEL  # noqa: PLW0603 -- a process-wide cache for a multi-second load.
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        _MODEL = SentenceTransformer(EMBED_MODEL)
    return _MODEL


def _phrase_ranking(query: str, index: dict[str, dict[str, Any]], layer: str) -> list[str]:
    """Rank pages by their best-matching phrase, semantically.

    A page is scored by the **maximum** similarity over its own phrases, not by
    one vector for the whole page. That matters: ``objects`` holds up to twelve
    unrelated noun phrases and ``beats`` up to three sentences, so a single
    page-level vector would average a fly swatter together with everything else
    and match nothing in particular. The queries are short and specific, so the
    right question is whether *some one thing* on the page matches.
    """
    pages = [p for p, blobs in index.items() if blobs[f"{layer}_parts"]]
    if not pages:
        return []
    model = _model()
    flat: list[str] = []
    owner: list[str] = []
    for page in pages:
        for phrase in index[page][f"{layer}_parts"]:
            flat.append(phrase)
            owner.append(page)

    vectors = model.encode(flat, normalize_embeddings=True, show_progress_bar=False)
    query_vector = model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
    best: dict[str, float] = {}
    for page, vector in zip(owner, vectors, strict=True):
        score = float(vector @ query_vector)
        if score > best.get(page, -1.0):
            best[page] = score

    values = list(best.values())
    if len(values) < MIN_PAGES_FOR_SPREAD:
        return []
    mean = sum(values) / len(values)
    spread = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
    if spread == 0.0:
        return []
    floor = mean + SEMANTIC_SIGMA * spread
    standout = {page: score for page, score in best.items() if score >= floor}
    return [page for page, _score in sorted(standout.items(), key=lambda kv: (-kv[1], kv[0]))]


def _fuse(lexical: list[str], semantic: list[str]) -> list[str]:
    """Fill the band with the lexical ranking, then top it up semantically.

    The dense retriever **backfills; it never displaces**. Reciprocal rank fusion
    was tried first and rejected on evidence: giving both rankers equal say let
    the semantic side push a correct lexical answer out of a full band, which cost
    Big Bin's #43 while buying wins elsewhere. That is the wrong trade, because
    the dense retriever was added to reach queries the lexical one *cannot* --
    re-ranking the ones it already answers is outside the problem it was brought
    in for.

    It also buys a property worth more than the queries it forfeits: under
    backfill a rise in the hit count can only mean the dense retriever found a
    page the lexical one missed. Two earlier rounds of this work produced hit-rate
    rises that turned out to be artifacts of a looser band, and each took a
    per-token trace to expose. This design cannot produce that class of result.
    """
    band = list(lexical[:TOP_BAND])
    for page in semantic:
        if len(band) >= TOP_BAND:
            break
        if page not in band:
            band.append(page)
    return band


def _search(
    query: str, index: dict[str, dict[str, Any]], layer: str, matcher: Matcher = LEXICAL
) -> list[str]:
    query_tokens = _query_tokens(query)
    weights = _idf(index, layer) if matcher.idf else {}
    scored = [
        (score, page)
        for page, blobs in index.items()
        if (
            score := _page_score(
                query_tokens, blobs[layer], weights, matcher, blobs[f"{layer}_compounds"]
            )
        )
        > 0
    ]
    ranked = sorted(scored, key=lambda s: (-s[0], s[1]))
    if matcher.semantic:
        # Fused even when the lexical side is empty: a query whose words appear
        # nowhere is exactly the case the dense retriever exists for. If neither
        # side proposes anything the result is still empty, so "no match" stays
        # expressible.
        return _fuse([page for _score, page in ranked], _phrase_ranking(query, index, layer))
    if not scored:
        return []
    if matcher.ranked_band:
        return [page for _score, page in ranked[:TOP_BAND]]
    best = max(score for score, _page in scored)
    return [page for score, page in ranked if score == best][:TOP_BAND]


def _fields_hit(
    query: str, index: dict[str, dict[str, Any]], page: str, matcher: Matcher = LEXICAL
) -> list[str]:
    query_tokens = _query_tokens(query)
    per_field = index[page]["per_field"]
    return [
        field
        for field in CAPTURE_FIELDS
        if any(any(_token_matches(q, r, matcher) for r in per_field[field]) for q in query_tokens)
    ]


def _score_title(
    title_str: str, index: dict[str, dict[str, Any]], matcher: Matcher = LEXICAL
) -> dict[str, Any]:
    queries = QUERIES[title_str]
    tally = {"hit": 0, "miss": 0, "capture_only": 0, "speech_answerable": 0}
    missed: list[int] = []

    print(
        f'\nRetrieval queries for "{title_str}" -- {len(index)} captured page(s)'
        f"   [matcher: {matcher.name}]\n"
    )
    for num, text, expected in queries:
        capture_pages = _search(text, index, "capture", matcher)
        speech_pages = _search(text, index, "speech", matcher)
        want = expected or []
        hit = any(p in capture_pages for p in want)
        by_speech = any(p in speech_pages for p in want)

        if hit:
            tally["hit"] += 1
            tally["speech_answerable" if by_speech else "capture_only"] += 1
        else:
            tally["miss"] += 1
            missed.append(num)

        print(f"  #{num:<4} {'hit ' if hit else 'MISS'}  {text}")
        print(f"           want {want or '(none committed)'}   capture {capture_pages or '-'}")
        if hit:
            fields = ", ".join(
                _fields_hit(text, index, next(p for p in want if p in capture_pages), matcher)
            )
            suffix = "   (the speech layer answers this too)" if by_speech else ""
            print(f"           via {fields}{suffix}")

    print(
        f"\n  {tally['hit']} hit / {tally['miss']} miss"
        f"   --   {tally['capture_only']} of the hits are capture-only,"
        f" {tally['speech_answerable']} are answerable from speech alone"
    )
    if missed:
        print(f"  missed: {', '.join('#' + str(n) for n in missed)}")
        print("  Split each by hand: is the thing recorded on the page and not retrieved,")
        print("  or not recorded at all?  They argue for opposite fixes.")
    return {**tally, "missed": missed}


@app.command(help="Score the retrieval queries for a title against its page capture.")
def main(
    title: Annotated[
        str,
        typer.Option("--title", "-t", help="The story title to score."),
    ] = TRIAL_1_TITLE,
    engine: Annotated[
        str, typer.Option("--engine", help="Which OCR engine's pages to score.")
    ] = OcrTypes.EASYOCR.value,
    matcher_name: Annotated[
        str,
        typer.Option(
            "--matcher",
            help='Matching rules to score with: "lexical" is the five-title trial\'s.',
        ),
    ] = DEFAULT_MATCHER.name,
    validate: Annotated[
        bool,
        typer.Option(
            "--validate",
            help="Re-score trial 1 and check it still matches the recorded result.",
        ),
    ] = False,
) -> None:
    if matcher_name not in MATCHERS:
        known = ", ".join(f'"{m}"' for m in MATCHERS)
        msg = f'Unknown matcher "{matcher_name}". Known: {known}.'
        raise typer.BadParameter(msg)
    matcher = MATCHERS[matcher_name]

    title_str = TRIAL_1_TITLE if validate else title
    if title_str not in QUERIES:
        known = ", ".join(f'"{t}"' for t in QUERIES)
        msg = f'No query set for "{title_str}". Known: {known}.'
        raise typer.BadParameter(msg)

    index = _index_title(title_str, OcrTypes(engine), matcher)
    if not index:
        msg = f'No "{CAPTURE_FILE_SUFFIX}" files found for "{title_str}"; run vision_apply first.'
        raise typer.BadParameter(msg)

    result = _score_title(title_str, index, matcher)

    if not validate:
        return

    expected = TRIAL_1_RESULTS[matcher.name]
    drift = [
        f"{key}: got {result[key]}, recorded {expected[key]}"
        for key in ("hit", "miss", "missed")
        if result[key] != expected[key]
    ]
    if drift:
        print(f'\nCalibration has DRIFTED for matcher "{matcher.name}":')
        for line in drift:
            print(f"  - {line}")
        print("Any other title's number is no longer comparable with Roscoe's until this is fixed.")
        raise typer.Exit(code=1)
    logger.info(f'Matcher "{matcher.name}" still reproduces its recorded trial-1 result exactly.')


if __name__ == "__main__":
    app()
