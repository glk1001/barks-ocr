# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# each mismatch is the whole point of running it.
"""Check that every `emphasis_markup` in an out-dir strips back to the stored text.

    uv run --offline python scripts/vision/emcheck.py <out-dir> [PAGE ...]

`vision_apply` validates this too, but only once the whole title has been
read: the round trip is checked against the **stored** `ai_text`, so a single
space written differently -- `AGE—` for the stored `AGE —`, `OFFICE!...` for
`OFFICE! ...` -- fails the apply after every page is written. Running this
after each page turns that into a two-second check. It caught three such
mismatches in the forty-third batch.

The comparison is deliberately the same one the apply makes: strip `[b]` and
`[i]` tags, undo the `&bl;` / `&br;` / `&amp;` escapes, and require equality
with `groups.json`'s `ai_text` -- not a whitespace-collapsed
form of it, which would hide exactly the errors this exists to find.

Assumes the out-dir laid out by `vision-prep`: one directory per page, each
holding `groups.json` and (once read) `result.json`. Pages with no
`result.json` yet are skipped, so it is safe to run mid-title.
"""

import json
import re
import sys
from pathlib import Path

TAGS = re.compile(r"\[/?[bi]\]")
ARGV_WITH_OUT_DIR = 2


def strip_markup(markup: str) -> str:
    """Return `markup` with emphasis tags removed and text escapes undone.

    Args:
        markup: The `emphasis_markup` value as written in a `result.json`.

    Returns:
        The plain text the markup should reduce to, for comparison against
        the group's stored `ai_text`.

    """
    stripped = TAGS.sub("", markup)
    return stripped.replace("&bl;", "[").replace("&br;", "]").replace("&amp;", "&")


def check_page(page_dir: Path) -> int:
    """Report every emphasis round-trip mismatch on one page.

    Args:
        page_dir: A page directory holding `groups.json` and `result.json`.

    Returns:
        The number of mismatches found; 0 if the page has not been read yet.

    """
    result_file = page_dir / "result.json"
    if not result_file.is_file():
        return 0
    groups = json.loads((page_dir / "groups.json").read_text())
    result = json.loads(result_file.read_text())
    bad = 0
    for gid, group in result["groups"].items():
        markup = group.get("emphasis_markup")
        if markup is None:
            continue
        stripped = strip_markup(markup)
        stored = groups[gid]["ai_text"]
        if stripped != stored:
            bad += 1
            print(f"MISMATCH {page_dir.name} g{gid}")
            print(f"  stripped={stripped!r}")
            print(f"  stored  ={stored!r}")
    return bad


def main() -> int:
    """Check the out-dir named on the command line, or the pages named after it.

    Returns:
        A process exit status: 1 if any mismatch was found, 0 otherwise.

    """
    if len(sys.argv) < ARGV_WITH_OUT_DIR:
        print(__doc__)
        return 2
    out_dir = Path(sys.argv[1]).expanduser()
    pages = sys.argv[2:] or sorted(p.name for p in out_dir.iterdir() if p.is_dir())
    bad = sum(check_page(out_dir / page) for page in pages)
    print(f"{'FAIL' if bad else 'OK'}: {bad} mismatch(es) over {len(pages)} page(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
