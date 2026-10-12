# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and
# printing the report is the whole point of running it.
"""Audit finished volumes: every page read, reviewed and transcribed faithfully.

    uv run --offline python scripts/vision/volume_audit.py VOLUMES [-o QUEUE] [--details N]
        [--padding]

    uv run --offline python scripts/vision/volume_audit.py 12 -o ~/barks-vision/audit-12.txt
    uv run --offline python scripts/vision/volume_audit.py 1-24,30

The per-title close-out (``scripts/closeout.sh --stage review``) runs most of these
checks when a title closes, but a volume keeps changing after that -- adds, merges,
re-sorts, corpus sweeps -- and running the close-out per title spawns a process per
check, which over a volume of titles takes hours. This runs every check once, in one
process, over whole volumes, and READS ONLY: it writes nothing but the queue file.

It prints one row per check per volume and a verdict per volume, then up to
``--details`` findings per check, and with ``-o`` writes every finding as a kivy-editor
queue (``volume page engine group kind``). A finding about a page rather than a group
is parked on the page's first group, as the missed-text queues are.

SILENCING A WARN THAT IS RIGHT. Rare words go in ``rare-word-allow.txt`` and near
misses in ``missed-text-ignore.txt``. The glyph and self-named checks have no word to
list, so they are dismissed on the group instead, with the editor's Mark OK popup
(``glyphs-are-right``, ``speaker-names-self``), which their queue lines pre-tick. On a
seed volume, mark easyocr and let ``seed sync --write`` carry it; elsewhere mark both.

THE TWO KINDS OF CHECK.

A **FAIL** check measures completeness: a volume with any count there is not
finished. A **WARN** check is a heuristic, and its count is a list to read, not a
defect total -- every one of them flags some correct lettering. Which is which was
ruled 2026-10-12:

FAIL
  unread pages         a page with groups but no ``vision_note`` on any of them: the
                       vision pass never ran there. Counts one-pagers, which
                       ``vision-status`` deliberately skips (``one_pager_todo.py``).
  corrections          a text or type correction still outstanding (``vision-corrections``).
  unreviewed speakers  a speaker never ticked reviewed, per engine.
  engine speakers      the engines disagree on a field ``vision-mirror`` carries, or a
                       read group has no partner on the other engine.
  missed text          lettering in the page capture that no group covers, not on
                       ``missed-text-ignore.txt``.
  seed copy            a seed page whose paddleocr copy differs from its easyocr source.
  structure            ``ocr_check``'s structural faults: a malformed box, an invalid
                       type or markup, empty text, groups out of order, a bad panel_num.

WARN
  near-missed text     capture lettering a group nearly matches -- usually the capture
                       off by a letter, sometimes a truncated group.
  engine text diff     text one engine has and the other has nothing like.
  end logo             a story whose last page has no ``the End`` group. One-pagers are
                       skipped: a gag page rarely carries the logo, and 18 of Vol. 12's
                       27 hits were one-pagers.
  census               an off-roster speaker, or one written in a non-canonical form.
  layout               ``ocr_check``'s other issues: fit, line packing, box size, panel
                       overhang, cross-engine boxes and attributes, the dismissable checks.
  padding              (``--padding`` only) ``box_too_tight``/``box_too_loose`` against
                       the ink. Reads every page image: about a minute a volume.
  split word           a rare word that only makes sense joined to its neighbour --
                       a word broken across a line that lost its hyphen, or gained a space.
  near typo            a rare word one edit from a common word the corpus uses
                       elsewhere -- ``HORNING`` for MORNING, but also faithful dialect,
                       ``HISSELF``. Add the faithful ones to ``rare-word-allow.txt``.
  glyphs               a digit inside a word, lowercase in all-capitals lettering, a
                       ``|``, unbalanced brackets, a doubled small word (``THE THE``).
                       Mark OK as ``glyphs-are-right`` when it is what is printed.
  self-named speaker   a roster speaker whose own name is in their line -- the
                       cheapest sign of a swapped pair, though Barks's characters do
                       announce themselves. Mark OK as ``speaker-names-self``.
  speaker/type         dialogue or thought with no speaker, ``none`` or ``narrator``;
                       narration spoken by anyone but the narrator; a sound effect,
                       sign or title given to the narrator. Read pages only.

THE RARE-WORD CHECKS count words over the WHOLE corpus, not the volume asked for, so
a word is rare only if Barks rarely uses it. Dictionary: enchant ``en_US`` and
``en_GB`` plus ``src/barks_ocr/resources/batch-ocr-barks-words.txt`` and
``scripts/vision/rare-word-allow.txt``. Sound effects, signs and titles are skipped,
and so are dialect ``-IN'`` endings whose ``-ING`` form is a word and runs of three
repeated letters (a growl). Measured 2026-10-12 over the corpus: 92 split-word
candidates and 457 near typos, mixed real misreads and faithful dialect.

Assumes the barks-ocr repo as the working directory, so the barks path dependencies
and the sibling scripts in ``scripts/vision`` import. The prelim directory is
``OCR_PRELIM_DIR``; ``BARKS_OCR_PRELIM_DIR`` moves it.
"""

import argparse
import copy
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import audit_missed_text as missed
import enchant
import engine_diff
import numpy as np
import seed_copy_check
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM, Titles
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_title_from_volume_page, get_titles
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from barks_fantagraphics.panel_boxes import TitlePanelBoxes
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups, SpeechPageGroup
from barks_fantagraphics.speech_markup import strip_markup
from comic_utils.pil_image_utils import load_pil_image_for_reading
from intspan import intspan
from loguru import logger
from spellchecker import SpellChecker

from barks_ocr.tools.ocr_check import (
    LineHeightLimits,
    OcrChecker,
    _page_median_line_height,
)
from barks_ocr.tools.vision_corrections import _text_correction, _type_correction
from barks_ocr.tools.vision_mirror import (
    _build_index,
    _copy_fields,
    _distance,
    _is_annotated,
    _match_key,
)
from barks_ocr.utils.box_padding import judge_padding, page_image_file
from barks_ocr.utils.group_checks import GLYPHS_OK_ISSUE, SELF_NAMED_OK_ISSUE, is_acknowledged
from barks_ocr.utils.story_cast import story_characters
from barks_ocr.utils.vision_schema import (
    OTHER_PREFIX,
    ROSTER,
    SPEAKER_KEY,
    SPEAKER_REVIEWED_KEY,
    VISION_NOTE_KEY,
    normalize_speaker,
)

GROUPS_SUFFIX = "-gemini-prelim-groups.json"
EASY, PADDLE = OcrTypes.EASYOCR.value, OcrTypes.PADDLEOCR.value
SEED_MARKER = "copied_from_engine"
ALLOW_FILE = Path(__file__).with_name("rare-word-allow.txt")
BARKS_WORDS = Path(__file__).parents[2] / "src/barks_ocr/resources/batch-ocr-barks-words.txt"

FAIL, WARN = "FAIL", "WARN"
# (key, label, gate), in report order.
CHECKS: tuple[tuple[str, str, str], ...] = (
    ("unread", "unread pages", FAIL),
    ("corrections", "corrections", FAIL),
    ("unreviewed", "unreviewed speakers", FAIL),
    ("engine_speakers", "engine speakers", FAIL),
    ("missed", "missed text", FAIL),
    ("seed_copy", "seed copy", FAIL),
    ("structure", "structure", FAIL),
    ("near_missed", "near-missed text", WARN),
    ("engine_text", "engine text diff", WARN),
    ("end_logo", "end logo", WARN),
    ("census", "census", WARN),
    ("layout", "layout", WARN),
    ("padding", "padding", WARN),
    ("split_word", "split word", WARN),
    ("near_typo", "near typo", WARN),
    ("glyphs", "glyphs", WARN),
    ("self_named", "self-named speaker", WARN),
    ("speaker_type", "speaker/type", WARN),
)
GATE = {key: gate for key, _, gate in CHECKS}

# ocr_check issue types that mean the stored data is malformed rather than doubtful.
STRUCTURAL_ISSUES = frozenset(
    {
        "bad_text_box",
        "invalid_markup",
        "invalid_type",
        "empty_text",
        "groups_out_of_order",
        "panel_unassigned",
        "panel_num_fixable",
        "panel_num_out_of_range",
        "panel_num_mismatch",
    }
)
PADDING_ISSUES = frozenset({"box_too_tight", "box_too_tight_deep", "box_too_loose"})

BALLOON_TYPES = frozenset({"dialogue", "thought", "narration"})
SPOKEN_TYPES = frozenset({"dialogue", "thought"})
STYLIZED_TYPES = frozenset({"sound_effect", "background", "title"})
NARRATOR, NO_SPEAKER = "narrator", "none"

# The names a roster speaker could be addressed by in their own line.
SELF_NAMES: dict[str, tuple[str, ...]] = {
    "Donald": ("DONALD",),
    "Scrooge": ("SCROOGE", "MCDUCK"),
    "Huey": ("HUEY",),
    "Dewey": ("DEWEY",),
    "Louie": ("LOUIE",),
    "Daisy": ("DAISY",),
    "Gladstone": ("GLADSTONE",),
    "Gyro": ("GYRO", "GEARLOOSE"),
}

WORD = re.compile(r"[A-Za-z][A-Za-z']*[A-Za-z]|[A-Za-z]")
ENTITY = re.compile(r"&[a-z]+;")
TRIPLE_LETTER = re.compile(r"(.)\1\1")
RARE_MAX_COUNT = 2  # a word used this many times or fewer across the corpus is rare
TYPO_MIN_ENGLISH_FREQ = (
    50_000  # the spellchecker package's frequency of the word it is one edit from...
)
TYPO_MIN_CORPUS_COUNT = 3  # ...which the corpus must also use this often
CAPITALS_SHARE = 0.9  # a group this upper-case is all-capitals lettering
DIGIT_IN_WORD = re.compile(r"\b(?=[A-Z0-9']*[A-Z])(?=[A-Z0-9']*[0-9])[A-Z0-9']+\b")
ORDINAL_OR_CODE = re.compile(r"^\d+(ST|ND|RD|TH|S|'S)$|^[A-Z]-?\d+$|^\d+[A-Z]$")
LOWER_WORD = re.compile(r"\b\w*[a-z]\w*\b")
MC_NAME = re.compile(r"^Mc[A-Z]")
DOUBLED = re.compile(r"\b([A-Z]+)\s+\1\b")
FUNCTION_WORDS = frozenset(
    [
        "THE",
        "A",
        "AN",
        "TO",
        "OF",
        "AND",
        "IS",
        "IN",
        "IT",
        "I",
        "YOU",
        "WE",
        "HE",
        "SHE",
        "THEY",
        "THAT",
        "THIS",
        "FOR",
        "ON",
        "AT",
        "BE",
        "WITH",
        "MY",
        "YOUR",
        "ARE",
        "WAS",
    ]
)


@dataclass(frozen=True)
class Finding:
    """One thing the audit found, and where."""

    check: str
    volume: int
    page: str
    engine: str | None  # None: the finding is about both engines, or neither
    group_id: str | None  # None: the finding is about the page, not a group
    detail: str


@dataclass
class Page:
    """One page of one volume, both engines' groups files as stored."""

    volume: int
    page: str
    title: str
    engines: dict[str, dict] = field(default_factory=dict)  # engine -> page JSON

    def groups(self, engine: str) -> dict[str, dict]:
        """Return one engine's groups, or an empty dict when it has none."""
        return self.engines.get(engine, {}).get("groups", {})

    def first_group(self) -> str | None:
        """Return the lowest group id on the page, to park a page-level finding on."""
        ids = {int(g) for e in self.engines for g in self.groups(e)}
        return str(min(ids)) if ids else None

    def is_read(self) -> bool:
        """Return whether the vision pass ran here: ``vision_status``'s own definition."""
        return any(VISION_NOTE_KEY in g for g in self.groups(EASY).values())


def _plain(group: dict) -> str:
    return ENTITY.sub(" ", strip_markup(group.get("ai_text") or ""))


# ── Loading ───────────────────────────────────────────────────────────────────


def _volume_dir(volume: int) -> Path | None:
    hits = sorted(OCR_PRELIM_DIR.glob(f"Carl Barks Vol. {volume} - *"))
    return hits[0] if hits else None


def load_pages(comics_database: ComicsDatabase, volume: int) -> list[Page]:
    """Load every groups file in the volume's prelim directory, keyed by page.

    The volume's own files rather than its titles' page maps, so one-pagers are
    included and no page is counted under two titles.
    """
    vol_dir = _volume_dir(volume)
    if vol_dir is None:
        return []
    pages: dict[str, Page] = {}
    for path in sorted(vol_dir.glob(f"*{GROUPS_SUFFIX}")):
        page, engine = path.name[:3], path.name.split("-")[1]
        if page not in pages:
            title, _ = get_title_from_volume_page(comics_database, volume, page)
            pages[page] = Page(volume, page, title or "")
        pages[page].engines[engine] = json.loads(path.read_text())
    return [pages[p] for p in sorted(pages)]


# ── Page-level checks ─────────────────────────────────────────────────────────


def check_unread(page: Page) -> list[Finding]:
    """Return the page as a finding when it has groups but the pass never ran there."""
    if not page.groups(EASY) or page.is_read():
        return []
    n = len(page.groups(EASY))
    return [Finding("unread", page.volume, page.page, None, page.first_group(), f"{n} groups")]


def check_corrections(page: Page) -> list[Finding]:
    """Return every outstanding text or type correction, per engine."""
    out = []
    for engine in page.engines:
        for gid, group in page.groups(engine).items():
            if (text := _text_correction(group)) is not None:
                out.append(
                    Finding(
                        "corrections", page.volume, page.page, engine, gid, f"text: {text[1]!r}"
                    )
                )
            if (kind := _type_correction(group)) is not None:
                out.append(
                    Finding(
                        "corrections",
                        page.volume,
                        page.page,
                        engine,
                        gid,
                        f"type: {kind[0]} -> {kind[1]}",
                    )
                )
    return out


def check_unreviewed(page: Page) -> list[Finding]:
    """Return every speaker not ticked reviewed, per engine (``speaker-queue --unreviewed``)."""
    return [
        Finding("unreviewed", page.volume, page.page, engine, gid, group[SPEAKER_KEY])
        for engine in page.engines
        for gid, group in page.groups(engine).items()
        if group.get(SPEAKER_KEY) and not group.get(SPEAKER_REVIEWED_KEY)
    ]


def check_engine_speakers(page: Page) -> list[Finding]:
    """Return each read group the mirror would still change, or could not pair.

    The ``vision_mirror.mirror_page`` pairing, run on a copy of paddleocr so
    nothing stored is touched: a pair whose mirrored fields differ is a finding,
    and so is a read group with no partner.
    """
    src, dst = page.groups(EASY), copy.deepcopy(page.groups(PADDLE))
    if not src or not dst or page.engines.get(PADDLE, {}).get(SEED_MARKER):
        return []  # a seed page's copy is check_seed_copy's to judge
    index, used, out = _build_index(dst), set(), []
    for gid, group in sorted(src.items(), key=lambda kv: int(kv[0])):
        if not _is_annotated(group):
            continue
        candidates = [
            (i, g) for i, g in index.get(_match_key(group.get("ai_text")), []) if i not in used
        ]
        if not candidates:
            out.append(
                Finding(
                    "engine_speakers", page.volume, page.page, EASY, gid, "no paddleocr partner"
                )
            )
            continue
        dst_gid, partner = min(
            candidates, key=lambda c: _distance(group.get("text_box"), c[1].get("text_box"))
        )
        used.add(dst_gid)
        if _copy_fields(group, partner):
            out.append(
                Finding(
                    "engine_speakers",
                    page.volume,
                    page.page,
                    PADDLE,
                    dst_gid,
                    f"differs from easyocr g{gid}",
                )
            )
    return out


def check_seed_copy(page: Page) -> list[Finding]:
    """Return each group on a seed page where the paddleocr copy differs from easyocr."""
    copy_json = page.engines.get(PADDLE, {})
    if not copy_json.get(SEED_MARKER) or EASY not in page.engines:
        return []
    _, _, details = seed_copy_check._compare_page(page.page, page.engines[EASY], copy_json)  # noqa: SLF001
    out = []
    for line in details:
        m = re.match(r"\s*\S+ g(\d+): (.*)", line)
        gid = m.group(1) if m else page.first_group()
        out.append(
            Finding(
                "seed_copy",
                page.volume,
                page.page,
                PADDLE,
                gid,
                (m.group(2) if m else line).strip(),
            )
        )
    return out


def check_engine_text(page: Page) -> list[Finding]:
    """Return text one engine holds that the other has nothing like (``engine_diff``)."""
    if len(page.engines) != 2:  # noqa: PLR2004
        return [
            Finding(
                "engine_text", page.volume, page.page, None, page.first_group(), "only one engine"
            )
        ]
    texts = {
        e: {engine_diff.normalize(g.get("ai_text")): gid for gid, g in page.groups(e).items()}
        for e in (EASY, PADDLE)
    }
    out = []
    for engine, other in ((EASY, PADDLE), (PADDLE, EASY)):
        others = set(texts[other]) - {""}
        for text, gid in texts[engine].items():
            if text and not engine_diff.covered(text, others):
                out.append(Finding("engine_text", page.volume, page.page, engine, gid, text[:50]))
    return out


def check_speaker_type(page: Page) -> list[Finding]:
    """Return groups whose speaker does not suit their type, on read pages only."""
    if not page.is_read():
        return []
    out = []
    for engine in page.engines:
        for gid, group in page.groups(engine).items():
            kind, speaker = group.get("type"), group.get(SPEAKER_KEY) or ""
            bad = (
                (kind in SPOKEN_TYPES and speaker in ("", NO_SPEAKER, NARRATOR))
                or (kind == "narration" and speaker != NARRATOR)
                or (kind in STYLIZED_TYPES and speaker == NARRATOR)
            )
            if bad:
                out.append(
                    Finding(
                        "speaker_type",
                        page.volume,
                        page.page,
                        engine,
                        gid,
                        f"{kind} by {speaker or '(no speaker)'}",
                    )
                )
    return out


def check_self_named(page: Page) -> list[Finding]:
    """Return groups whose roster speaker is named in their own line."""
    out = []
    for engine in page.engines:
        for gid, group in page.groups(engine).items():
            if is_acknowledged(group, SELF_NAMED_OK_ISSUE):
                continue
            names = SELF_NAMES.get(group.get(SPEAKER_KEY) or "")
            text = _plain(group).upper()
            if names and any(re.search(rf"\b{n}\b", text) for n in names):
                out.append(
                    Finding(
                        "self_named",
                        page.volume,
                        page.page,
                        engine,
                        gid,
                        f"{group[SPEAKER_KEY]}: {text[:50]!r}",
                    )
                )
    return out


def check_glyphs(page: Page) -> list[Finding]:
    """Return groups with an implausible glyph sequence, on easyocr and paddleocr alike."""
    out = []
    for engine in page.engines:
        for gid, group in page.groups(engine).items():
            if is_acknowledged(group, GLYPHS_OK_ISSUE):
                continue
            raw = _plain(group)
            letters = [c for c in raw if c.isalpha()]
            capitals = (
                letters and sum(c.isupper() for c in letters) / len(letters) >= CAPITALS_SHARE
            )
            why = []
            if capitals:
                why += [
                    f"digit in {t}"
                    for t in DIGIT_IN_WORD.findall(raw)
                    if not ORDINAL_OR_CODE.match(t)
                ]
                why += [f"lowercase {w}" for w in LOWER_WORD.findall(raw) if not MC_NAME.match(w)]
            if "|" in raw:
                why.append("a |")
            if raw.count("(") != raw.count(")"):
                why.append("unbalanced brackets")
            why += [
                f"doubled {m.group(0)!r}"
                for m in DOUBLED.finditer(raw)
                if m.group(1) in FUNCTION_WORDS
            ]
            if why:
                out.append(
                    Finding("glyphs", page.volume, page.page, engine, gid, "; ".join(why)[:80])
                )
    return out


# ── Rare words ────────────────────────────────────────────────────────────────


class RareWords:
    """The corpus's word counts and dictionary, for the split-word and near-typo checks."""

    def __init__(self) -> None:
        self._us = enchant.DictWithPWL("en_US", str(BARKS_WORDS))
        self._gb = enchant.Dict("en_GB")
        self._allow = self._load_allow()
        self._english = SpellChecker(distance=1)
        self.counts: Counter[str] = Counter()
        for path in OCR_PRELIM_DIR.glob(f"*/*-{EASY}{GROUPS_SUFFIX}"):
            for group in json.loads(path.read_text()).get("groups", {}).values():
                self.counts.update(w for w in self.words(group) if w)

    @staticmethod
    def _load_allow() -> set[str]:
        if not ALLOW_FILE.is_file():
            return set()
        lines = (line.split("#", 1)[0].strip() for line in ALLOW_FILE.read_text().splitlines())
        return {line.upper() for line in lines if line}

    @staticmethod
    def words(group: dict) -> list[str]:
        """Return the group's words, upper-cased, apostrophes trimmed at the ends."""
        return [w.strip("'").upper() for w in WORD.findall(_plain(group))]

    def known(self, word: str) -> bool:
        """Return whether the word is English, British English, or allowed."""
        if word in self._allow:
            return True
        return any(
            d.check(x)
            for d in (self._us, self._gb)
            for x in (word, word.lower(), word.capitalize())
        )

    def rare_unknown(self, word: str) -> bool:
        """Return whether the word is rare in the corpus and in no dictionary."""
        if not word or self.counts[word] > RARE_MAX_COUNT or TRIPLE_LETTER.search(word):
            return False
        if word.endswith("IN") and self.known(word + "G"):
            return False  # dialect: an -IN' ending
        return not self.known(word)

    def typo_for(self, word: str) -> str | None:
        """Return the common word this one is a single edit from, if the corpus uses it too."""
        lower = word.lower().replace("'", "")
        found = [
            w
            for w in self._english.edit_distance_1(lower)
            if w in self._english.word_frequency.dictionary
        ]
        if not found:
            return None
        best = max(found, key=lambda w: self._english.word_frequency[w])
        if self._english.word_frequency[best] < TYPO_MIN_ENGLISH_FREQ:
            return None
        return best.upper() if self.counts[best.upper()] >= TYPO_MIN_CORPUS_COUNT else None

    def check(self, page: Page) -> list[Finding]:
        """Return the page's split-word and near-typo findings."""
        out = []
        for engine in page.engines:
            for gid, group in page.groups(engine).items():
                if group.get("type") not in BALLOON_TYPES:
                    continue
                words = self.words(group)
                for i, word in enumerate(words):
                    if not self.rare_unknown(word):
                        continue
                    before = words[i - 1] if i else ""
                    after = words[i + 1] if i + 1 < len(words) else ""
                    if (before and self.known(before + word)) or (
                        after and self.known(word + after)
                    ):
                        joined = (
                            before + word if before and self.known(before + word) else word + after
                        )
                        out.append(
                            Finding(
                                "split_word",
                                page.volume,
                                page.page,
                                engine,
                                gid,
                                f"{word} -> {joined}",
                            )
                        )
                    elif (typo := self.typo_for(word)) is not None:
                        out.append(
                            Finding(
                                "near_typo",
                                page.volume,
                                page.page,
                                engine,
                                gid,
                                f"{word} -> {typo}?",
                            )
                        )
        return out


# ── Title-level checks ────────────────────────────────────────────────────────


def _title_pages(pages: list[Page]) -> dict[str, list[Page]]:
    by_title: dict[str, list[Page]] = defaultdict(list)
    for page in pages:
        if page.title:
            by_title[page.title].append(page)
    return by_title


def check_missed(
    comics_database: ComicsDatabase, speech_groups: SpeechGroups, title: str, pages: list[Page]
) -> list[Finding]:
    """Return the missed-text audit's findings for one title, minus the ignore list."""
    own = {p.page: p for p in pages}
    findings, near, _, _ = missed.audit_title(comics_database, speech_groups, title)
    ignores = missed.load_ignores()
    out = []
    for finding in findings:
        _, volume, page, item, _, engines = finding
        if page not in own or missed.ignored(ignores, finding):
            continue
        who = "neither engine" if not engines else "only " + ", ".join(e.value for e in engines)
        out.append(
            Finding("missed", volume, page, None, own[page].first_group(), f"{item[:50]!r} ({who})")
        )
    for near_miss in near:
        _, volume, page, item, close = near_miss
        if page in own and not missed.ignored(ignores, near_miss):
            out.append(
                Finding(
                    "near_missed",
                    volume,
                    page,
                    None,
                    own[page].first_group(),
                    f"{item[:40]!r} ~ {close[:30]!r}",
                )
            )
    return out


def check_end_logo(title: str, pages: list[Page]) -> list[Finding]:
    """Return the title's last page when it carries no ``the End`` group."""
    if len(pages) < 2:  # noqa: PLR2004 -- a one-pager
        return []
    last = max(pages, key=lambda p: p.page)
    texts = {
        " ".join((g.get("ai_text") or "").split()).lower()
        for e in last.engines
        for g in last.groups(e).values()
    }
    if "the end" in texts:
        return []
    return [
        Finding(
            "end_logo", last.volume, last.page, None, last.first_group(), f"{title}: no 'the End'"
        )
    ]


def check_census(title: str, pages: list[Page]) -> list[Finding]:
    """Return speakers off the roster and story cast, or written non-canonically."""
    cast = frozenset(story_characters(STR_TITLE_TO_ENUM[title]))
    out = []
    for page in pages:
        for engine in page.engines:
            for gid, group in page.groups(engine).items():
                speaker = group.get(SPEAKER_KEY)
                if not speaker:
                    continue
                if (
                    speaker not in ROSTER
                    and not speaker.startswith(OTHER_PREFIX)
                    and speaker not in cast
                ):
                    out.append(
                        Finding(
                            "census",
                            page.volume,
                            page.page,
                            engine,
                            gid,
                            f"off the roster: {speaker}",
                        )
                    )
                elif (canonical := normalize_speaker(speaker, cast)) != speaker:
                    out.append(
                        Finding(
                            "census",
                            page.volume,
                            page.page,
                            engine,
                            gid,
                            f"{speaker!r} -> {canonical!r}",
                        )
                    )
    return out


class OcrChecks:
    """``ocr_check``'s issues for a title, without its printing or queue file."""

    def __init__(self, comics_database: ComicsDatabase, *, padding: bool) -> None:
        self._checker = OcrChecker(
            comics_database, line_height_limits=LineHeightLimits(), check_padding=False
        )
        self._speech_groups = SpeechGroups(comics_database)
        self._panel_boxes = TitlePanelBoxes(comics_database)
        self._comics_database = comics_database
        self._padding = padding

    def check(self, title: str, own_pages: set[str]) -> list[Finding]:
        """Return the title's issues on its own pages, structural and layout apart."""
        enum = STR_TITLE_TO_ENUM[title]
        pages: dict[str, dict[OcrTypes, SpeechPageGroup]] = defaultdict(dict)
        for page_group in self._speech_groups.get_speech_page_groups(enum, skip_missing=True):
            if page_group.fanta_page in own_pages:
                pages[page_group.fanta_page][page_group.ocr_index] = page_group
        if not pages:
            return []
        panel_boxes = self._panel_boxes.get_page_panel_boxes(enum)
        issues, _, _, _ = self._checker._check_title_to_convergence(title, pages, panel_boxes)  # noqa: SLF001
        out = []
        for issue in issues:
            check = "structure" if issue.issue_type in STRUCTURAL_ISSUES else "layout"
            # ocr_check appends its own reason after the group's notes, so the tail is
            # the part that says what is wrong.
            tail = issue.notes[-70:] if issue.notes else ""
            note = f"{issue.issue_type}" + (f": ...{tail}" if tail else "")
            out.append(
                Finding(check, issue.volume, issue.fanta_page, issue.engine, issue.group_id, note)
            )
        if self._padding:
            out += self._padding_findings(enum, pages)
        return out

    def _padding_findings(
        self, enum: Titles, pages: dict[str, dict[OcrTypes, SpeechPageGroup]]
    ) -> list[Finding]:
        out = []
        for fanta_page, variants in sorted(pages.items()):
            any_group = next(iter(variants.values()))
            try:
                image = page_image_file(
                    self._comics_database, enum, any_group.fanta_vol, fanta_page
                )
                gray = np.asarray(load_pil_image_for_reading(image).convert("L"))
            except (OSError, ValueError, KeyError, IndexError) as e:
                logger.warning(f"Vol {any_group.fanta_vol} page {fanta_page}: no page image ({e}).")
                continue
            for engine, page_group in variants.items():
                groups = page_group.speech_page_json.get("groups", {})
                line_height = _page_median_line_height(groups)
                for gid, group in groups.items():
                    verdict = judge_padding(gray, group, line_height)
                    if verdict is not None and verdict.issue_type in (
                        "box_too_tight",
                        "box_too_loose",
                    ):
                        out.append(
                            Finding(
                                "padding",
                                page_group.fanta_vol,
                                fanta_page,
                                engine.value,
                                gid,
                                f"{verdict.issue_type}: {verdict.note}",
                            )
                        )
        return out


# ── Running and reporting ─────────────────────────────────────────────────────


PAGE_CHECKS = (
    check_unread,
    check_corrections,
    check_unreviewed,
    check_engine_speakers,
    check_seed_copy,
    check_engine_text,
    check_speaker_type,
    check_self_named,
    check_glyphs,
)


def audit_volume(
    comics_database: ComicsDatabase,
    speech_groups: SpeechGroups,
    ocr: OcrChecks,
    rare: RareWords,
    volume: int,
) -> list[Finding]:
    """Run every check over one volume and return the findings."""
    pages = load_pages(comics_database, volume)
    findings: list[Finding] = []
    for page in pages:
        for check in PAGE_CHECKS:
            findings += check(page)
        findings += rare.check(page)

    by_title = _title_pages(pages)
    configured = set(get_titles(comics_database, [volume], "", exclude_non_comics=True))
    for title in sorted(set(by_title) | (configured & set(by_title))):
        title_pages = by_title[title]
        own = {p.page for p in title_pages}
        try:
            findings += check_missed(comics_database, speech_groups, title, title_pages)
            findings += check_census(title, title_pages)
            findings += check_end_logo(title, title_pages)
            findings += ocr.check(title, own)
        except (RuntimeError, FileNotFoundError, KeyError) as e:
            logger.error(f'Vol {volume} "{title}": a title-level check could not run ({e}).')
            findings.append(
                Finding(
                    "structure",
                    volume,
                    title_pages[0].page,
                    None,
                    title_pages[0].first_group(),
                    f"{title}: check failed: {e}",
                )
            )
    return sorted(
        set(findings),
        key=lambda f: (f.volume, f.page, int(f.group_id or -1), f.engine or "", f.check),
    )


def print_report(
    volumes: list[int], findings: list[Finding], details: int, *, padding: bool
) -> None:
    """Print the per-check, per-volume table, the verdicts, and some detail per check."""
    counts: Counter[tuple[str, int]] = Counter((f.check, f.volume) for f in findings)
    width = max(len(label) for _, label, _ in CHECKS)
    print(f"{'check':<{width}}  gate  " + "".join(f"{f'Vol. {v}':>9}" for v in volumes))
    for key, label, gate in CHECKS:
        if key == "padding" and not padding:
            continue
        print(f"{label:<{width}}  {gate}  " + "".join(f"{counts[key, v]:>9}" for v in volumes))
    print()
    for volume in volumes:
        failing = [label for key, label, gate in CHECKS if gate == FAIL and counts[key, volume]]
        verdict = "FAIL -- " + ", ".join(failing) if failing else "PASS"
        print(f"Vol. {volume}: {verdict}")
    if details <= 0:
        return
    for key, label, gate in CHECKS:
        rows = [f for f in findings if f.check == key]
        if not rows:
            continue
        print(f"\n{label} ({gate}, {len(rows)}):")
        for f in rows[:details]:
            where = (
                f"Vol. {f.volume} {f.page}"
                + (f" {f.engine}" if f.engine else "")
                + (f" g{f.group_id}" if f.group_id else "")
            )
            print(f"  {where}: {f.detail}")
        if len(rows) > details:
            print(f"  ... and {len(rows) - details} more")


# Checks a reviewer can Mark OK on the group in the kivy editor. Their queue lines
# carry the acknowledgement's own name as the kind, so the editor's Mark OK popup
# opens with it pre-ticked; every other check's kind is `audit-<check>`.
ACKNOWLEDGE_AS = {"self_named": SELF_NAMED_OK_ISSUE, "glyphs": GLYPHS_OK_ISSUE}


def write_queue(findings: list[Finding], dest: Path) -> int:
    """Write every finding with a group as a kivy-editor queue line; return the line count."""
    lines = set()
    for f in findings:
        if f.group_id is None:
            continue
        for engine in [f.engine] if f.engine else [EASY, PADDLE]:
            kind = ACKNOWLEDGE_AS.get(f.check, f"audit-{f.check}")
            lines.add((f.volume, f.page, int(f.group_id), engine, kind))
    ordered = sorted(lines, key=lambda r: (r[0], r[1], r[2], r[3]))
    with dest.open("w") as queue:
        queue.write(f"# volume_audit: {len(ordered)} entries\n")
        for volume, page, gid, engine, kind in ordered:
            queue.write(f"{volume} {page} {engine} {gid} {kind}\n")
    return len(ordered)


def main() -> None:
    """Audit the volumes named on the command line."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("volumes", help="volumes, as intspan: 12 or 1-24,30")
    parser.add_argument("-o", "--output", type=Path, help="write every finding to this queue file")
    parser.add_argument(
        "--details", type=int, default=10, help="findings shown per check (0: none)"
    )
    parser.add_argument(
        "--padding", action="store_true", help="also judge balloon boxes against the ink"
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(lambda m: print(m, end=""), level="ERROR")
    volumes = list(intspan(args.volumes))
    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    ocr = OcrChecks(comics_database, padding=args.padding)
    rare = RareWords()

    findings: list[Finding] = []
    for volume in volumes:
        findings += audit_volume(comics_database, speech_groups, ocr, rare, volume)
    print_report(volumes, findings, args.details, padding=args.padding)
    if args.output:
        print(f"\nqueue: {write_queue(findings, args.output)} entries -> {args.output}")


if __name__ == "__main__":
    main()
