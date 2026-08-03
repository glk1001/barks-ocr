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

Matching is deliberately lexical and nothing more -- no stemmer, no embeddings:

* parentheticals are dropped, so "a fly (the insect)" searches for "a fly";
* function words are dropped, and so are one-character tokens, since the ``s``
  that falls out of every possessive would otherwise match everything;
* a query token matches a record token when they are equal, when one is a prefix
  of the other and the shorter is at least 4 characters ("alley" / "alleyway"),
  or when they are within one edit and at least 6 characters, which is what
  carries the query set's own typo in #91 ("dumbells" / "dumbbells");
* a page scores the number of *distinct* query tokens it matches, and the result
  is the highest-scoring band, capped at ``TOP_BAND``.

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
import re
from typing import Annotated, Any

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from barks_fantagraphics.speech_markup import strip_markup, unescape_markup
from loguru import logger

from barks_ocr.utils.vision_schema import (
    BEATS_KEY,
    CHARACTERS_KEY,
    OBJECTS_KEY,
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
TRIAL_1_RESULT: dict[str, object] = {"hit": 15, "miss": 1, "missed": [93]}


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


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


def _token_matches(query_token: str, record_token: str) -> bool:
    if query_token == record_token:
        return True
    short, long_ = sorted((query_token, record_token), key=len)
    if len(short) >= MIN_PREFIX and long_.startswith(short):
        return True
    return len(short) >= MIN_FUZZY and _within_one_edit(query_token, record_token)


def _flatten(value: Any) -> str:  # noqa: ANN401 -- capture values are free-form JSON.
    """Return every string anywhere in a capture field, space-joined.

    ``panels_of_note`` is a list of ``[panel, phrase]`` pairs and ``vision_apply``
    stamps each field with its publication class, so this has to walk both lists
    and the ``{"value": ..., "class": ...}`` wrapper rather than assume a shape.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return _flatten(value["value"] if "value" in value else list(value.values()))
    if isinstance(value, list):
        return " ".join(_flatten(item) for item in value)
    return str(value)


def _index_title(title_str: str, engine: OcrTypes) -> dict[str, dict[str, Any]]:
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
        per_field = {f: _tokens(_flatten(capture.get(f))) for f in CAPTURE_FIELDS}
        groups = page_group.speech_page_json.get("groups", {})
        speech = _tokens(
            " ".join(strip_markup(unescape_markup(g.get("ai_text", ""))) for g in groups.values())
        )
        index[page] = {
            "capture": set().union(*per_field.values()) if per_field else set(),
            "per_field": per_field,
            "speech": speech,
        }
    return dict(sorted(index.items()))


def _search(query: str, index: dict[str, dict[str, Any]], layer: str) -> list[str]:
    query_tokens = _query_tokens(query)
    scored: list[tuple[int, str]] = []
    for page, blobs in index.items():
        matched = sum(any(_token_matches(q, r) for r in blobs[layer]) for q in query_tokens)
        if matched:
            scored.append((matched, page))
    if not scored:
        return []
    best = max(score for score, _page in scored)
    return [page for score, page in sorted(scored, key=lambda s: (-s[0], s[1])) if score == best][
        :TOP_BAND
    ]


def _fields_hit(query: str, index: dict[str, dict[str, Any]], page: str) -> list[str]:
    query_tokens = _query_tokens(query)
    per_field = index[page]["per_field"]
    return [
        field
        for field in CAPTURE_FIELDS
        if any(any(_token_matches(q, r) for r in per_field[field]) for q in query_tokens)
    ]


def _score_title(title_str: str, index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    queries = QUERIES[title_str]
    tally = {"hit": 0, "miss": 0, "capture_only": 0, "speech_answerable": 0}
    missed: list[int] = []

    print(f'\nRetrieval queries for "{title_str}" -- {len(index)} captured page(s)\n')
    for num, text, expected in queries:
        capture_pages = _search(text, index, "capture")
        speech_pages = _search(text, index, "speech")
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
                _fields_hit(text, index, next(p for p in want if p in capture_pages))
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
    validate: Annotated[
        bool,
        typer.Option(
            "--validate",
            help="Re-score trial 1 and check it still matches the recorded result.",
        ),
    ] = False,
) -> None:
    title_str = TRIAL_1_TITLE if validate else title
    if title_str not in QUERIES:
        known = ", ".join(f'"{t}"' for t in QUERIES)
        msg = f'No query set for "{title_str}". Known: {known}.'
        raise typer.BadParameter(msg)

    index = _index_title(title_str, OcrTypes(engine))
    if not index:
        msg = f'No "{CAPTURE_FILE_SUFFIX}" files found for "{title_str}"; run vision_apply first.'
        raise typer.BadParameter(msg)

    result = _score_title(title_str, index)

    if not validate:
        return

    drift = [
        f"{key}: got {result[key]}, trial 1 recorded {TRIAL_1_RESULT[key]}"
        for key in ("hit", "miss", "missed")
        if result[key] != TRIAL_1_RESULT[key]
    ]
    if drift:
        print("\nCalibration has DRIFTED from the recorded trial-1 result:")
        for line in drift:
            print(f"  - {line}")
        print("Any other title's number is no longer comparable with Roscoe's until this is fixed.")
        raise typer.Exit(code=1)
    logger.info("Scorer still reproduces the recorded trial-1 result exactly.")


if __name__ == "__main__":
    app()
