# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and
# printing the candidate markup is the whole point of running it.
"""Turn an `allbold.py` run into candidate `emphasis_markup` for every group.

    VISION_OUT_DIR=<out-dir> uv run --offline python scripts/vision/allbold.py > raw.txt
    uv run --offline python scripts/vision/emphasis_candidates.py raw.txt <out-dir>

WHY THIS EXISTS. `allbold.py` is the measurement; this is the transcription.
On a twenty-page title it reports a few hundred per-word ratios, and turning
those into `emphasis_markup` strings by hand is where a pass both loses hours
and makes mistakes -- the run that prompted this file produced 157 markup
strings across two titles from one command, every one of which round-tripped
against the stored `ai_text`.

Marks `[b]` on words whose stroke-width ratio is at least THRESH, and drops two
classes of false hit `allbold` explicitly warns about: the first word of a
caption, which is the drop capital, and a blob sitting on the group's box edge,
which is the balloon outline rather than lettering.

WHAT IT ASSUMES, AND WHERE IT IS WRONG.

  * `allbold` reports PANEL x, while `groups.json`'s `text_box` is PAGE x. The
    edge filter therefore reads the panel-space boxes out of `<out-dir>/boxes.txt`,
    which `panel_boxes.py` writes. Without that file the edge filter is skipped
    and balloon outlines come back as emphasis.
  * A line `allbold` flagged `!` had a blob count that disagreed with the word
    count, so the word-to-ratio pairing on it is a guess. Those are NOT marked;
    they are printed under `??` for hand review against a crop or a montage.
  * The substitution marks the FIRST occurrence of each bold word in the group.
    Where the same word appears twice and only the later one is heavy -- `YES!
    THEY HAD COURAGE! ... YOU HAD BETTER GO HOME!` -- it tags the wrong one.
    Read the output before using it.

THIS IS A CANDIDATE, NOT AN ANSWER. Every string still has to round-trip
against the stored `ai_text` before it goes into a `result.json`; `vision_apply`
refuses the run if it does not, which is the backstop rather than the check.
"""

import json
import pathlib
import re
import sys

THRESH = 1.30  # stroke-width ratio at or above which allbold calls a word heavy
MIN_BLOB_PX = 30  # narrower than this is a stroke of the balloon, not a word
EDGE_PX = 6  # a blob this close to the box edge is the balloon outline

raw, outdir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
PUNCT = '!?,.;:"—'

groups = {}
cur = None
for line in raw.read_text().splitlines():
    m = re.match(r"^--- (\d+) g(\d+) p(\d+) (?:base=([\d.]+)|(\S+))", line)
    if m:
        cur = (m.group(1), m.group(2))
        groups[cur] = []
        continue
    m = re.match(r"^\s+L(\d+)([=!])\s+\[(.*?)\]\s+(.*)$", line.rstrip("\n"))
    if m and cur:
        ratios = [
            (float(a), int(b), int(c))
            for a, b, c in re.findall(r"([\d.]+)@(-?\d+)-(-?\d+)", m.group(3))
        ]
        groups[cur].append((m.group(2), ratios, m.group(4)))

PANEL_BOXES = {}
_pg = None
for _l in (outdir / "boxes.txt").read_text().splitlines():
    if _l.startswith("== "):
        _pg = _l.split()[1]
    else:
        _m = re.match(r"\s+g(\d+) p\d+ \[\d+x\d+\] x(-?\d+)-(-?\d+)", _l)
        if _m and _pg:
            PANEL_BOXES[(_pg, _m.group(1))] = (int(_m.group(2)), int(_m.group(3)))

out: dict[str, tuple[str, list[tuple[str, float, int, int]]]] = {}
for (page, gid), lines in groups.items():
    gj = json.loads((outdir / page / "groups.json").read_text())
    if gid not in gj:
        continue
    text = gj[gid]["ai_text"]
    box = PANEL_BOXES.get((page, gid))
    is_caption = gj[gid]["type"] in ("narration", "title")
    bold, unsure = set(), []
    for li, (kind, ratios, shown) in enumerate(lines):
        words = shown.split()
        for wi, (r, x0, x1) in enumerate(ratios):
            if r < THRESH:
                continue
            edge = box is not None and (x1 <= box[0] + EDGE_PX or x0 >= box[1] - EDGE_PX)
            if x1 - x0 < MIN_BLOB_PX or edge:
                continue  # balloon outline, not lettering
            if li == 0 and wi == 0 and is_caption:
                continue  # drop capital
            if kind == "!" or wi >= len(words):
                unsure.append((shown, round(r, 2), x0, x1))
                continue
            bold.add(words[wi].strip(PUNCT))
    if not bold and not unsure:
        continue
    marked = text
    for w in sorted(bold, key=len, reverse=True):
        if not w:
            continue
        marked = re.sub(rf"(?<!\[b\])\b{re.escape(w)}\b(?!\[/b\])", f"[b]{w}[/b]", marked, count=1)
    out[f"{page} g{gid}"] = (marked, unsure)

for key in sorted(out, key=lambda s: (s.split()[0], int(s.split()[1][1:]))):
    marked_text, unsure_lines = out[key]
    print(f"== {key}")
    print("   " + marked_text.replace("\n", " / "))
    if unsure_lines:
        print("   ?? " + "; ".join(f"{s!r} {r}@{a}-{b}" for s, r, a, b in unsure_lines))
