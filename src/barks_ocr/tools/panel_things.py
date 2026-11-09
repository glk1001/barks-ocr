"""Tag panels with the things they show (car, mountain, barrel, ...) using TypeSafe's Jev.

Each panel is sent once with one yes/no question per thing, all sharing the image, and the
answers go into the panel-tags repo beside the silhouette tags::

    "tags": {"things": {"jev_model": "jev-1.14.0",
                        "jev": {"car": 0.0123, "camera": 0.41, ...},
                        "question": {"car": "v1", "camera": "v2", ...},
                        "box": {"camera": [0.61, 0.20, 0.70, 0.31, 0.88]},
                        "labels": {"car": "yes", "camera": "no"}}}

``question`` holds each thing's wording version. A run asks only the things a panel has
no answer for at their current version, so a new or reworded thing costs one more pass
over the image, and the rest are not re-billed.

Small objects (``camera``, ``jewels``, ``flashlight``) also ask a box question in the same
request, at almost no cost: ``box`` is where Jev puts the object (left, top, right,
bottom as fractions of the panel, then Jev's confidence), drawn on the review page so the
reviewer sees what it meant. A box is returned even when the object is absent.

``labels`` are written only by ``review``, a local browser page (source: a human); a run
never touches them. A panel has a thing when it is labelled ``yes``, or when it is
unlabelled and scores at least the thing's ``sure`` cut-off (source: Jev). Below that,
down to ``floor``, is the thing's review band: panels the review page offers for a human
to settle. Both cut-offs come from GLK's labels of the pilot (Lost in the Andes!, Back
to the Klondike, The Firebug; 626 panels, 2026-11-09): ``sure`` is where at least ~90%
of flagged panels were real, ``floor`` the score under which no (or nearly no) real one
fell. A thing with ``sure`` None has none: it was weak on the pilot (``printed``,
``vase``, ``lighthouse``) and is found only by review. Things the pilot had too few of
to judge (``camera``, ``flashlight``, ``bicycle``, ``train``, ``kite``, ``radio_tv``)
take the score of their 60th-best corpus hit as ``sure``: GLK looked through those top
60 and found them mostly right, and nothing below them has been looked at.
``things-panels.tsv`` at the repo root lists every panel that has a thing.

Wording rules agreed with GLK (2026-11-09): ``animal`` is a real animal drawn as one,
never the clothed, upright, talking cast; ``gun`` is broad (cannons too); ``car`` is any
motor road vehicle; ``printed`` and ``reading`` cover all printed or written matter, not
only books; ``fire`` is any visible flame, a lit match too; ``smoke`` is smoke only, not
steam, dust or cloud; ``flashlight`` is the electric kind, not a flaming torch; ``food``
includes drink; ``jewels`` are gems and jewelry, not gold coins or nuggets.

Dropped after the pilot: ``explosion`` mostly found fire and smoke, which became tags of
their own. ``explosive``, worded broadly or narrowly, answered yes to anything
stick-shaped (canes, staffs, nightsticks). ``smoking`` (cigarette, cigar, pipe; asked
apart first, when Jev confused the three) found no real one in the 56 panels it flagged,
even with a second question on its box cut out and enlarged.
"""

# ruff: noqa: T201

import csv
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import typer
from barks_fantagraphics.comics_database import ComicsDatabase
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg
from loguru import logger

from barks_ocr.cli_setup import get_comic_titles, init_logging
from barks_ocr.tools.panel_tags import (
    SHEETS_SUBDIR,
    GridSection,
    PagePanels,
    checked_pages,
    crop_panel,
    get_panel_tags_root,
    load_rgb,
    load_tags,
    paginate_sections,
    panel_image,
    save_tags,
    segments_size,
    selected_titles,
    write_grid_sheet,
)
from barks_ocr.utils.panel_review import (
    DEFAULT_PORT,
    DEFAULT_REVIEW_LIMIT,
    LABELS,
    ReviewSession,
    run_review,
)
from barks_ocr.utils.typesafe_jev import JevClient, NoulAnswers

APP_LOGGING_NAME = "things"
THINGS = "things"
DEFAULT_WORKERS = 8
THINGS_LIST_FILE = "things-panels.tsv"

_PANEL = "`image` is one panel from a Carl Barks Donald Duck comic. "
_SMALL = " Count it even when it is small or in the background."


@dataclass(frozen=True)
class Thing:
    """How Jev is asked about one thing, and how its answer is read.

    ``version`` changes with any of the wording, which re-asks the thing (and drops its
    old box). ``sure`` and ``floor`` are the cut-offs described in the module docstring.
    ``box`` is set only for small objects.
    """

    version: str
    question: str
    sure: float | None = None
    floor: float = 0.2
    box: str | None = None


THING_QUESTIONS: dict[str, Thing] = {
    "car": Thing(
        "v1",
        _PANEL + "Is there a car, truck or bus: a motor road vehicle (Donald's car counts)? "
        "Not a train, plane, boat, bicycle, wagon or cart." + _SMALL,
        sure=0.6,  # pilot: 10 of 10 real
    ),
    "mountain": Thing(
        "v1",
        _PANEL + "Is there a mountain, a mountain range or a rocky peak, even far in the "
        "background? Not low rolling hills.",
        sure=0.5,  # 79 of 79
        floor=0.3,
    ),
    "vase": Thing(
        "v1",
        _PANEL
        + "Is there a vase, urn or decorative jar? Not a cup, bottle or cooking pot."
        + _SMALL,
    ),
    "printed": Thing(
        "v1",
        _PANEL + "Is there any printed or written matter as an object: a book, newspaper, "
        "magazine, letter, map or document? Not a sign, poster or label." + _SMALL,
        floor=0.3,
    ),
    "reading": Thing(
        "v1",
        _PANEL + "Is a character reading something: a book, newspaper, letter, map or "
        "document? Looking at it attentively counts; only holding it does not.",
        sure=0.8,  # 3 of 3
        floor=0.3,
    ),
    "barrel": Thing(
        "v1", _PANEL + "Is there a barrel, keg or cask?" + _SMALL, sure=0.7, floor=0.4
    ),  # 11 of 12
    "camera": Thing(
        "v2",
        _PANEL + "Is there a camera, still or movie? Not binoculars or a telescope." + _SMALL,
        sure=0.98,  # GLK: its top 60 corpus hits (2026-11-09) looked mostly right
        box="the camera in `image`",
    ),
    "river": Thing(
        "v1",
        _PANEL + "Is there a river, stream or creek, including rapids and waterfalls? Not a "
        "lake, the sea or a puddle.",
        sure=0.7,  # 8 of 10
    ),
    "gun": Thing(
        "v1",
        _PANEL + "Is there a firearm: a pistol, rifle, shotgun or cannon?" + _SMALL,
        sure=0.7,  # 9 of 10
        floor=0.4,
    ),
    "fire": Thing(
        "v1",
        _PANEL + "Is there fire: visible flames of any size, from a blaze or a burning "
        "building to a campfire, a stove, a torch, a candle or a lit match?" + _SMALL,
        sure=0.4,  # 35 of 38
    ),
    "smoke": Thing(
        "v1",
        _PANEL + "Is there smoke: a cloud, plume or puff of smoke from a fire, a chimney or "
        "smokestack, an engine, a gun or a cigar? Not steam, a dust cloud, fog or clouds in "
        "the sky." + _SMALL,
        sure=0.5,  # 45 of 49
        floor=0.4,
    ),
    "insect": Thing(
        "v1",
        _PANEL + "Is there an insect or spider (a bee, fly, ant, mosquito, beetle)? Count "
        "it even when it is tiny or drawn as a cartoon.",
        sure=0.7,  # 4 of 4
    ),
    "animal": Thing(
        "v2",
        _PANEL + "Is there a real, non-human animal behaving as an animal: on all fours, "
        "flying, swimming, perching or pecking, wearing no clothes (a collar is fine) and "
        "not talking? A horse, cow, dog, bear, llama, bird or fish counts, and so does a pet "
        "dog such as Bolivar. Do NOT count any character who stands upright like a person, "
        "wears clothes or talks: the ducks (Donald, Scrooge, the nephews) and the townsfolk, "
        "who have dog, pig or other animal faces but are people. Do not count insects." + _SMALL,
        sure=0.5,  # 35 of 36
    ),
    "jewels": Thing(
        "v1",
        _PANEL + "Is there a gem or a piece of jewelry: a loose precious stone, a "
        "necklace, ring, bracelet, earring, crown, tiara or jewelled ornament? Not gold coins "
        "or gold nuggets." + _SMALL,
        sure=0.7,  # 21 of 21
        floor=0.4,
        box="the gem or jewelry in `image`",
    ),
    "painting": Thing(
        "v1",
        _PANEL + "Is there a painting or framed picture: a portrait or landscape hanging on a "
        "wall or standing on an easel, or someone painting one? Not a poster, a sign or a "
        "window." + _SMALL,
        sure=0.4,  # 8 of 9
        floor=0.3,
    ),
    "radio_tv": Thing(
        "v1",
        _PANEL + "Is there a radio or a television set? Not a telephone." + _SMALL,
        sure=0.99,  # GLK: its top 60 corpus hits (2026-11-09) looked mostly right
    ),
    "suitcase": Thing(
        "v1",
        _PANEL + "Is there a suitcase or other luggage: a valise, carpetbag, travelling trunk "
        "or hatbox? Not a sack, a basket or a backpack." + _SMALL,
        sure=0.8,  # 7 of 7, but only 7 of the 21 real ones
    ),
    "kite": Thing("v1", _PANEL + "Is there a kite, flying or held?" + _SMALL, sure=0.81),
    "boat": Thing(
        "v1",
        _PANEL + "Is there a ship or boat of any size: an ocean liner, steamer, sailing ship, "
        "fishing boat, rowboat, canoe or raft?" + _SMALL,
        sure=0.6,  # 21 of 24
        floor=0.4,
    ),
    "food": Thing(
        "v1",
        _PANEL + "Is there food or drink: a meal, fruit, vegetables, bread, cake, pie, a "
        "sandwich, sweets, or a bottle, cup or glass of drink, whether eaten, cooked, held or "
        "on display?" + _SMALL,
        sure=0.8,  # 45 of 48
        floor=0.3,
    ),
    "flashlight": Thing(
        "v1",
        _PANEL + "Is there a flashlight (an electric hand torch), lit or not? Not a lantern, "
        "a candle or a flaming torch." + _SMALL,
        sure=0.81,  # GLK: its top 60 corpus hits (2026-11-09) looked mostly right
        box="the flashlight in `image`",
    ),
    "lighthouse": Thing("v1", _PANEL + "Is there a lighthouse?" + _SMALL),
    "bicycle": Thing("v1", _PANEL + "Is there a bicycle or tricycle?" + _SMALL, sure=0.94),
    "train": Thing(
        "v1",
        _PANEL + "Is there a railway train: a locomotive, or railway carriages or wagons on "
        "rails? Not a streetcar or a bus." + _SMALL,
        sure=0.91,  # GLK: its top 60 corpus hits (2026-11-09) looked mostly right
    ),
    "airplane": Thing(
        "v1",
        _PANEL + "Is there an airplane: any fixed-wing aircraft, a seaplane too? Not a "
        "blimp, a balloon, a helicopter or a bird." + _SMALL,
        sure=0.7,  # 4 of 4
        floor=0.3,
    ),
}

THUMB_W, THUMB_H, SHEET_COLS = 400, 300, 5
CAPTION = (0.5, 22)
DEFAULT_PER_SHEET = 40
DEFAULT_MIN_SCORE = 0.3
SCORE_BANDS = (0.9, 0.7, 0.5)  # sheet sections: >= 0.9, 0.7-0.9, 0.5-0.7, min-0.5


app = typer.Typer(help="Tag panels with the things they show (Jev) and build per-thing sheets.")


def things_tag(row: dict[str, Any]) -> dict[str, Any]:
    """Return a panel row's things tag, creating it and its maps empty."""
    tag = row["tags"].setdefault(THINGS, {"jev_model": None})
    for key in ("jev", "question"):
        tag.setdefault(key, {})
    return tag


def tidy_things_tag(tag: dict[str, Any]) -> None:
    """Order each map by the questions and drop things no longer asked (and empty maps).

    Also drops ``zoom``, the enlarged-box answers of the dropped ``smoking`` tag.
    """
    tag.pop("zoom", None)
    for key in ("jev", "question", "box", "labels"):
        if key in tag:
            tag[key] = {t: tag[key][t] for t in THING_QUESTIONS if t in tag[key]}
            if not tag[key] and key not in {"jev", "question"}:
                del tag[key]


def thing_score(tag: dict[str, Any], thing: str) -> float | None:
    """Return a thing's score on a panel, or None if not asked at its current wording."""
    if tag.get("question", {}).get(thing) != THING_QUESTIONS[thing].version:
        return None
    return float(tag["jev"][thing])


def due_things(row: dict[str, Any], wanted: list[str], *, force: bool) -> list[str]:
    """Return the wanted things a panel has no answer for at their current wording."""
    asked = row["tags"].get(THINGS, {}).get("question", {})
    return [t for t in wanted if force or asked.get(t) != THING_QUESTIONS[t].version]


class PanelCrops:
    """Panel crops for a run, each page image read once and kept until the run ends."""

    def __init__(self) -> None:
        """Start with no page loaded."""
        self._pages: dict[Path, np.ndarray] = {}

    def preload(self, pages: list[PagePanels]) -> None:
        """Read the page images up front, so worker threads never race to load one."""
        for page in pages:
            if page.image_file not in self._pages:
                self._pages[page.image_file] = load_rgb(page.image_file)

    def crop(self, page: PagePanels, row: dict[str, Any]) -> np.ndarray:
        """Return a panel's crop from its (preloaded) page."""
        size = segments_size(page.segments_file)
        return crop_panel(self._pages[page.image_file], size, row["box"])


Asked = tuple[PagePanels, dict[str, Any], list[str]]


def _ask_panels(todo: list[Asked], crops: PanelCrops, client: JevClient, workers: int) -> int:
    """Ask each panel its due things (with box questions for small objects); return tokens."""

    def ask(item: Asked) -> NoulAnswers:
        page, row, due = item
        questions = {t: THING_QUESTIONS[t].question for t in due}
        boxes = {f"{t}_box": box for t in due if (box := THING_QUESTIONS[t].box)}
        return client.ask_image_questions(crops.crop(page, row), questions, boxes)

    tokens = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for (_, row, due), answer in zip(todo, pool.map(ask, todo), strict=True):
            tag = things_tag(row)
            for thing in due:
                tag["jev"][thing] = round(answer.probabilities[thing], 4)
                tag["question"][thing] = THING_QUESTIONS[thing].version
                tag.get("box", {}).pop(thing, None)
                if (found := answer.boxes.get(f"{thing}_box")) is not None:
                    edges, conf = found
                    tag.setdefault("box", {})[thing] = [*(round(v, 4) for v in edges), conf]
            tag["jev_model"] = answer.model
            tokens += answer.input_tokens
    return tokens


def jev_title(
    pages: list[PagePanels], client: JevClient, wanted: list[str], workers: int, *, force: bool
) -> tuple[int, int]:
    """Ask Jev about the due things of every panel of a title and save the answers.

    Every panel's things tag is tidied too, so a dropped thing leaves even the panels with
    nothing to ask.

    Args:
        pages: The title's pages.
        client: The Jev client.
        wanted: The things to ask about.
        workers: Concurrent requests.
        force: Re-ask things already answered at their current wording.

    Returns:
        (panels asked, input tokens billed).

    """
    loaded = [(page, load_tags(page)) for page in pages]
    todo = [
        (page, row, due)
        for page, rows in loaded
        for row in rows
        if (due := due_things(row, wanted, force=force))
    ]
    crops = PanelCrops()
    crops.preload([page for page, _, _ in todo])
    tokens = _ask_panels(todo, crops, client, workers)
    for page, rows in loaded:
        for row in rows:
            if THINGS in row["tags"]:
                tidy_things_tag(row["tags"][THINGS])
        save_tags(page, rows)
    return len(todo), tokens


@dataclass(frozen=True)
class ThingPanel:
    """One panel's score for one thing, with where to find it."""

    title: str
    volume: int
    page: PagePanels
    row: dict[str, Any]
    thing: str
    score: float

    @property
    def tag(self) -> dict[str, Any]:
        """The panel's things tag."""
        return self.row["tags"][THINGS]

    @property
    def label(self) -> str | None:
        """The panel's reviewed label for the thing, if any."""
        return self.tag.get("labels", {}).get(self.thing)

    @property
    def source(self) -> str | None:
        """Who says the panel has the thing: ``human`` (labelled yes), ``jev`` or None."""
        if self.label is not None:
            return "human" if self.label == "yes" else None
        sure = THING_QUESTIONS[self.thing].sure
        return "jev" if sure is not None and self.score >= sure else None

    @property
    def in_band(self) -> bool:
        """Whether the panel is unlabelled and in the thing's review band."""
        thing = THING_QUESTIONS[self.thing]
        below_sure = thing.sure is None or self.score < thing.sure
        return self.label is None and self.score >= thing.floor and below_sure

    def caption(self) -> str:
        """`v7 027:3 0.93 Lost in the Andes`: volume, fanta page:panel, score, title."""
        index = self.row["index"]
        label = f" [{self.label}]" if self.label else ""
        return (
            f"v{self.volume} {self.page.fanta_page}:{index} {self.score:.2f}{label} "
            f"{self.title[:22]}"
        )

    def image(self, width: int | None = None) -> np.ndarray:
        """Return the panel's crop (box drawn in, for a small object), optionally narrowed."""
        panel = panel_image(self.page, self.row["box"], width)
        box = self.tag.get("box", {}).get(self.thing)
        if box is not None:
            h, w = panel.shape[:2]
            p0, p1 = (round(box[0] * w), round(box[1] * h)), (round(box[2] * w), round(box[3] * h))
            cv2.rectangle(panel, p0, p1, (255, 0, 255), max(2, w // 300))
        return panel


def scan_panels(
    comics_database: ComicsDatabase, titles: list[str], tags_root: Path, things: list[str]
) -> dict[str, list[ThingPanel]]:
    """Return, per thing, every panel of the titles scored for it at its current wording.

    Each tags file is read once; a panel's entries for different things share its row, so
    a label saved through one is seen by the others.
    """
    found: dict[str, list[ThingPanel]] = {t: [] for t in things}
    for title in titles:
        if (pages := checked_pages(comics_database, title, tags_root)) is None:
            continue
        volume = comics_database.get_fanta_volume_int(title)
        for page in pages:
            if not page.tags_file.is_file():
                continue
            for row in load_tags(page):
                tag = row["tags"].get(THINGS, {})
                for thing in things:
                    if (score := thing_score(tag, thing)) is not None:
                        found[thing].append(ThingPanel(title, volume, page, row, thing, score))
    return found


def write_things_list(comics_database: ComicsDatabase, tags_root: Path) -> tuple[Path, int]:
    """Write every panel in the corpus that has a thing to the repo's list file.

    Returns:
        The list file and its number of rows.

    """
    _, titles, _ = selected_titles("", "")
    found = scan_panels(comics_database, titles, tags_root, list(THING_QUESTIONS))
    order = {t: k for k, t in enumerate(THING_QUESTIONS)}
    rows = sorted(
        (p for panels in found.values() for p in panels if p.source),
        key=lambda p: (p.volume, p.page.fanta_page, p.row["index"], order[p.thing]),
    )
    out = tags_root / THINGS_LIST_FILE
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(
            ["volume", "fanta_page", "panel", "title", "story_page", "thing", "score", "source"]
        )
        for p in rows:
            writer.writerow(
                [
                    p.volume,
                    p.page.fanta_page,
                    p.row["index"],
                    p.title,
                    p.page.story_page,
                    p.thing,
                    f"{p.score:.2f}",
                    p.source,
                ]
            )
    return out, len(rows)


def scored_panels(
    comics_database: ComicsDatabase, titles: list[str], tags_root: Path, thing: str
) -> list[ThingPanel]:
    """Return every panel of the titles scored for a thing at its current wording."""
    return scan_panels(comics_database, titles, tags_root, [thing])[thing]


def write_thing_sheets(
    panels: list[ThingPanel], thing: str, out_dir: Path, min_score: float, per_sheet: int
) -> int:
    """Write a thing's panels scoring at least min_score as numbered sheets, best first.

    Returns:
        The number of sheets written; the folder's earlier sheets are replaced.

    """
    ranked = sorted((p for p in panels if p.score >= min_score), key=lambda p: -p.score)
    bounds = [*(b for b in SCORE_BANDS if b > min_score), min_score]
    sections: list[GridSection] = []
    upper = None
    for lower in bounds:
        band = [p for p in ranked if p.score >= lower and (upper is None or p.score < upper)]
        label = f">= {lower}" if upper is None else f"{lower} - {upper}"
        sections.append((f"{thing.upper()} {label} ({len(band)})", [_item(p) for p in band]))
        upper = lower
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("sheet-*.png"):
        old.unlink()
    if not ranked:
        return 0
    sheets = paginate_sections(sections, per_sheet)
    for n, sheet in enumerate(sheets, start=1):
        write_grid_sheet(
            f"{thing}: {len(ranked)} of {len(panels)} panels score >= {min_score} -- sheet {n} "
            f"of {len(sheets)}",
            sheet,
            (THUMB_W, THUMB_H, SHEET_COLS),
            out_dir / f"sheet-{n:02d}.png",
            caption=CAPTION,
        )
    return len(sheets)


def _item(panel: ThingPanel) -> tuple[Callable[[], np.ndarray], str]:
    return panel.image, panel.caption()


def save_labels(panels: list[ThingPanel], labels: dict[int, str | None]) -> dict[str, int]:
    """Write review labels (by position in ``panels``) into the tags files.

    A None label clears the panel's label. Each file is re-read before writing, so a
    page whose panels were saved earlier in the same review keeps those labels.

    Returns:
        How many panels got each label (``cleared`` for None).

    """
    by_file: dict[Path, list[tuple[ThingPanel, str | None]]] = {}
    for k, label in labels.items():
        by_file.setdefault(panels[k].page.tags_file, []).append((panels[k], label))
    counts = dict.fromkeys((*LABELS, "cleared"), 0)
    for items in by_file.values():
        page = items[0][0].page
        rows = load_tags(page)
        for panel, label in items:
            row = rows[panel.row["index"] - 1]
            tag = things_tag(row)
            if label is None:
                tag.get("labels", {}).pop(panel.thing, None)
            else:
                tag.setdefault("labels", {})[panel.thing] = label
            tidy_things_tag(tag)
            panel.tag["labels"] = dict(tag.get("labels", {}))
            counts[label or "cleared"] += 1
        save_tags(page, rows)
    return counts


class ThingsSession(ReviewSession[ThingPanel]):
    """The panels a things review page offers, per thing, best first."""

    def __init__(self, found: dict[str, list[ThingPanel]], *, everything: bool, limit: int) -> None:
        """Keep each thing's review band (or, with everything, all from its floor up).

        Args:
            found: Each thing's scored panels.
            everything: Also offer labelled panels and confident yeses, to look again.
            limit: At most this many panels a thing, the best scores first.

        """
        offered: dict[str, list[ThingPanel]] = {}
        for thing, panels in found.items():
            floor = THING_QUESTIONS[thing].floor
            kept = [
                p for p in panels if p.in_band or (everything and (p.label or p.score >= floor))
            ]
            if kept:
                offered[thing] = sorted(kept, key=lambda p: -p.score)[:limit]
        super().__init__(offered)

    def panels_data(self, thing: str) -> dict[str, Any]:
        """Return what the page shows for a thing: the question, cut-off and each panel.

        The cut-off is the thing's ``sure`` (1 if it has none): unlabelled panels at or
        above it start as yes, the rest as no.
        """
        sure = THING_QUESTIONS[thing].sure
        return {
            "thing": thing,
            "question": THING_QUESTIONS[thing].question,
            "cutoff": 1.0 if sure is None else sure,
            "panels": [
                {
                    "caption": p.caption(),
                    "score": round(p.score, 4),
                    "scores": f"jev {p.tag['jev'][thing]:.2f}",
                    "label": p.label,
                }
                for p in self.panels[thing]
            ],
        }

    def write_labels(
        self, panels: list[ThingPanel], labels: dict[int, str | None]
    ) -> dict[str, int]:
        """Write labels into the panels' tags files."""
        return save_labels(panels, labels)


def why_nothing(thing: str, panels: list[ThingPanel]) -> str:
    """Say why a thing offers no panel to review: how its panels split, labelled or not."""
    if not panels:
        return f"{thing}: no panels scored."
    spec = THING_QUESTIONS[thing]
    labelled = sum(p.label is not None for p in panels)
    sure = sum(p.label is None and p.source == "jev" for p in panels)
    below = sum(p.label is None and p.score < spec.floor for p in panels)
    parts = [f"{labelled} labelled", f"{below} below the floor ({spec.floor})"]
    if spec.sure is not None:
        parts.append(f"{sure} confident yes (>= {spec.sure})")
    return f"{thing}: {len(panels)} panels -- " + ", ".join(parts) + "."


def parse_things(text: str) -> list[str]:
    """Parse a comma list of things (empty means all), in the questions' order.

    Raises:
        typer.BadParameter: On a thing with no question.

    """
    names = [t.strip() for t in text.split(",") if t.strip()]
    unknown = [t for t in names if t not in THING_QUESTIONS]
    if unknown:
        msg = f"Unknown thing(s) {', '.join(unknown)}; known: {', '.join(THING_QUESTIONS)}."
        raise typer.BadParameter(msg)
    return [t for t in THING_QUESTIONS if not names or t in names]


ThingsOpt = typer.Option("", "--thing", help="Comma list of things (default: all).")


@app.command(help="Ask Jev (TypeSafe API, billed) which things each panel shows.")
def jev(  # noqa: PLR0913 -- a typer command: one parameter per CLI option.
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    things_str: str = ThingsOpt,
    workers: int = typer.Option(DEFAULT_WORKERS, "--workers", help="Concurrent requests."),
    force: bool = typer.Option(default=False, help="Re-ask things already answered."),
    log_level_str: LogLevelArg = "INFO",
) -> None:
    """Score each title's panels for the things, asking only what is missing."""
    init_logging(APP_LOGGING_NAME, "panel-things.log", log_level_str)
    if not volumes_str and not title_str:
        msg = "Give --volume or --title: a corpus run is billed and must be asked for."
        raise typer.BadParameter(msg)
    wanted = parse_things(things_str)
    comics_database, titles = get_comic_titles(volumes_str, title_str, exclude_non_comics=True)
    tags_root = get_panel_tags_root(comics_database)
    client = JevClient()
    total_panels = total_tokens = 0
    for title in titles:
        if (pages := checked_pages(comics_database, title, tags_root)) is None:
            continue
        n, tokens = jev_title(pages, client, wanted, workers, force=force)
        total_panels += n
        total_tokens += tokens
        logger.info(f'"{title}": {n} panels, {tokens} input tokens.')
        print(f"{title}: {n} panels, {tokens} input tokens")
    print(f"Total: {total_panels} panels, {total_tokens} input tokens.")
    out, n = write_things_list(comics_database, tags_root)
    print(f"{n} panel things in the corpus -> {out}")


@app.command(help="Build each thing's sheets: its panels ranked by score.")
def sheet(  # noqa: PLR0913 -- a typer command: one parameter per CLI option.
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    things_str: str = ThingsOpt,
    min_score: float = typer.Option(DEFAULT_MIN_SCORE, "--min-score", help="Lowest score shown."),
    per_sheet: int = typer.Option(DEFAULT_PER_SHEET, "--per-sheet", help="Panels a sheet."),
    log_level_str: LogLevelArg = "INFO",
) -> None:
    """Rebuild the sheets for the selected titles (default: every panel scored so far)."""
    init_logging(APP_LOGGING_NAME, "panel-things.log", log_level_str)
    wanted = parse_things(things_str)
    comics_database, titles, scope = selected_titles(volumes_str, title_str)
    tags_root = get_panel_tags_root(comics_database)
    print(f"{'thing':<10} {'panels':>7} {'>=0.5':>6} {'>=0.7':>6} {'>=0.9':>6}  sheets")
    for thing in wanted:
        panels = scored_panels(comics_database, titles, tags_root, thing)
        out_dir = tags_root / SHEETS_SUBDIR / THINGS / thing / scope
        n = write_thing_sheets(panels, thing, out_dir, min_score, per_sheet)
        counts = [sum(p.score >= c for p in panels) for c in (0.5, 0.7, 0.9)]
        cols = " ".join(f"{c:>6}" for c in counts)
        print(f"{thing:<10} {len(panels):>7} {cols}  {n} -> {out_dir}")


@app.command(help="Review things' panels in a local browser page; Save writes labels.")
def review(  # noqa: PLR0913 -- a typer command: one parameter per CLI option.
    things_str: str = ThingsOpt,
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    everything: bool = typer.Option(
        default=False, help="Also show labelled panels and confident yeses, not only the band."
    ),
    limit: int = typer.Option(DEFAULT_REVIEW_LIMIT, "--limit", help="Most panels a thing."),
    port: int = typer.Option(DEFAULT_PORT, "--port", help="Local port."),
    log_level_str: LogLevelArg = "INFO",
) -> None:
    """Serve the review page on localhost until Ctrl-C, then rewrite the corpus list."""
    init_logging(APP_LOGGING_NAME, "panel-things.log", log_level_str)
    wanted = parse_things(things_str)
    comics_database, titles, scope = selected_titles(volumes_str, title_str)
    tags_root = get_panel_tags_root(comics_database)
    found = scan_panels(comics_database, titles, tags_root, wanted)
    session = ThingsSession(found, everything=everything, limit=limit)
    if not session.panels:
        print(f"Nothing to review in {scope if title_str else scope.lower()}:")
        for thing in wanted:
            print(f"  {why_nothing(thing, found[thing])}")
        if not everything:
            print("Add --everything to see labelled panels and confident yeses as well.")
        raise typer.Exit(code=1)

    def write_list() -> None:
        out, n = write_things_list(comics_database, tags_root)
        print(f"{n} panel things in the corpus -> {out}")

    run_review(session, port, write_list)


@app.command(name="list", help="Rewrite the corpus list of panels that have a thing.")
def list_things(log_level_str: LogLevelArg = "INFO") -> None:
    """Rewrite ``things-panels.tsv`` from the tags as they stand."""
    init_logging(APP_LOGGING_NAME, "panel-things.log", log_level_str)
    comics_database = ComicsDatabase()
    out, n = write_things_list(comics_database, get_panel_tags_root(comics_database))
    print(f"{n} panel things in the corpus -> {out}")


if __name__ == "__main__":
    app()
