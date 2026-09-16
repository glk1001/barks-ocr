# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the candidate list is the whole point of running it.
"""List every nephew whose recorded `cap_colour` disagrees with the roster key.

    uv run --offline python scripts/vision/cap_mismatch.py [--min N] [--all]

WHY THIS EXISTS. `cap_colour` records the ink the colourist actually printed, never
the colour the character's name implies -- that rule is in `roster.txt`, and the
whole reason for it is that the disagreement is the only record the corpus keeps of
a colourist's mistake. This is the query that reads that record back.

**A MISMATCH IS A CANDIDATE, NOT A CONFIRMED ERROR.** Three shapes come out, and
they mean different things:

* **Bijective and repeated** -- boy A wears B's colour and boy B wears A's, several
  times over. That is a colourist error: he swapped two inks and kept going.
* **One-directional** -- Dewey prints green six times and nobody prints blue. More
  likely a naming or reading problem than a colourist one, because a real swap has
  to put the other ink somewhere.
* **A singleton** -- one group in a whole title. Usually a misread, and note that
  `cap_colour` also carries GARMENT colour (a shirt, a parka hood), so a boy named
  off his tail while wearing a red shirt lands here and is nobody's error.

**THE CLINCHER IS SAME-PANEL CO-OCCURRENCE.** If one panel holds boy A in B's
colour AND boy B in A's, the two caps were exchanged in that frame; two independent
misreads do not come out symmetric and repeated. Measured 2026-09-16 over the
corpus: 121 mismatches against 6,621 agreements, and *Donald Duck Tells About
Kites* carries a clean red/blue swap over 23 groups with the exchange visible in
SIX separate panels. *The Mysterious Stone Ray* has nine mismatches and no
same-panel co-occurrence at all, so it is not confirmed by this test.

Zero co-occurrence does not disprove a swap -- the boys may simply never share a
panel -- so it promotes a candidate rather than clearing one.

Read-only. Must be run with `uv run` from the barks-ocr checkout.
"""

import collections
import json
import sys
from pathlib import Path

from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_title_from_volume_page
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from loguru import logger

from barks_ocr.utils.vision_schema import CAP_COLOUR_KEY, SPEAKER_KEY

# The corpus-wide key. Not a per-title convention: a title that disagrees is the
# colourist getting it wrong, which is what this script is for.
STD = {"Huey": "red", "Dewey": "blue", "Louie": "green"}
ENGINE_GLOB = "[0-9][0-9][0-9]-easyocr-gemini-prelim-groups.json"
REVIEWED_KEY = "speaker_reviewed"
PANEL_KEY = "panel_num"
BIJECTIVE_PAIR = 2  # a swap involves exactly two boys


def volume_of(directory: Path) -> int | None:
    """Return the Fantagraphics volume number a prelim directory holds, or None."""
    try:
        return int(directory.name.split("Vol. ")[1].split(" ")[0].rstrip("-"))
    except (IndexError, ValueError):
        return None


def collect(prelim: Path) -> dict[str, list[tuple[str, int, str, str, str, bool]]]:
    """Return the mismatches per title, as (page, panel, group, speaker, cap, reviewed)."""
    database = ComicsDatabase()
    per_title: dict[str, list[tuple[str, int, str, str, str, bool]]] = collections.defaultdict(list)
    agree = 0
    for directory in sorted(p for p in prelim.iterdir() if p.is_dir()):
        volume = volume_of(directory)
        if volume is None:
            continue
        for path in sorted(directory.glob(ENGINE_GLOB)):
            page = path.name[:3]
            try:
                groups = json.loads(path.read_text(encoding="utf-8"))["groups"]
            except (OSError, ValueError, KeyError):
                logger.warning(f"Unreadable: {path}")
                continue
            for group_id, group in groups.items():
                speaker, cap = group.get(SPEAKER_KEY), group.get(CAP_COLOUR_KEY)
                if speaker not in STD or not cap:
                    continue
                if STD[speaker] == cap:
                    agree += 1
                    continue
                try:
                    title = str(get_title_from_volume_page(database, volume, page)[0])
                except Exception:  # noqa: BLE001 -- a page the map cannot place is still a finding
                    title = f"vol {volume}"
                per_title[title].append(
                    (
                        page,
                        group.get(PANEL_KEY, 0),
                        group_id,
                        speaker,
                        cap,
                        bool(group.get(REVIEWED_KEY)),
                    )
                )
    per_title["__agree__"] = [("", 0, "", "", "", False)] * agree
    return per_title


def swap_panels(rows: list[tuple[str, int, str, str, str, bool]]) -> list[tuple[str, int, str]]:
    """Return the panels holding two DIFFERENT mismatched boys -- an exchange in one frame."""
    by_panel: dict[tuple[str, int], list[tuple[str, str]]] = collections.defaultdict(list)
    for page, panel, _, speaker, cap, _ in rows:
        by_panel[(page, panel)].append((speaker, cap))
    out = []
    for (page, panel), pairs in sorted(by_panel.items()):
        if len({s for s, _ in pairs}) >= BIJECTIVE_PAIR:
            out.append((page, panel, ", ".join(f"{s}->{c}" for s, c in pairs)))
    return out


def verdict(rows: list[tuple[str, int, str, str, str, bool]], panels: list) -> str:
    """Classify a title's mismatches as a confirmed swap, a candidate, or a singleton."""
    if panels:
        return f"SWAP CONFIRMED in {len(panels)} panel(s)"
    boys = {s for _, _, _, s, _, _ in rows}
    if len(rows) == 1:
        return "singleton -- probably a misread or a garment colour"
    if len(boys) >= BIJECTIVE_PAIR:
        return "candidate: bijective but never in one panel"
    return "candidate: one-directional -- suspect the NAME, not the colourist"


def main() -> None:
    """Print the mismatch list, worst-evidenced first."""
    min_n = 1
    show_all = "--all" in sys.argv
    if "--min" in sys.argv:
        min_n = int(sys.argv[sys.argv.index("--min") + 1])
    per_title = collect(Path(OCR_PRELIM_DIR))
    agree = len(per_title.pop("__agree__", []))
    total = sum(len(v) for v in per_title.values())
    print(
        f"cap_colour agrees with the roster key on {agree} nephew group(s), disagrees on {total}."
    )
    print(f"{'title':44s} {'n':>3s} {'revd':>5s}  verdict / pattern")
    for title, rows in sorted(per_title.items(), key=lambda kv: -len(kv[1])):
        if len(rows) < min_n:
            continue
        panels = swap_panels(rows)
        pairs = collections.Counter((s, c) for _, _, _, s, c, _ in rows)
        reviewed = sum(1 for r in rows if r[5])
        sig = ", ".join(f"{s}->{c} x{n}" for (s, c), n in pairs.most_common())
        print(f"{title[:44]:44s} {len(rows):3d} {reviewed:5d}  {verdict(rows, panels)}")
        print(f"{'':44s} {'':3s} {'':5s}  {sig}")
        if show_all:
            for page, panel, detail in panels:
                print(f"{'':52s}  {page} p{panel}: {detail}")


if __name__ == "__main__":
    main()
