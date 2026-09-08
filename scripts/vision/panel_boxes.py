# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the boxes is the whole point.
"""Print every group's text box in PANEL coordinates, page by page.

    uv run --offline python scripts/vision/dump_boxes.py "<title>" <out-dir>/boxes-<slug>.json
    uv run --offline python scripts/vision/panel_boxes.py <out-dir> [PAGE ...]

WHY THIS EXISTS. `groups.json` gives `text_box` in FULL-PAGE coordinates, and every
census tool -- `capscan`, `capwide`, `probe`, `heads` -- reports PANEL pixels. So
asking "which balloon sits over which head" means converting by hand, panel origin
by panel origin, which is the same two-coordinate-space trap `pcrop.py` exists for
on the cropping side and which is silent when it goes wrong.

This does the sum once. Each line carries the group id, its panel and that panel's
size, the box already converted, the stored type and the head of the text -- which
is enough to pair balloons with figures, and to spot a balloon whose box spans two
of them, without opening an image at all.

IT PLACES BALLOONS, IT DOES NOT NAME SPEAKERS. A box sitting over a boy is not a
tail landing on him; the roster is explicit that reading order and position are not
evidence. Use this to decide which panel to crop, then trace the tail.

Needs `boxes-<slug>.json` in the out-dir, so run `dump_boxes.py` first.
"""

import json
import sys
from pathlib import Path

TEXT_HEAD = 46  # characters of ai_text to show


def _panel_origin(page_boxes: dict[str, dict[str, int]], panel: str, pad: int) -> tuple[int, int]:
    """Return the full-page (x, y) that panel-NN.png's top-left corner sits at.

    `dump_boxes.py` records the panel's own rectangle; the cropped PNG carries
    `pad` extra pixels on every side, so the origin is the rectangle less the pad.

    Args:
        page_boxes: one page's entry from the boxes JSON, keyed by panel number.
        panel: the panel number, as a string key.
        pad: the padding `dump_boxes.py` added around each panel.

    Returns:
        The (x, y) offset to subtract from a full-page coordinate.

    """
    box = page_boxes[panel]
    return box["x0"] - pad, box["y0"] - pad


def dump(out_dir: Path, pages: list[str] | None = None) -> None:
    """Print each group's panel-local box for the pages asked for, or for all of them.

    Args:
        out_dir: a prepped vision out-dir holding one directory per page.
        pages: page names to print; None prints every page in the out-dir.

    """
    try:
        boxes_file = next(out_dir.glob("boxes-*.json"))
    except StopIteration:
        print(f"panel_boxes: no boxes-*.json in {out_dir} -- run dump_boxes.py first")
        raise SystemExit(2) from None

    boxes = json.loads(boxes_file.read_text())
    pad = boxes["pad"]
    wanted = pages or sorted(boxes["pages"])

    for page in wanted:
        page_boxes = boxes["pages"][page]
        groups = json.loads((out_dir / page / "groups.json").read_text())
        print(f"== {page}")
        for gid, group in groups.items():
            panel = str(group["panel_num"])
            off_x, off_y = _panel_origin(page_boxes, panel, pad)
            xs = [corner[0] - off_x for corner in group["text_box"]]
            ys = [corner[1] - off_y for corner in group["text_box"]]
            size = f"{page_boxes[panel]['w'] + 2 * pad}x{page_boxes[panel]['h'] + 2 * pad}"
            text = group["ai_text"][:TEXT_HEAD].replace("\n", " / ")
            print(
                f"  g{gid} p{panel} [{size}] x{min(xs)}-{max(xs)} y{min(ys)}-{max(ys)} "
                f"{group['type'][:4]} {text!r}"
            )


def main() -> None:
    """Dump the out-dir named on the command line, for the pages named after it."""
    if len(sys.argv) < 2:  # noqa: PLR2004 -- script, argv shape is the usage line
        print(__doc__)
        raise SystemExit(2)
    out_dir = Path(sys.argv[1])
    if not out_dir.is_dir():
        print(f"panel_boxes: {out_dir} is not a directory")
        raise SystemExit(2)
    dump(out_dir, sys.argv[2:] or None)


if __name__ == "__main__":
    main()
