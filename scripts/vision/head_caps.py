# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and
# printing the per-head census is the whole point of running it.
"""Attribute a `title_heads` census's cap ink to the heads it actually sits on.

    uv run --offline python scripts/vision/title_heads.py <out-dir> 300 6 > census6.txt
    uv run --offline python scripts/vision/head_caps.py census6.txt [PAGE ...]

WHY THIS EXISTS. `title_heads.py` prints every head and every blob on one line,
and on a cap-dense title that line runs to several thousand characters -- the
run that prompted this file had single lines carrying eighty blobs, of which two
were caps. Reading it is how a real cap gets missed, and how a background blob
gets read as one.

For each panel this prints ONE LINE PER HEAD, carrying only the blobs that could
belong to that head: roster inks (`#e5`/`#e6` red, `#00a4`/`#00a5` blue,
`#009d`/`#009e` green) whose x-centre falls inside the head's span. Each is
tagged `ON-HEAD` when its y-centre sits on the white skull or in the 90px above
it -- where a cap is -- and `off` otherwise, which is the "a blob must sit on a
head" check made explicit.

WHAT IT ASSUMES, AND WHERE IT IS WRONG.

  * The ROSTER filter is a hue shortlist, so an ink outside it is silently
    dropped. That is exactly the *Lovelorn Fireman* failure: Louie's cap there
    prints `#4ba43f` and does not appear in this report at all. When a title
    shows no green anywhere, run `capwide.py` before believing it.
  * A head span wider than 500px is a whole-panel blob rather than a head, and
    is printed as `(panel-wide, skipped)` rather than being given ink.
  * `ON-HEAD` is a geometry test, not an identification. An adult's hat band
    passes it exactly as a nephew's cap does, and in Vol. 22 they print the same
    `#00a4d5`. AREA is the discriminator there, and only at the extremes.
"""

import pathlib
import re
import sys

BLOB = re.compile(r"(red|green|blue)\((\d+),(\d+),(\d+),(\d+)\) a=(\d+) (#[0-9a-f]{6})")
ROSTER = re.compile(r"#(e[56]1[0-9a-f]|00a[45]d|009[de]4)")

MAX_HEAD_PX = 500  # wider than this is a whole-panel blob, not a head
CAP_ABOVE_PX = 90  # a cap sits on the skull or this far above it

census, pages = pathlib.Path(sys.argv[1]), set(sys.argv[2:])
panel = None
for line in census.read_text().splitlines():
    m = re.match(r"^(\d+) (panel-\d+) \((\d+), (\d+)\)", line)
    if m:
        panel = (m.group(1), m.group(2), m.group(3), m.group(4))
        if not pages or m.group(1) in pages:
            print(f"\n{m.group(1)} {m.group(2)} {m.group(3)}x{m.group(4)}")
        continue
    if not panel or (pages and panel[0] not in pages):
        continue
    hm = re.search(r"head\+beak x=\((\d+)\.\.(\d+)\) white=\((\d+),(\d+),(\d+),(\d+)\)", line)
    if not hm:
        continue
    x0, x1 = int(hm.group(1)), int(hm.group(2))
    wy0, wy1 = int(hm.group(4)), int(hm.group(6))
    if x1 - x0 > MAX_HEAD_PX:  # a whole-panel blob, not a head
        print(f"   head x={x0}-{x1} (panel-wide, skipped)")
        continue
    hits = []
    for b in BLOB.finditer(line):
        col, bx0, by0, bx1, by1, a, hex_value = b.groups()
        if not ROSTER.match(hex_value):
            continue
        cx = (int(bx0) + int(bx1)) // 2
        if not (x0 - 20 <= cx <= x1 + 20):
            continue
        cy = (int(by0) + int(by1)) // 2
        # A cap sits ON or just ABOVE the white skull, never far below it.
        where = "ON-HEAD" if wy0 - CAP_ABOVE_PX <= cy <= wy1 else "off"
        hits.append(f"{col} {a}px y{by0}-{by1} {hex_value} [{where}]")
    print(
        f"   head x={x0}-{x1} skull y={wy0}-{wy1}: "
        + ("; ".join(hits) if hits else "-- no roster ink on this head")
    )
